# UltraViewer

A universal folder-based dashboard for organizing, executing, and visualizing script outputs. Built for **fully offline** environments with no internet, no root access, and no build tools required.

Primary use case: test/CI result comparison (golden vs target), but the universal design works for any folder-based workflow.

## How It Works

One abstraction drives everything:

**Suite** = folder path + script + rendering config

1. Point a suite at a folder
2. UltraViewer scans it for subfolders (leaf nodes)
3. Select leaves and click **Run** — the configured script executes against each one
4. Scripts return JSON, rendered as tables, diffs, HTML, or mixed content

**Tabs** are independent workspaces. The system has no built-in concept of "test cases" vs "results" — that's defined entirely by how you configure your suites.

## Example: Golden/Target Comparison

```
golden/module_a/          target/module_a/
├── case_1/               ├── run_03-22/
├── case_2/               │   ├── case_1/
└── case_3/               │   ├── case_2/
                          │   └── case_3/
                          └── run_03-21/
                              ├── case_1/
                              └── case_2/
```

- **Cases tab** → suite points at `golden/module_a/` → shows case inventory
- **Results tab** → suite points at `target/module_a/` → script compares against golden

## Features

- **Tabs** — create, rename, reorder, delete independent workspaces
- **Suite settings** — configure interpreter, script path, timeout, parallel execution, extra args, env vars
- **Folder browser** — browse the filesystem to select paths (no manual typing needed)
- **Selective execution** — check/uncheck individual leaves, run only what you need
- **Live progress** — WebSocket-powered progress bar during execution
- **Multiple renderers** — table, diff, raw HTML, or mixed sections (auto-detected from script output)
- **Run history** — past results stored in SQLite, viewable per leaf or per run
- **Fully offline** — ships with pre-downloaded dependency wheels, no internet required

## Quick Start

```bash
# Clone and install
git clone https://github.com/hwei8/ultraviewer.git
cd ultraviewer
pip install -e .

# Run
python3 -m ultraviewer --port 8080
```

Open `http://localhost:8080` in your browser.

## Offline Installation

For machines without internet access:

```bash
# On a machine WITH internet — download wheels
pip download websockets aiosqlite -d offline-packages/

# Copy the entire project to the offline machine, then:
bash install-offline.sh

# Run
python3 -m ultraviewer --port 8080
```

## Script Output Format

Scripts receive the leaf folder path as the first argument. They must print JSON to stdout.

The `type` field determines the renderer:

```json
{"type": "table", "columns": ["Name", "Status"], "rows": [{"Name": "test_1", "Status": "pass"}]}
```

```json
{"type": "diff", "files": [{"name": "output.txt", "golden": "expected", "actual": "got"}]}
```

```json
{"type": "html", "content": "<div>Custom HTML content</div>"}
```

```json
{"type": "sections", "sections": [{"type": "table", ...}, {"type": "diff", ...}]}
```

## CLI Options

```
python3 -m ultraviewer [OPTIONS]

  --port PORT      Port to listen on (default: 8080)
  --host HOST      Host to bind to (default: 0.0.0.0)
  --db-path PATH   SQLite database path (default: ~/.ultraviewer/data.db)
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + SQLite (aiosqlite) |
| Frontend | Vue 3 (bundled, no build step) |
| Communication | REST API + WebSocket |
| Language | Python 3.8+ |

## Project Structure

```
ultraviewer/
├── ultraviewer/
│   ├── main.py              # FastAPI app + CLI
│   ├── db.py                # SQLite schema + connection
│   ├── models.py            # Pydantic models
│   ├── scanner.py           # Folder scanning
│   ├── runner.py            # Script execution engine
│   ├── api/
│   │   ├── tabs.py          # Tab CRUD
│   │   ├── suites.py        # Suite CRUD + settings
│   │   ├── execution.py     # Run scripts + WebSocket
│   │   ├── results.py       # Query results + history
│   │   └── browse.py        # Filesystem browser API
│   └── static/              # Vue 3 frontend (served by FastAPI)
├── tests/                   # pytest test suite
├── offline-packages/        # Pre-downloaded wheels
└── install-offline.sh       # Offline install script
```

## License

MIT
