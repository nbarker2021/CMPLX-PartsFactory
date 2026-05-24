"""Tests for the Regime C' D_4 quadratic chart codec."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.chart_codec_d4 import (
    CHART_STATES,
    ANTIPODAL_LABEL,
    SHEET_SIGN,
    chart_state,
    rule30_chart_trajectory,
    encode_d4,
    decode_d4,
    axis_sheet_subsequence,
    verify_chart_codec_d4,
)


def test_8_chart_states():
    assert len(CHART_STATES) == 8


def test_antipodal_label_partition():
    """4 axes, each with exactly 2 states (bit-complement antipodes)."""
    from collections import Counter
    counts = Counter(ANTIPODAL_LABEL.values())
    assert set(counts) == {0, 1, 2, 3}
    assert all(c == 2 for c in counts.values())
    for state, axis in ANTIPODAL_LABEL.items():
        antipode = tuple(1 - b for b in state)
        assert ANTIPODAL_LABEL[antipode] == axis


def test_sheet_sign_partition():
    """Sheet sign is 1 iff popcount >= 2, distinguishing the two states in
    each antipodal pair."""
    for state in CHART_STATES:
        assert SHEET_SIGN[state] == (1 if sum(state) >= 2 else 0)


def test_axis_sheet_inverse():
    """(axis, sheet) uniquely identifies each of the 8 chart states."""
    seen = set()
    for state in CHART_STATES:
        key = (ANTIPODAL_LABEL[state], SHEET_SIGN[state])
        assert key not in seen
        seen.add(key)
        assert chart_state(*key) == state


def test_round_trip_at_4096():
    r = verify_chart_codec_d4(max_depth=4096)
    assert r["status"] == "pass"
    assert r["round_trip_mismatches"] == 0


def test_axis_sheet_subsequence_length():
    """Sum of per-axis lengths equals total trajectory length."""
    traj = rule30_chart_trajectory(256)
    enc = encode_d4(traj)
    total = sum(len(axis_sheet_subsequence(enc, a)) for a in range(4))
    assert total == len(traj)
