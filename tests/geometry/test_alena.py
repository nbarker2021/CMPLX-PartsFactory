"""
Smoke tests for cmplx.geometry.alena — projection primitives.
"""
from __future__ import annotations

import math

import pytest

from cmplx.geometry.alena import (
    ALENA,
    COUPLING,
    E8_NORM,
    PHI,
    fibonacci_radii,
)
from cmplx.geometry.e8 import nearest_root, DIMENSION


@pytest.fixture
def alena():
    return ALENA()


# ---------------------------------------------------------------------------
# fibonacci_radii
# ---------------------------------------------------------------------------

def test_fibonacci_radii_sorted_ascending():
    radii = fibonacci_radii()
    assert radii == sorted(radii)


def test_fibonacci_radii_uses_phi():
    radii = fibonacci_radii(0, 1)
    # PHI^0 * COUPLING and PHI^1 * COUPLING
    assert math.isclose(radii[0], COUPLING)
    assert math.isclose(radii[1], COUPLING * PHI)


# ---------------------------------------------------------------------------
# r_theta_snap
# ---------------------------------------------------------------------------

def test_r_theta_snap_preserves_direction(alena):
    v = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0)
    snapped = alena.r_theta_snap(v)
    v_norm = math.sqrt(sum(x * x for x in v))
    s_norm = math.sqrt(sum(x * x for x in snapped))
    # direction preserved → unit-vector dot product == 1
    dot = sum(a / v_norm * b / s_norm for a, b in zip(v, snapped))
    assert math.isclose(dot, 1.0, abs_tol=1e-9)


def test_r_theta_snap_magnitude_is_fibonacci(alena):
    v = (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    snapped = alena.r_theta_snap(v)
    s_norm = math.sqrt(sum(x * x for x in snapped))
    radii = fibonacci_radii()
    assert any(math.isclose(s_norm, r, abs_tol=1e-9) for r in radii)


def test_r_theta_snap_zero_vector(alena):
    v = (0.0,) * 8
    assert alena.r_theta_snap(v) == v


# ---------------------------------------------------------------------------
# weyl_flip
# ---------------------------------------------------------------------------

def test_weyl_flip_reflects_across_root(alena):
    v = (0.5, 0.5, 0, 0, 0, 0, 0, 0)
    flipped = alena.weyl_flip(v)
    # The dot product of v with its nearest root has flipped sign
    root = nearest_root(v)
    dot_before = sum(a * b for a, b in zip(v, root))
    dot_after = sum(a * b for a, b in zip(flipped, root))
    # Opposite signs (or both zero)
    assert dot_before * dot_after <= 1e-9


def test_weyl_flip_rejects_wrong_dim(alena):
    with pytest.raises(ValueError, match="8-D"):
        alena.weyl_flip((1.0, 2.0, 3.0))


# ---------------------------------------------------------------------------
# midpoint_ecc
# ---------------------------------------------------------------------------

def test_midpoint_ecc_same_vector_snaps_to_root(alena):
    v = (1.0, 1.0, 0, 0, 0, 0, 0, 0)
    mid = alena.midpoint_ecc(v, v)
    # Should be on the E8 manifold (norm ≈ E8_NORM)
    norm = math.sqrt(sum(x * x for x in mid))
    assert math.isclose(norm, E8_NORM, abs_tol=1e-6)


def test_midpoint_ecc_distinct_vectors(alena):
    v1 = (1.0, 1.0, 0, 0, 0, 0, 0, 0)
    v2 = (1.0, -1.0, 0, 0, 0, 0, 0, 0)
    mid = alena.midpoint_ecc(v1, v2)
    norm = math.sqrt(sum(x * x for x in mid))
    # On the E8 manifold (snapped to a root)
    assert math.isclose(norm, E8_NORM, abs_tol=1e-6)


def test_midpoint_ecc_length_mismatch(alena):
    with pytest.raises(ValueError, match="same length"):
        alena.midpoint_ecc((1.0, 2.0), (1.0, 2.0, 3.0))


# ---------------------------------------------------------------------------
# project_curvature
# ---------------------------------------------------------------------------

def test_project_curvature_returns_8d(alena):
    v = (0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    out = alena.project_curvature(v, face_angle=0.5)
    assert len(out) == DIMENSION


def test_project_curvature_rejects_wrong_dim(alena):
    with pytest.raises(ValueError, match="8-D"):
        alena.project_curvature((1.0, 2.0, 3.0))


# ---------------------------------------------------------------------------
# project_to_channels
# ---------------------------------------------------------------------------

def test_project_to_channels_constrains_components(alena):
    v = (10.5, -7.2, 4.1, 8.0, -3.3, 5.5, 12.0, 1.0)
    out = alena.project_to_channels(v, (3, 6, 9))
    # Each output component's abs value < the corresponding channel rail
    for i, comp in enumerate(out):
        ch = (3, 6, 9)[i % 3]
        assert abs(comp) < ch


def test_project_to_channels_preserves_sign(alena):
    v = (5.0, -5.0, 5.0, -5.0, 5.0, -5.0, 5.0, -5.0)
    out = alena.project_to_channels(v, (3, 6, 9))
    for a, b in zip(v, out):
        # Same sign (or zero)
        assert (a >= 0) == (b >= 0)


def test_project_to_channels_empty_channels_raises(alena):
    with pytest.raises(ValueError, match="non-empty"):
        alena.project_to_channels((1.0,), ())


# ---------------------------------------------------------------------------
# Determinism + immutability
# ---------------------------------------------------------------------------

def test_operations_deterministic(alena):
    v = (0.3, -0.7, 0.5, 0.1, 0.0, 0.2, -0.4, 0.6)
    assert alena.r_theta_snap(v) == alena.r_theta_snap(v)
    assert alena.weyl_flip(v) == alena.weyl_flip(v)
    assert alena.midpoint_ecc(v, v) == alena.midpoint_ecc(v, v)
    assert alena.project_curvature(v, 0.5) == alena.project_curvature(v, 0.5)


def test_operations_do_not_mutate_input(alena):
    v_list = [0.3, -0.7, 0.5, 0.1, 0.0, 0.2, -0.4, 0.6]
    v_orig = list(v_list)
    alena.r_theta_snap(v_list)
    alena.weyl_flip(v_list)
    alena.midpoint_ecc(v_list, v_list)
    alena.project_curvature(v_list, 0.5)
    alena.project_to_channels(v_list)
    assert v_list == v_orig
