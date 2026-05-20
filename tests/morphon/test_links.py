"""Explicit morphon ↔ TarPit atom linkage."""
from __future__ import annotations

from cmplx.morphon import (
    Morphon,
    MorphonController,
    MorphonSubstrateProvider,
    decode_link_from_payload,
    is_tarpit_linked,
    link_morphon_to_tarpit_atom,
)
from cmplx.morphon.links import KEY_MORPHON_ID, KEY_TARPIT_ATOM_ID, LINKAGE_MORPHON_TARPIT
from cmplx.receipt.provider import ReceiptProvider
from cmplx.symbolic.tarpit.provider import TarPitSymbolicProvider


def test_link_morphon_to_tarpit_atom_explicit_labels():
    m = Morphon.forge(payload={"concat": "abcd1234"})
    atom_out = {
        "atom": {"atom_id": "deadbeef1234", "mass": 0.5},
        "derivation_hash": "abc123",
    }
    linked = link_morphon_to_tarpit_atom(m, atom_out, tarpit_program="}01")
    assert linked.id == m.id
    assert is_tarpit_linked(linked.payload)
    assert linked.payload[KEY_MORPHON_ID] == m.id
    assert linked.payload[KEY_TARPIT_ATOM_ID] == "deadbeef1234"
    assert linked.payload["linkage_kind"] == LINKAGE_MORPHON_TARPIT
    decoded = decode_link_from_payload(linked.payload)
    assert decoded is not None
    assert decoded["morphon_id"] == m.id


def test_probe_atom_for_morphon_integration():
    MorphonController.reset_for_tests()
    MorphonController.get().register("receipt", ReceiptProvider())
    MorphonController.get().register("symbolic", TarPitSymbolicProvider())
    m = Morphon.forge(payload={"text": "link-test"})
    sym = MorphonController.get().get_provider("symbolic")
    atom_out, linked = sym.probe_atom_for_morphon(m)
    assert linked.id == m.id
    assert is_tarpit_linked(linked.payload)
    assert atom_out["atom"]["atom_id"] == linked.payload[KEY_TARPIT_ATOM_ID]


def test_substrate_pipeline_link_only():
    MorphonController.reset_for_tests()
    MorphonController.get().register("receipt", ReceiptProvider())
    MorphonController.get().register("symbolic", TarPitSymbolicProvider())
    sub = MorphonSubstrateProvider()
    out = sub.pipeline({"concat": "12345678"}, link_tarpit=True, admit_and_store=False)
    assert out["linkage_explicit"] is True
    assert out["linkage"]["morphon_id"] == out["morphon_id"]
    assert out["tarpit_atom"]["atom_id"] == out["linkage"]["tarpit_atom_id"]
