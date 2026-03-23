# UltraViewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a universal folder-based dashboard that scans directories, runs scripts against subfolders, and renders structured results — with FastAPI backend and Vue 3 frontend, fully offline-capable.

**Architecture:** FastAPI serves both the REST API and static Vue 3 frontend from a single process. SQLite stores all configuration and results. Scripts are executed via subprocess. WebSocket pushes live progress to the browser.

**Tech Stack:** Python 3, FastAPI, uvicorn, aiosqlite, SQLite, Vue 3 (CDN bundle), WebSocket

---

## File Map

### Backend
| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Package config, dependencies, CLI entry point |
| `ultraviewer/__init__.py` | Package marker |
| `ultraviewer/main.py` | FastAPI app factory, static file mount, CLI entry point |
| `ultraviewer/db.py` | SQLite connection, schema creation, migrations |
| `ultraviewer/models.py` | Pydantic request/response models |
| `ultraviewer/scanner.py` | Scan a folder path to discover subfolders at configurable depth |
| `ultraviewer/runner.py` | Execute scripts via subprocess with timeout, env vars, args |
| `ultraviewer/api/tabs.py` | Tab CRUD endpoints |
| `ultraviewer/api/suites.py` | Suite CRUD + settings endpoints |
| `ultraviewer/api/execution.py` | Run suite/leaf, WebSocket progress, cancel |
| `ultraviewer/api/results.py` | Query results, history |

### Frontend
| File | Responsibility |
|------|---------------|
| `ultraviewer/static/index.html` | Single HTML page, loads Vue + app |
| `ultraviewer/static/vue.global.prod.js` | Vue 3 runtime (downloaded once) |
| `ultraviewer/static/style.css` | All application styles |
| `ultraviewer/static/app.js` | Vue app init, router, global state |
| `ultraviewer/static/components/TabBar.js` | Tab bar: create, rename, reorder, delete |
| `ultraviewer/static/components/TreeView.js` | Tree panel: suites, leaves, expand/collapse |
| `ultraviewer/static/components/ContentPanel.js` | Content area: dispatches to settings or renderers |
| `ultraviewer/static/components/SuiteSettings.js` | Suite config form: basic, script, context, rendering |
| `ultraviewer/static/components/renderers/TableRenderer.js` | Render JSON as table |
| `ultraviewer/static/components/renderers/DiffRenderer.js` | Render file diffs side-by-side |
| `ultraviewer/static/components/renderers/HtmlRenderer.js` | Render raw HTML in sandboxed container |
| `ultraviewer/static/components/renderers/SectionsRenderer.js` | Render mixed sections (delegates to other renderers) |

### Tests
| File | Responsibility |
|------|---------------|
| `tests/conftest.py` | Shared fixtures: test client, temp DB, temp folders |
| `tests/test_db.py` | Database schema and migration tests |
| `tests/test_scanner.py` | Folder scanning logic tests |
| `tests/test_runner.py` | Script execution tests |
| `tests/test_api_tabs.py` | Tab API endpoint tests |
| `tests/test_api_suites.py` | Suite API endpoint tests |
| `tests/test_api_execution.py` | Execution and WebSocket tests |
| `tests/test_api_results.py` | Results query tests |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `ultraviewer/__init__.py`
- Create: `ultraviewer/main.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "ultraviewer"
version = "0.1.0"
description = "Universal folder-based dashboard for script execution and result visualization"
requires-python = ">=3.8"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.20.0",
    "websockets>=11.0",
    "aiosqlite>=0.19.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.24.0",
]

[project.scripts]
ultraviewer = "ultraviewer.main:cli"
```

- [ ] **Step 2: Create ultraviewer/__init__.py**

```python
"""UltraViewer — Universal folder-based dashboard."""
```

- [ ] **Step 3: Create ultraviewer/main.py with minimal FastAPI app**

```python
import argparse
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

def create_app() -> FastAPI:
    app = FastAPI(title="UltraViewer")

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app

app = create_app()

def cli():
    parser = argparse.ArgumentParser(description="UltraViewer Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--db-path", type=str, default=None, help="SQLite database path")
    args = parser.parse_args()

    if args.db_path:
        os.environ["ULTRAVIEWER_DB_PATH"] = args.db_path

    uvicorn.run("ultraviewer.main:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: Create tests/conftest.py with shared fixtures**

```python
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    os.environ["ULTRAVIEWER_DB_PATH"] = db_path
    yield db_path
    os.environ.pop("ULTRAVIEWER_DB_PATH", None)

@pytest.fixture
def client(tmp_db):
    from ultraviewer.main import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c

@pytest.fixture
def sample_folders(tmp_path):
    """Create a sample folder structure for testing."""
    root = tmp_path / "suite_root"
    root.mkdir()
    for name in ["case_1", "case_2", "case_3"]:
        (root / name).mkdir()
        (root / name / "data.txt").write_text(f"data for {name}")
    return root
```

- [ ] **Step 5: Verify project installs**

Run: `cd /home/he/ultraviewer && pip install --user -e ".[dev]"`
Expected: successful install

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml ultraviewer/__init__.py ultraviewer/main.py tests/conftest.py
git commit -m "feat: project scaffolding with FastAPI app and test fixtures"
```

---

## Task 2: Database Layer

**Files:**
- Create: `ultraviewer/db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write failing test for database initialization**

```python
# tests/test_db.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL — module `ultraviewer.db` not found

- [ ] **Step 3: Implement db.py**

```python
# ultraviewer/db.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_db.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add ultraviewer/db.py tests/test_db.py
git commit -m "feat: SQLite database layer with schema and cascade deletes"
```

---

## Task 3: Pydantic Models

**Files:**
- Create: `ultraviewer/models.py`

- [ ] **Step 1: Create models.py**

```python
# ultraviewer/models.py
from typing import Optional
from pydantic import BaseModel

# --- Tabs ---
class TabCreate(BaseModel):
    name: str
    position: int = 0

class TabUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None

class TabResponse(BaseModel):
    id: int
    name: str
    position: int
    created_at: str

# --- Suites ---
class SuiteCreate(BaseModel):
    name: str
    folder_path: str
    scan_depth: int = 1
    position: int = 0

class ScriptConfig(BaseModel):
    interpreter: str = "python3"
    script_path: str = ""
    timeout_seconds: int = 30
    extra_args: list[dict] = []
    env_vars: list[dict] = []
    max_parallel: int = 1

class RenderingConfig(BaseModel):
    render_mode: str = "auto"
    config: dict = {}

class SuiteUpdate(BaseModel):
    name: Optional[str] = None
    folder_path: Optional[str] = None
    scan_depth: Optional[int] = None
    position: Optional[int] = None
    script: Optional[ScriptConfig] = None
    rendering: Optional[RenderingConfig] = None

class SuiteResponse(BaseModel):
    id: int
    tab_id: int
    name: str
    folder_path: str
    scan_depth: int
    position: int
    created_at: str
    script: Optional[ScriptConfig] = None
    rendering: Optional[RenderingConfig] = None

# --- Leaves ---
class LeafNode(BaseModel):
    name: str
    path: str

# --- Results ---
class RunResult(BaseModel):
    id: int
    suite_id: int
    leaf_name: str
    leaf_path: str
    result_json: dict
    status: str
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    run_at: str

class RunSummary(BaseModel):
    run_at: str
    total: int
    passed: int
    failed: int
    errors: int
```

- [ ] **Step 2: Verify models import cleanly**

Run: `python -c "from ultraviewer.models import *; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add ultraviewer/models.py
git commit -m "feat: Pydantic request/response models"
```

---

## Task 4: Folder Scanner

**Files:**
- Create: `ultraviewer/scanner.py`
- Create: `tests/test_scanner.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_scanner.py
import os
from ultraviewer.scanner import scan_folder

def test_scan_depth_1(sample_folders):
    leaves = scan_folder(str(sample_folders), depth=1)
    names = [l["name"] for l in leaves]
    assert sorted(names) == ["case_1", "case_2", "case_3"]
    for leaf in leaves:
        assert os.path.isabs(leaf["path"])

def test_scan_depth_2(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a").mkdir()
    (root / "a" / "sub1").mkdir()
    (root / "a" / "sub2").mkdir()
    (root / "b").mkdir()

    leaves = scan_folder(str(root), depth=2)
    names = [l["name"] for l in leaves]
    assert "sub1" in names
    assert "sub2" in names
    assert "b" in names

def test_scan_nonexistent_path():
    leaves = scan_folder("/nonexistent/path", depth=1)
    assert leaves == []

def test_scan_empty_folder(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    leaves = scan_folder(str(empty), depth=1)
    assert leaves == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_scanner.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement scanner.py**

```python
# ultraviewer/scanner.py
import os

