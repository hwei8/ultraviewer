import json
from fastapi import APIRouter, HTTPException
from ultraviewer.db import get_db

router = APIRouter(tags=["results"])

@router.get("/api/suites/{suite_id}/results")
async def get_latest_results(suite_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM suites WHERE id = ?", (suite_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Suite not found")

        cursor = await db.execute(
            """SELECT r.* FROM run_results r
            INNER JOIN (
                SELECT leaf_name, MAX(run_at) as max_run_at
                FROM run_results WHERE suite_id = ?
                GROUP BY leaf_name
            ) latest ON r.leaf_name = latest.leaf_name AND r.run_at = latest.max_run_at
            WHERE r.suite_id = ?
            ORDER BY r.leaf_name""",
            (suite_id, suite_id),
        )
        rows = await cursor.fetchall()

    results = []
    for row in rows:
        r = dict(row)
        r["result_json"] = json.loads(r["result_json"]) if isinstance(r["result_json"], str) else r["result_json"]
        results.append(r)
    return results

@router.get("/api/suites/{suite_id}/results/history")
async def get_run_history(suite_id: int):
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM suites WHERE id = ?", (suite_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Suite not found")

        cursor = await db.execute(
            """SELECT run_at,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as passed,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as errors
            FROM run_results WHERE suite_id = ?
            GROUP BY run_at ORDER BY run_at DESC""",
            (suite_id,),
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]

@router.get("/api/suites/{suite_id}/results/history/{run_at}")
async def get_historical_run(suite_id: int, run_at: str):
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT * FROM run_results
            WHERE suite_id = ? AND run_at = ?
            ORDER BY leaf_name""",
            (suite_id, run_at),
        )
        rows = await cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Run not found")

    results = []
    for row in rows:
        r = dict(row)
        r["result_json"] = json.loads(r["result_json"]) if isinstance(r["result_json"], str) else r["result_json"]
        results.append(r)
    return results

@router.get("/api/suites/{suite_id}/results/{leaf_name}")
async def get_leaf_result(suite_id: int, leaf_name: str):
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT * FROM run_results
            WHERE suite_id = ? AND leaf_name = ?
            ORDER BY run_at DESC LIMIT 1""",
            (suite_id, leaf_name),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Result not found")
    r = dict(row)
    r["result_json"] = json.loads(r["result_json"]) if isinstance(r["result_json"], str) else r["result_json"]
    return r
