"""Tests for cmplx.transform.token_index.bonds."""
from __future__ import annotations

import pytest

from cmplx.transform.token_index.bonds import (
    DEFAULT_BASE_CHAR,
    QUAD_LEN,
    QuadBond,
    count_bonds,
    enumerate_bonds,
    enumerate_levels,
)


def test_quadbond_concat_and_seam():
    b = QuadBond(quad_left="baaa", quad_right="aaab", level=1)
    assert b.concat == "baaaaaab"
    assert b.seam == "baaa|aaab"


def test_quadbond_rejects_wrong_length():
    with pytest.raises(ValueError):
        QuadBond(quad_left="bad", quad_right="aaab", level=1)


def test_level_1_enumerates_alphabet_minus_base():
    bonds = list(enumerate_bonds(1, alphabet="abc", base_char="a"))
    # alphabet "abc" minus the all-base "aaaa|aaaa" entry.
    assert len(bonds) == 2  # 'b' and 'c'
    concats = sorted(b.concat for b in bonds)
    assert concats == ["baaaaaab", "caaaaaac"]


def test_level_1_outer_ring_positions_match():
    for bond in enumerate_bonds(1, alphabet="abcd", base_char="a"):
        s = bond.concat
        # Outer ring: position 0 must equal position 7.
        assert s[0] == s[7]


def test_level_2_has_inner_ring_too():
    bonds = list(enumerate_bonds(2, alphabet="ab", base_char="a"))
    # 2^2 = 4 combinations minus the all-base one = 3.
    assert len(bonds) == 3
    for b in bonds:
        s = b.concat
        assert s[0] == s[7]  # outer ring
        assert s[1] == s[6]  # first inner ring


def test_level_3_has_three_rings():
    for bond in enumerate_bonds(3, alphabet="abc", base_char="a"):
        s = bond.concat
        assert s[0] == s[7]
        assert s[1] == s[6]
        assert s[2] == s[5]


def test_count_bonds_excludes_all_base():
    assert count_bonds(1, alphabet_size=26) == 25
    assert count_bonds(2, alphabet_size=26) == 26 * 26 - 1
    assert count_bonds(3, alphabet_size=26) == 26**3 - 1


def test_enumerate_levels_chains_in_order():
    seen_levels: list[int] = []
    for bond in enumerate_levels((1, 2), alphabet="ab"):
        seen_levels.append(bond.level)
    # Level 1 bonds appear before any level 2 bonds.
    first_level_2 = seen_levels.index(2)
    assert all(lv == 1 for lv in seen_levels[:first_level_2])


def test_palindrome_helper():
    pal = QuadBond(quad_left="baaa", quad_right="aaab", level=1)
    assert pal.is_palindrome() is True
    non_pal = QuadBond(quad_left="baaa", quad_right="aabb", level=1)
    assert non_pal.is_palindrome() is False
