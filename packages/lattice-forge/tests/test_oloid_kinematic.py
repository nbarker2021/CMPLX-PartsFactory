"""Tests for the Oloid kinematic correspondence harness."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.oloid_kinematic import (
    KinematicOloidState,
    QUARTER_PERIOD,
    correspondence_test,
    gauge_inverted_kinematic_initial,
    gauge_inverted_quad_initial,
    roll_kinematic,
    verify_alternating_bits_zero_net,
    verify_bit_complement_inverts_rotation,
    verify_four_period_returns_to_origin,
    verify_oloid_kinematic,
    verify_two_period_is_pi_phase_advance,
)


def test_quarter_period_is_pi_over_two():
    assert abs(QUARTER_PERIOD - math.pi / 2) < 1e-12


def test_kinematic_initial_state():
    s = KinematicOloidState()
    assert s.theta == 0.0
    assert s.parity == 0
    assert s.quarter_index() == 0
    assert s.sheet() == 0
    assert s.phase() == 0


def test_kinematic_four_period_returns_to_origin():
    assert verify_four_period_returns_to_origin()


def test_kinematic_two_period_is_pi_phase_advance():
    assert verify_two_period_is_pi_phase_advance()


def test_kinematic_bit_complement_inverts_rotation():
    assert verify_bit_complement_inverts_rotation()


def test_kinematic_alternating_bits_zero_net():
    assert verify_alternating_bits_zero_net()


def test_gauge_inverted_kinematic_initial_starts_at_pi():
    """The gauge inversion sets θ = π (180° phase advance from default)."""
    s = gauge_inverted_kinematic_initial()
    assert abs(s.theta - math.pi) < 1e-12
    assert s.parity == 0


def test_gauge_inverted_quad_initial_has_negated_octonions():
    """Gauge-inverted quad has every Oloid's octonion multiplied by -1."""
    q = gauge_inverted_quad_initial()
    for o in (q.o1, q.o2, q.o3, q.o4):
        assert o.octonion.components[0] == -1.0
        assert all(abs(c) < 1e-12 for c in o.octonion.components[1:])


def test_correspondence_test_returns_structured_dict():
    bits = [1, 0, 1, 1, 0, 0, 1, 0]
    r = correspondence_test(bits, force_bijection=True)
    assert r["total_steps"] == 8
    assert "joint_match_count" in r
    assert "sheet_match_count" in r
    assert "phase_match_count" in r
    assert "first_divergence_step" in r


def test_verify_oloid_kinematic_runs_and_reports_honestly():
    r = verify_oloid_kinematic()
    assert r["status"] == "pass"
    assert r["structural_identities_pass"]
    assert r["honesty"] in {
        "PROVEN_AT_TESTED_DEPTH",
        "BOUNDED_EXEC_STRONG",
        "BOUNDED_EXEC_WEAK",
        "BOUNDED_EXEC_PARTIAL",
    }
    assert r["trigger_status"] in {
        "WP-OLOID-01-PROMOTABLE",
        "WP-OLOID-01-DEFERRED",
    }


def test_all_four_structural_identities_pass():
    r = verify_oloid_kinematic()
    checks = r["kinematic_checks"]
    assert checks["four_period_returns_to_origin"]
    assert checks["two_period_is_pi_phase_advance"]
    assert checks["bit_complement_inverts_rotation"]
    assert checks["alternating_bits_zero_net"]
