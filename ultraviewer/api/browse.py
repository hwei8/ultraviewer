import os
from fastapi import APIRouter, Query

router = APIRouter(tags=["browse"])

@router.get("/api/browse")
async def browse_directory(path: str = Query(default="~")):
    """List directories at the given path for the folder browser."""
    expanded = os.path.expanduser(path)
    if not os.path.isdir(expanded):
        return {"path": expanded, "parent": os.path.dirname(expanded), "entries": [], "error": "Not a directory"}

    entries = []
    try:
        for name in sorted(os.listdir(expanded)):
            full = os.path.join(expanded, name)
            if name.startswith('.'):
                continue
            if os.path.isdir(full):
                entries.append({"name": name, "path": os.path.abspath(full), "type": "dir"})
            else:
                entries.append({"name": name, "path": os.path.abspath(full), "type": "file"})
    except PermissionError:
        return {"path": os.path.abspath(expanded), "parent": os.path.dirname(os.path.abspath(expanded)), "entries": [], "error": "Permission denied"}

    return {
        "path": os.path.abspath(expanded),
        "parent": os.path.dirname(os.path.abspath(expanded)),
        "entries": entries,
    }
