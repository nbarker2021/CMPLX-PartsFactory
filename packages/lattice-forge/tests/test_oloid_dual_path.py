"""Tests for the dual-path Oloid (3-dyad S_3-symmetric structure).

These tests verify the *structural* properties of the dual-path Oloid:
S_3 cyclic involution, dyad-addressing arithmetic, parallel rolling.
They do NOT verify the per-dyad roll rule against Rule 30 — that
mapping is presently speculative and is the open scope for the
dual-path solver to become a true tape predictor.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.oloid_dual_path import (
    DualPathOloid,
    dyad_index_at_depth,
    involution_superscript_advances_dyad,
    roll_dual_path,
    read_tape_at_depth,
    read_tape_with_enumeration,
    verify_read_then_verify,
    gauge_inverted_initial,
    verify_dual_path_oloid,
)
from lattice_forge.block_tower import rule30_center_column
from lattice_forge.oloid_rolling import OloidState


def test_initial_dual_path_state():
    d = DualPathOloid()
    assert d.podal.sheet == 0
    assert d.antipodal.sheet == 1
    assert d.shared.phase == 2
    assert d.level == 0


def test_triple_involution_returns_to_original_dyads():
    """S_3's cyclic subgroup has order 3: three involutions restore the
    dyad roles (though `level` is incremented monotonically)."""
    d = DualPathOloid()
    d3 = d.involute().involute().involute()
    assert d3.podal == d.podal
    assert d3.antipodal == d.antipodal
    assert d3.shared == d.shared
    assert d3.level == 3


def test_dyad_index_arithmetic():
    """d_N = (N + level) mod 3."""
    for N in range(20):
        for level in range(7):
            assert dyad_index_at_depth(N, level) == (N + level) % 3


def test_involution_superscript_cyclic_property():
    for d_init in range(3):
        for k in range(10):
            assert (
                involution_superscript_advances_dyad(d_init, k)
                == (d_init + k) % 3
            )


def test_parallel_roll_advances_all_three_dyads():
    """Rolling advances all three dyads simultaneously."""
    d = DualPathOloid()
    bits = [1, 0, 1, 1]
    rolled = roll_dual_path(bits)
    # Phase should advance by len(bits) for each dyad
    assert rolled.podal.phase == (0 + len(bits)) % 4
    assert rolled.antipodal.phase == (0 + len(bits)) % 4
    assert rolled.shared.phase == (2 + len(bits)) % 4


def test_full_verifier_passes_structural_checks():
    """The verifier passes the structural checks (S_3, addressing, etc.).
    Tape-readout match rate is NOT required to pass — that mapping is
    speculative and remains the open scope for the dual-path solver."""
    r = verify_dual_path_oloid()
    assert r["status"] == "pass"
    # Document the actual readout rate; do not assert above-chance.
    assert "tape_readout_match_rate" in r


def test_head_tail_triad_after_known_input():
    """The triad after a known bit input is deterministic."""
    bits = [1, 0, 1, 1, 0, 0, 1, 0]
    state = roll_dual_path(bits)
    triad = state.head_tail_triad()
    # Three dyads, each a (head, tail) pair of bits
    assert len(triad) == 3
    for dyad in triad:
        assert len(dyad) == 2
        assert all(b in (0, 1) for b in dyad)


def test_gauge_inverted_initial_state():
    """The 180° gauge inversion flips each dyad's sheet and advances
    each phase by 2."""
    state = gauge_inverted_initial()
    assert state.podal.sheet == 1
    assert state.podal.phase == 2
    assert state.antipodal.sheet == 0
    assert state.antipodal.phase == 2
    assert state.shared.sheet == 1
    assert state.shared.phase == 0


def test_read_then_verify_achieves_100_percent_match():
    """The read-then-verify workflow always returns the enumeration bit;
    consistency check passes at every depth."""
    bits = rule30_center_column(200)
    def enum(N): return bits[N - 1]
    result = verify_read_then_verify(enum, sample_depths=list(range(1, 201)))
    assert result["bit_match_rate"] == 1.0
    assert result["consistency_rate"] == 1.0


def test_read_then_verify_returns_correct_bit_per_query():
    """Per-query: returned bit equals enumeration bit exactly."""
    bits = rule30_center_column(100)
    def enum(N): return bits[N - 1]
    for N in [1, 5, 17, 63, 64, 99, 100]:
        r = read_tape_with_enumeration(N, enum)
        assert r["bit"] == bits[N - 1]
        assert r["bit_at_minus_N"] == (1 - bits[N - 1])


def test_orient_bit_is_present_and_balanced():
    """The orient bit is computed and roughly balanced over many depths."""
    bits = rule30_center_column(500)
    def enum(N): return bits[N - 1]
    orient_seq = [
        read_tape_with_enumeration(N, enum)["orient_bit"] for N in range(1, 501)
    ]
    density = sum(orient_seq) / len(orient_seq)
    assert 0.3 < density < 0.7


def test_read_tape_at_depth_returns_structured_dict():
    """The read function returns the structured dyad-selection record."""
    bits = [1, 0, 1, 1, 0, 0, 1, 0]
    for N in range(1, len(bits) + 1):
        r = read_tape_at_depth(N, bits, level=0)
        assert r["N"] == N
        assert r["level"] == 0
        assert r["dyad_index"] in (0, 1, 2)
        assert r["dyad_name"] in DualPathOloid.DYAD_NAMES
        assert r["head"] in (0, 1)
        assert r["tail"] in (0, 1)
        assert r["true_bit_at_N"] == bits[N - 1]
