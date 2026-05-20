"""Tests for translation_links schema."""
from __future__ import annotations

from cmplx.transform.token_index.store import TokenIndexStore
from cmplx.transform.translation_store import TranslationLinkStore


def test_translation_links_upsert_and_query(tmp_path):
    db = tmp_path / "idx.sqlite"
    store = TokenIndexStore(db)
    links = TranslationLinkStore.from_connection(store._conn, str(db))
    links.upsert(
        translation_key="doc:0",
        stream="en",
        concat="baaaaaab",
        snap_key="snap-en",
    )
    links.upsert(
        translation_key="doc:0",
        stream="native",
        concat="bonjourxx",
        snap_key="snap-fr",
    )
    rows = links.by_translation_key("doc:0")
    assert len(rows) == 2
    assert links.stats()["total_rows"] == 2
    store.close()
    links.close()
