import os


def test_browse_directory(client, tmp_path):
    """Test browsing a directory returns its entries."""
    (tmp_path / "subdir_a").mkdir()
    (tmp_path / "subdir_b").mkdir()
    (tmp_path / "file.txt").write_text("hello")

    resp = client.get(f"/api/browse?path={tmp_path}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == str(tmp_path)
    names = [e["name"] for e in data["entries"]]
    assert "subdir_a" in names
    assert "subdir_b" in names
    assert "file.txt" in names
    # Check types
    types = {e["name"]: e["type"] for e in data["entries"]}
    assert types["subdir_a"] == "dir"
    assert types["file.txt"] == "file"


def test_browse_nonexistent(client):
    resp = client.get("/api/browse?path=/nonexistent/path/xyz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] == "Not a directory"


def test_browse_default_home(client):
    resp = client.get("/api/browse?path=~")
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == os.path.expanduser("~")


def test_browse_hidden_files_excluded(client, tmp_path):
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "visible").mkdir()

    resp = client.get(f"/api/browse?path={tmp_path}")
    data = resp.json()
    names = [e["name"] for e in data["entries"]]
    assert "visible" in names
    assert ".hidden" not in names
