"""HTTP adapter for TarPit (:8844)."""
from __future__ import annotations


def test_http_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_http_canonical_forms(client):
    r = client.get("/canonical-forms")
    assert r.status_code == 200
    forms = r.json()["forms"]
    assert "evolving_tarpit" in forms
    assert "glyphic_tarpit" in forms
    assert "unified_tarpit" in forms


def test_http_run_program(client):
    r = client.post("/run", json={"program": "}01", "max_steps": 20})
    assert r.status_code == 200
    assert "summary" in r.json() or "ledger" in r.json()


def test_http_encode(client):
    r = client.post("/encode", json={"payload": {"text": "hello"}})
    assert r.status_code == 200
    assert len(r.json()["program"]) >= 1
