import time
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
    # Run again to create second run (sleep to ensure different timestamp)
    time.sleep(1.1)
    client.post(f"/api/suites/{suite_with_results}/run")
    resp = client.get(f"/api/suites/{suite_with_results}/results/history")
    assert resp.status_code == 200
    runs = resp.json()
    assert len(runs) >= 2

def test_get_nonexistent_results(client):
    resp = client.get("/api/suites/999/results")
    assert resp.status_code == 404
