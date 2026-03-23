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
