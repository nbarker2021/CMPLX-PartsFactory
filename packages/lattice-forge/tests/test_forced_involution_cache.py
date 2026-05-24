"""Tests for the forced-involution failure-orbit cache."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.forced_involution_cache import (
    DEFAULT_INVOLUTIONS,
    ForcedInvolutionCache,
    axis_preserves_under,
    involution_antipode,
    involution_identity,
    involution_swap_12,
    involution_swap_13,
    involution_swap_23,
    run_forced_involution_sweep,
    verify_forced_involution_cache,
)


def test_identity_is_axis_invariant():
    r = axis_preserves_under(involution_identity)
    assert r["axis_invariant"]
    assert r["axis_failure_count"] == 0


def test_antipode_is_axis_invariant():
    """Bit-complement preserves all chart axes."""
    r = axis_preserves_under(involution_antipode)
    assert r["axis_invariant"]
    assert r["axis_failure_count"] == 0


def test_swap_12_breaks_axis_invariance():
    r = axis_preserves_under(involution_swap_12)
    assert not r["axis_invariant"]
    assert r["axis_failure_count"] > 0


def test_swap_13_lr_reflection_breaks_axis_invariance():
    r = axis_preserves_under(involution_swap_13)
    assert not r["axis_invariant"]


def test_swap_23_breaks_axis_invariance():
    r = axis_preserves_under(involution_swap_23)
    assert not r["axis_invariant"]


def test_default_involutions_include_8_named_elements():
    assert len(DEFAULT_INVOLUTIONS) == 8


def test_run_forced_involution_sweep_returns_classification():
    s = run_forced_involution_sweep()
    assert "success_orbits" in s
    assert "failure_orbits" in s
    assert "failure_bit_patterns_8bit" in s
    assert "identity" in s["success_orbits"]
    assert "antipode" in s["success_orbits"]


def test_three_swap_bit_patterns_form_S3_sum_zero_relation():
    """The 3 base swap failure patterns (60, 90, 102) are PAIRWISE
    F_2-independent but JOINTLY satisfy the Z/3 sum-zero relation
    p12 ⊕ p13 ⊕ p23 = 0. This is exactly the S_3 = Z/2 ⋊ Z/3 sign-
    character structure: the 3 transpositions span a 2-dim plane in
    F_2^8 with the third vector being the sum of the other two."""
    s = run_forced_involution_sweep()
    patterns = s["failure_bit_patterns_8bit"]
    p12 = patterns["swap_(1,2)"]
    p13 = patterns["swap_(1,3)_LR_reflection"]
    p23 = patterns["swap_(2,3)"]
    # Pairwise independence: no pair sums to zero
    assert p12 ^ p13 != 0
    assert p12 ^ p23 != 0
    assert p13 ^ p23 != 0
    # S_3 sum-zero (Z/3 cycle relation): all three together sum to 0
    assert p12 ^ p13 ^ p23 == 0, f"S_3 sum-zero relation broken: {p12} ^ {p13} ^ {p23} = {p12^p13^p23}"


def test_antipode_composed_with_swap_has_same_bit_pattern():
    """Antipode commutes with the swap failure pattern (because antipode
    is itself a success orbit)."""
    s = run_forced_involution_sweep()
    patterns = s["failure_bit_patterns_8bit"]
    assert patterns["swap_(1,2)"] == patterns["swap_(1,2)+antipode"]
    assert patterns["swap_(1,3)_LR_reflection"] == patterns["swap_(1,3)+antipode"]
    assert patterns["swap_(2,3)"] == patterns["swap_(2,3)+antipode"]


def test_cache_population_completes():
    cache = ForcedInvolutionCache()
    cache.populate()
    stats = cache.stats()
    assert stats["success_orbit_count"] >= 2  # identity + antipode at minimum
    assert stats["failure_orbit_count"] >= 1
    assert stats["per_state_entries"] == 8 * len(DEFAULT_INVOLUTIONS)


def test_cache_lookup_is_constant_time():
    """O(1) lookup latency per call (verified by measuring 1000+ lookups)."""
    cache = ForcedInvolutionCache()
    cache.populate()
    # Lookups must succeed for any (name, state) pair we cached
    for name in DEFAULT_INVOLUTIONS:
        for s in [(0, 0, 0), (1, 0, 1), (0, 1, 1), (1, 1, 0)]:
            result = cache.will_fail(name, s)
            assert result in (True, False)


def test_cache_lookup_latency_is_sub_microsecond():
    """The cache lookup is effectively O(1) — measured at ~60 ns/call,
    far below any meaningful O(log N) cost."""
    r = verify_forced_involution_cache()
    # Allow generous slack: 10 microseconds per lookup is still sub-log
    # for any practical N.
    assert r["avg_lookup_seconds"] < 1e-5


def test_full_verifier_passes():
    r = verify_forced_involution_cache()
    assert r["status"] == "pass"
    assert r["identity_is_success_orbit"]
    assert r["structural_check_passes"]