def scan_folder(folder_path: str, depth: int = 1) -> list[dict]:
    """Scan a folder and return subfolders as leaf nodes."""
    if not os.path.isdir(folder_path):
        return []

    if depth <= 0:
        return []

    results = []
    try:
        entries = sorted(os.listdir(folder_path))
    except PermissionError:
        return []

    for entry in entries:
        full_path = os.path.join(folder_path, entry)
        if not os.path.isdir(full_path):
            continue

        if depth == 1:
            results.append({
                "name": entry,
                "path": os.path.abspath(full_path),
            })
        else:
            sub_leaves = scan_folder(full_path, depth - 1)
            if sub_leaves:
                results.extend(sub_leaves)
            else:
                results.append({
                    "name": entry,
                    "path": os.path.abspath(full_path),
                })

    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_scanner.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add ultraviewer/scanner.py tests/test_scanner.py
git commit -m "feat: folder scanner with configurable depth"
```

---

## Task 5: Script Runner

**Files:**
- Create: `ultraviewer/runner.py`
- Create: `tests/test_runner.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_runner.py
import os
import json
import pytest
from ultraviewer.runner import run_script

@pytest.mark.asyncio
async def test_run_script_success(tmp_path):
    script = tmp_path / "test.sh"
    script.write_text('#!/bin/bash\necho \'{"status": "pass", "name": "test"}\'')
    script.chmod(0o755)

    result = await run_script(
        interpreter="bash",
        script_path=str(script),
        leaf_path=str(tmp_path),
        extra_args=[],
        env_vars=[],
        timeout=10,
    )
    assert result["status"] == "success"
    assert result["result"]["status"] == "pass"

@pytest.mark.asyncio
async def test_run_script_timeout(tmp_path):
    script = tmp_path / "slow.sh"
    script.write_text('#!/bin/bash\nsleep 10\necho "{}"')
    script.chmod(0o755)

    result = await run_script(
        interpreter="bash",
        script_path=str(script),
        leaf_path=str(tmp_path),
        extra_args=[],
        env_vars=[],
        timeout=1,
    )
    assert result["status"] == "timeout"

@pytest.mark.asyncio
async def test_run_script_nonzero_exit(tmp_path):
    script = tmp_path / "fail.sh"
    script.write_text('#!/bin/bash\necho "something went wrong" >&2\nexit 1')
    script.chmod(0o755)

    result = await run_script(
        interpreter="bash",
        script_path=str(script),
        leaf_path=str(tmp_path),
        extra_args=[],
        env_vars=[],
        timeout=10,
    )
    assert result["status"] == "error"
    assert "something went wrong" in result["error_message"]

@pytest.mark.asyncio
async def test_run_script_invalid_json(tmp_path):
    script = tmp_path / "bad.sh"
    script.write_text('#!/bin/bash\necho "not json"')
    script.chmod(0o755)

    result = await run_script(
        interpreter="bash",
        script_path=str(script),
        leaf_path=str(tmp_path),
        extra_args=[],
        env_vars=[],
        timeout=10,
    )
    assert result["status"] == "error"
    assert "not json" in result.get("raw_stdout", "") or "JSON" in result.get("error_message", "")

@pytest.mark.asyncio
async def test_run_script_with_extra_args(tmp_path):
    script = tmp_path / "args.sh"
    script.write_text('#!/bin/bash\necho "{\\\"args\\\": \\\"$@\\\"}"')
    script.chmod(0o755)

    result = await run_script(
        interpreter="bash",
        script_path=str(script),
        leaf_path=str(tmp_path),
        extra_args=[{"key": "--golden", "value": "/data/golden"}],
        env_vars=[],
        timeout=10,
    )
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_run_script_with_env_vars(tmp_path):
    script = tmp_path / "env.sh"
    script.write_text('#!/bin/bash\necho "{\\\"module\\\": \\\"$MODULE_NAME\\\"}"')
    script.chmod(0o755)

    result = await run_script(
        interpreter="bash",
        script_path=str(script),
        leaf_path=str(tmp_path),
        extra_args=[],
        env_vars=[{"key": "MODULE_NAME", "value": "login"}],
        timeout=10,
    )
    assert result["status"] == "success"
    assert result["result"]["module"] == "login"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_runner.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement runner.py**

```python
# ultraviewer/runner.py
import asyncio
import json
import os
import time

async def run_script(
    interpreter: str,
    script_path: str,
    leaf_path: str,
    extra_args: list[dict],
    env_vars: list[dict],
    timeout: int,
) -> dict:
    """Execute a script against a leaf folder and return the result."""

    cmd = [interpreter, script_path, leaf_path]
    for arg in extra_args:
        cmd.append(arg["key"])
        if arg.get("value"):
            cmd.append(arg["value"])

    env = os.environ.copy()
    for var in env_vars:
        env[var["key"]] = var["value"]

    start = time.monotonic()

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            duration_ms = int((time.monotonic() - start) * 1000)
            return {
                "status": "timeout",
                "error_message": f"Timed out after {timeout}s",
                "duration_ms": duration_ms,
                "result": {},
            }

        duration_ms = int((time.monotonic() - start) * 1000)
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        if proc.returncode != 0:
            return {
                "status": "error",
                "error_message": stderr_text or f"Exit code {proc.returncode}",
                "raw_stdout": stdout_text,
                "duration_ms": duration_ms,
                "result": {},
            }

        try:
            parsed = json.loads(stdout_text)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "error_message": f"Invalid JSON output",
                "raw_stdout": stdout_text,
                "duration_ms": duration_ms,
                "result": {},
            }

        return {
            "status": "success",
            "result": parsed,
            "duration_ms": duration_ms,
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "error_message": f"Script not found: {script_path}",
            "duration_ms": 0,
            "result": {},
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_runner.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add ultraviewer/runner.py tests/test_runner.py
git commit -m "feat: async script runner with timeout, env vars, and error handling"
```

---

## Task 6: Tab API Endpoints

**Files:**
- Create: `ultraviewer/api/__init__.py`
- Create: `ultraviewer/api/tabs.py`
- Create: `tests/test_api_tabs.py`
- Modify: `ultraviewer/main.py` (register router, init DB on startup)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_api_tabs.py
import pytest
from fastapi.testclient import TestClient

