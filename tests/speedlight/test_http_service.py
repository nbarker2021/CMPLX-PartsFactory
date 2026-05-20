"""HTTP adapter tests for SpeedLight (:8843)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cmplx.speedlight._adapters import http_service


@pytest.fixture
def client():
    return TestClient(http_service.app)


def test_http_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_http_cache_put_get_roundtrip(client):
    put = client.post("/v1/cache", json={"key": "k1", "value": {"n": 1}, "ttl": 60})
    assert put.status_code == 200
    got = client.get("/v1/cache/k1")
    assert got.status_code == 200
    assert got.json()["value"] == {"n": 1}


def test_http_receipt_lookup_by_task(client):
    prov = http_service.get_provider()
    _, _, comp = prov.compute("task-a", lambda: 7)
    r = client.get(f"/v1/receipts/{comp.receipt_id}")
    assert r.status_code == 200
    assert r.json()["task_id"] == "task-a"
