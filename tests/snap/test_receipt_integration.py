"""SNAP ↔ receipt spine integration."""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from cmplx.receipt.provider import ReceiptProvider
from cmplx.snap import SNAPEngine
from cmplx.snap._receipt_bridge import snap_mint_receipt_enabled
from cmplx.snap.gate369 import Body, Gate369Engine, Predicate


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_snap_mint_env_default_on():
    assert snap_mint_receipt_enabled()


def test_engine_mints_receipt_on_label(monkeypatch):
    monkeypatch.setenv("SNAP_MINT_RECEIPT", "1")
    MorphonController.get().register("receipt", ReceiptProvider())
    eng = SNAPEngine()
    eng.label("hello", key="h")
    chain = MorphonController.get().get_provider("receipt").chain
    assert len(chain._chain) >= 1


def test_engine_mints_receipt_off(monkeypatch):
    monkeypatch.setenv("SNAP_MINT_RECEIPT", "0")
    MorphonController.get().register("receipt", ReceiptProvider())
    eng = SNAPEngine()
    eng.label("x", key="x")
    chain = MorphonController.get().get_provider("receipt").chain
    assert len(chain._chain) == 0


def test_ledger_and_receipt_both_grow_on_label(monkeypatch):
    monkeypatch.setenv("SNAP_MINT_RECEIPT", "1")
    MorphonController.get().register("receipt", ReceiptProvider())
    eng = SNAPEngine()
    eng.label("dual", key="d")
    assert eng.ledger.length == 1
    assert eng.ledger.verify()
    assert len(MorphonController.get().get_provider("receipt").chain._chain) >= 1


def test_gate369_mints_gate_when_not_crystallized(monkeypatch):
    monkeypatch.setenv("SNAP_MINT_RECEIPT", "1")
    MorphonController.get().register("receipt", ReceiptProvider())
    eng = SNAPEngine()
    bodies = [Body(id=str(i), payload=i) for i in range(2)]
    eng.process_gate369(bodies, [Predicate(name="p")])
    assert eng.ledger.length >= 1
