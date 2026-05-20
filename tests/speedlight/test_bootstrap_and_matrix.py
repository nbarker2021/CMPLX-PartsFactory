"""Bootstrap port registration and matrix-backed smoke tests."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from cmplx.morphon import MorphonController
from cmplx.speedlight import SpeedLightProvider
from cmplx.speedlight.provider import _mint_receipt_on_miss_enabled


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_bootstrap_cache_port_registers():
    from runtime.cmplx_bootstrap import register_all

    register_all()
    prov = MorphonController.get().get_provider("cache")
    assert prov is not None
    assert prov.name == "speedlight_provider"


def test_mint_receipt_env_default_on():
    assert _mint_receipt_on_miss_enabled()


def test_mint_receipt_env_off(monkeypatch):
    monkeypatch.setenv("SPEEDLIGHT_MINT_RECEIPT", "0")
    assert not _mint_receipt_on_miss_enabled()


def test_provider_health_shape():
    h = SpeedLightProvider().health
    assert h["ok"] is True
    assert "cache" in h


def test_mint_cache_snapshot_writes_ledger(tmp_path: Path):
    ws = tmp_path / "ws"
    (ws / "runs" / "r1").mkdir(parents=True)
    prov = SpeedLightProvider()
    rec = prov.mint_cache_snapshot(ws, "r1", "s1", outputs={"done": True})
    assert (ws / "runs" / "r1" / "ledger.jsonl").exists()
    assert rec.get("receipt_id")


def test_sidecar_ledger_reexport():
    from cmplx.speedlight._persistence.sidecar_ledger import MerkleLedger, SpeedLightV2

    assert MerkleLedger is not None
    assert SpeedLightV2 is not None


def test_http_module_port_default():
    from cmplx.speedlight._adapters import http_service

    assert http_service.PORT == 8843


def test_compute_caches_second_call_matrix():
    sl = SpeedLightProvider()
    calls = []

    def fn():
        calls.append(1)
        return 42

    sl.compute("m1", fn)
    sl.compute("m1", fn)
    assert len(calls) == 1


def test_worldline_unattached_by_default():
    prov = SpeedLightProvider()
    assert prov.worldline is None
