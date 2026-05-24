"""Tests for the Regime A block-addressed Rule 30 extractor."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.block_tower import (
    Rule30Checkpoints,
    rule30_center_column,
    verify_block_tower,
)
from lattice_forge.rule30_block_extractor import (
    Rule30BlockExtractor,
    verify_extractor,
)


def test_checkpoint_store_round_trip_512():
    r = verify_block_tower(max_depth=512)
    assert r["status"] == "pass"
    assert r["mismatch_count"] == 0


def test_extractor_individual_bits_match_brute_force():
    r = verify_extractor(max_depth=512)
    assert r["status"] == "pass"
    assert r["individual_mismatch_count"] == 0


def test_extractor_range_read_matches_brute_force():
    ex = Rule30BlockExtractor(max_depth=512)
    bf = rule30_center_column(512)
    rr = ex.bit_range(1, 512)
    assert rr["bits"] == bf


def test_extractor_query_time_independent_of_depth():
    """Per-query work is bounded by base_page, not by n."""
    import time
    ex = Rule30BlockExtractor(max_depth=4096)
    t_small = t_large = 0.0
    N = 50
    for _ in range(N):
        t0 = time.perf_counter()
        ex.nth_bit(64)
        t_small += time.perf_counter() - t0
        t0 = time.perf_counter()
        ex.nth_bit(4096)
        t_large += time.perf_counter() - t0
    # Allow a 5x slack to absorb timer noise on Windows.
    assert t_large < 5 * t_small, f"t_large={t_large}, t_small={t_small}"


def test_checkpoint_at_page_boundary():
    store = Rule30Checkpoints(max_depth=256)
    # Direct row at a checkpoint requires zero replay.
    anchor = store.nearest_checkpoint_at_or_before(128)
    assert anchor == 128
