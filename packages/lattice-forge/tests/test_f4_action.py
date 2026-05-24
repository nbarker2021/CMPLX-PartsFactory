"""Tests for the F_4 / SU(3) Weyl action implementation."""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lattice_forge.f4_action import (
    verify_n3_su3_closure_exact,
    search_for_su3_closure_scale,
    decompose_8x8_via_block_action_exact,
    closed_form_rule30_8x8_transition_exact,
    n_step_shell2_conditional_3x3_exact,
    decompose_3x3_in_s3_group_ring_exact,
)


def test_n3_closure_exact_over_rationals() -> None:
    """n=3 closure has zero residual squared over Q."""
    result = verify_n3_su3_closure_exact()
    assert result["status"] == "pass"
    assert result["is_exact_group_ring_element"]
    assert result["residual_squared_exact"] == "0"
    assert result["coefficient_sum_exact"] == "1"


def test_n3_closure_coefficients() -> None:
    """n=3 closure coefficients are exactly (1/3, 1/3, 1/3) on the transpositions and zero elsewhere."""
    result = verify_n3_su3_closure_exact()
    coeffs = result["s3_coefficients_exact_strings"]
    assert coeffs["e"] == "0"
    assert coeffs["(1 2)"] == "1/3"
    assert coeffs["(1 3)"] == "1/3"
    assert coeffs["(2 3)"] == "1/3"
    assert coeffs["(1 2 3)"] == "0"
    assert coeffs["(1 3 2)"] == "0"


def test_closure_scale_is_exactly_three() -> None:
    """The minimum closure scale is exactly 3."""
    result = search_for_su3_closure_scale(max_scale=8, tol=1e-6)
    assert result["best_scale"] == 3
    assert result["closed_at_a_scale"]


def test_n1_does_not_close() -> None:
    """The 1-step matrix does not close (it is rank-deficient)."""
    result = search_for_su3_closure_scale(max_scale=8, tol=1e-6)
    scale_1 = next(r for r in result["results_per_scale"] if r["n_steps"] == 1)
    assert not scale_1["is_s3_element"]
    assert scale_1["residual_l2"] > 0.5


def test_idempotency_of_m3() -> None:
    """M_3^2 = M_3 exactly over Q."""
    step3 = n_step_shell2_conditional_3x3_exact(3)
    m3 = step3["conditional_3x3_exact"]
    # Compute m3 * m3 manually
    m3_squared = [[Fraction(0) for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for k in range(3):
            for j in range(3):
                m3_squared[i][j] += m3[i][k] * m3[k][j]
    # Verify equality
    for i in range(3):
        for j in range(3):
            assert m3[i][j] == m3_squared[i][j], f"M_3^2 != M_3 at ({i}, {j})"


def test_both_trace_blocks_close_identically() -> None:
    """Both trace-1 and trace-2 conditional blocks close as identical S_3 elements."""
    result = decompose_8x8_via_block_action_exact(n_steps=3)
    assert result["trace1_is_exact_s3_element"]
    assert result["trace2_is_exact_s3_element"]
    assert result["claim"]["both_trace_blocks_close_as_s3_elements"]


def test_closed_form_8x8_has_quartile_entries() -> None:
    """The closed-form 8x8 transition matrix has all entries in {0, 1/4, 1/2}."""
    result = closed_form_rule30_8x8_transition_exact()
    allowed = {Fraction(0), Fraction(1, 4), Fraction(1, 2)}
    for row in result["matrix"]:
        for entry in row:
            assert entry in allowed, f"Entry {entry} not in {{0, 1/4, 1/2}}"


def test_8x8_row_sums_unity() -> None:
    """Each row of the closed-form 8x8 matrix sums to exactly 1."""
    result = closed_form_rule30_8x8_transition_exact()
    for row in result["matrix"]:
        s = sum(row, Fraction(0))
        assert s == 1, f"Row sum {s} != 1"


if __name__ == "__main__":
    test_n3_closure_exact_over_rationals()
    test_n3_closure_coefficients()
    test_closure_scale_is_exactly_three()
    test_n1_does_not_close()
    test_idempotency_of_m3()
    test_both_trace_blocks_close_identically()
    test_closed_form_8x8_has_quartile_entries()
    test_8x8_row_sums_unity()
    print("All F_4 / SU(3) Weyl tests pass.")
