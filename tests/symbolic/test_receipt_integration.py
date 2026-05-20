"""TarPit receipt bridge integration."""
from __future__ import annotations

import pytest

from cmplx.morphon import Morphon, MorphonController
from cmplx.receipt.provider import ReceiptProvider
from cmplx.receipt.types import ReceiptType
from cmplx.symbolic.tarpit import TarPitSymbolicProvider
from cmplx.symbolic.tarpit._receipt_bridge import tarpit_mint_receipt_enabled


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_tarpit_mint_env_toggle(monkeypatch):
    monkeypatch.setenv("TARPIT_MINT_RECEIPT", "0")
    assert not tarpit_mint_receipt_enabled()
    monkeypatch.setenv("TARPIT_MINT_RECEIPT", "1")
    assert tarpit_mint_receipt_enabled()


def test_derive_mints_etp_receipts(monkeypatch):
    monkeypatch.setenv("TARPIT_MINT_RECEIPT", "1")
    MorphonController.get().register("receipt", ReceiptProvider())
    prov = TarPitSymbolicProvider(program_length=8, default_max_steps=16)
    m = Morphon.forge(payload={"x": 1})
    report = prov.derive(m)
    assert report.summary
    rec = MorphonController.get().get_provider("receipt").chain._chain[-1]
    assert rec.receipt_type in (
        ReceiptType.PROCESS.value,
        ReceiptType.GATE.value,
        ReceiptType.DEATH.value,
    )
    assert rec.payload.get("tarpit_op") == "etp_step"
