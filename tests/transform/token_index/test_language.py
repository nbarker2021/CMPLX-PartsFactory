"""Tests for cmplx.transform.token_index.language."""
from __future__ import annotations

from cmplx.transform.token_index.bonds import QuadBond
from cmplx.transform.token_index.language import (
    LanguageFilter,
    any_filter,
    english_filter,
    get_filter,
)


def _bond(left: str, right: str) -> QuadBond:
    return QuadBond(quad_left=left, quad_right=right, level=1)


def test_any_filter_accepts_everything():
    f = any_filter()
    assert f.accept(_bond("xxxx", "qqqq"))
    assert f.accept(_bond("aaaa", "aaaa"))


def test_english_rejects_forbidden_bigrams():
    f = english_filter()
    assert f.accept(_bond("thea", "anth"))  # contains "th", common
    assert not f.accept(_bond("qqxx", "aaaa"))  # forbidden qq, xx


def test_english_requires_at_least_one_common_bigram():
    f = english_filter(min_common=1)
    assert not f.accept(_bond("zzzz", "yyyy"))  # no common bigrams


def test_filter_streaming_method():
    f = english_filter()
    bonds = [
        _bond("thea", "anth"),  # accept
        _bond("qqxx", "aaaa"),  # reject (forbidden)
        _bond("them", "anin"),  # accept (contains 'th', 'he', 'in')
    ]
    kept = list(f.filter(bonds))
    assert len(kept) == 2


def test_registry_falls_back_to_any():
    f = get_filter("klingon_unknown")
    assert f.name == "any"
