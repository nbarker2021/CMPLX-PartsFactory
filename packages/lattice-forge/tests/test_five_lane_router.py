"""Tests for the 5-lane McKay-Thompson router and L/C/R chirality partition."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.voa_harness import (
    LANE_PARTITION,
    T_1A_COEFFICIENTS,
    T_2A_COEFFICIENTS,
    T_3A_COEFFICIENTS,
    T_5A_COEFFICIENTS,
    T_7A_COEFFICIENTS,
    VALID_CLASSES,
    five_lane_router,
    mckay_thompson_coefficient_parity,
)


def test_all_five_classes_registered():
    assert set(VALID_CLASSES.keys()) == {"1A", "2A", "3A", "5A", "7A"}


def test_lane_partition_covers_all_classes():
    assert set(LANE_PARTITION.keys()) == set(VALID_CLASSES.keys())
    # All values in {L, C, R}
    assert set(LANE_PARTITION.values()) <= {"L", "C", "R"}


def test_lane_partition_has_3_lane_core_and_2_lane_chirality():
    """3 classes in C (1A, 2A, 3A) + 1 in L (5A) + 1 in R (7A) = 5 lanes."""
    c_count = sum(1 for v in LANE_PARTITION.values() if v == "C")
    l_count = sum(1 for v in LANE_PARTITION.values() if v == "L")
    r_count = sum(1 for v in LANE_PARTITION.values() if v == "R")
    assert c_count == 3
    assert l_count == 1
    assert r_count == 1


def test_T_1A_first_coefficient_is_196884():
    """j(τ) - 744 has q-expansion 196884 q + 21493760 q^2 + ..."""
    assert T_1A_COEFFICIENTS[0] == 196884


def test_T_5A_first_coefficient_is_134():
    assert T_5A_COEFFICIENTS[0] == 134


def test_T_7A_first_coefficient_is_51():
    assert T_7A_COEFFICIENTS[0] == 51


def test_parity_lookup_works_for_all_five_classes():
    for g in ("1A", "2A", "3A", "5A", "7A"):
        p = mckay_thompson_coefficient_parity(g, 1)
        assert p in (0, 1)
    # 196884 is even
    assert mckay_thompson_coefficient_parity("1A", 1) == 0
    # 134 is even
    assert mckay_thompson_coefficient_parity("5A", 1) == 0
    # 51 is odd
    assert mckay_thompson_coefficient_parity("7A", 1) == 1


def test_five_lane_router_returns_structured_dict():
    r = five_lane_router(max_depth=128)
    assert "lane_match_rate" in r
    assert "lcr_match_count" in r
    assert "lcr_match_rate" in r
    assert "lr_match_rate_difference" in r
    # All 5 classes present
    for g in ("1A", "2A", "3A", "5A", "7A"):
        assert g in r["lane_match_rate"]


def test_five_lane_router_partition_sums_correctly():
    """LCR totals should sum to the total lane totals."""
    r = five_lane_router(max_depth=256)
    total_by_lane = sum(r["lane_total_tested"].values())
    total_by_lcr = sum(r["lcr_total_tested"].values())
    assert total_by_lane == total_by_lcr