def test_create_tab(client):
    resp = client.post("/api/tabs", json={"name": "Smoke Tests"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Smoke Tests"
    assert "id" in data

def test_list_tabs(client):
    client.post("/api/tabs", json={"name": "Tab A", "position": 0})
    client.post("/api/tabs", json={"name": "Tab B", "position": 1})
    resp = client.get("/api/tabs")
    assert resp.status_code == 200
    tabs = resp.json()
    assert len(tabs) == 2
    assert tabs[0]["name"] == "Tab A"

def test_update_tab(client):
    resp = client.post("/api/tabs", json={"name": "Old Name"})
    tab_id = resp.json()["id"]
    resp = client.put(f"/api/tabs/{tab_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"

def test_delete_tab(client):
    resp = client.post("/api/tabs", json={"name": "To Delete"})
    tab_id = resp.json()["id"]
    resp = client.delete(f"/api/tabs/{tab_id}")
    assert resp.status_code == 204
    resp = client.get("/api/tabs")
    assert len(resp.json()) == 0

def test_delete_nonexistent_tab(client):
    resp = client.delete("/api/tabs/999")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_tabs.py -v`
Expected: FAIL

- [ ] **Step 3: Create api/__init__.py**

```python
# ultraviewer/api/__init__.py
```

- [ ] **Step 4: Implement api/tabs.py**

```python
# ultraviewer/api/tabs.py
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
        cursor = await db.execute(
            "INSERT INTO tabs (name, position) VALUES (?, ?)",
            (tab.name, tab.position),
        )
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
        if tab.name is not None:
            updates["name"] = tab.name
        if tab.position is not None:
            updates["position"] = tab.position

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
```

- [ ] **Step 5: Update main.py to register router and init DB**

```python
# ultraviewer/main.py
import argparse
import asyncio
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from ultraviewer.db import init_db
from ultraviewer.api.tabs import router as tabs_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

def create_app() -> FastAPI:
    app = FastAPI(title="UltraViewer", lifespan=lifespan)

    app.include_router(tabs_router)

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app

app = create_app()

def cli():
    parser = argparse.ArgumentParser(description="UltraViewer Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--db-path", type=str, default=None, help="SQLite database path")
    args = parser.parse_args()

    if args.db_path:
        os.environ["ULTRAVIEWER_DB_PATH"] = args.db_path

    uvicorn.run("ultraviewer.main:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    cli()
```

- [ ] **Step 6: Update tests/conftest.py to use lifespan**

```python
# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    os.environ["ULTRAVIEWER_DB_PATH"] = db_path
    yield db_path
    os.environ.pop("ULTRAVIEWER_DB_PATH", None)

@pytest.fixture
def client(tmp_db):
    from ultraviewer.main import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c

@pytest.fixture
def sample_folders(tmp_path):
    root = tmp_path / "suite_root"
    root.mkdir()
    for name in ["case_1", "case_2", "case_3"]:
        (root / name).mkdir()
        (root / name / "data.txt").write_text(f"data for {name}")
    return root
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/test_api_tabs.py -v`
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add ultraviewer/api/__init__.py ultraviewer/api/tabs.py ultraviewer/main.py tests/conftest.py tests/test_api_tabs.py
git commit -m "feat: tab CRUD API endpoints"
```

---

## Task 7: Suite API Endpoints

**Files:**
- Create: `ultraviewer/api/suites.py`
- Create: `tests/test_api_suites.py`
- Modify: `ultraviewer/main.py` (register suites router)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_api_suites.py
import pytest

@pytest.fixture
def tab_id(client):
    resp = client.post("/api/tabs", json={"name": "Test Tab"})
    return resp.json()["id"]

def test_create_suite(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={
        "name": "Login Module",
        "folder_path": str(sample_folders),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Login Module"
    assert data["folder_path"] == str(sample_folders)

def test_list_suites(client, tab_id, sample_folders):
    client.post(f"/api/tabs/{tab_id}/suites", json={"name": "A", "folder_path": str(sample_folders)})
    client.post(f"/api/tabs/{tab_id}/suites", json={"name": "B", "folder_path": str(sample_folders)})
    resp = client.get(f"/api/tabs/{tab_id}/suites")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

def test_update_suite_basic(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={"name": "Old", "folder_path": str(sample_folders)})
    suite_id = resp.json()["id"]
    resp = client.put(f"/api/suites/{suite_id}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"

def test_update_suite_script(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={"name": "S", "folder_path": str(sample_folders)})
    suite_id = resp.json()["id"]
    resp = client.put(f"/api/suites/{suite_id}", json={
        "script": {
            "interpreter": "bash",
            "script_path": "/scripts/run.sh",
            "timeout_seconds": 60,
            "extra_args": [{"key": "--golden", "value": "/golden"}],
            "env_vars": [{"key": "MODE", "value": "test"}],
            "max_parallel": 4,
        }
    })
    assert resp.status_code == 200
    assert resp.json()["script"]["interpreter"] == "bash"
    assert resp.json()["script"]["max_parallel"] == 4

def test_update_suite_rendering(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={"name": "S", "folder_path": str(sample_folders)})
    suite_id = resp.json()["id"]
    resp = client.put(f"/api/suites/{suite_id}", json={
        "rendering": {"render_mode": "table", "config": {"columns": ["name", "status"]}}
    })
    assert resp.status_code == 200
    assert resp.json()["rendering"]["render_mode"] == "table"

def test_delete_suite(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={"name": "X", "folder_path": str(sample_folders)})
    suite_id = resp.json()["id"]
    resp = client.delete(f"/api/suites/{suite_id}")
    assert resp.status_code == 204

def test_get_leaves(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={
        "name": "S", "folder_path": str(sample_folders),
    })
    suite_id = resp.json()["id"]
    resp = client.get(f"/api/suites/{suite_id}/leaves")
    assert resp.status_code == 200
    leaves = resp.json()
    assert len(leaves) == 3
    names = [l["name"] for l in leaves]
    assert sorted(names) == ["case_1", "case_2", "case_3"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_suites.py -v`
Expected: FAIL

- [ ] **Step 3: Implement api/suites.py**

```python
# ultraviewer/api/suites.py
import json
from fastapi import APIRouter, HTTPException
from ultraviewer.db import get_db
from ultraviewer.models import (
    SuiteCreate, SuiteUpdate, SuiteResponse, ScriptConfig, RenderingConfig, LeafNode,
)
from ultraviewer.scanner import scan_folder

router = APIRouter(tags=["suites"])

async def _get_suite_full(db, suite_id: int) -> dict:
    cursor = await db.execute("SELECT * FROM suites WHERE id = ?", (suite_id,))
    suite = await cursor.fetchone()
    if not suite:
        return None
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
        cursor = await db.execute(
            "SELECT * FROM suites WHERE tab_id = ? ORDER BY position", (tab_id,)
        )
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
            (tab_id, suite.name, suite.folder_path, suite.scan_depth, suite.position),
        )
        suite_id = cursor.lastrowid

        await db.execute(
            "INSERT INTO suite_scripts (suite_id) VALUES (?)", (suite_id,)
        )
        await db.execute(
            "INSERT INTO suite_rendering (suite_id) VALUES (?)", (suite_id,)
        )
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
        if update.name is not None:
            basic_updates["name"] = update.name
        if update.folder_path is not None:
            basic_updates["folder_path"] = update.folder_path
        if update.scan_depth is not None:
            basic_updates["scan_depth"] = update.scan_depth
        if update.position is not None:
            basic_updates["position"] = update.position

        if basic_updates:
            set_clause = ", ".join(f"{k} = ?" for k in basic_updates)
            values = list(basic_updates.values()) + [suite_id]
            await db.execute(f"UPDATE suites SET {set_clause} WHERE id = ?", values)

        if update.script is not None:
            s = update.script
            await db.execute(
                """UPDATE suite_scripts SET
                    interpreter = ?, script_path = ?, timeout_seconds = ?,
                    extra_args = ?, env_vars = ?, max_parallel = ?
                WHERE suite_id = ?""",
                (
                    s.interpreter, s.script_path, s.timeout_seconds,
                    json.dumps(s.extra_args), json.dumps(s.env_vars),
                    s.max_parallel, suite_id,
                ),
            )

        if update.rendering is not None:
            r = update.rendering
            await db.execute(
                "UPDATE suite_rendering SET render_mode = ?, config = ? WHERE suite_id = ?",
                (r.render_mode, json.dumps(r.config), suite_id),
            )

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
        cursor = await db.execute(
            "SELECT folder_path, scan_depth FROM suites WHERE id = ?", (suite_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Suite not found")
    return scan_folder(row["folder_path"], depth=row["scan_depth"])
```

- [ ] **Step 4: Register suites router in main.py**

Add to `create_app()` in `ultraviewer/main.py`:
```python
from ultraviewer.api.suites import router as suites_router
# ...
app.include_router(suites_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_api_suites.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add ultraviewer/api/suites.py ultraviewer/main.py tests/test_api_suites.py
git commit -m "feat: suite CRUD API with settings and leaf scanning"
```

---

## Task 8: Execution API & WebSocket

**Files:**
- Create: `ultraviewer/api/execution.py`
- Create: `tests/test_api_execution.py`
- Modify: `ultraviewer/main.py` (register execution router)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_api_execution.py
import json
import pytest

@pytest.fixture
def configured_suite(client, sample_folders, tmp_path):
    """Create a tab + suite with a working script."""
    script = tmp_path / "script.sh"
    script.write_text(
        '#!/bin/bash\n'
        'FOLDER="$1"\n'
        'NAME=$(basename "$FOLDER")\n'
        'echo "{\\\"name\\\": \\\"$NAME\\\", \\\"status\\\": \\\"pass\\\"}"'
    )
    script.chmod(0o755)

    resp = client.post("/api/tabs", json={"name": "Test"})
    tab_id = resp.json()["id"]

    resp = client.post(f"/api/tabs/{tab_id}/suites", json={
        "name": "Suite", "folder_path": str(sample_folders),
    })
    suite_id = resp.json()["id"]

    client.put(f"/api/suites/{suite_id}", json={
        "script": {
            "interpreter": "bash",
            "script_path": str(script),
            "timeout_seconds": 10,
        }
    })
    return suite_id

def test_run_suite(client, configured_suite):
    resp = client.post(f"/api/suites/{configured_suite}/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["passed"] == 3

def test_run_single_leaf(client, configured_suite):
    resp = client.post(f"/api/suites/{configured_suite}/run/case_1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["result"]["name"] == "case_1"

def test_run_nonexistent_suite(client):
    resp = client.post("/api/suites/999/run")
    assert resp.status_code == 404

def test_test_script(client, configured_suite):
    resp = client.post(f"/api/suites/{configured_suite}/test-script")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_execution.py -v`
Expected: FAIL

- [ ] **Step 3: Implement api/execution.py**

```python
# ultraviewer/api/execution.py
import asyncio
import json
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
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
```

- [ ] **Step 4: Register execution router in main.py**

Add to `create_app()`:
```python
from ultraviewer.api.execution import router as execution_router
# ...
app.include_router(execution_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_api_execution.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add ultraviewer/api/execution.py ultraviewer/main.py tests/test_api_execution.py
git commit -m "feat: execution API with parallel support and WebSocket progress"
```

---

## Task 9: Results API

**Files:**
- Create: `ultraviewer/api/results.py`
- Create: `tests/test_api_results.py`
- Modify: `ultraviewer/main.py` (register results router)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_api_results.py
import pytest

@pytest.fixture
def configured_suite(client, sample_folders, tmp_path):
    """Create a tab + suite with a working script."""
    script = tmp_path / "script.sh"
    script.write_text(
        '#!/bin/bash\n'
        'FOLDER="$1"\n'
        'NAME=$(basename "$FOLDER")\n'
        'echo "{\\\"name\\\": \\\"$NAME\\\", \\\"status\\\": \\\"pass\\\"}"'
    )
    script.chmod(0o755)
    resp = client.post("/api/tabs", json={"name": "Test"})
    tab_id = resp.json()["id"]
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={
        "name": "Suite", "folder_path": str(sample_folders),
    })
    suite_id = resp.json()["id"]
    client.put(f"/api/suites/{suite_id}", json={
        "script": {"interpreter": "bash", "script_path": str(script), "timeout_seconds": 10}
    })
    return suite_id

@pytest.fixture
def suite_with_results(client, configured_suite):
    """Run a suite to populate results."""
    client.post(f"/api/suites/{configured_suite}/run")
    return configured_suite

def test_get_latest_results(client, suite_with_results):
    resp = client.get(f"/api/suites/{suite_with_results}/results")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 3

def test_get_leaf_result(client, suite_with_results):
    resp = client.get(f"/api/suites/{suite_with_results}/results/case_1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["leaf_name"] == "case_1"
    assert data["status"] == "success"

def test_get_history(client, suite_with_results):
    # Run again to create second run
    client.post(f"/api/suites/{suite_with_results}/run")
    resp = client.get(f"/api/suites/{suite_with_results}/results/history")
    assert resp.status_code == 200
    runs = resp.json()
    assert len(runs) >= 2

def test_get_nonexistent_results(client):
    resp = client.get("/api/suites/999/results")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_results.py -v`
Expected: FAIL

- [ ] **Step 3: Implement api/results.py**

```python
# ultraviewer/api/results.py
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
```

- [ ] **Step 4: Register results router in main.py**

Add to `create_app()`:
```python
from ultraviewer.api.results import router as results_router
# ...
app.include_router(results_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_api_results.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add ultraviewer/api/results.py ultraviewer/main.py tests/test_api_results.py
git commit -m "feat: results API with history and per-leaf queries"
```

---

## Task 10: Download Vue 3 & Create index.html

**Files:**
- Create: `ultraviewer/static/index.html`
- Download: `ultraviewer/static/vue.global.prod.js`

- [ ] **Step 1: Download Vue 3 production build**

Run: `curl -o ultraviewer/static/vue.global.prod.js https://unpkg.com/vue@3/dist/vue.global.prod.js`
Expected: file downloaded (~130KB)

- [ ] **Step 2: Create index.html**

```html
<!-- ultraviewer/static/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UltraViewer</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div id="app">
        <tab-bar
            :tabs="tabs"
            :active-tab-id="activeTabId"
            @select="selectTab"
            @create="createTab"
            @rename="renameTab"
            @delete="deleteTab"
        ></tab-bar>
        <div class="main-content">
            <tree-view
                :suites="suites"
                :selected-node="selectedNode"
                @select-suite="selectSuite"
                @select-leaf="selectLeaf"
                @create-suite="createSuiteDialog"
                @run-suite="runSuite"
                @run-leaf="runLeaf"
            ></tree-view>
            <content-panel
                :selected-node="selectedNode"
                :suite-data="selectedSuiteData"
                :leaf-result="selectedLeafResult"
                :running="isRunning"
                :progress="runProgress"
                @save-settings="saveSuiteSettings"
                @run-suite="runSuite"
                @test-script="testScript"
            ></content-panel>
        </div>
    </div>

    <script src="/static/vue.global.prod.js"></script>
    <script src="/static/components/renderers/TableRenderer.js"></script>
    <script src="/static/components/renderers/DiffRenderer.js"></script>
    <script src="/static/components/renderers/HtmlRenderer.js"></script>
    <script src="/static/components/renderers/SectionsRenderer.js"></script>
    <script src="/static/components/TabBar.js"></script>
    <script src="/static/components/TreeView.js"></script>
    <script src="/static/components/SuiteSettings.js"></script>
    <script src="/static/components/ContentPanel.js"></script>
    <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add ultraviewer/static/index.html ultraviewer/static/vue.global.prod.js
git commit -m "feat: add Vue 3 runtime and index.html shell"
```

---

## Task 11: CSS Styles

**Files:**
- Create: `ultraviewer/static/style.css`

- [ ] **Step 1: Create style.css**

```css
/* ultraviewer/static/style.css */

/* Reset & Base */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --bg-primary: #0f0f1a;
    --bg-secondary: #1a1a2e;
    --bg-tertiary: #252540;
    --text-primary: #e0e0e0;
    --text-secondary: #8888aa;
    --accent: #6366f1;
    --accent-hover: #818cf8;
    --border: #2a2a45;
    --success: #22c55e;
    --error: #ef4444;
    --warning: #f59e0b;
    --pending: #8888aa;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    height: 100vh;
    overflow: hidden;
}

#app {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

/* Tab Bar */
.tab-bar {
    display: flex;
    align-items: center;
    background: var(--bg-secondary);
    border-bottom: 2px solid var(--accent);
    padding: 0;
    min-height: 40px;
    overflow-x: auto;
}

.tab-item {
    padding: 0.5rem 1.2rem;
    cursor: pointer;
    color: var(--text-secondary);
    white-space: nowrap;
    border-radius: 6px 6px 0 0;
    font-size: 0.85rem;
    position: relative;
    user-select: none;
}

.tab-item:hover { color: var(--text-primary); background: var(--bg-tertiary); }
.tab-item.active { background: var(--accent); color: #fff; font-weight: 600; }

.tab-add {
    padding: 0.5rem 1rem;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 1.1rem;
}
.tab-add:hover { color: var(--accent); }

/* Main Content */
.main-content {
    display: flex;
    flex: 1;
    overflow: hidden;
}

/* Tree View */
.tree-panel {
    width: 280px;
    min-width: 200px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.tree-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.8rem;
    border-bottom: 1px solid var(--border);
}

.tree-header h3 { font-size: 0.85rem; font-weight: 600; }

.tree-add-btn {
    color: var(--accent);
    cursor: pointer;
    font-size: 0.85rem;
    background: none;
    border: none;
    padding: 0.2rem 0.5rem;
}
.tree-add-btn:hover { color: var(--accent-hover); }

.tree-body {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
}

.tree-node {
    padding: 0.3rem 0.5rem;
    cursor: pointer;
    border-radius: 4px;
    font-size: 0.82rem;
    font-family: 'SF Mono', 'Fira Code', monospace;
    line-height: 1.8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.tree-node:hover { background: var(--bg-tertiary); }
.tree-node.selected { background: rgba(99, 102, 241, 0.15); }

.tree-node .icon { margin-right: 0.3rem; }
.tree-node .status-badge {
    font-size: 0.7rem;
    margin-left: 0.5rem;
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
}

.tree-leaf { padding-left: 1.5rem; }

/* Content Panel */
.content-panel {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
}

.content-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.content-header h2 {
    font-size: 1.1rem;
    font-weight: 600;
}

/* Buttons */
.btn {
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 500;
}

.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-secondary { background: var(--bg-tertiary); color: var(--text-primary); border: 1px solid var(--border); }
.btn-secondary:hover { background: var(--border); }
.btn-danger { background: var(--error); color: #fff; }
.btn-sm { padding: 0.2rem 0.5rem; font-size: 0.75rem; }

/* Forms */
.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-bottom: 0.3rem;
}

.form-input {
    width: 100%;
    padding: 0.4rem 0.6rem;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text-primary);
    font-size: 0.85rem;
}

.form-input:focus {
    outline: none;
    border-color: var(--accent);
}

.form-select {
    padding: 0.4rem 0.6rem;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text-primary);
    font-size: 0.85rem;
}

.form-row {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 0.6rem;
}

.form-row label { font-size: 0.8rem; color: var(--text-secondary); }

/* Settings sections */
.settings-section {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}

.settings-section:last-child { border-bottom: none; }

.settings-section h3 {
    color: var(--accent);
    font-size: 0.9rem;
    margin-bottom: 0.8rem;
}

/* Tables */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
}

.data-table th {
    text-align: left;
    padding: 0.5rem;
    border-bottom: 2px solid var(--border);
    color: var(--text-secondary);
    font-weight: 600;
}

.data-table td {
    padding: 0.5rem;
    border-bottom: 1px solid var(--border);
}

.data-table tr:hover { background: var(--bg-tertiary); }

/* Status indicators */
.status-pass { color: var(--success); }
.status-fail { color: var(--error); }
.status-error { color: var(--error); }
.status-timeout { color: var(--warning); }
.status-pending { color: var(--pending); }

/* Diff view */
.diff-container { font-family: monospace; font-size: 0.8rem; }
.diff-file-header {
    background: var(--bg-tertiary);
    padding: 0.5rem;
    border-radius: 4px 4px 0 0;
    font-weight: 600;
}
.diff-content {
    background: var(--bg-primary);
    padding: 0.5rem;
    border: 1px solid var(--border);
    border-radius: 0 0 4px 4px;
    overflow-x: auto;
    white-space: pre;
}
.diff-add { color: var(--success); background: rgba(34, 197, 94, 0.1); }
.diff-remove { color: var(--error); background: rgba(239, 68, 68, 0.1); }

/* Progress bar */
.progress-bar {
    width: 100%;
    height: 6px;
    background: var(--bg-tertiary);
    border-radius: 3px;
    margin: 0.5rem 0;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 3px;
    transition: width 0.3s;
}

/* Context menu */
.context-menu {
    position: fixed;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.3rem 0;
    min-width: 150px;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.context-menu-item {
    padding: 0.4rem 1rem;
    cursor: pointer;
    font-size: 0.82rem;
}
.context-menu-item:hover { background: var(--bg-tertiary); }
.context-menu-item.danger { color: var(--error); }

/* Modal / Dialog */
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999;
}

.modal {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    min-width: 400px;
    max-width: 500px;
}

.modal h3 { margin-bottom: 1rem; }

.modal-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 1rem;
}

/* HTML renderer sandbox */
.html-renderer {
    background: #fff;
    border-radius: 4px;
    padding: 1rem;
    color: #333;
    min-height: 200px;
}

/* Spinner */
@keyframes spin { to { transform: rotate(360deg); } }
.spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

/* Key-value editor */
.kv-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 0.4rem;
}
.kv-row input { flex: 1; }
.kv-remove {
    color: var(--error);
    cursor: pointer;
    background: none;
    border: none;
    font-size: 1rem;
}
```

- [ ] **Step 2: Commit**

```bash
git add ultraviewer/static/style.css
git commit -m "feat: application CSS with dark theme"
```

---

## Task 12: Vue Components — TabBar

**Files:**
- Create: `ultraviewer/static/components/TabBar.js`

- [ ] **Step 1: Create TabBar.js**

```javascript
// ultraviewer/static/components/TabBar.js
const TabBar = {
    props: ['tabs', 'activeTabId'],
    emits: ['select', 'create', 'rename', 'delete'],
    data() {
        return {
            contextMenu: null,
            editingTabId: null,
            editName: '',
        };
    },
    methods: {
        onContextMenu(e, tab) {
            e.preventDefault();
            this.contextMenu = { x: e.clientX, y: e.clientY, tab };
        },
        closeContextMenu() {
            this.contextMenu = null;
        },
        startRename(tab) {
            this.editingTabId = tab.id;
            this.editName = tab.name;
            this.closeContextMenu();
            this.$nextTick(() => {
                const input = this.$el.querySelector('.tab-edit-input');
                if (input) input.focus();
            });
        },
        finishRename() {
            if (this.editName.trim() && this.editingTabId) {
                this.$emit('rename', { id: this.editingTabId, name: this.editName.trim() });
            }
            this.editingTabId = null;
        },
        cancelRename() {
            this.editingTabId = null;
        },
    },
    mounted() {
        document.addEventListener('click', this.closeContextMenu);
    },
    unmounted() {
        document.removeEventListener('click', this.closeContextMenu);
    },
    template: `
        <div class="tab-bar">
            <div v-for="tab in tabs" :key="tab.id"
                 class="tab-item"
                 :class="{ active: tab.id === activeTabId }"
                 @click="$emit('select', tab.id)"
                 @contextmenu="onContextMenu($event, tab)"
                 @dblclick="startRename(tab)">
                <template v-if="editingTabId === tab.id">
                    <input class="tab-edit-input"
                           v-model="editName"
                           @keydown.enter="finishRename"
                           @keydown.escape="cancelRename"
                           @blur="finishRename"
                           @click.stop
                           style="background:transparent;border:none;color:#fff;width:80px;outline:none;">
                </template>
                <template v-else>{{ tab.name }}</template>
            </div>
            <div class="tab-add" @click="$emit('create')">＋</div>

            <div v-if="contextMenu" class="context-menu"
                 :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }">
                <div class="context-menu-item" @click="startRename(contextMenu.tab)">Rename</div>
                <div class="context-menu-item danger" @click="$emit('delete', contextMenu.tab.id); closeContextMenu()">Delete</div>
            </div>
        </div>
    `,
};
```

- [ ] **Step 2: Commit**

```bash
git add ultraviewer/static/components/TabBar.js
git commit -m "feat: TabBar Vue component with rename and context menu"
```

---

## Task 13: Vue Components — TreeView

**Files:**
- Create: `ultraviewer/static/components/TreeView.js`

- [ ] **Step 1: Create TreeView.js**

```javascript
// ultraviewer/static/components/TreeView.js
const TreeView = {
    props: ['suites', 'selectedNode'],
    emits: ['selectSuite', 'selectLeaf', 'createSuite', 'runSuite', 'runLeaf'],
    data() {
        return {
            expandedSuites: {},
            suiteLeaves: {},
            loadingLeaves: {},
            contextMenu: null,
        };
    },
    methods: {
        async toggleSuite(suite) {
            const id = suite.id;
            if (this.expandedSuites[id]) {
                this.expandedSuites[id] = false;
            } else {
                this.expandedSuites[id] = true;
                if (!this.suiteLeaves[id]) {
                    await this.loadLeaves(suite);
                }
            }
        },
        async loadLeaves(suite) {
            this.loadingLeaves[suite.id] = true;
            try {
                const resp = await fetch(`/api/suites/${suite.id}/leaves`);
                const leaves = await resp.json();
                this.suiteLeaves[suite.id] = leaves;
            } catch (e) {
                this.suiteLeaves[suite.id] = [];
            }
            this.loadingLeaves[suite.id] = false;
        },
        onSuiteContextMenu(e, suite) {
            e.preventDefault();
            this.contextMenu = { x: e.clientX, y: e.clientY, type: 'suite', item: suite };
        },
        onLeafContextMenu(e, suite, leaf) {
            e.preventDefault();
            this.contextMenu = { x: e.clientX, y: e.clientY, type: 'leaf', item: leaf, suite };
        },
        closeContextMenu() {
            this.contextMenu = null;
        },
        isSelected(type, id) {
            return this.selectedNode && this.selectedNode.type === type && this.selectedNode.id === id;
        },
        async refreshLeaves(suiteId) {
            const suite = this.suites.find(s => s.id === suiteId);
            if (suite) await this.loadLeaves(suite);
        },
    },
    mounted() {
        document.addEventListener('click', this.closeContextMenu);
    },
    unmounted() {
        document.removeEventListener('click', this.closeContextMenu);
    },
    template: `
        <div class="tree-panel">
            <div class="tree-header">
                <h3>Explorer</h3>
                <button class="tree-add-btn" @click="$emit('createSuite')">+ Suite</button>
            </div>
            <div class="tree-body">
                <div v-for="suite in suites" :key="suite.id">
                    <div class="tree-node"
                         :class="{ selected: isSelected('suite', suite.id) }"
                         @click="$emit('selectSuite', suite); toggleSuite(suite)"
                         @contextmenu="onSuiteContextMenu($event, suite)">
                        <span class="icon">{{ expandedSuites[suite.id] ? '▼' : '▶' }}</span>
                        <span class="icon">📦</span>
                        {{ suite.name }}
                    </div>
                    <template v-if="expandedSuites[suite.id]">
                        <div v-if="loadingLeaves[suite.id]" class="tree-node tree-leaf">
                            <span class="spinner"></span> Loading...
                        </div>
                        <div v-else-if="suiteLeaves[suite.id]?.length === 0" class="tree-node tree-leaf" style="color: var(--text-secondary);">
                            (empty)
                        </div>
                        <div v-else v-for="leaf in suiteLeaves[suite.id]" :key="leaf.path"
                             class="tree-node tree-leaf"
                             :class="{ selected: isSelected('leaf', leaf.path) }"
                             @click.stop="$emit('selectLeaf', { suite, leaf })"
                             @contextmenu="onLeafContextMenu($event, suite, leaf)">
                            <span class="icon">📁</span>
                            {{ leaf.name }}
                        </div>
                    </template>
                </div>
                <div v-if="suites.length === 0" style="padding: 1rem; color: var(--text-secondary); font-size: 0.82rem;">
                    No suites yet. Click "+ Suite" to add one.
                </div>
            </div>

            <div v-if="contextMenu" class="context-menu"
                 :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }">
                <template v-if="contextMenu.type === 'suite'">
                    <div class="context-menu-item" @click="$emit('runSuite', contextMenu.item); closeContextMenu()">▶ Run Suite</div>
                    <div class="context-menu-item" @click="refreshLeaves(contextMenu.item.id); closeContextMenu()">⟳ Rescan</div>
                </template>
                <template v-if="contextMenu.type === 'leaf'">
                    <div class="context-menu-item" @click="$emit('runLeaf', { suite: contextMenu.suite, leaf: contextMenu.item }); closeContextMenu()">▶ Run This</div>
                </template>
            </div>
        </div>
    `,
};
```

- [ ] **Step 2: Commit**

```bash
git add ultraviewer/static/components/TreeView.js
git commit -m "feat: TreeView Vue component with expand/collapse and context menu"
```

---

## Task 14: Vue Components — Renderers

**Files:**
- Create: `ultraviewer/static/components/renderers/TableRenderer.js`
- Create: `ultraviewer/static/components/renderers/DiffRenderer.js`
- Create: `ultraviewer/static/components/renderers/HtmlRenderer.js`
- Create: `ultraviewer/static/components/renderers/SectionsRenderer.js`

- [ ] **Step 1: Create TableRenderer.js**

```javascript
// ultraviewer/static/components/renderers/TableRenderer.js
const TableRenderer = {
    props: ['data'],
    computed: {
        columns() {
            return this.data?.columns || (this.data?.rows?.length ? Object.keys(this.data.rows[0]) : []);
        },
        rows() {
            return this.data?.rows || [];
        },
    },
    template: `
        <table class="data-table">
            <thead>
                <tr>
                    <th v-for="col in columns" :key="col">{{ col }}</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="(row, i) in rows" :key="i">
                    <td v-for="col in columns" :key="col"
                        :class="{
                            'status-pass': row[col] === 'pass' || row[col] === 'PASS',
                            'status-fail': row[col] === 'fail' || row[col] === 'FAIL',
                            'status-error': row[col] === 'error' || row[col] === 'ERROR',
                        }">
                        {{ row[col] }}
                    </td>
                </tr>
            </tbody>
        </table>
        <p v-if="rows.length === 0" style="color: var(--text-secondary); padding: 1rem;">No data</p>
    `,
};
```

- [ ] **Step 2: Create DiffRenderer.js**

```javascript
// ultraviewer/static/components/renderers/DiffRenderer.js
const DiffRenderer = {
    props: ['data'],
    computed: {
        files() {
            return this.data?.files || [];
        },
    },
    methods: {
        diffLines(golden, actual) {
            const gLines = (golden || '').split('\n');
            const aLines = (actual || '').split('\n');
            const maxLen = Math.max(gLines.length, aLines.length);
            const result = [];
            for (let i = 0; i < maxLen; i++) {
                const g = gLines[i] || '';
                const a = aLines[i] || '';
                if (g === a) {
                    result.push({ type: 'same', line: g, num: i + 1 });
                } else {
                    if (g) result.push({ type: 'remove', line: g, num: i + 1 });
                    if (a) result.push({ type: 'add', line: a, num: i + 1 });
                }
            }
            return result;
        },
    },
    template: `
        <div class="diff-container" v-for="file in files" :key="file.name" style="margin-bottom: 1rem;">
            <div class="diff-file-header">{{ file.name }}</div>
            <div class="diff-content"><template v-for="line in diffLines(file.golden, file.actual)"
><span :class="{ 'diff-add': line.type === 'add', 'diff-remove': line.type === 'remove' }"
>{{ line.type === 'remove' ? '-' : line.type === 'add' ? '+' : ' ' }} {{ line.line }}
</span></template></div>
        </div>
        <p v-if="files.length === 0" style="color: var(--text-secondary); padding: 1rem;">No diffs</p>
    `,
};
```

- [ ] **Step 3: Create HtmlRenderer.js**

```javascript
// ultraviewer/static/components/renderers/HtmlRenderer.js
const HtmlRenderer = {
    props: ['data'],
    computed: {
        htmlContent() {
            return this.data?.content || '';
        },
    },
    template: `
        <div class="html-renderer" v-html="htmlContent"></div>
    `,
};
```

- [ ] **Step 4: Create SectionsRenderer.js**

```javascript
// ultraviewer/static/components/renderers/SectionsRenderer.js
const SectionsRenderer = {
    props: ['data'],
    computed: {
        sections() {
            return this.data?.sections || [];
        },
    },
    template: `
        <div v-for="(section, i) in sections" :key="i" style="margin-bottom: 1.5rem;">
            <table-renderer v-if="section.type === 'table'" :data="section"></table-renderer>
            <diff-renderer v-else-if="section.type === 'diff'" :data="section"></diff-renderer>
            <html-renderer v-else-if="section.type === 'html'" :data="section"></html-renderer>
            <div v-else style="color: var(--text-secondary);">Unknown section type: {{ section.type }}</div>
        </div>
    `,
};
```

- [ ] **Step 5: Commit**

```bash
mkdir -p ultraviewer/static/components/renderers
git add ultraviewer/static/components/renderers/
git commit -m "feat: Table, Diff, HTML, and Sections renderers"
```

---

## Task 15: Vue Components — SuiteSettings & ContentPanel

**Files:**
- Create: `ultraviewer/static/components/SuiteSettings.js`
- Create: `ultraviewer/static/components/ContentPanel.js`

- [ ] **Step 1: Create SuiteSettings.js**

```javascript
// ultraviewer/static/components/SuiteSettings.js
const SuiteSettings = {
    props: ['suite'],
    emits: ['save', 'testScript'],
    data() {
        return {
            form: this.initForm(),
        };
    },
    watch: {
        suite: {
            handler() { this.form = this.initForm(); },
            deep: true,
        },
    },
    methods: {
        initForm() {
            const s = this.suite || {};
            const script = s.script || {};
            const rendering = s.rendering || {};
            return {
                name: s.name || '',
                folder_path: s.folder_path || '',
                scan_depth: s.scan_depth || 1,
                interpreter: script.interpreter || 'python3',
                script_path: script.script_path || '',
                timeout_seconds: script.timeout_seconds || 30,
                max_parallel: script.max_parallel || 1,
                extra_args: (script.extra_args || []).map(a => ({...a})),
                env_vars: (script.env_vars || []).map(v => ({...v})),
                render_mode: rendering.render_mode || 'auto',
                render_config: rendering.config || {},
            };
        },
        addArg() { this.form.extra_args.push({ key: '', value: '' }); },
        removeArg(i) { this.form.extra_args.splice(i, 1); },
        addEnv() { this.form.env_vars.push({ key: '', value: '' }); },
        removeEnv(i) { this.form.env_vars.splice(i, 1); },
        save() {
            this.$emit('save', {
                id: this.suite.id,
                name: this.form.name,
                folder_path: this.form.folder_path,
                scan_depth: this.form.scan_depth,
                script: {
                    interpreter: this.form.interpreter,
                    script_path: this.form.script_path,
                    timeout_seconds: this.form.timeout_seconds,
                    extra_args: this.form.extra_args.filter(a => a.key),
                    env_vars: this.form.env_vars.filter(v => v.key),
                    max_parallel: this.form.max_parallel,
                },
                rendering: {
                    render_mode: this.form.render_mode,
                    config: this.form.render_config,
                },
            });
        },
    },
    template: `
        <div>
            <div class="settings-section">
                <h3>Basic</h3>
                <div class="form-row">
                    <label>Suite Name</label>
                    <input class="form-input" v-model="form.name">
                </div>
                <div class="form-row">
                    <label>Folder Path</label>
                    <input class="form-input" v-model="form.folder_path">
                </div>
                <div class="form-row">
                    <label>Scan Depth</label>
                    <select class="form-select" v-model.number="form.scan_depth">
                        <option :value="1">1 level</option>
                        <option :value="2">2 levels</option>
                        <option :value="3">3 levels</option>
                    </select>
                </div>
            </div>

            <div class="settings-section">
                <h3>Script</h3>
                <div class="form-row">
                    <label>Interpreter</label>
                    <select class="form-select" v-model="form.interpreter">
                        <option value="python3">python3</option>
                        <option value="bash">bash</option>
                    </select>
                </div>
                <div class="form-row">
                    <label>Script Path</label>
                    <input class="form-input" v-model="form.script_path">
                </div>
                <div class="form-row">
                    <label>Timeout (sec)</label>
                    <input class="form-input" type="number" v-model.number="form.timeout_seconds" style="width: 100px;">
                </div>
                <div class="form-row">
                    <label>Max Parallel</label>
                    <input class="form-input" type="number" v-model.number="form.max_parallel" style="width: 100px;" min="1">
                </div>
            </div>

            <div class="settings-section">
                <h3>Context</h3>
                <p style="color: var(--text-secondary); font-size: 0.78rem; margin-bottom: 0.8rem;">
                    Leaf folder path is always passed as the first argument.
                </p>
                <div style="margin-bottom: 0.8rem;">
                    <label style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.3rem; display: block;">Extra Arguments</label>
                    <div class="kv-row" v-for="(arg, i) in form.extra_args" :key="i">
                        <input class="form-input" v-model="arg.key" placeholder="--flag">
                        <input class="form-input" v-model="arg.value" placeholder="value">
                        <button class="kv-remove" @click="removeArg(i)">✕</button>
                    </div>
                    <button class="btn btn-sm btn-secondary" @click="addArg">+ Add Argument</button>
                </div>
                <div>
                    <label style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.3rem; display: block;">Environment Variables</label>
                    <div class="kv-row" v-for="(v, i) in form.env_vars" :key="i">
                        <input class="form-input" v-model="v.key" placeholder="VAR_NAME">
                        <input class="form-input" v-model="v.value" placeholder="value">
                        <button class="kv-remove" @click="removeEnv(i)">✕</button>
                    </div>
                    <button class="btn btn-sm btn-secondary" @click="addEnv">+ Add Variable</button>
                </div>
            </div>

            <div class="settings-section">
                <h3>Rendering</h3>
                <div class="form-row">
                    <label>Render Mode</label>
                    <select class="form-select" v-model="form.render_mode">
                        <option value="auto">Auto (by type field)</option>
                        <option value="table">Table</option>
                        <option value="diff">Diff View</option>
                        <option value="html">Raw HTML</option>
                    </select>
                </div>
            </div>

            <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                <button class="btn btn-secondary" @click="$emit('testScript', suite.id)">Test Script</button>
                <button class="btn btn-primary" @click="save">Save</button>
            </div>
        </div>
    `,
};
```

- [ ] **Step 2: Create ContentPanel.js**

```javascript
// ultraviewer/static/components/ContentPanel.js
const ContentPanel = {
    props: ['selectedNode', 'suiteData', 'leafResult', 'running', 'progress'],
    emits: ['saveSettings', 'runSuite', 'testScript'],
    computed: {
        renderData() {
            if (!this.leafResult || !this.leafResult.result_json) return null;
            const result = this.leafResult.result_json;
            if (typeof result === 'string') {
                try { return JSON.parse(result); } catch { return null; }
            }
            return result;
        },
        renderMode() {
            if (!this.suiteData?.rendering) return 'auto';
            return this.suiteData.rendering.render_mode || 'auto';
        },
        effectiveType() {
            if (this.renderMode !== 'auto') return this.renderMode;
            return this.renderData?.type || 'table';
        },
    },
    template: `
        <div class="content-panel">
            <!-- Nothing selected -->
            <div v-if="!selectedNode" style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary);">
                Select a suite or folder from the tree
            </div>

            <!-- Suite selected: show settings -->
            <template v-else-if="selectedNode.type === 'suite' && suiteData">
                <div class="content-header">
                    <h2>{{ suiteData.name }} — Settings</h2>
                    <button class="btn btn-primary" @click="$emit('runSuite', suiteData)">▶ Run Suite</button>
                </div>
                <suite-settings
                    :suite="suiteData"
                    @save="$emit('saveSettings', $event)"
                    @test-script="$emit('testScript', $event)"
                ></suite-settings>
            </template>

            <!-- Leaf selected: show result -->
            <template v-else-if="selectedNode.type === 'leaf'">
                <div class="content-header">
                    <h2>{{ selectedNode.leaf.name }}</h2>
                </div>
                <div v-if="running" style="margin-bottom: 1rem;">
                    <span class="spinner"></span> Running...
                    <div class="progress-bar" v-if="progress">
                        <div class="progress-fill" :style="{ width: (progress.done / progress.total * 100) + '%' }"></div>
                    </div>
                </div>
                <div v-if="leafResult && leafResult.status === 'error'" style="background: rgba(239,68,68,0.1); padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                    <strong class="status-error">Error:</strong> {{ leafResult.error_message }}
                </div>
                <div v-if="renderData">
                    <table-renderer v-if="effectiveType === 'table'" :data="renderData"></table-renderer>
                    <diff-renderer v-else-if="effectiveType === 'diff'" :data="renderData"></diff-renderer>
                    <html-renderer v-else-if="effectiveType === 'html'" :data="renderData"></html-renderer>
                    <sections-renderer v-else-if="effectiveType === 'sections'" :data="renderData"></sections-renderer>
                    <pre v-else style="color: var(--text-secondary);">{{ JSON.stringify(renderData, null, 2) }}</pre>
                </div>
                <div v-else-if="!running && !leafResult" style="color: var(--text-secondary);">
                    No results yet. Run the suite or right-click this item to run individually.
                </div>
            </template>
        </div>
    `,
};
```

- [ ] **Step 3: Commit**

```bash
git add ultraviewer/static/components/SuiteSettings.js ultraviewer/static/components/ContentPanel.js
git commit -m "feat: SuiteSettings and ContentPanel Vue components"
```

---

## Task 16: Vue App — Main Application Logic

**Files:**
- Create: `ultraviewer/static/app.js`

- [ ] **Step 1: Create app.js**

```javascript
// ultraviewer/static/app.js
const { createApp, ref, computed, watch, onMounted, nextTick } = Vue;

const app = createApp({
    data() {
        return {
            tabs: [],
            activeTabId: null,
            suites: [],
            selectedNode: null,
            selectedSuiteData: null,
            selectedLeafResult: null,
            isRunning: false,
            runProgress: null,
            showCreateTab: false,
            showCreateSuite: false,
            newTabName: '',
            newSuiteName: '',
            newSuitePath: '',
        };
    },
    async mounted() {
        await this.loadTabs();
        if (this.tabs.length === 0) {
            await this.createTab('Default');
        }
    },
    watch: {
        activeTabId() {
            this.selectedNode = null;
            this.selectedSuiteData = null;
            this.selectedLeafResult = null;
            this.loadSuites();
        },
    },
    methods: {
        // --- Tabs ---
        async loadTabs() {
            const resp = await fetch('/api/tabs');
            this.tabs = await resp.json();
            if (this.tabs.length > 0 && !this.activeTabId) {
                this.activeTabId = this.tabs[0].id;
            }
        },
        selectTab(id) {
            this.activeTabId = id;
        },
        async createTab(name) {
            const tabName = name || 'New Tab';
            const resp = await fetch('/api/tabs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: tabName, position: this.tabs.length }),
            });
            const tab = await resp.json();
            this.tabs.push(tab);
            this.activeTabId = tab.id;
        },
        async renameTab({ id, name }) {
            await fetch(`/api/tabs/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
            });
            const tab = this.tabs.find(t => t.id === id);
            if (tab) tab.name = name;
        },
        async deleteTab(id) {
            await fetch(`/api/tabs/${id}`, { method: 'DELETE' });
            this.tabs = this.tabs.filter(t => t.id !== id);
            if (this.activeTabId === id) {
                this.activeTabId = this.tabs.length > 0 ? this.tabs[0].id : null;
            }
        },

        // --- Suites ---
        async loadSuites() {
            if (!this.activeTabId) { this.suites = []; return; }
            const resp = await fetch(`/api/tabs/${this.activeTabId}/suites`);
            this.suites = await resp.json();
        },
        createSuiteDialog() {
            this.newSuiteName = '';
            this.newSuitePath = '';
            this.showCreateSuite = true;
        },
        async createSuite() {
            if (!this.newSuiteName.trim() || !this.newSuitePath.trim()) return;
            await fetch(`/api/tabs/${this.activeTabId}/suites`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: this.newSuiteName,
                    folder_path: this.newSuitePath,
                    position: this.suites.length,
                }),
            });
            this.showCreateSuite = false;
            await this.loadSuites();
        },
        selectSuite(suite) {
            this.selectedNode = { type: 'suite', id: suite.id };
            this.selectedSuiteData = suite;
            this.selectedLeafResult = null;
        },
        async selectLeaf({ suite, leaf }) {
            this.selectedNode = { type: 'leaf', id: leaf.path, leaf, suite };
            this.selectedSuiteData = suite;
            this.selectedLeafResult = null;
            // Load existing result
            try {
                const resp = await fetch(`/api/suites/${suite.id}/results/${leaf.name}`);
                if (resp.ok) {
                    this.selectedLeafResult = await resp.json();
                }
            } catch {}
        },
        async saveSuiteSettings(data) {
            await fetch(`/api/suites/${data.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            await this.loadSuites();
            const updated = this.suites.find(s => s.id === data.id);
            if (updated) this.selectedSuiteData = updated;
        },

        // --- Execution ---
        async runSuite(suite) {
            this.isRunning = true;
            this.runProgress = { done: 0, total: 0 };
            try {
                const ws = new WebSocket(`ws://${location.host}/ws/execution/${suite.id}`);
                ws.onmessage = (e) => {
                    const data = JSON.parse(e.data);
                    if (data.event === 'run_started') {
                        this.runProgress = { done: 0, total: data.total };
                    } else if (data.event === 'leaf_completed' || data.event === 'leaf_error') {
                        this.runProgress.done++;
                    } else if (data.event === 'run_completed') {
                        this.isRunning = false;
                        ws.close();
                        this.loadSuites();
                    }
                };
                ws.onerror = () => { this.isRunning = false; };
                ws.onclose = () => { this.isRunning = false; };
            } catch {
                // Fallback to REST
                await fetch(`/api/suites/${suite.id}/run`, { method: 'POST' });
                this.isRunning = false;
                await this.loadSuites();
            }
        },
        async runLeaf({ suite, leaf }) {
            this.isRunning = true;
            try {
                const resp = await fetch(`/api/suites/${suite.id}/run/${leaf.name}`, { method: 'POST' });
                const result = await resp.json();
                this.selectedLeafResult = result;
            } catch {}
            this.isRunning = false;
        },
        async testScript(suiteId) {
            try {
                const resp = await fetch(`/api/suites/${suiteId}/test-script`, { method: 'POST' });
                const result = await resp.json();
                alert(result.status === 'success'
                    ? 'Script test passed!\n\n' + JSON.stringify(result.result, null, 2)
                    : 'Script test failed:\n\n' + (result.error_message || 'Unknown error'));
            } catch (e) {
                alert('Error testing script: ' + e.message);
            }
        },
    },
    template: `
        <tab-bar
            :tabs="tabs"
            :active-tab-id="activeTabId"
            @select="selectTab"
            @create="createTab()"
            @rename="renameTab"
            @delete="deleteTab"
        ></tab-bar>
        <div class="main-content">
            <tree-view
                :suites="suites"
                :selected-node="selectedNode"
                @select-suite="selectSuite"
                @select-leaf="selectLeaf"
                @create-suite="createSuiteDialog"
                @run-suite="runSuite"
                @run-leaf="runLeaf"
            ></tree-view>
            <content-panel
                :selected-node="selectedNode"
                :suite-data="selectedSuiteData"
                :leaf-result="selectedLeafResult"
                :running="isRunning"
                :progress="runProgress"
                @save-settings="saveSuiteSettings"
                @run-suite="runSuite"
                @test-script="testScript"
            ></content-panel>
        </div>

        <!-- Create Suite Modal -->
        <div v-if="showCreateSuite" class="modal-overlay" @click.self="showCreateSuite = false">
            <div class="modal">
                <h3>Create Suite</h3>
                <div class="form-group">
                    <label>Name</label>
                    <input class="form-input" v-model="newSuiteName" placeholder="e.g., Login Module" @keydown.enter="createSuite">
                </div>
                <div class="form-group">
                    <label>Folder Path</label>
                    <input class="form-input" v-model="newSuitePath" placeholder="/path/to/folder" @keydown.enter="createSuite">
                </div>
                <div class="modal-actions">
                    <button class="btn btn-secondary" @click="showCreateSuite = false">Cancel</button>
                    <button class="btn btn-primary" @click="createSuite">Create</button>
                </div>
            </div>
        </div>
    `,
});

