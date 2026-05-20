"""Six pair-combination methods + serialization with CQE fields."""
from __future__ import annotations

import pytest

from cmplx.morphon import (
    CombineMethod,
    Morphon,
    MorphonController,
    combine_pair,
    is_tarpit_linked,
)
from cmplx.morphon.links import link_labels
from cmplx.receipt.provider import ReceiptProvider
from cmplx.receipt.types import ReceiptType
from cmplx.symbolic.tarpit.provider import TarPitSymbolicProvider


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_combine_merge_new_id_and_parents():
    a = Morphon.forge(payload={"x": 1, "concat": "11111111"})
    b = Morphon.forge(payload={"y": 2, "concat": "22222222"})
    c = combine_pair(a, b, CombineMethod.MERGE)
    assert isinstance(c, Morphon)
    assert c.id != a.id
    assert c.payload["combination"] == "merge"
    assert c.payload["parents"] == [a.id, b.id]
    assert c.payload["x"] == 1 and c.payload["y"] == 2


def test_combine_concat_joins_concat_field():
    a = Morphon.forge(payload={"concat": "abcd"})
    b = Morphon.forge(payload={"concat": "efgh"})
    c = combine_pair(a, b, CombineMethod.CONCAT)
    assert c.payload["concat"] == "abcd0000efgh0000"


def test_combine_quad_sets_cqe_fields():
    a = Morphon.forge(payload={"text": "alpha"})
    b = Morphon.forge(payload={"text": "beta"})
    c = combine_pair(a, b, CombineMethod.QUAD)
    assert c.quad_encoding is not None
    assert c.digital_root is not None
    assert c.payload["combination"] == "quad"


def test_combine_inherit_link_explicit_labels():
    a = Morphon.forge(payload={"concat": "aaaaaaaa"})
    labels = link_labels(a, tarpit_atom_id="abc123abc123", derivation_hash="h1")
    a = a.annotate_links(**labels)
    b = Morphon.forge(payload={"concat": "bbbbbbbb"})
    c = combine_pair(a, b, CombineMethod.INHERIT_LINK)
    assert is_tarpit_linked(c.payload)
    assert c.payload["tarpit_atom_id"] == "abc123abc123"
    assert c.payload["morphon_id"] == c.id
    assert c.payload["linkage_inherited_from"] == a.id


def test_controller_combine_mints_birth():
    MorphonController.get().register("receipt", ReceiptProvider())
    a = Morphon.forge(payload={})
    b = Morphon.forge(payload={})
    c = MorphonController.get().combine(a, b, "merge")
    prov = MorphonController.get().get_provider("receipt")
    assert prov.chain._chain[-1].receipt_type == ReceiptType.BIRTH.value
    assert prov.chain._chain[-1].atom_id == c.id


def test_serialize_roundtrip_cqe_and_linkage():
    MorphonController.get().register("symbolic", TarPitSymbolicProvider())
    m = Morphon.forge(payload={"concat": "12345678"})
    _atom_out, linked = MorphonController.get().get_provider("symbolic").probe_atom_for_morphon(m)
    linked.quad_encoding = (1, 2, 3, 4)
    linked.digital_root = 1
    blob = linked.serialize()
    back = Morphon.deserialize(blob)
    assert back.id == linked.id
    assert is_tarpit_linked(back.payload)
    assert back.quad_encoding == (1, 2, 3, 4)
    assert back.digital_root == 1
