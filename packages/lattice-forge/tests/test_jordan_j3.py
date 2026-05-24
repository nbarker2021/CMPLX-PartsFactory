"""Tests for the J_3(O) Jordan algebra implementation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lattice_forge.jordan_j3 import (
    J3O,
    J3_TRACE2_E11_E22, J3_TRACE2_E11_E33, J3_TRACE2_E22_E33,
    verify_j3o_axioms,
)


def test_axioms_pass() -> None:
    result = verify_j3o_axioms()
    assert result["status"] == "pass", f"J_3(O) axioms failed: {result['errors']}"


def test_diagonal_idempotents_are_idempotent() -> None:
    for i in (1, 2, 3):
        E = J3O.diagonal_idempotent(i)
        E_sq = E.jordan_product(E)
        assert E._close_to(E_sq)


def test_diagonal_idempotents_jordan_orthogonal() -> None:
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            if i == j:
                continue
            E_i = J3O.diagonal_idempotent(i)
            E_j = J3O.diagonal_idempotent(j)
            prod = E_i.jordan_product(E_j)
            assert prod._close_to(J3O.zero())


def test_diagonal_idempotents_sum_to_identity() -> None:
    E_sum = (
        J3O.diagonal_idempotent(1)
        + J3O.diagonal_idempotent(2)
        + J3O.diagonal_idempotent(3)
    )
    assert E_sum._close_to(J3O.identity())


def test_trace_2_idempotents_have_trace_2() -> None:
    for (i, j) in [(1, 2), (1, 3), (2, 3)]:
        T = J3O.trace_2_idempotent(i, j)
        assert abs(T.trace() - 2.0) < 1e-9


def test_trace_2_idempotents_are_jordan_idempotent() -> None:
    for (i, j) in [(1, 2), (1, 3), (2, 3)]:
        T = J3O.trace_2_idempotent(i, j)
        T_sq = T.jordan_product(T)
        assert T._close_to(T_sq)


def test_weyl_13_fixes_e11_e33() -> None:
    """The (1,3) transposition fixes E_11 + E_33 (the chirality-balanced state)."""
    fixed = J3_TRACE2_E11_E33.weyl_13_transposition()
    assert fixed._close_to(J3_TRACE2_E11_E33)


def test_weyl_13_swaps_e11_e22_with_e22_e33() -> None:
    """The (1,3) transposition swaps E_11+E_22 with E_22+E_33 (chirality-broken pair)."""
    swap_a = J3_TRACE2_E11_E22.weyl_13_transposition()
    assert swap_a._close_to(J3_TRACE2_E22_E33)
    swap_b = J3_TRACE2_E22_E33.weyl_13_transposition()
    assert swap_b._close_to(J3_TRACE2_E11_E22)


if __name__ == "__main__":
    test_axioms_pass()
    test_diagonal_idempotents_are_idempotent()
    test_diagonal_idempotents_jordan_orthogonal()
    test_diagonal_idempotents_sum_to_identity()
    test_trace_2_idempotents_have_trace_2()
    test_trace_2_idempotents_are_jordan_idempotent()
    test_weyl_13_fixes_e11_e33()
    test_weyl_13_swaps_e11_e22_with_e22_e33()
    print("All J_3(O) tests pass.")
