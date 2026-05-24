"""Tests for the chart-to-J_3(O) isomorphism."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lattice_forge.rule30 import (
    verify_chart_j3o_isomorphism,
    verify_rule30_chart_local_readout,
    chart_state_to_j3o,
    j3o_to_chart_state,
)


def test_isomorphism_pass_at_128() -> None:
    """Chart-J_3(O) isomorphism passes at depth 128 (quick verification)."""
    result = verify_chart_j3o_isomorphism(max_depth=128)
    assert result["status"] == "pass"
    assert result["bijection_failures"] == 0
    assert result["trace_mismatches"] == 0
    assert result["weyl_mismatches"] == 0
    assert result["readout_mismatches"] == 0


def test_chart_readout_matches_rule30() -> None:
    """The chart readout law matches Rule 30 at all 4096 depths with 0 defects."""
    result = verify_rule30_chart_local_readout(max_depth=4096)
    assert result["status"] == "pass"
    assert result["forward_defect_count"] == 0
    assert result["forward_accuracy"] == 1.0


def test_bijection_round_trip() -> None:
    """Chart state -> J_3(O) -> chart state recovers the original."""
    for L in range(2):
        for C in range(2):
            for R in range(2):
                j3o = chart_state_to_j3o(L, C, R)
                recovered = j3o_to_chart_state(j3o)
                assert recovered == (L, C, R), f"({L},{C},{R}) did not round-trip"


def test_trace_equals_shell() -> None:
    """The J_3(O) trace equals the chart's shell."""
    for L in range(2):
        for C in range(2):
            for R in range(2):
                j3o = chart_state_to_j3o(L, C, R)
                shell = L + C + R
                assert abs(j3o.trace() - shell) < 1e-9


def test_all_shell_2_are_trace_2_idempotents() -> None:
    """All shell=2 chart states map to trace-2 J_3(O) idempotents."""
    for L in range(2):
        for C in range(2):
            for R in range(2):
                if L + C + R == 2:
                    j3o = chart_state_to_j3o(L, C, R)
                    assert j3o.is_idempotent()
                    assert abs(j3o.trace() - 2.0) < 1e-9


if __name__ == "__main__":
    test_isomorphism_pass_at_128()
    test_chart_readout_matches_rule30()
    test_bijection_round_trip()
    test_trace_equals_shell()
    test_all_shell_2_are_trace_2_idempotents()
    print("All chart-J_3(O) isomorphism tests pass.")
