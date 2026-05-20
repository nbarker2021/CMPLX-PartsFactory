"""Morphon → cmplx.receipt spine wiring (slots 10–11)."""
from __future__ import annotations

import os

import pytest

from cmplx.morphon import Morphon, MorphonController, MorphonState
from cmplx.morphon._receipt_bridge import mint_morphon_event, morphon_mint_receipt_enabled
from cmplx.receipt.provider import ReceiptProvider
from cmplx.receipt.types import ReceiptType


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


@pytest.fixture
def receipt_provider():
    prov = ReceiptProvider()
    MorphonController.get().register("receipt", prov)
    return prov


def test_mint_enabled_default():
    assert morphon_mint_receipt_enabled()


def test_forge_mints_birth_on_receipt_port(receipt_provider):
    m = Morphon.forge(payload={"x": 1})
    assert m.payload["identity_kind"] == "morphon"
    assert len(receipt_provider.chain._chain) >= 1
    last = receipt_provider.chain._chain[-1]
    assert last.receipt_type == ReceiptType.BIRTH.value
    assert last.atom_id == m.id


def test_etp_derived_identity_kind():
    m = Morphon.forge(payload={"etp_decode": True, "steps": 1})
    assert m.payload["identity_kind"] == "morphon_etp_derived"


def test_transition_mints_crossing(receipt_provider):
    m = Morphon.forge(payload={})
    n_before = len(receipt_provider.chain._chain)
    m.transition_to(MorphonState.VALIDATING)
    assert len(receipt_provider.chain._chain) > n_before
    assert receipt_provider.chain._chain[-1].receipt_type == ReceiptType.CROSSING.value


def test_register_mints_assign(receipt_provider):
    class _Fake:
        name = "fake_addressing"

        def channel_for(self, morphon):
            return 3

    MorphonController.get().register("addressing", _Fake())
    assert receipt_provider.chain._chain[-1].receipt_type == ReceiptType.ASSIGN.value


def test_gate_miss_mints_gate(receipt_provider):
    with pytest.raises(LookupError):
        MorphonController.get().get_provider("geometry")
    assert receipt_provider.chain._chain[-1].receipt_type == ReceiptType.GATE.value


def test_mint_disabled(monkeypatch):
    monkeypatch.setenv("MORPHON_MINT_RECEIPT", "0")
    prov = ReceiptProvider()
    MorphonController.get().register("receipt", prov)
    n0 = len(prov.chain._chain)
    mint_morphon_event("forge", morphon_id="x")
    assert len(prov.chain._chain) == n0
