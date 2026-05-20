"""HTTP adapter for SNAP (:8823)."""
from __future__ import annotations


def test_http_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_http_gate369_items(client):
    r = client.post("/gate369", json={"items": ["a", "b", "c"], "context": "t"})
    assert r.status_code == 200
    assert "ennead" in r.json()


def test_http_stratify(client):
    r = client.post("/stratify", json={"concept": "E8 lattice", "depth": 2})
    assert r.status_code == 200
    assert "labels" in r.json()


def test_http_taxonomy(client):
    r = client.get("/taxonomy")
    assert r.status_code == 200
    assert "lenses" in r.json()


def test_http_angles(client):
    r = client.get("/angles")
    assert r.status_code == 200
    assert "angles" in r.json()


def test_http_ledger_verify(client):
    client.post("/v1/label", json={"item": "a", "key": "a"})
    r = client.get("/ledger/verify")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_http_evaluate_lenses(client):
    r = client.post(
        "/evaluate_lenses",
        json={
            "state": {"mirror_pass": True, "polarity_conflict": 0.0, "containment_c": 0.9},
            "lens": "base",
        },
    )
    assert r.status_code == 200
    assert r.json()["verdict"] == "pass"


def test_http_run_snapshot(client, tmp_path):
    ws = str(tmp_path / "ws")
    r = client.post(
        "/v1/run-snapshot",
        json={"workspace": ws, "run_id": "r1", "step_id": "s0"},
    )
    assert r.status_code == 200
    assert r.json().get("receipt_hash")


def test_http_tick(client):
    r = client.post("/tick", json={})
    assert r.status_code == 200
    assert r.json()["ledger_length"] >= 1
