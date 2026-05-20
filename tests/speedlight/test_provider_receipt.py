"""Provider dual-receipt and mint helpers."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from cmplx.morphon import MorphonController
from cmplx.receipt.provider import ReceiptProvider
from cmplx.speedlight.provider import SpeedLightProvider


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_computation_receipt_on_cache_miss():
    prov = SpeedLightProvider()
    _, cost1, r1 = prov.compute("t-miss", lambda: 99)
    _, cost2, r2 = prov.compute("t-miss", lambda: 99)
    assert cost1 >= 0
    assert r1.receipt_id
    assert r2.receipt_id == r1.receipt_id


def test_provider_mints_post_receipt_on_snapshot(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SPEEDLIGHT_MINT_RECEIPT", "0")
    prov = SpeedLightProvider()
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "runs" / "r1").mkdir(parents=True)
    rec = prov.mint_cache_snapshot(ws, "r1", "s1", task_id="snap-1", outputs={"v": 1})
    assert rec.get("receipt_hash")


def test_provider_mints_on_miss_when_enabled(monkeypatch):
    monkeypatch.setenv("SPEEDLIGHT_MINT_RECEIPT", "1")
    MorphonController.get().register("receipt", ReceiptProvider())
    prov = SpeedLightProvider()
    prov.compute("mint-me", lambda: 1)
    chain = MorphonController.get().get_provider("receipt").chain
    assert len(chain._chain) >= 1


def test_sidecar_shim_import():
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from cmplx.speedlight._persistence import sidecar_ledger  # noqa: F401

        assert sidecar_ledger.SpeedLightV2 is not None
