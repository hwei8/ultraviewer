import pytest

@pytest.fixture
def tab_id(client):
    resp = client.post("/api/tabs", json={"name": "Test Tab"})
    return resp.json()["id"]

def test_create_suite(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={"name": "Login Module", "folder_path": str(sample_folders)})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Login Module"
    assert data["folder_path"] == str(sample_folders)

def test_list_suites(client, tab_id, sample_folders):
    client.post(f"/api/tabs/{tab_id}/suites", json={"name": "A", "folder_path": str(sample_folders)})
    client.post(f"/api/tabs/{tab_id}/suites", json={"name": "B", "folder_path": str(sample_folders)})
    resp = client.get(f"/api/tabs/{tab_id}/suites")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

def test_update_suite_basic(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={"name": "Old", "folder_path": str(sample_folders)})
    suite_id = resp.json()["id"]
    resp = client.put(f"/api/suites/{suite_id}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"

def test_update_suite_script(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={"name": "S", "folder_path": str(sample_folders)})
    suite_id = resp.json()["id"]
    resp = client.put(f"/api/suites/{suite_id}", json={
        "script": {"interpreter": "bash", "script_path": "/scripts/run.sh", "timeout_seconds": 60,
            "extra_args": [{"key": "--golden", "value": "/golden"}],
            "env_vars": [{"key": "MODE", "value": "test"}], "max_parallel": 4}
    })
    assert resp.status_code == 200
    assert resp.json()["script"]["interpreter"] == "bash"
    assert resp.json()["script"]["max_parallel"] == 4

def test_update_suite_rendering(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={"name": "S", "folder_path": str(sample_folders)})
    suite_id = resp.json()["id"]
    resp = client.put(f"/api/suites/{suite_id}", json={
        "rendering": {"render_mode": "table", "config": {"columns": ["name", "status"]}}
    })
    assert resp.status_code == 200
    assert resp.json()["rendering"]["render_mode"] == "table"

def test_delete_suite(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={"name": "X", "folder_path": str(sample_folders)})
    suite_id = resp.json()["id"]
    resp = client.delete(f"/api/suites/{suite_id}")
    assert resp.status_code == 204

def test_get_leaves(client, tab_id, sample_folders):
    resp = client.post(f"/api/tabs/{tab_id}/suites", json={"name": "S", "folder_path": str(sample_folders)})
    suite_id = resp.json()["id"]
    resp = client.get(f"/api/suites/{suite_id}/leaves")
    assert resp.status_code == 200
    leaves = resp.json()
    assert len(leaves) == 3
    names = [l["name"] for l in leaves]
    assert sorted(names) == ["case_1", "case_2", "case_3"]
