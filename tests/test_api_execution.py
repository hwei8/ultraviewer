import json
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
        "script": {
            "interpreter": "bash",
            "script_path": str(script),
            "timeout_seconds": 10,
        }
    })
    return suite_id

def test_run_suite(client, configured_suite):
    resp = client.post(f"/api/suites/{configured_suite}/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["passed"] == 3

def test_run_single_leaf(client, configured_suite):
    resp = client.post(f"/api/suites/{configured_suite}/run/case_1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["result"]["name"] == "case_1"

def test_run_nonexistent_suite(client):
    resp = client.post("/api/suites/999/run")
    assert resp.status_code == 404

def test_test_script(client, configured_suite):
    resp = client.post(f"/api/suites/{configured_suite}/test-script")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
