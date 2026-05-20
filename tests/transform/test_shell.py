"""Tests for MorphonShell slice / admit / complete."""
from __future__ import annotations

import pytest

from cmplx.transform.meaning_store import AddressMeaningStore
from cmplx.transform.shell import MorphonShell
from cmplx.transform.shell_config import ShellConfig
from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    TokenIndexStore,
    any_filter,
)


@pytest.fixture
def indexed_db(tmp_path):
    db = str(tmp_path / "token_index.sqlite")
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1, 2),
            alphabet=tuple("abcdefghijklmnopqrstuvwxyz"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=db,
            progress_every=0,
            max_entries=200,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    return db


def test_slice_ribbon_splits_long_tokens():
    shell = MorphonShell(
        ShellConfig(max_arity=8),
        TokenIndexStore(":memory:"),
    )
    segments = shell.slice_ribbon("unification morphonic")
    assert all(len(s) <= 8 for s in segments)
    assert sum(len(s) for s in segments) >= len("unification")


def test_admit_rejects_invalid_length():
    store = TokenIndexStore(":memory:")
    shell = MorphonShell(ShellConfig(), store)
    result = shell.admit("tiny")
    assert not result.admitted
    assert result.reason == "invalid_length"


def test_admit_rejects_forbidden_bigram():
    store = TokenIndexStore(":memory:")
    shell = MorphonShell(ShellConfig(), store)
    result = shell.admit("qqqqqqqq", lang="english")
    assert not result.admitted
    assert result.reason == "language_rejected"


def test_admit_accepts_substrate_row(indexed_db):
    store = TokenIndexStore(indexed_db)
    shell = MorphonShell(ShellConfig(), store)
    rows = store.by_concat("baaaaaab")
    if not rows:
        pytest.skip("expected level-1 bond baaaaaab in partial index")
    result = shell.admit("baaaaaab")
    assert result.admitted
    assert result.snap_key


def test_complete_returns_candidates(indexed_db):
    store = TokenIndexStore(indexed_db)
    shell = MorphonShell(ShellConfig(), store)
    candidates = shell.complete("baaa")
    assert isinstance(candidates, list)
    if candidates:
        assert all(isinstance(c, str) for c in candidates)
    store.close()


def test_bond_separator_token_shape():
    store = TokenIndexStore(":memory:")
    shell = MorphonShell(ShellConfig(bond_separator="|"), store)
    bad = shell.admit("abcd|ef")
    assert not bad.admitted
    assert bad.reason == "invalid_bond_shape"
