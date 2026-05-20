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
    body = r.json()
    assert "result" in body or "summary" in body or "ledger" in body


def test_http_encode(client):
    r = client.post("/encode", json={"payload": {"text": "hello"}})
    assert r.status_code == 200
    assert len(r.json()["program"]) >= 1


def test_http_aggregate_glyph_mode(client):
    r = client.post("/run", json={"program": "🧠", "mode": "glyph", "max_steps": 30})
    assert r.status_code == 200
    body = r.json()
    assert "session" in body or "result" in body


def test_http_evolve(client):
    r = client.post("/evolve", json={"program": "}01", "iterations": 2})
    assert r.status_code == 200
    assert r.json()["canonical_form"] == "evolving_tarpit"
