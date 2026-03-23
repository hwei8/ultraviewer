# UltraViewer — Design Specification

A universal folder-based dashboard for organizing, executing, and visualizing script outputs. Primary use case: Test/CI result comparison (golden vs target). Designed for fully offline deployment.

## Core Concept

One universal abstraction drives the entire system:

**Suite** = folder path + script + rendering config

- The system scans the folder path to discover **leaf nodes** (subfolders)
- Clicking a leaf runs the configured **script** against that subfolder
- The script returns **JSON**, which the system renders using the configured **renderer**
- **Tabs** are independent workspaces — each has its own tree of suites
- The system has no built-in knowledge of "test cases" vs "results" — that distinction is entirely user-defined through how tabs and suites are configured

## Primary Use Case

The user has test modules with a golden/target folder structure:

```
golden/
└── module_a/
    ├── case_1/
    ├── case_2/
    └── case_3/

target/
└── module_a/
    ├── case_run_03-22-2026/
    │   ├── case_1/
    │   ├── case_2/
    │   └── case_3/
    └── case_run_03-21-2026/
        ├── case_1/
        └── case_2/
```

- **Cases tab**: suite points to `golden/module_a/` → shows case inventory with metadata
- **Results tab**: suite points to `target/module_a/` → each run folder is a leaf → script compares against golden and returns results

## Architecture

- **Backend**: FastAPI (Python) with SQLite for persistence
- **Frontend**: Vue 3 (bundled as a single `.js` file, no build tools required at runtime)
- **Communication**: REST API for CRUD, WebSocket for live execution progress
- **Offline**: packaged as a Python wheel with pre-downloaded dependency wheels included

## UI Layout

### Top Tab Bar
- User creates, renames, reorders, and deletes tabs freely
- Each tab is an independent workspace with its own tree view
- "+" button to add new tabs, right-click for rename/delete

### Left Tree Panel
- "+" button to add suites
- Suites expand to show scanned subfolders (leaf nodes)
- Click a **suite node** → opens Suite Settings page in content panel
- Click a **leaf node** → runs script and renders output in content panel
- Right-click for context menu (run, delete, etc.)

### Content Panel
- When a suite is selected: shows Suite Settings (configuration form)
- When a leaf is selected: shows rendered script output (table, diff, HTML, or mixed)

## Suite Settings

Four configuration sections when clicking a suite node:

### Basic
- **Suite Name**: display label
- **Folder Path**: the directory to scan for leaf nodes
- **Scan Depth**: how many levels deep to scan (default: 1)

### Script
- **Interpreter**: `python3`, `bash`, or custom path
- **Script Path**: path to the script file
- **Timeout**: max seconds per leaf execution (default: 30)

### Context (passed to script)
- Leaf node folder path is **always passed as the first argument**
- Extra CLI arguments: key-value pairs appended to the command
- Environment variables: set before script execution
- Suite-level defaults can be overridden at the folder level

### Rendering
- **Render Mode**: one of `table`, `diff`, `html`, or `auto`
- `auto` mode: script returns JSON with a `type` field that selects the renderer:
  - `{"type": "table", "columns": [...], "rows": [...]}`
  - `{"type": "diff", "files": [{"name": "f.txt", "golden": "...", "actual": "..."}]}`
  - `{"type": "html", "content": "<div>...</div>"}`
  - `{"type": "sections", "sections": [...]}` — mixed content, multiple renderers on one page

## Database Schema (SQLite)

### tabs
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PRIMARY KEY |
| name | TEXT | |
| position | INTEGER | for ordering |
| created_at | TIMESTAMP | |

### suites
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PRIMARY KEY |
| tab_id | INTEGER | → tabs.id |
| name | TEXT | |
| folder_path | TEXT | |
| scan_depth | INTEGER | DEFAULT 1 |
| position | INTEGER | for ordering within tab |
| created_at | TIMESTAMP | |

### suite_scripts
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PRIMARY KEY |
| suite_id | INTEGER | → suites.id |
| interpreter | TEXT | "python3", "bash", or custom path |
| script_path | TEXT | |
| timeout_seconds | INTEGER | DEFAULT 30 |
| extra_args | JSON | `[{"key": "--golden-path", "value": "/data/golden/"}]` |
| env_vars | JSON | `[{"key": "MODULE_NAME", "value": "login"}]` |

### suite_rendering
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PRIMARY KEY |
| suite_id | INTEGER | → suites.id |
| render_mode | TEXT | "table", "diff", "html", "auto" |
| config | JSON | mode-specific config |

### run_results
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PRIMARY KEY |
| suite_id | INTEGER | → suites.id |
| leaf_name | TEXT | subfolder name |
| leaf_path | TEXT | full path to subfolder |
| result_json | JSON | script output |
| status | TEXT | "success", "error", "timeout" |
| error_message | TEXT | |
| duration_ms | INTEGER | |
| run_at | TIMESTAMP | |

## REST API

