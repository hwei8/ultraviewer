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


def test_websocket_execution(client, configured_suite):
    with client.websocket_connect(f"/ws/execution/{configured_suite}") as ws:
        data = ws.receive_json()
        assert data["event"] == "run_started"
        assert data["total"] == 3

        events = []
        for _ in range(6):  # 3 leaves × 2 events each (started + completed)
            events.append(ws.receive_json())

        final = ws.receive_json()
        assert final["event"] == "run_completed"
        assert final["passed"] == 3


def test_run_suite_with_error_script(client, sample_folders, tmp_path):
    """Test that script errors are captured properly."""
    script = tmp_path / "bad_script.sh"
    script.write_text('#!/bin/bash\nexit 1\n')
    script.chmod(0o755)

    resp = client.post("/api/tabs", json={"name": "ErrTab"})
    tab_id = resp.json()["id"]
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={
        "name": "ErrSuite", "folder_path": str(sample_folders),
    })
    suite_id = resp.json()["id"]
    client.put(f"/api/suites/{suite_id}", json={
        "script": {"interpreter": "bash", "script_path": str(script), "timeout_seconds": 10}
    })

    resp = client.post(f"/api/suites/{suite_id}/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["failed"] == 3
    assert data["passed"] == 0


def test_run_suite_no_leaves(client, tmp_path):
    """Test running a suite with an empty folder."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    resp = client.post("/api/tabs", json={"name": "EmptyTab"})
    tab_id = resp.json()["id"]
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={
        "name": "EmptySuite", "folder_path": str(empty_dir),
    })
    suite_id = resp.json()["id"]

    script = tmp_path / "dummy.sh"
    script.write_text('#!/bin/bash\necho "{}"\n')
    script.chmod(0o755)
    client.put(f"/api/suites/{suite_id}", json={
        "script": {"interpreter": "bash", "script_path": str(script), "timeout_seconds": 10}
    })

    resp = client.post(f"/api/suites/{suite_id}/run")
    assert resp.status_code == 400


def test_run_selected_leaves(client, configured_suite):
    """Test running only selected leaves."""
    resp = client.post(
        f"/api/suites/{configured_suite}/run-selected",
        json=["case_1", "case_3"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["passed"] == 2
    leaf_names = [r["leaf"] for r in data["results"]]
    assert "case_1" in leaf_names
    assert "case_3" in leaf_names
    assert "case_2" not in leaf_names


def test_run_selected_empty_list(client, configured_suite):
    """Test running with empty selection returns 400."""
    resp = client.post(
        f"/api/suites/{configured_suite}/run-selected",
        json=[],
    )
    assert resp.status_code == 400


def test_run_selected_missing_leaf(client, configured_suite):
    """Test running with nonexistent leaf name returns 404."""
    resp = client.post(
        f"/api/suites/{configured_suite}/run-selected",
        json=["case_1", "nonexistent_case"],
    )
    assert resp.status_code == 404
