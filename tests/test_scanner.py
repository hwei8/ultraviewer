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
