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
    """Create a sample folder structure for testing."""
    root = tmp_path / "suite_root"
    root.mkdir()
    for name in ["case_1", "case_2", "case_3"]:
        (root / name).mkdir()
        (root / name / "data.txt").write_text(f"data for {name}")
    return root
