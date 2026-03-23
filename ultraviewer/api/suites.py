import json
from fastapi import APIRouter, HTTPException
from ultraviewer.db import get_db
from ultraviewer.models import (SuiteCreate, SuiteUpdate, SuiteResponse, ScriptConfig, RenderingConfig, LeafNode)
from ultraviewer.scanner import scan_folder

router = APIRouter(tags=["suites"])

async def _get_suite_full(db, suite_id: int) -> dict:
    cursor = await db.execute("SELECT * FROM suites WHERE id = ?", (suite_id,))
    suite = await cursor.fetchone()
    if not suite: return None
    result = dict(suite)
    cursor = await db.execute("SELECT * FROM suite_scripts WHERE suite_id = ?", (suite_id,))
    script_row = await cursor.fetchone()
    if script_row:
        script = dict(script_row)
        script["extra_args"] = json.loads(script["extra_args"])
        script["env_vars"] = json.loads(script["env_vars"])
        result["script"] = script
    else:
        result["script"] = None
    cursor = await db.execute("SELECT * FROM suite_rendering WHERE suite_id = ?", (suite_id,))
    render_row = await cursor.fetchone()
    if render_row:
        render = dict(render_row)
        render["config"] = json.loads(render["config"])
        result["rendering"] = render
    else:
        result["rendering"] = None
    return result

@router.get("/api/tabs/{tab_id}/suites", response_model=list[SuiteResponse])
async def list_suites(tab_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM suites WHERE tab_id = ? ORDER BY position", (tab_id,))
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            full = await _get_suite_full(db, row["id"])
            results.append(full)
    return results

@router.post("/api/tabs/{tab_id}/suites", response_model=SuiteResponse, status_code=201)
async def create_suite(tab_id: int, suite: SuiteCreate):
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM tabs WHERE id = ?", (tab_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Tab not found")
        cursor = await db.execute(
            "INSERT INTO suites (tab_id, name, folder_path, scan_depth, position) VALUES (?, ?, ?, ?, ?)",
            (tab_id, suite.name, suite.folder_path, suite.scan_depth, suite.position))
        suite_id = cursor.lastrowid
        await db.execute("INSERT INTO suite_scripts (suite_id) VALUES (?)", (suite_id,))
        await db.execute("INSERT INTO suite_rendering (suite_id) VALUES (?)", (suite_id,))
        await db.commit()
        result = await _get_suite_full(db, suite_id)
    return result

@router.put("/api/suites/{suite_id}", response_model=SuiteResponse)
async def update_suite(suite_id: int, update: SuiteUpdate):
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM suites WHERE id = ?", (suite_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Suite not found")
        basic_updates = {}
        if update.name is not None: basic_updates["name"] = update.name
        if update.folder_path is not None: basic_updates["folder_path"] = update.folder_path
        if update.scan_depth is not None: basic_updates["scan_depth"] = update.scan_depth
        if update.position is not None: basic_updates["position"] = update.position
        if basic_updates:
            set_clause = ", ".join(f"{k} = ?" for k in basic_updates)
            values = list(basic_updates.values()) + [suite_id]
            await db.execute(f"UPDATE suites SET {set_clause} WHERE id = ?", values)
        if update.script is not None:
            s = update.script
            await db.execute(
                """UPDATE suite_scripts SET interpreter=?, script_path=?, timeout_seconds=?,
                    extra_args=?, env_vars=?, max_parallel=? WHERE suite_id=?""",
                (s.interpreter, s.script_path, s.timeout_seconds,
                 json.dumps(s.extra_args), json.dumps(s.env_vars), s.max_parallel, suite_id))
        if update.rendering is not None:
            r = update.rendering
            await db.execute("UPDATE suite_rendering SET render_mode=?, config=? WHERE suite_id=?",
                (r.render_mode, json.dumps(r.config), suite_id))
        await db.commit()
        result = await _get_suite_full(db, suite_id)
    return result

@router.delete("/api/suites/{suite_id}", status_code=204)
async def delete_suite(suite_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM suites WHERE id = ?", (suite_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Suite not found")
        await db.execute("DELETE FROM suites WHERE id = ?", (suite_id,))
        await db.commit()

@router.get("/api/suites/{suite_id}/leaves", response_model=list[LeafNode])
async def get_leaves(suite_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT folder_path, scan_depth FROM suites WHERE id = ?", (suite_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Suite not found")
    return scan_folder(row["folder_path"], depth=row["scan_depth"])
