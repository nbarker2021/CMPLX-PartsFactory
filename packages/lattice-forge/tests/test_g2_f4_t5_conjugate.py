"""Tests for the G_2 / F_4 / T_5A conjugate triple router."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.g2_f4_t5_conjugate import (
    F4_REPRESENTATIVE_AXIS_CYCLE,
    G2_REPRESENTATIVE_PERMUTATION,
    conjugate_triple_route,
    f4_representative_chart_cycle,
    g2_representative_permutation,
    t5_modular_conjugate,
    verify_conjugate_triple,
)
from lattice_forge.octonion import Octonion
from lattice_forge.oloid_octonionic import OctonionicOloidState


def test_g2_permutation_fixes_real_and_e4():
    """G_2 fixes the real line (e_0) and e_4 (the Cayley-Dickson generator)."""
    assert G2_REPRESENTATIVE_PERMUTATION[0] == 0
    assert G2_REPRESENTATIVE_PERMUTATION[4] == 4


def test_g2_permutation_acts_on_imaginary_basis():
    """G_2 acts nontrivially on the 7 imaginary octonion units."""
    # At least some basis elements move
    moved = sum(1 for i in range(1, 8) if G2_REPRESENTATIVE_PERMUTATION[i] != i)
    assert moved >= 4


def test_g2_applied_to_e1_moves_it():
    """e_1 is not fixed by the G_2 representative."""
    state = OctonionicOloidState(Octonion((0, 1, 0, 0, 0, 0, 0, 0)))
    result = g2_representative_permutation(state)
    # Component at position 1 should now be 0
    assert result.octonion.components[1] == 0.0
    # Some other component should be 1
    assert any(result.octonion.components[i] == 1.0 for i in (2, 3))


def test_f4_chart_cycle_fixes_axis_0():
    assert f4_representative_chart_cycle(0) == 0


def test_f4_chart_cycle_is_3cycle_on_axes_1_2_3():
    assert f4_representative_chart_cycle(1) == 2
    assert f4_representative_chart_cycle(2) == 3
    assert f4_representative_chart_cycle(3) == 1


def test_f4_chart_cycle_period_is_3():
    """Three applications of the F_4 chart cycle returns to identity."""
    for axis in (1, 2, 3):
        x = axis
        for _ in range(3):
            x = f4_representative_chart_cycle(x)
        assert x == axis


def test_f4_invalid_axis_raises():
    import pytest
    with pytest.raises(ValueError):
        f4_representative_chart_cycle(4)


def test_t5_modular_conjugate_returns_bit():
    p = t5_modular_conjugate(1)
    assert p in (0, 1)
    # T_5A's a_1 = 134, even → parity 0
    assert p == 0


def test_conjugate_triple_route_returns_structured_dict():
    from lattice_forge.block_tower import rule30_center_column
    bits = rule30_center_column(64)
    def enum(n): return bits[n - 1]
    r = conjugate_triple_route(5, enum)
    assert "N" in r
    assert "moves_to_resolution" in r
    assert "resolved_bit" in r
    assert "conjugate_path" in r
    assert r["moves_to_resolution"] in (0, 1, 2, 3, -1)


def test_conjugate_triple_route_all_within_3_moves():
    """The 3-max-0-bijections claim: every query resolves in ≤3 moves."""
    from lattice_forge.block_tower import rule30_center_column
    bits = rule30_center_column(256)
    def enum(n): return bits[n - 1]
    for N in range(1, 257):
        r = conjugate_triple_route(N, enum)
        assert r["moves_to_resolution"] in (0, 1, 2, 3), (
            f"N={N} required {r['moves_to_resolution']} moves"
        )


def test_conjugate_triple_route_resolves_all_chart_axes():
    """Each of the 4 chart axes routes through a different conjugate path."""
    from lattice_forge.block_tower import rule30_center_column
    bits = rule30_center_column(256)
    def enum(n): return bits[n - 1]
    seen_axes = set()
    for N in range(1, 257):
        r = conjugate_triple_route(N, enum)
        seen_axes.add(r["chart_axis"])
    assert seen_axes == {0, 1, 2, 3}


def test_verify_conjugate_triple_passes():
    r = verify_conjugate_triple(max_depth=256)
    assert r["status"] == "pass"
    assert r["all_resolved_in_3_or_less"]
    assert r["matches_enumeration_rate"] == 1.0
