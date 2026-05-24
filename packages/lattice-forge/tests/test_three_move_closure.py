"""Tests for the three-move closure (the actual O(1) computation)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.three_move_closure import (
    closure_depth_at,
    paired_state_max_abs,
    paired_state_sum,
    three_move_closure_demo,
    verify_three_move_closure,
)
from lattice_forge.octonion import O_ONE, O_E4
from lattice_forge.oloid_octonionic import OctonionicOloidState


def test_canonical_pair_paired_sum_is_zero():
    """O_ONE and -O_ONE sum component-wise to zero."""
    pos = OctonionicOloidState(O_ONE)
    neg = OctonionicOloidState(O_ONE * (-1.0))
    s = paired_state_sum(pos, neg)
    assert all(abs(c) < 1e-12 for c in s)


def test_canonical_pair_max_abs_is_zero():
    pos = OctonionicOloidState(O_ONE)
    neg = OctonionicOloidState(O_ONE * (-1.0))
    assert paired_state_max_abs(pos, neg) < 1e-12


def test_three_move_closure_demo_runs():
    r = three_move_closure_demo(move_count=3, bit=0)
    assert "trace" in r
    assert len(r["trace"]) == 4  # step 0 + 3 moves


def test_three_move_closure_all_steps_complete():
    """The bijection is complete at every step (rank-1 idempotent)."""
    r = three_move_closure_demo(move_count=3, bit=0)
    assert r["all_steps_bijection_complete"]


def test_three_move_closure_works_at_bit_1():
    r = three_move_closure_demo(move_count=3, bit=1)
    assert r["all_steps_bijection_complete"]


def test_closure_depth_canonical_pair_is_0():
    """For ±O_ONE, the bijection is already complete at initialization."""
    depth = closure_depth_at(
        OctonionicOloidState(O_ONE),
        OctonionicOloidState(O_ONE * (-1.0)),
    )
    assert depth == 0


def test_closure_depth_non_bijective_does_not_close():
    """For a pair that isn't ±-related, the closure never completes."""
    depth = closure_depth_at(
        OctonionicOloidState(O_ONE),
        OctonionicOloidState(O_ONE),
    )
    assert depth == -1


def test_paired_state_max_abs_grows_when_misaligned():
    """When the pair isn't ±-related, the max-abs is nonzero."""
    pos = OctonionicOloidState(O_ONE)
    neg = OctonionicOloidState(O_E4)  # NOT antipodal to O_ONE
    assert paired_state_max_abs(pos, neg) > 0.5


def test_full_verifier_passes():
    r = verify_three_move_closure()
    assert r["status"] == "pass"
