"""HTTP adapter tests — ReceiptChain delegation (no duplicate _chain)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from cmplx.receipt._adapters import http_service


def test_health_reports_chain_delegate():
    client = TestClient(http_service.app)
    http_service._provider.chain.clear()
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["chain_length"] == 0
    assert "head" in body


def test_mint_and_verify_via_chain():
    client = TestClient(http_service.app)
    http_service._provider.chain.clear()
    minted = client.post(
        "/mint",
        json={
            "receipt_type": "PROCESS",
            "agent_id": "alice",
            "atom_id": "a1",
            "operation": "test-op",
        },
    )
    assert minted.status_code == 200
    data = minted.json()
    assert data["receipt_hash"]
    assert http_service._provider.length == 1

    verified = client.post("/verify", json={})
    assert verified.status_code == 200
    assert verified.json()["valid"] is True


def test_permissive_legacy_type():
    client = TestClient(http_service.app)
    http_service._provider.chain.clear()
    r = client.post(
        "/mint",
        json={"receipt_type": "morphon.created", "operation": "create"},
    )
    assert r.status_code == 200
    assert r.json()["receipt_type"] == "MINT"


def test_mint_operation_on_chain():
    from cmplx.receipt import ReceiptChain

    chain = ReceiptChain()
    op = chain.mint_operation(
        "test_claim",
        {"x": 1},
        {"x": 2},
        also_mint_spine=True,
    )
    assert op.sequence == 1
    assert chain.length == 1
