import pytest
from fastapi.testclient import TestClient

def test_create_tab(client):
    resp = client.post("/api/tabs", json={"name": "Smoke Tests"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Smoke Tests"
    assert "id" in data

def test_list_tabs(client):
    client.post("/api/tabs", json={"name": "Tab A", "position": 0})
    client.post("/api/tabs", json={"name": "Tab B", "position": 1})
    resp = client.get("/api/tabs")
    assert resp.status_code == 200
    tabs = resp.json()
    assert len(tabs) == 2
    assert tabs[0]["name"] == "Tab A"

def test_update_tab(client):
    resp = client.post("/api/tabs", json={"name": "Old Name"})
    tab_id = resp.json()["id"]
    resp = client.put(f"/api/tabs/{tab_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"

def test_delete_tab(client):
    resp = client.post("/api/tabs", json={"name": "To Delete"})
    tab_id = resp.json()["id"]
    resp = client.delete(f"/api/tabs/{tab_id}")
    assert resp.status_code == 204
    resp = client.get("/api/tabs")
    assert len(resp.json()) == 0

def test_delete_nonexistent_tab(client):
    resp = client.delete("/api/tabs/999")
    assert resp.status_code == 404
