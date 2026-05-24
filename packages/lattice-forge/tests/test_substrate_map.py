"""Tests for the substrate directional map."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lattice_forge.substrate_map import (
    verify_substrate_map,
    state_to_index,
    index_to_state,
    rule30_next_state,
    weyl_13_permutation_index,
    emit_bit,
    WEYL_13_TABLE,
    EMISSION_TABLE,
    RULE30_ROUTING_TABLE,
)


def test_verification_passes() -> None:
    """The substrate map verifier passes at 4096 depths."""
    result = verify_substrate_map(max_depth=4096)
    assert result["status"] == "pass"
    assert result["checks"]["rule30_routing_state_mismatches"] == 0
    assert result["checks"]["rule30_routing_bit_mismatches"] == 0


def test_state_to_index_bijection() -> None:
    """state_to_index and index_to_state are inverses."""
    for L in range(2):
        for C in range(2):
            for R in range(2):
                idx = state_to_index(L, C, R)
                assert index_to_state(idx) == (L, C, R)


def test_weyl_is_involutive() -> None:
    """Weyl involution applied twice returns identity."""
    for i in range(8):
        assert WEYL_13_TABLE[WEYL_13_TABLE[i]] == i


def test_weyl_fixed_points() -> None:
    """Weyl fixed points are exactly the states with L = R."""
    fixed = [i for i in range(8) if WEYL_13_TABLE[i] == i]
    assert fixed == [0, 2, 5, 7]


def test_weyl_swap_pairs() -> None:
    """Weyl swap pairs are exactly (1, 4) and (3, 6)."""
    swaps = [[i, WEYL_13_TABLE[i]] for i in range(8) if WEYL_13_TABLE[i] > i]
    assert swaps == [[1, 4], [3, 6]]


def test_emission_table_matches_rule30() -> None:
    """The emission table matches Rule 30's truth table."""
    expected = (0, 1, 1, 1, 1, 0, 0, 0)
    assert EMISSION_TABLE == expected


def test_rule30_routing_destination_counts() -> None:
    """States with R=1 have 2 distinct destinations; states with R=0 have 4."""
    for src_idx in range(8):
        _, _, R = index_to_state(src_idx)
        destinations = set(RULE30_ROUTING_TABLE[src_idx])
        if R == 1:
            assert len(destinations) == 2, f"R=1 state {src_idx} should have 2 destinations"
        else:
            assert len(destinations) == 4, f"R=0 state {src_idx} should have 4 destinations"


if __name__ == "__main__":
    test_verification_passes()
    test_state_to_index_bijection()
    test_weyl_is_involutive()
    test_weyl_fixed_points()
    test_weyl_swap_pairs()
    test_emission_table_matches_rule30()
    test_rule30_routing_destination_counts()
    print("All substrate map tests pass.")
