#!/bin/bash
# Install UltraViewer dependencies on an offline machine
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
pip install --user --no-index --find-links "$SCRIPT_DIR/offline-packages/" websockets aiosqlite
echo "Dependencies installed. Run: python -m ultraviewer --port 8080"
