"""Deep-pass tests: receipt grammar, run snapshot, matrix coverage."""
from __future__ import annotations

from pathlib import Path

import pytest

from cmplx.morphon import MorphonController
from cmplx.receipt.provider import ReceiptProvider
from cmplx.receipt.types import ReceiptType
from cmplx.snap import SNAPEngine
from cmplx.snap.gate369 import Body, Predicate


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_label_mints_post_on_receipt_spine(monkeypatch):
    monkeypatch.setenv("SNAP_MINT_RECEIPT", "1")
    MorphonController.get().register("receipt", ReceiptProvider())
    eng = SNAPEngine()
    eng.label("e8 lattice", key="e8")
    rec = MorphonController.get().get_provider("receipt").chain._chain[-1]
    assert rec.receipt_type == ReceiptType.POST.value
    assert rec.payload.get("snap_op") == "label"


def test_gate369_failure_mints_gate_receipt(monkeypatch):
    monkeypatch.setenv("SNAP_MINT_RECEIPT", "1")
    MorphonController.get().register("receipt", ReceiptProvider())
    eng = SNAPEngine()
    bodies = [Body(id="a"), Body(id="b")]
    eng.process_gate369(bodies, [Predicate(name="p")])
    rec = MorphonController.get().get_provider("receipt").chain._chain[-1]
    assert rec.receipt_type in (ReceiptType.GATE.value, ReceiptType.PROCESS.value)


def test_mint_run_snapshot_writes_jsonl(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SNAP_MINT_RECEIPT", "0")
    ws = tmp_path / "ws"
    eng = SNAPEngine()
    eng.label("x", key="x")
    rec = eng.mint_run_snapshot(ws, "run-a", "s0", mirror_to_receipt_port=False)
    assert rec.get("receipt_hash")
    ledger = ws / "runs" / "run-a" / "ledger.jsonl"
    assert ledger.exists()


def test_ledger_export_shape():
    eng = SNAPEngine()
    eng.label(1, key="n")
    exp = eng.ledger_export()
    assert exp["length"] == 1
    assert exp["verified"] is True
    assert exp["entries"][0]["op"] == "label"


def test_snap_tx_hash_in_receipt_payload(monkeypatch):
    monkeypatch.setenv("SNAP_MINT_RECEIPT", "1")
    MorphonController.get().register("receipt", ReceiptProvider())
    eng = SNAPEngine()
    eng.label("z", key="z")
    rec = MorphonController.get().get_provider("receipt").chain._chain[-1]
    assert rec.payload.get("snap_tx_hash") or rec.payload.get("tx_hash")
