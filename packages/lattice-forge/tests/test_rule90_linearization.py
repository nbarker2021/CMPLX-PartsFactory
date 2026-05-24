"""Tests for the Rule 30 = Rule 90 + correction linearization."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.rule90_linearization import (
    correction,
    linearization_identity_holds,
    lucas_bit,
    correction_from_chart,
    rule30_center_via_decomposition,
    verify_rule90_linearization,
    CORRECTION_FIRING_AXES_SHEETS,
)
from lattice_forge.chart_codec_d4 import ANTIPODAL_LABEL, SHEET_SIGN, CHART_STATES


def test_truth_table_identity():
    """Rule 30 = Rule 90 XOR (C AND NOT R) at every truth-table input."""
    assert linearization_identity_holds()


def test_lucas_bit_matches_direct_rule90():
    """Lucas binomial closed form matches direct Rule 90 simulation."""
    for d in [0, 1, 2, 3, 5, 8, 13, 21, 33, 64]:
        width = 2 * d + 3
        center = width // 2
        row = [0] * width
        row[center] = 1
        for _ in range(d):
            nr = [0] * width
            for i in range(width):
                l = row[i - 1] if i > 0 else 0
                r = row[i + 1] if i + 1 < width else 0
                nr[i] = l ^ r
            row = nr
        for x in range(-d, d + 1):
            assert row[center + x] == lucas_bit(d, x)


def test_correction_firing_set():
    """corr(L,C,R) = C AND NOT R fires exactly on {(0,1,0), (1,1,0)}."""
    firing = {s for s in CHART_STATES if correction(*s)}
    assert firing == {(0, 1, 0), (1, 1, 0)}


def test_correction_d4_codec_projection():
    """The correction firing set corresponds to (axis2, sheet0) U (axis3, sheet1)."""
    for state in CHART_STATES:
        key = (ANTIPODAL_LABEL[state], SHEET_SIGN[state])
        assert correction(*state) == (1 if key in CORRECTION_FIRING_AXES_SHEETS else 0)
        assert correction(*state) == correction_from_chart(state)


def test_decomposition_matches_direct_at_depths_1_through_64():
    """For depths 1..64, the Rule 30 center bit reconstructed via
    LucasBit(N,0) XOR XOR-of-corrections matches direct simulation."""
    for N in range(1, 65):
        r = rule30_center_via_decomposition(N)
        assert r["match"], (
            f"decomposition mismatch at N={N}: "
            f"decomposed {r['bit']} vs direct {r['direct_simulated_bit']}"
        )


def test_full_verifier_passes():
    r = verify_rule90_linearization()
    assert r["status"] == "pass"
    assert r["identity_at_truth_table"]
    assert r["lucas_matches_direct_rule90_at_depth_64"]
    assert r["decomposition_matches_at_all_depths"]
