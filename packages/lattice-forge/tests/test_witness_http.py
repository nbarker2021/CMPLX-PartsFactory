"""HTTP witness routes on CMPLX forge adapter."""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from starlette.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_OVERLAY_ROOT", str(tmp_path / "overlay"))
    from cmplx.worlds.forge._adapters import http_service

    http_service.reset_provider(str(tmp_path / "overlay"))
    return TestClient(http_service.app)


def test_witness_spec(client):
    response = client.get("/witness/spec")
    assert response.status_code == 200
    assert "/witness/regime-c/encode" in response.json()["endpoints"]


def test_witness_regime_c_and_syndrome(client):
    regime = client.post("/witness/regime-c/encode", json={"max_depth": 64})
    assert regime.status_code == 200
    assert regime.json()["kind"] == "regime_c"

    syndrome = client.post("/witness/syndrome", json={"syndrome_keys": ["ecc_shed"]})
    assert syndrome.status_code == 200
    assert syndrome.json()["kind"] == "syndrome"


def test_deprecated_mint_route_returns_deprecation_header(client):
    response = client.post(
        "/witness/regime-a/query-mint",
        json={"n": 10, "max_depth": 128, "base_page": 64},
    )
    assert response.status_code == 200
    assert response.headers.get("deprecation") or response.headers.get("Deprecation")
