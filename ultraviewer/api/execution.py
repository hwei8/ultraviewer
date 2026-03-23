import asyncio
import json
from typing import Optional
from fastapi import APIRouter, Body, HTTPException, WebSocket, WebSocketDisconnect
from ultraviewer.db import get_db
from ultraviewer.runner import run_script
from ultraviewer.scanner import scan_folder

router = APIRouter(tags=["execution"])

async def _get_suite_config(suite_id: int) -> dict:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM suites WHERE id = ?", (suite_id,))
        suite = await cursor.fetchone()
        if not suite:
            return None
        suite = dict(suite)

        cursor = await db.execute("SELECT * FROM suite_scripts WHERE suite_id = ?", (suite_id,))
        script_row = await cursor.fetchone()
        suite["script"] = dict(script_row) if script_row else None
    return suite

async def _run_leaf(suite_config: dict, leaf: dict) -> dict:
    script = suite_config["script"]
    extra_args = json.loads(script["extra_args"]) if isinstance(script["extra_args"], str) else script["extra_args"]
    env_vars = json.loads(script["env_vars"]) if isinstance(script["env_vars"], str) else script["env_vars"]

    result = await run_script(
        interpreter=script["interpreter"],
        script_path=script["script_path"],
        leaf_path=leaf["path"],
        extra_args=extra_args,
        env_vars=env_vars,
        timeout=script["timeout_seconds"],
    )

    async with get_db() as db:
        await db.execute(
            """INSERT INTO run_results
                (suite_id, leaf_name, leaf_path, result_json, status, error_message, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                suite_config["id"],
                leaf["name"],
                leaf["path"],
                json.dumps(result.get("result", {})),
                result["status"],
                result.get("error_message"),
                result.get("duration_ms"),
            ),
        )
        await db.commit()

    return {
        "leaf": leaf["name"],
        "status": result["status"],
        "result": result.get("result", {}),
        "error_message": result.get("error_message"),
        "duration_ms": result.get("duration_ms"),
    }

@router.post("/api/suites/{suite_id}/run")
async def run_suite(suite_id: int):
    config = await _get_suite_config(suite_id)
    if not config:
        raise HTTPException(status_code=404, detail="Suite not found")
    if not config["script"] or not config["script"]["script_path"]:
        raise HTTPException(status_code=400, detail="No script configured")

    leaves = scan_folder(config["folder_path"], depth=config["scan_depth"])
    if not leaves:
        raise HTTPException(status_code=400, detail="No leaf nodes found")

    max_parallel = config["script"].get("max_parallel", 1)
    if isinstance(max_parallel, str):
        max_parallel = int(max_parallel)

    results = []
    if max_parallel <= 1:
        for leaf in leaves:
            r = await _run_leaf(config, leaf)
            results.append(r)
    else:
        sem = asyncio.Semaphore(max_parallel)
        async def run_with_sem(leaf):
            async with sem:
                return await _run_leaf(config, leaf)
        results = await asyncio.gather(*[run_with_sem(leaf) for leaf in leaves])
        results = list(results)

    passed = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")
    timeouts = sum(1 for r in results if r["status"] == "timeout")

    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "errors": timeouts,
        "results": results,
    }

@router.post("/api/suites/{suite_id}/run-selected")
async def run_selected_leaves(suite_id: int, leaf_names: list[str] = Body(...)):
    config = await _get_suite_config(suite_id)
    if not config:
        raise HTTPException(status_code=404, detail="Suite not found")
    if not config["script"] or not config["script"]["script_path"]:
        raise HTTPException(status_code=400, detail="No script configured")
    if not leaf_names:
        raise HTTPException(status_code=400, detail="No leaves selected")

    all_leaves = scan_folder(config["folder_path"], depth=config["scan_depth"])
    leaves_by_name = {l["name"]: l for l in all_leaves}
    missing = [n for n in leaf_names if n not in leaves_by_name]
    if missing:
        raise HTTPException(status_code=404, detail=f"Leaves not found: {', '.join(missing)}")

    selected = [leaves_by_name[n] for n in leaf_names]

    max_parallel = config["script"].get("max_parallel", 1)
    if isinstance(max_parallel, str):
        max_parallel = int(max_parallel)

    results = []
    if max_parallel <= 1:
        for leaf in selected:
            r = await _run_leaf(config, leaf)
            results.append(r)
    else:
        sem = asyncio.Semaphore(max_parallel)
        async def run_with_sem(leaf):
            async with sem:
                return await _run_leaf(config, leaf)
        results = list(await asyncio.gather(*[run_with_sem(leaf) for leaf in selected]))

    passed = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")
    timeouts = sum(1 for r in results if r["status"] == "timeout")

    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "errors": timeouts,
        "results": results,
    }

@router.post("/api/suites/{suite_id}/run/{leaf_name}")
async def run_single_leaf(suite_id: int, leaf_name: str):
    config = await _get_suite_config(suite_id)
    if not config:
        raise HTTPException(status_code=404, detail="Suite not found")
    if not config["script"] or not config["script"]["script_path"]:
        raise HTTPException(status_code=400, detail="No script configured")

    leaves = scan_folder(config["folder_path"], depth=config["scan_depth"])
    leaf = next((l for l in leaves if l["name"] == leaf_name), None)
    if not leaf:
        raise HTTPException(status_code=404, detail=f"Leaf '{leaf_name}' not found")

    return await _run_leaf(config, leaf)

@router.post("/api/suites/{suite_id}/test-script")
async def test_script(suite_id: int):
    config = await _get_suite_config(suite_id)
    if not config:
        raise HTTPException(status_code=404, detail="Suite not found")
    if not config["script"] or not config["script"]["script_path"]:
        raise HTTPException(status_code=400, detail="No script configured")

    leaves = scan_folder(config["folder_path"], depth=config["scan_depth"])
    if not leaves:
        raise HTTPException(status_code=400, detail="No leaf nodes found")

    return await _run_leaf(config, leaves[0])

@router.websocket("/ws/execution/{suite_id}")
async def ws_execution(websocket: WebSocket, suite_id: int):
    await websocket.accept()
    try:
        config = await _get_suite_config(suite_id)
        if not config or not config["script"]:
            await websocket.send_json({"event": "error", "message": "Suite not found or not configured"})
            await websocket.close()
            return

        leaves = scan_folder(config["folder_path"], depth=config["scan_depth"])
        await websocket.send_json({"event": "run_started", "total": len(leaves)})

        passed = 0
        failed = 0
        errors = 0

        for leaf in leaves:
            await websocket.send_json({"event": "leaf_started", "leaf": leaf["name"]})
            result = await _run_leaf(config, leaf)

            if result["status"] == "success":
                passed += 1
                await websocket.send_json({
                    "event": "leaf_completed",
                    "leaf": leaf["name"],
                    "status": "success",
                    "duration_ms": result.get("duration_ms"),
                })
            else:
                if result["status"] == "timeout":
                    errors += 1
                else:
                    failed += 1
                await websocket.send_json({
                    "event": "leaf_error",
                    "leaf": leaf["name"],
                    "error": result.get("error_message", "Unknown error"),
                })

        await websocket.send_json({
            "event": "run_completed",
            "passed": passed,
            "failed": failed,
            "errors": errors,
        })
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
