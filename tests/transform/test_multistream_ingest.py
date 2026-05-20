"""Multistream ingest — EN-first link policy (temp DB, no corpus walk)."""
from __future__ import annotations

from pathlib import Path

import pytest

from cmplx.transform.ingest import MultistreamIngestPolicy, ingest_multistream
from cmplx.transform.lib_encoder import (
    MathLibEncoder,
    NativeLibEncoder,
    NoOpHub,
    NotationLibEncoder,
    translate_hub_from_env,
)
from cmplx.transform.token_index.store import TokenIndexStore
from cmplx.transform.translation_store import TranslationLinkStore


@pytest.fixture
def sample_corpus(tmp_path: Path) -> Path:
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "sample_en.md").write_text(
        "# Glossary\n\nMorphonic substrate admits eight-char bond windows.\n",
        encoding="utf-8",
    )
    (root / "sample_native.md").write_text(
        "Morphonique substrat admet fenetres de liaison.\n",
        encoding="utf-8",
    )
    return root


def test_translate_hub_factory_noop():
    hub = translate_hub_from_env()
    assert isinstance(hub, NoOpHub)
    assert hub.translate("bonjour") == "bonjour"


def test_native_encoder_word_boundaries():
    enc = NativeLibEncoder(min_token_len=3)
    segs = enc.encode("word-boundary test", translation_key="k:0")
    labels = {s.label for s in segs}
    assert "boundary" in labels or "word" in labels


def test_math_encoder_symbol_runs():
    enc = MathLibEncoder()
    segs = enc.encode(r"\alpha + \beta = \gamma", translation_key="k:0")
    assert segs
    assert all(s.stream == "math" for s in segs)


def test_notation_blocks_yaml_merges():
    enc = NotationLibEncoder()
    norm_text = "α ≤ β"
    segs = enc.encode(norm_text, translation_key="k:0")
    assert segs


def test_multistream_en_first_links(sample_corpus: Path, tmp_path: Path):
    db = tmp_path / "multistream.sqlite"
    policy = MultistreamIngestPolicy(streams=("en", "native"), en_first=True)
    stats = ingest_multistream(
        sample_corpus,
        db=db,
        policy=policy,
        max_files=4,
        register_ports=False,
    )
    assert "en" in stats and "native" in stats
    assert stats["en"].chunks_seen >= 1

    store = TokenIndexStore(db)
    links = TranslationLinkStore.from_connection(store._conn, str(db))
    by_stream = links.stats()["by_stream"]
    assert by_stream.get("en", 0) >= 1
    assert by_stream.get("native", 0) >= 1

    en_rows = links.by_stream("en", limit=5)
    if en_rows:
        tkey = en_rows[0].translation_key
        rows = links.by_translation_key(tkey)
        streams = {r.stream for r in rows}
        assert "en" in streams
    store.close()
    links.close()


def test_reingest_warmstart_ratio(sample_corpus: Path, tmp_path: Path):
    db = tmp_path / "warm.sqlite"
    policy = MultistreamIngestPolicy(streams=("en",), en_first=True)
    first = ingest_multistream(
        sample_corpus, db=db, policy=policy, max_files=2, register_ports=False
    )["en"]
    second = ingest_multistream(
        sample_corpus, db=db, policy=policy, max_files=2, register_ports=False
    )["en"]
    denom = max(second.chunks_seen, 1)
    hit_ratio = second.cache_hits / denom
    assert hit_ratio >= 0.95 or second.bond_skips >= first.new_bonds
