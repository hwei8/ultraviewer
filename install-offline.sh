#!/bin/bash
# Install UltraViewer and all dependencies on an offline machine
# Usage: bash install-offline.sh [/path/to/python3.12]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${1:-python3}"

# Verify Python version
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
if [ -z "$PY_VER" ]; then
    echo "Error: Could not find Python at '$PYTHON'"
    echo "Usage: bash install-offline.sh /path/to/python3.12"
    exit 1
fi
echo "Using Python $PY_VER at $PYTHON"

# Install all dependencies from bundled wheels
"$PYTHON" -m pip install --user --no-index --find-links "$SCRIPT_DIR/offline-packages/" \
    fastapi uvicorn websockets aiosqlite

# Install ultraviewer itself
"$PYTHON" -m pip install --user --no-deps "$SCRIPT_DIR"

echo ""
echo "Installation complete!"
echo "Run:  $PYTHON -m ultraviewer --port 8080"
