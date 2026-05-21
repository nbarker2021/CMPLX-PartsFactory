"""SNAP labels carry explicit morphon / TarPit linkage context."""
from __future__ import annotations

import pytest

from cmplx.morphon import Morphon
from cmplx.morphon.links import link_labels
from cmplx.snap import SNAPEngine, label_context_from_morphon, enrich_label_from_morphon
from cmplx.snap.labeler import SNAPLabeler


def test_label_context_from_morphon_includes_snap_key():
    m = Morphon.forge(payload={"concat": "12345678", "snap_key": "sk-1"})
    ctx = label_context_from_morphon(m, base={"text": "chunk"})
    assert ctx["morphon_id"] == m.id
    assert ctx["snap_key"] == "sk-1"
    assert ctx["concat"] == "12345678"


def test_label_context_includes_tarpit_linkage():
    m = Morphon.forge(payload={"concat": "aaaaaaaa"})
    m = m.annotate_links(**link_labels(m, tarpit_atom_id="deadbeef1234"))
    ctx = label_context_from_morphon(m)
    assert ctx["linkage_kind"] == "morphon_tarpit"
    assert ctx["tarpit_atom_id"] == "deadbeef1234"
    assert ctx["morphon_id"] == m.id


def test_engine_label_with_morphon_enriches_custom():
    eng = SNAPEngine()
    m = Morphon.forge(payload={"concat": "abcdefgh", "snap_key": "key-9"})
    m = m.annotate_links(**link_labels(m, tarpit_atom_id="cafebabe1234"))
    label = eng.label("abcdefgh", key=m.id, morphon=m)
    assert "tarpit_linked" in label.semantic
    assert "morphon_tarpit" in label.custom.get("linkage_kind", set())
    assert m.id in label.custom.get("morphon_id", set())


def test_labeler_context_morphonic_domain_with_linkage_text():
    labeler = SNAPLabeler()
    m = Morphon.forge(payload={"text": "morphon substrate", "snap_key": "k"})
    ctx = label_context_from_morphon(m, base={"text": "morphon substrate pipeline"})
    label = labeler.label("morphon substrate", key="t", context=ctx)
    enrich_label_from_morphon(label, m)
    assert "morphon" in label.domain or "morphonic" in label.domain
