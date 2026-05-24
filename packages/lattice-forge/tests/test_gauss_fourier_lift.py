"""Tests for the Gauss/Fourier lift module."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.gauss_fourier_lift import (
    dft_9_complex,
    dft_9_real_cosine,
    gauss_sum_9_against,
    gauss_sum_9_principal,
    inverse_dft_9_complex,
    octonion_gauss_reduce,
    octonion_l2_reduce,
    paired_spectrograph,
    spectrograph_readout,
    verify_gauss_fourier_lift,
)
from lattice_forge.octonion import O_ONE, O_E4, Octonion


def test_octonion_gauss_reduce_returns_9_bits():
    g = octonion_gauss_reduce(O_ONE)
    assert len(g) == 9
    assert all(b in (0, 1) for b in g)


def test_O_ONE_f2_reduction_has_dc_bit_1():
    g = octonion_gauss_reduce(O_ONE)
    # O_ONE = (1, 0, 0, ..., 0); DC = 1 (one odd bit)
    assert g[8] == 1


def test_octonion_l2_reduce_is_antisymmetric_under_negation():
    """The signed sum 9th coordinate flips sign under negation."""
    pos = octonion_l2_reduce(O_ONE)
    neg = octonion_l2_reduce(Octonion.real(-1.0))
    assert all(abs(pos[i] + neg[i]) < 1e-12 for i in range(9))


def test_dft_inverse_is_identity():
    v = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    F = dft_9_complex(v)
    v_back = inverse_dft_9_complex(F)
    for j in range(9):
        assert abs(v[j] - v_back[j].real) < 1e-9


def test_dft_dc_equals_sum():
    """The k=0 Fourier coefficient is the sum of inputs."""
    v = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    F_real = dft_9_real_cosine(v)
    assert abs(F_real[0] - sum(v)) < 1e-9


def test_gauss_sum_principal_is_ramanujan_zero():
    """c_9(1) = 0 since 9 = 3² is not squarefree (μ(9) = 0)."""
    g = gauss_sum_9_principal()
    assert abs(g) < 1e-9


def test_paired_spectrograph_consistent_under_negation():
    """A pair (o, -o) is bijection-consistent."""
    minus = Octonion.real(-1.0)
    r = paired_spectrograph(O_ONE, minus)
    assert r["bijection_consistent"]


def test_paired_spectrograph_inconsistent_when_same():
    """A pair (o, o) is NOT bijection-consistent (no spectral negation)."""
    r = paired_spectrograph(O_ONE, O_ONE)
    assert not r["bijection_consistent"]


def test_spectrograph_has_middle_bar():
    """The DC component (middle bar) is the first real-DFT coefficient
    and equals the sum of the L1-reduced vector."""
    sp = spectrograph_readout(O_E4)
    v = octonion_l2_reduce(O_E4)
    assert abs(sp["middle_bar_dc"] - sum(v)) < 1e-9


def test_gauss_sum_against_O_ONE_lift():
    """Gauss sum against the lift of O_ONE = 1·ω^0 + 0 + ... + 1·ω^8
    = 1 + ω^8 = 1 + e^(2πi·8/9). Verifies the primitive computes
    the kernel inner product correctly."""
    import cmath
    v = octonion_l2_reduce(O_ONE)
    g = gauss_sum_9_against(v)
    expected = 1 + cmath.exp(2j * math.pi * 8 / 9)
    assert abs(g - expected) < 1e-9


def test_full_verifier_passes():
    r = verify_gauss_fourier_lift()
    assert r["status"] == "pass"
