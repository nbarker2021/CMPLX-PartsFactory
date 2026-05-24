"""Tests for the Oloid rolling chart bijection carrier."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.oloid_rolling import (
    OloidState,
    roll_chart_landing,
    roll_chart_trace,
    cyclic_rotate,
    antipodal_swap,
    weyl_mirror,
    landing_under_symmetry,
    enumerate_landings,
    landing_orbit_invariance,
    verify_oloid_rolling,
)


def test_oloid_state_initial():
    s = OloidState()
    assert s.as_tuple() == (0, 0, 0)


def test_oloid_state_invalid():
    import pytest
    with pytest.raises(ValueError):
        OloidState(sheet=2)
    with pytest.raises(ValueError):
        OloidState(phase=4)
    with pytest.raises(ValueError):
        OloidState(parity=2)


def test_rolling_period_4_on_constant_bits():
    """With constant bit input, the (sheet, phase) returns to start after
    4 rolls; the parity may differ by K * bit mod 2."""
    for bit in (0, 1):
        s = OloidState()
        for _ in range(4):
            s = s.roll(bit)
        assert s.sheet == 0
        assert s.phase == 0
        # parity = 4 XORs of bit = 0 regardless of bit
        assert s.parity == 0


def test_full_verifier_passes():
    r = verify_oloid_rolling()
    assert r["status"] == "pass"


def test_antipodal_swap_preserves_sheet_and_phase():
    """Bit-complement does not change which sheet is in contact, only
    the cumulative parity is XORed with the input length."""
    bits = [0, 1, 1, 0, 1, 0, 1, 1]
    a = roll_chart_landing(bits)
    b = roll_chart_landing(antipodal_swap(bits))
    assert a.sheet == b.sheet
    assert a.phase == b.phase
    assert (a.parity ^ b.parity) == (len(bits) & 1)


def test_cyclic_invariance_at_k6():
    inv = landing_orbit_invariance(K=6)
    assert inv["invariant_sheet_count"] == inv["total_inputs"]
    assert inv["invariant_phase_count"] == inv["total_inputs"]


def test_landing_table_at_k8_has_256_entries():
    table = enumerate_landings(K=8)
    assert len(table) == 256


def test_landing_factors_through_length_and_parity():
    """The minimal Oloid model predicts: (sheet, phase) depends only on
    input length; parity depends only on cumulative bit XOR. Verify."""
    for K in (3, 5, 7, 11):
        # All inputs of length K should share (sheet, phase)
        ref_sheet = None
        ref_phase = None
        for n in range(1 << K):
            bits = [(n >> i) & 1 for i in range(K)]
            l = roll_chart_landing(bits)
            if ref_sheet is None:
                ref_sheet, ref_phase = l.sheet, l.phase
            else:
                assert l.sheet == ref_sheet
                assert l.phase == ref_phase
            # Parity should equal popcount(bits) mod 2
            assert l.parity == (sum(bits) & 1)


def test_dyad_head_equals_sheet():
    """The visible-tape bit (head of the dyad) is always the current sheet."""
    for sheet in (0, 1):
        for phase in (0, 1, 2, 3):
            for parity in (0, 1):
                s = OloidState(sheet, phase, parity)
                head, tail = s.as_dyad()
                assert head == sheet
