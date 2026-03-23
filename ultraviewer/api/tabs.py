from fastapi import APIRouter, HTTPException
from ultraviewer.db import get_db
from ultraviewer.models import TabCreate, TabUpdate, TabResponse

router = APIRouter(prefix="/api/tabs", tags=["tabs"])

@router.get("", response_model=list[TabResponse])
async def list_tabs():
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM tabs ORDER BY position")
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]

@router.post("", response_model=TabResponse, status_code=201)
async def create_tab(tab: TabCreate):
    async with get_db() as db:
        cursor = await db.execute("INSERT INTO tabs (name, position) VALUES (?, ?)", (tab.name, tab.position))
        tab_id = cursor.lastrowid
        await db.commit()
        cursor = await db.execute("SELECT * FROM tabs WHERE id = ?", (tab_id,))
        row = await cursor.fetchone()
    return dict(row)

@router.put("/{tab_id}", response_model=TabResponse)
async def update_tab(tab_id: int, tab: TabUpdate):
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM tabs WHERE id = ?", (tab_id,))
        existing = await cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Tab not found")
        updates = {}
        if tab.name is not None: updates["name"] = tab.name
        if tab.position is not None: updates["position"] = tab.position
        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [tab_id]
            await db.execute(f"UPDATE tabs SET {set_clause} WHERE id = ?", values)
            await db.commit()
        cursor = await db.execute("SELECT * FROM tabs WHERE id = ?", (tab_id,))
        row = await cursor.fetchone()
    return dict(row)

@router.delete("/{tab_id}", status_code=204)
async def delete_tab(tab_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM tabs WHERE id = ?", (tab_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Tab not found")
        await db.execute("DELETE FROM tabs WHERE id = ?", (tab_id,))
        await db.commit()
