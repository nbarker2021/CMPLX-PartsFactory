"""Tests for cmplx.transform.token_index.case."""
from __future__ import annotations

from cmplx.transform.token_index.bonds import QuadBond
from cmplx.transform.token_index.case import (
    CaseMode,
    DEFAULT_CASE_MODES,
    SEAM_CASE_MODES,
    apply_case,
    case_variants,
)


def _bond() -> QuadBond:
    return QuadBond(quad_left="baaa", quad_right="aaab", level=1)


def test_lower_is_all_lower():
    out = apply_case(_bond(), CaseMode.LOWER)
    assert out.concat == "baaaaaab"


def test_upper_is_all_upper():
    out = apply_case(_bond(), CaseMode.UPPER)
    assert out.concat == "BAAAAAAB"


def test_lead_left():
    out = apply_case(_bond(), CaseMode.LEAD_LEFT)
    assert out.concat == "Baaaaaab"


def test_lead_right_is_a_seam_case():
    out = apply_case(_bond(), CaseMode.LEAD_RIGHT)
    assert out.concat == "baaaAaab"
    assert CaseMode.LEAD_RIGHT in SEAM_CASE_MODES


def test_camel_inner_capitalizes_both_seam_sides():
    out = apply_case(_bond(), CaseMode.CAMEL_INNER)
    assert out.concat == "baaAAaab"
    assert CaseMode.CAMEL_INNER in SEAM_CASE_MODES


def test_alternating_pattern():
    out = apply_case(_bond(), CaseMode.ALTERNATING)
    assert out.concat == "BaAaAaAb"


def test_palindrome_case_keeps_outer_symmetry():
    out = apply_case(_bond(), CaseMode.PALINDROME)
    # Capitals at 0, 3, 4, 7 → seam palindromic.
    assert out.concat[0] == out.concat[7]
    assert out.concat[3] == out.concat[4]


def test_case_variants_returns_all_default_modes():
    pairs = case_variants(_bond())
    assert len(pairs) == len(DEFAULT_CASE_MODES)
    modes = {p[0] for p in pairs}
    assert modes == set(DEFAULT_CASE_MODES)
