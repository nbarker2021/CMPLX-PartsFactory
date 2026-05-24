"""Port of rule30-decomposition-paper/tests/test_paper_claims.py for lattice_forge.decomposition."""
from __future__ import annotations

from lattice_forge.decomposition import (
    CHART_STATES,
    CORRECTION_FIRING_CHART_STATES,
    Rule30Checkpoints,
    center_density,
    chart_conditional_entropy,
    chart_periodicity_scan,
    correction,
    correction_from_chart,
    linearization_identity_holds,
    lucas_bit,
    lucas_sparsity_at,
    rule30,
    rule30_center_column,
    rule30_center_via_decomposition,
    rule90,
    rule90_full_grid,
    verify_all_theorems,
    verify_checkpoint_store,
)


def test_theorem_2_1_linearization_identity():
    assert linearization_identity_holds()


def test_truth_table_exhaustive():
    for left in (0, 1):
        for center in (0, 1):
            for right in (0, 1):
                assert rule30(left, center, right) == rule90(left, center, right) ^ correction(
                    left, center, right
                )


def test_theorem_3_1_lucas_matches_direct_rule90():
    for depth in [0, 1, 2, 3, 5, 8, 13, 21, 33, 64, 127, 128]:
        grid, center = rule90_full_grid(depth)
        for x in range(-depth, depth + 1):
            assert grid[depth][center + x] == lucas_bit(depth, x), (depth, x)


def test_theorem_4_1_decomposition_at_depths_1_to_128():
    for n in range(1, 129):
        result = rule30_center_via_decomposition(n)
        assert result["match"], (n, result)


def test_theorem_5_1_firing_set_is_exactly_two_states():
    firing = {state for state in CHART_STATES if correction(*state)}
    assert firing == {(0, 1, 0), (1, 1, 0)}
    assert firing == CORRECTION_FIRING_CHART_STATES


def test_correction_from_chart_agrees_with_truth_table():
    for state in CHART_STATES:
        assert correction(*state) == correction_from_chart(state)


def test_result_6_1_sparsity_at_small_depth():
    report = lucas_sparsity_at(128)
    assert 0 < report["lucas_density"] < 1
    assert 0 < report["correction_density"] < 1
    assert report["contributing_cells"] > 0


def test_construction_7_1_checkpoint_round_trip_depth_512():
    report = verify_checkpoint_store(max_depth=512)
    assert report["status"] == "pass"
    assert report["mismatch_count"] == 0


def test_checkpoint_store_anchor_arithmetic():
    store = Rule30Checkpoints(max_depth=256)
    assert store.nearest_checkpoint_at_or_before(128) == 128
    assert store.nearest_checkpoint_at_or_before(129) == 128
    assert store.nearest_checkpoint_at_or_before(63) == 0


def test_result_8_1_chart_entropy_at_depth_4096():
    report = chart_conditional_entropy(4096, order_max=2)
    assert 2.9 < report["H_1_gram"] <= 3.0
    assert 1.0 < report["H_cond_order_1"] < 2.0


def test_result_8_2_density_approaches_half():
    report = center_density(4096)
    assert 0.45 < report["density_of_1"] < 0.55


def test_result_8_3_no_period_below_512():
    report = chart_periodicity_scan(
        2048, shifts=[1, 2, 3, 5, 8, 16, 32, 64, 128, 256, 512]
    )
    assert not report["any_exact_period_found"]


def test_verify_all_theorems_passes():
    report = verify_all_theorems()
    assert report["status"] == "pass"


def test_rule30_center_column_matches_decomposition():
    column = rule30_center_column(64)
    for n, bit in enumerate(column, start=1):
        assert rule30_center_via_decomposition(n)["direct_bit"] == bit
