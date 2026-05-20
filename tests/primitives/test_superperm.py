"""Tests for cmplx.primitives.superperm."""
from __future__ import annotations

import pytest

from cmplx.primitives.superperm import (
    N4_LENGTH,
    N4_PERM_COUNT,
    SUPERPERM_N4,
    coverage_check,
    coverage_checksum,
    digit_at,
    is_palindrome_phase,
    load_n4_metadata,
    n4_permutation_set,
    n5_status,
    phase_at,
    status_for_n,
    superperm_n,
    superperm_length,
)


def test_superperm_n4_length_and_coverage():
    assert len(SUPERPERM_N4) == N4_LENGTH == 33
    assert coverage_check() is True
    assert coverage_check(SUPERPERM_N4) is True
    assert N4_PERM_COUNT == 24


def test_digit_at_and_phase_at():
    assert digit_at(0) == 1
    assert phase_at(0) == 1
    assert digit_at(32) == 1
    assert digit_at(33) == digit_at(0)


def test_n4_json_metadata():
    meta = load_n4_metadata()
    assert meta["length"] == 33
    assert meta["n"] == 4
    sp = meta.get("superperm") or meta.get("superpermutation")
    assert sp == SUPERPERM_N4


def test_all_permutations_present():
    perms = n4_permutation_set()
    assert len(perms) == 24
    found = set()
    for i in range(len(SUPERPERM_N4) - 3):
        found.add(SUPERPERM_N4[i : i + 4])
    assert perms <= found


def test_coverage_checksum_stable():
    assert len(coverage_checksum()) == 16


def test_superperm_n4_always_available():
    assert superperm_n(4) == SUPERPERM_N4


def test_superperm_n5_when_validated():
    if status_for_n(5) != "validated":
        pytest.skip("n5.json not validated")
    assert superperm_length(5) == 153
    assert coverage_check(superperm_n(5), n=5)


def test_is_palindrome_phase_prefix():
    assert is_palindrome_phase(0) is False
    assert isinstance(is_palindrome_phase(3), bool)


def test_n5_status_not_pending_when_ingested():
    if n5_status() == "pending":
        pytest.skip("n5 not ingested in this checkout")
    assert n5_status() == "validated"