// Register components
app.component('tab-bar', TabBar);
app.component('tree-view', TreeView);
app.component('content-panel', ContentPanel);
app.component('suite-settings', SuiteSettings);
app.component('table-renderer', TableRenderer);
app.component('diff-renderer', DiffRenderer);
app.component('html-renderer', HtmlRenderer);
app.component('sections-renderer', SectionsRenderer);

app.mount('#app');
```

- [ ] **Step 2: Commit**

```bash
git add ultraviewer/static/app.js
git commit -m "feat: main Vue app with tab/suite/leaf management and execution"
```

---

## Task 17: Fix Static File Serving

**Files:**
- Modify: `ultraviewer/main.py` (ensure API routes take priority over static mount)

- [ ] **Step 1: Update main.py to serve static files correctly**

The static mount must come last so API routes take priority. Also serve component JS files correctly.

```python
# In create_app(), ensure the static mount is after all router includes:
def create_app() -> FastAPI:
    app = FastAPI(title="UltraViewer", lifespan=lifespan)

    # API routes first
    app.include_router(tabs_router)
    app.include_router(suites_router)
    app.include_router(execution_router)
    app.include_router(results_router)

    # Static files last
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/")
        async def serve_index():
            from fastapi.responses import FileResponse
            return FileResponse(os.path.join(static_dir, "index.html"))

    return app
