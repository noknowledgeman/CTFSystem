import pytest
from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