### Tabs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tabs` | List all tabs |
| POST | `/api/tabs` | Create tab |
| PUT | `/api/tabs/{id}` | Update tab (rename, reorder) |
| DELETE | `/api/tabs/{id}` | Delete tab |

### Suites
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tabs/{tab_id}/suites` | List suites in tab |
| POST | `/api/tabs/{tab_id}/suites` | Create suite |
| PUT | `/api/suites/{id}` | Update suite settings |
| DELETE | `/api/suites/{id}` | Delete suite |

### Leaf Nodes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/suites/{id}/leaves` | Scan folder → return leaf nodes |

### Execution
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/suites/{id}/run` | Run script for all leaves |
| POST | `/api/suites/{id}/run/{leaf}` | Run script for single leaf |
| POST | `/api/suites/{id}/test-script` | Test script against first leaf |

### Results
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/suites/{id}/results` | Get latest results for all leaves |
| GET | `/api/suites/{id}/results/{leaf}` | Get result for specific leaf |

### WebSocket
| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/ws/execution/{suite_id}` | Live progress during suite run |

## Script Execution

### Invocation
```
{interpreter} {script_path} {leaf_folder_path} {extra_args...}
```
Environment variables are set before execution.

### Execution Modes
- **Sequential** (default): one leaf at a time
- **Parallel**: N leaves concurrently (configurable per suite)
- **Single leaf**: run one specific leaf via right-click
- **Cancel**: kills running processes, marks remaining as "cancelled"

### Error Handling

| Condition | Behavior |
|-----------|----------|
| Non-zero exit code | Store status="error", capture stderr |
| Timeout exceeded | Kill process, store status="timeout" |
| Invalid JSON output | Store status="error", save raw stdout |
| Script not found | Fail immediately, show error in UI |
| Folder path not found | Warning badge on suite in tree |
| No subfolders found | "Empty" state, prompt to check path |
| Permission denied | Show error with specific path |

### WebSocket Events
```json
{"event": "run_started", "total": 15}
{"event": "leaf_started", "leaf": "case_1"}
{"event": "leaf_completed", "leaf": "case_1", "status": "success", "duration_ms": 230}
{"event": "leaf_error", "leaf": "case_2", "error": "timeout after 30s"}
{"event": "run_completed", "passed": 13, "failed": 1, "errors": 1}
```

### Live UI Updates
- Tree view: spinner on running leaves, pass/fail icons on completion
- Content panel: progress bar showing X/N leaves completed

## Project Structure

```
ultraviewer/
├── pyproject.toml
├── offline-packages/          # pre-downloaded wheels for offline install
│   ├── websockets-*.whl
│   └── aiosqlite-*.whl
├── ultraviewer/
│   ├── __init__.py
│   ├── main.py                # FastAPI app + CLI entry point
│   ├── db.py                  # SQLite setup + migrations
│   ├── models.py              # Pydantic models
│   ├── api/
│   │   ├── tabs.py            # tab CRUD
│   │   ├── suites.py          # suite CRUD + settings
│   │   ├── execution.py       # script runner + WebSocket
│   │   └── results.py         # result queries
│   ├── runner.py              # script execution engine (subprocess)
│   ├── scanner.py             # folder scanning logic
│   └── static/                # frontend (served by FastAPI)
│       ├── index.html
│       ├── vue.global.prod.js # Vue 3 runtime (~40KB gzipped)
│       ├── app.js             # main Vue application
│       ├── components/
│       │   ├── TabBar.js
│       │   ├── TreeView.js
│       │   ├── ContentPanel.js
│       │   ├── SuiteSettings.js
│       │   └── renderers/
│       │       ├── TableRenderer.js
│       │       ├── DiffRenderer.js
│       │       └── HtmlRenderer.js
│       └── style.css
```

## Deployment

### Dependencies
| Package | Purpose | Required |
|---------|---------|----------|
| fastapi | Web framework | Yes (pre-installed on target) |
| uvicorn | ASGI server | Yes (pre-installed on target) |
| websockets | WebSocket support | Yes (install from offline-packages/) |
| aiosqlite | Async SQLite | Yes (install from offline-packages/) |
| sqlite3 | Database | Built into Python stdlib |
| Vue 3 | Frontend framework | Bundled as static JS file |

### Offline Installation
```bash
# On machine with internet: build the package
pip download websockets aiosqlite -d offline-packages/

# Copy entire project to offline machine, then:
pip install --user --no-index --find-links ./offline-packages/ websockets aiosqlite

# Run
python -m ultraviewer --port 8080
# or if installed as package:
ultraviewer --port 8080
```

### Target Machine Constraints
- No root access — install with `pip install --user`
- Write access limited to `~/` and `/nfs/SQA/hewei/`
- SQLite database stored in user-writable location (configurable, default: `~/.ultraviewer/data.db`)

## Future Extensibility
- **Knowledge Base**: add "blank page" and "file" node types to the tree for documentation/notes (not in scope for v1)
- **Video information extraction**: separate project can output results to a folder, UltraViewer can point a suite at it
