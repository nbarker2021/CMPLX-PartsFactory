"""Tests for the octonion algebra implementation.

Verifies all six axioms (identity, imaginary squares, Fano triple positive,
Fano triple antisymmetry, Hurwitz norm composition, left alternativity) at
machine precision.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lattice_forge.octonion import (
    Octonion,
    O_ONE, O_E1, O_E2, O_E3, O_E4, O_E5, O_E6, O_E7,
    verify_octonion_axioms,
)


def test_axioms_pass() -> None:
    result = verify_octonion_axioms()
    assert result["status"] == "pass", f"Octonion axioms failed: {result['errors']}"
    assert result["errors"] == []


def test_identity_action() -> None:
    """1 * e_i = e_i for all i."""
    for i in range(1, 8):
        e_i = Octonion.basis(i)
        product = O_ONE * e_i
        assert product.as_tuple() == e_i.as_tuple()


def test_imaginary_squares() -> None:
    """e_i * e_i = -1 for all i in 1..7."""
    minus_one = Octonion.real(-1.0)
    for i in range(1, 8):
        e_i = Octonion.basis(i)
        product = e_i * e_i
        assert product.as_tuple() == minus_one.as_tuple()


def test_fano_triple_e1_e2_e3() -> None:
    """e_1 * e_2 = +e_3 (Fano triple)."""
    product = O_E1 * O_E2
    assert product.as_tuple() == O_E3.as_tuple()


def test_fano_triple_reverse() -> None:
    """e_2 * e_1 = -e_3 (Fano reverse antisymmetry)."""
    product = O_E2 * O_E1
    assert product.as_tuple() == (-O_E3).as_tuple()


def test_norm_composition_hurwitz() -> None:
    """|xy|^2 = |x|^2 * |y|^2 (Hurwitz's theorem)."""
    x = Octonion((1.0, 2.0, -1.0, 0.5, 0.0, 1.5, -0.5, 0.25))
    y = Octonion((0.5, 1.0, 0.0, -1.5, 2.0, 0.0, 0.5, -1.0))
    xy = x * y
    norm_xy_sq = xy.norm_squared()
    norm_product = x.norm_squared() * y.norm_squared()
    assert abs(norm_xy_sq - norm_product) < 1e-9


def test_left_alternativity() -> None:
    """x * (x * y) = (x * x) * y."""
    x = Octonion((1.0, 2.0, -1.0, 0.5, 0.0, 1.5, -0.5, 0.25))
    y = Octonion((0.5, 1.0, 0.0, -1.5, 2.0, 0.0, 0.5, -1.0))
    lhs = x * (x * y)
    rhs = (x * x) * y
    diff = sum((a - b) ** 2 for a, b in zip(lhs.components, rhs.components))
    assert diff ** 0.5 < 1e-9


if __name__ == "__main__":
    test_axioms_pass()
    test_identity_action()
    test_imaginary_squares()
    test_fano_triple_e1_e2_e3()
    test_fano_triple_reverse()
    test_norm_composition_hurwitz()
    test_left_alternativity()
    print("All octonion tests pass.")
