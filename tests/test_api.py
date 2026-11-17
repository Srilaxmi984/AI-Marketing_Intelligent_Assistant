"""API endpoint integration tests."""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_serve_static_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI Marketing Intelligence Assistant" in resp.text
    assert "auditForm" in resp.text


def test_api_invalid_url_scheme(client):
    resp = client.post("/api/audit", json={"url": "ftp://example.com/site"})
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"]["code"] == "INVALID_URL"


def test_api_blocked_private_target(client):
    resp = client.post("/api/audit", json={"url": "http://127.0.0.1/admin"})
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == "BLOCKED_TARGET"


def test_api_max_pages_out_of_range(client):
    # Max pages cap is 100
    resp1 = client.post("/api/audit", json={"url": "https://example.com", "max_pages": 150})
    assert resp1.status_code == 422
    assert resp1.json()["error"]["code"] == "INVALID_REQUEST"
    assert "max_pages" in resp1.json()["error"]["message"]

    # Max pages min is 1
    resp2 = client.post("/api/audit", json={"url": "https://example.com", "max_pages": 0})
    assert resp2.status_code == 422
    assert resp2.json()["error"]["code"] == "INVALID_REQUEST"


def test_api_missing_body(client):
    resp = client.post("/api/audit", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "INVALID_REQUEST"
    assert "url" in body["error"]["message"]  # names the missing field, no raw exception dump
    assert "Traceback" not in body["error"]["message"]