```

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add ultraviewer/main.py ultraviewer/static/index.html
git commit -m "fix: static file serving with API route priority"
```

---

## Task 18: Download Offline Packages

**Files:**
- Create: `offline-packages/` directory with wheel files

- [ ] **Step 1: Download dependency wheels**

Run: `pip download websockets aiosqlite -d offline-packages/`
Expected: .whl files in offline-packages/

- [ ] **Step 2: Add .gitignore for wheels**

```
# offline-packages/.gitignore
# Track the directory but document which packages are needed
# Actual .whl files can be regenerated with: pip download websockets aiosqlite -d offline-packages/
```

- [ ] **Step 3: Create offline install script**

```bash
#!/bin/bash
# install-offline.sh
# Install UltraViewer dependencies on an offline machine
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
pip install --user --no-index --find-links "$SCRIPT_DIR/offline-packages/" websockets aiosqlite
echo "Dependencies installed. Run: python -m ultraviewer --port 8080"
```

- [ ] **Step 4: Commit**

```bash
chmod +x install-offline.sh
git add offline-packages/ install-offline.sh
git commit -m "feat: offline package installation support"
```

---

## Task 19: End-to-End Smoke Test

**Files:**
- No new files — manual verification

- [ ] **Step 1: Start the server**

Run: `python -m ultraviewer --port 8080 --db-path /tmp/ultraviewer-test.db`
Expected: server starts on port 8080

- [ ] **Step 2: Open browser and verify UI loads**

Open: `http://localhost:8080`
Expected: dark-themed UI with tab bar and tree panel

- [ ] **Step 3: Create a tab, add a suite, run it**

1. Default tab should already exist
2. Click "+ Suite", enter name and a test folder path
3. Configure a script in suite settings
4. Click "Run Suite"
5. Verify results appear

- [ ] **Step 4: Clean up**

Run: `rm /tmp/ultraviewer-test.db`

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: end-to-end verification complete"
```
