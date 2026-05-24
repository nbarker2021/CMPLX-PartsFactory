"""Tests for the 9×9 j-modular matrix and octonion → V_9 lift."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.j_modular_matrix import (
    J_MATRIX_2A,
    J_MATRIX_3A,
    apply_j_matrix,
    get_j_matrix,
    lift_octonion_to_v9,
    modular_parity_per_coordinate,
    modular_parity_signature,
    verify_j_modular_matrix,
)
from lattice_forge.octonion import O_ONE, O_E4
from lattice_forge.voa_harness import T_2A_COEFFICIENTS, T_3A_COEFFICIENTS


def test_j_matrices_are_9x9():
    assert len(J_MATRIX_2A) == 9
    assert all(len(row) == 9 for row in J_MATRIX_2A)
    assert len(J_MATRIX_3A) == 9
    assert all(len(row) == 9 for row in J_MATRIX_3A)


def test_J_3A_first_coefficient_is_a1_of_T3A():
    assert J_MATRIX_3A[1][0] == T_3A_COEFFICIENTS[0]
    assert J_MATRIX_3A[1][0] == 783


def test_J_2A_first_coefficient_is_a1_of_T2A():
    assert J_MATRIX_2A[1][0] == T_2A_COEFFICIENTS[0]
    assert J_MATRIX_2A[1][0] == 4372


def test_j_matrix_diagonal_is_1():
    for i in range(9):
        assert J_MATRIX_3A[i][i] == 1
        assert J_MATRIX_2A[i][i] == 1


def test_j_matrix_strictly_upper_triangle_is_0():
    for i in range(9):
        for j in range(i + 1, 9):
            assert J_MATRIX_3A[i][j] == 0
            assert J_MATRIX_2A[i][j] == 0


def test_get_j_matrix_known_classes():
    assert get_j_matrix("2A") == J_MATRIX_2A
    assert get_j_matrix("3A") == J_MATRIX_3A


def test_get_j_matrix_unknown_class_raises():
    import pytest
    with pytest.raises(ValueError):
        get_j_matrix("99Z")


def test_lift_O_ONE_returns_9_components():
    v = lift_octonion_to_v9(O_ONE)
    assert len(v) == 9
    assert v[0] == 1.0
    assert v[8] == 1.0  # L_2 norm squared of O_ONE = 1


def test_lift_O_E4_basis_element():
    v = lift_octonion_to_v9(O_E4)
    assert v[0] == 0.0
    assert v[4] == 1.0
    assert v[8] == 1.0  # norm squared = 1


def test_apply_j_matrix_to_O_ONE():
    """Applying J_3A to lift(O_ONE) = (1,0,0,0,0,0,0,0,1):
    Row 0 = identity row [1,0,...,0] · v = 1
    Row 1 = [783, 1, 0, ..., 0] · v = 783*1 + 1*0 + ... = 783
    """
    v = lift_octonion_to_v9(O_ONE)
    Jv = apply_j_matrix(v, J_MATRIX_3A)
    assert Jv[0] == 1.0
    assert Jv[1] == 783.0


def test_apply_j_matrix_dimension_check():
    import pytest
    with pytest.raises(ValueError):
        apply_j_matrix((1.0, 2.0, 3.0), J_MATRIX_3A)


def test_modular_parity_signature_is_binary():
    v = lift_octonion_to_v9(O_ONE)
    Jv = apply_j_matrix(v, J_MATRIX_3A)
    sig = modular_parity_signature(Jv)
    assert sig in (0, 1)


def test_modular_parity_per_coordinate_returns_9_tuple():
    v = lift_octonion_to_v9(O_ONE)
    Jv = apply_j_matrix(v, J_MATRIX_3A)
    pcp = modular_parity_per_coordinate(Jv)
    assert len(pcp) == 9
    assert all(b in (0, 1) for b in pcp)


def test_full_verifier_passes():
    r = verify_j_modular_matrix()
    assert r["status"] == "pass"
