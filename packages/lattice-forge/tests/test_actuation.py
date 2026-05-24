"""Tests for the ±1 spectral actuation primitives and paired-read."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.actuation import (
    Actuation,
    actuate_kinematic,
    actuate_octonionic,
    actuate_quad,
    actuation_for_query,
    paired_actuation_read_octonionic,
    verify_actuation_module,
)
from lattice_forge.octonion import O_ONE, O_E4
from lattice_forge.oloid_octonionic import OctonionicOloidState
from lattice_forge.oloid_kinematic import KinematicOloidState


def test_actuation_signs():
    assert Actuation.POSITIVE.sign == 1
    assert Actuation.NEGATIVE.sign == -1


def test_actuation_composition():
    """The actuation group is Z/2: POS * POS = POS, NEG * NEG = POS."""
    assert Actuation.POSITIVE.compose(Actuation.POSITIVE) == Actuation.POSITIVE
    assert Actuation.NEGATIVE.compose(Actuation.NEGATIVE) == Actuation.POSITIVE
    assert Actuation.POSITIVE.compose(Actuation.NEGATIVE) == Actuation.NEGATIVE
    assert Actuation.NEGATIVE.compose(Actuation.POSITIVE) == Actuation.NEGATIVE


def test_actuation_spectrality():
    assert Actuation.POSITIVE.spectrality == 0
    assert Actuation.NEGATIVE.spectrality == 1


def test_actuate_octonionic_positive_is_identity():
    s = OctonionicOloidState(O_ONE)
    assert actuate_octonionic(s, Actuation.POSITIVE).octonion.components == s.octonion.components


def test_actuate_octonionic_negative_negates():
    s = OctonionicOloidState(O_ONE)
    neg = actuate_octonionic(s, Actuation.NEGATIVE)
    assert neg.octonion.components[0] == -1.0


def test_actuate_octonionic_negative_is_involution():
    s = OctonionicOloidState(O_ONE)
    back = actuate_octonionic(actuate_octonionic(s, Actuation.NEGATIVE), Actuation.NEGATIVE)
    assert back.octonion.components == s.octonion.components


def test_actuate_kinematic_negative_advances_pi():
    k = KinematicOloidState()
    neg = actuate_kinematic(k, Actuation.NEGATIVE)
    assert abs(neg.theta - math.pi) < 1e-12


def test_actuate_kinematic_negative_is_involution():
    k = KinematicOloidState()
    back = actuate_kinematic(actuate_kinematic(k, Actuation.NEGATIVE), Actuation.NEGATIVE)
    assert abs(back.theta) < 1e-12


def test_actuation_for_query():
    """Positive depth uses +1 actuation, negative depth uses -1."""
    assert actuation_for_query(5) == Actuation.POSITIVE
    assert actuation_for_query(-5) == Actuation.NEGATIVE


def test_paired_actuation_read_consistency_at_known_depths():
    """The paired-read consistency rate using the orient-bit signature
    should be 100% across known Rule 30 depths."""
    from lattice_forge.block_tower import rule30_center_column
    bits = rule30_center_column(64)
    def enum(n): return bits[n - 1]
    for N in (1, 2, 3, 5, 17, 33, 64):
        r = paired_actuation_read_octonionic(N, enum)
        assert r["bijection_consistent"], (
            f"Bijection inconsistent at N={N}: "
            f"pos_orient={r['positive_orient_bit']}, "
            f"neg_orient={r['negative_orient_bit']}"
        )


def test_paired_actuation_returns_structured_dict():
    from lattice_forge.block_tower import rule30_center_column
    bits = rule30_center_column(32)
    def enum(n): return bits[n - 1]
    r = paired_actuation_read_octonionic(5, enum)
    expected_keys = {
        "N", "bit_at_N", "bit_at_minus_N",
        "positive_state", "negative_state",
        "positive_orient_bit", "negative_orient_bit",
        "positive_dominant_index", "negative_dominant_index",
        "joint_spectral_signature", "bijection_consistent",
    }
    assert expected_keys <= set(r.keys())


def test_full_verifier_passes():
    r = verify_actuation_module()
    assert r["status"] == "pass"
    assert r["paired_read_consistency_rate"] == 1.0
