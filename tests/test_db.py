import pytest
from ultraviewer.db import get_db, init_db

@pytest.mark.asyncio
async def test_init_db_creates_tables(tmp_db):
    await init_db(tmp_db)
    async with get_db(tmp_db) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in await cursor.fetchall()]
    assert "tabs" in tables
    assert "suites" in tables
    assert "suite_scripts" in tables
    assert "suite_rendering" in tables
    assert "run_results" in tables

@pytest.mark.asyncio
async def test_cascade_delete_tab(tmp_db):
    await init_db(tmp_db)
    async with get_db(tmp_db) as db:
        await db.execute("INSERT INTO tabs (name, position) VALUES ('test', 0)")
        cursor = await db.execute("SELECT last_insert_rowid()")
        tab_id = (await cursor.fetchone())[0]
        await db.execute(
            "INSERT INTO suites (tab_id, name, folder_path, position) VALUES (?, 'suite', '/tmp', 0)",
            (tab_id,),
        )
        await db.commit()
        await db.execute("DELETE FROM tabs WHERE id = ?", (tab_id,))
        await db.commit()
        cursor = await db.execute("SELECT COUNT(*) FROM suites WHERE tab_id = ?", (tab_id,))
        count = (await cursor.fetchone())[0]
    assert count == 0
