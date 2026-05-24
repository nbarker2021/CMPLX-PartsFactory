"""Tests for the Regime C chart codec (S_3 word encoding of shell=2)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.chart_codec import (
    SHELL2_STATES,
    S3,
    apply_s3,
    shell2_transition_element,
    rule30_chart_trajectory,
    shell2_subtrajectory,
    encode,
    decode,
    verify_chart_codec,
)


def test_s3_group_closure():
    """S_3 elements applied to a shell=2 state stay in {0,1}^3."""
    for state in SHELL2_STATES:
        for name in S3:
            out = apply_s3(name, state)
            assert all(b in (0, 1) for b in out)
            assert len(out) == 3


def test_transposition_inverse_self():
    """Every transposition is its own inverse: g(g(s)) = s."""
    for state in SHELL2_STATES:
        for name in ("(1 2)", "(1 3)", "(2 3)"):
            assert apply_s3(name, apply_s3(name, state)) == state


def test_shell2_pairwise_transitions():
    """Between any two distinct shell=2 states, exactly one transposition
    maps src → dst, and identity maps src → src."""
    for src in SHELL2_STATES:
        for dst in SHELL2_STATES:
            g = shell2_transition_element(src, dst)
            assert apply_s3(g, src) == dst


def test_round_trip_at_depth_4096():
    result = verify_chart_codec(max_depth=4096)
    assert result["status"] == "pass"
    assert result["round_trip_mismatches"] == 0
    # No 3-cycles in atomic single-step transitions
    assert result["element_counts"]["(1 2 3)"] == 0
    assert result["element_counts"]["(1 3 2)"] == 0


def test_encode_decode_round_trip_small():
    traj = rule30_chart_trajectory(64)
    shell2 = shell2_subtrajectory(traj)
    decoded = decode(encode(shell2))
    assert decoded == shell2
