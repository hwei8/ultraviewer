import os
from contextlib import asynccontextmanager
import aiosqlite

DEFAULT_DB_PATH = os.path.expanduser("~/.ultraviewer/data.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tabs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tab_id INTEGER NOT NULL REFERENCES tabs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    folder_path TEXT NOT NULL,
    scan_depth INTEGER NOT NULL DEFAULT 1,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suite_scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suite_id INTEGER NOT NULL UNIQUE REFERENCES suites(id) ON DELETE CASCADE,
    interpreter TEXT NOT NULL DEFAULT 'python3',
    script_path TEXT NOT NULL DEFAULT '',
    timeout_seconds INTEGER NOT NULL DEFAULT 30,
    extra_args TEXT NOT NULL DEFAULT '[]',
    env_vars TEXT NOT NULL DEFAULT '[]',
    max_parallel INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS suite_rendering (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suite_id INTEGER NOT NULL UNIQUE REFERENCES suites(id) ON DELETE CASCADE,
    render_mode TEXT NOT NULL DEFAULT 'auto',
    config TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS run_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suite_id INTEGER NOT NULL REFERENCES suites(id) ON DELETE CASCADE,
    leaf_name TEXT NOT NULL,
    leaf_path TEXT NOT NULL,
    result_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    duration_ms INTEGER,
    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_run_results_suite ON run_results(suite_id, run_at);
CREATE INDEX IF NOT EXISTS idx_run_results_leaf ON run_results(suite_id, leaf_name);
"""

def get_db_path() -> str:
    path = os.environ.get("ULTRAVIEWER_DB_PATH", DEFAULT_DB_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

@asynccontextmanager
async def get_db(db_path: str = None):
    path = db_path or get_db_path()
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = aiosqlite.Row
        yield db

async def init_db(db_path: str = None):
    async with get_db(db_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()
