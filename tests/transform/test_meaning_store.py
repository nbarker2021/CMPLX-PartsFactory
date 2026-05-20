"""Tests for AddressMeaningStore."""
from __future__ import annotations

from cmplx.transform.meaning_store import AddressMeaningStore


def test_meaning_crud_and_query(tmp_path):
    db = tmp_path / "idx.sqlite"
    store = AddressMeaningStore(db)
    store.upsert(
        snap_key="snap-1",
        lane="L1",
        digital_root=3,
        label="morphonic transformer",
        label_source="ingest",
        source_doc="identity_review/EVIDENCE_LAYER_MAP.md",
        source_span="chunk:0",
    )
    by_label = store.by_label("morphonic")
    assert len(by_label) == 1
    assert by_label[0].snap_key == "snap-1"
    by_snap = store.by_snap_key("snap-1")
    assert len(by_snap) == 1
    assert store.count() == 1
    store.close()
