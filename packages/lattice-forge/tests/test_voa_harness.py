"""Tests for the VOA / McKay-Thompson empirical harness."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.voa_harness import (
    T_2A_COEFFICIENTS,
    T_3A_COEFFICIENTS,
    INDEX_HYPOTHESES,
    mckay_thompson_coefficient_parity,
    run_hypothesis,
    verify_voa_harness,
)


def test_coefficient_tables_are_nonempty_and_consistent():
    assert len(T_2A_COEFFICIENTS) >= 64
    assert len(T_3A_COEFFICIENTS) >= 64
    # First T_2A coefficient is 4372 (Atlas / Borcherds 1992)
    assert T_2A_COEFFICIENTS[0] == 4372
    # First T_3A coefficient is 783
    assert T_3A_COEFFICIENTS[0] == 783


def test_parity_lookup_works():
    # 4372 is even → parity 0
    assert mckay_thompson_coefficient_parity("2A", 1) == 0
    # 783 is odd → parity 1
    assert mckay_thompson_coefficient_parity("3A", 1) == 1


def test_parity_lookup_rejects_unknown_class():
    import pytest
    with pytest.raises(ValueError):
        mckay_thompson_coefficient_parity("4A", 1)


def test_parity_lookup_rejects_out_of_range():
    import pytest
    with pytest.raises(ValueError):
        mckay_thompson_coefficient_parity("2A", 0)
    with pytest.raises(ValueError):
        mckay_thompson_coefficient_parity("2A", 65 + len(T_2A_COEFFICIENTS))


def test_at_least_four_hypotheses_available():
    assert len(INDEX_HYPOTHESES) >= 4
    assert "k=N" in INDEX_HYPOTHESES
    assert "k=N-1" in INDEX_HYPOTHESES


def test_run_hypothesis_returns_structured_dict():
    r = run_hypothesis(max_depth=128, index_fn=INDEX_HYPOTHESES["k=N"])
    assert "per_class_total_tested" in r
    assert "per_class_match_count" in r
    assert "per_class_match_rate" in r
    assert "per_class_bijective_match_rate" in r
    # Bijective rate is the load-bearing signal — must be present
    for g in ("2A", "3A"):
        assert g in r["per_class_bijective_match_rate"]


def test_verify_voa_harness_runs_and_reports_honestly():
    r = verify_voa_harness(max_depth=128)
    assert r["status"] == "pass"  # harness runs successfully
    assert r["honesty"] in {
        "PROVEN_AT_TESTED_DEPTH",
        "BOUNDED_EXEC_STRONG",
        "BOUNDED_EXEC_WEAK",
        "CONJ",
    }
    assert r["trigger_status"] in {
        "WP-MOONSHINE-PROMOTABLE",
        "WP-MOONSHINE-DEFERRED",
    }
    assert "by_hypothesis" in r
    assert "best_hypothesis" in r


def test_t3a_bijective_signal_above_chance():
    """The empirical finding: with bijection forced, T_3A best-hypothesis
    rate is well above 50% chance at the tested depths. This documents
    the load-bearing pattern that forcing the bijection unlocks
    structural signal."""
    r = verify_voa_harness(max_depth=256)
    best_3a_biject = 0.0
    for hyp in r["by_hypothesis"].values():
        rate = hyp["per_class_bijective_match_rate"].get("3A", 0.0)
        if rate > best_3a_biject:
            best_3a_biject = rate
    # Above chance by at least 5 percentage points
    assert best_3a_biject >= 0.55, f"T_3A bijective rate {best_3a_biject:.3f} not above chance"
