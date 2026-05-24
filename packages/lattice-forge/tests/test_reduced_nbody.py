"""Tests for the reduced n-body (N, C, K) Lagrangian formulation."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lattice_forge.reduced_nbody import (
    ReducedNBodyState,
    conserved_quantities,
    evolve_one_step,
    evolve_many_steps,
    lagrangian_value,
    reduced_state_at_depth,
    reduced_trajectory,
    verify_reduced_nbody,
)


def test_state_construction_at_depth_1():
    s = reduced_state_at_depth(1)
    assert s.N == 1
    # Rule 30 from single seed at depth 1: center bit is 1
    assert s.C == 1
    assert s.K == 0  # 1 // 64
    assert s.chart_axis in (0, 1, 2, 3)
    assert s.chart_sheet in (0, 1)


def test_state_dimension_is_5():
    s = reduced_state_at_depth(100)
    # 5 integer coordinates per state
    assert len(s.as_tuple()) == 5
    assert len(s.as_dict()) == 5


def test_K_increments_at_page_boundaries():
    s_63 = reduced_state_at_depth(63)
    s_64 = reduced_state_at_depth(64)
    s_65 = reduced_state_at_depth(65)
    assert s_63.K == 0
    assert s_64.K == 1
    assert s_65.K == 1


def test_lagrangian_value_axis_0_equals_sheet():
    """At chart axis 0 (rank-1 idempotent), L = sheet exactly."""
    s = ReducedNBodyState(N=1, C=0, K=0, chart_axis=0, chart_sheet=0)
    assert lagrangian_value(s) == 0.0
    s = ReducedNBodyState(N=1, C=1, K=0, chart_axis=0, chart_sheet=1)
    assert lagrangian_value(s) == 1.0


def test_lagrangian_value_axis_1_2_3_uses_weyl_average():
    """At axes 1-3, L = (1/3)*sheet + (2/3)*(1-sheet)."""
    s = ReducedNBodyState(N=1, C=0, K=0, chart_axis=1, chart_sheet=0)
    assert abs(lagrangian_value(s) - 2.0 / 3.0) < 1e-9
    s = ReducedNBodyState(N=1, C=0, K=0, chart_axis=2, chart_sheet=1)
    assert abs(lagrangian_value(s) - 1.0 / 3.0) < 1e-9


def test_conserved_quantities_include_axis_and_arf():
    s = reduced_state_at_depth(50)
    cq = conserved_quantities(s)
    assert "chart_axis" in cq
    assert "correction_arf_invariant" in cq
    assert "f4_weyl_orbit_class" in cq
    # Arf is always 0 (Theorem 4.2)
    assert cq["correction_arf_invariant"] == 0


def test_evolve_one_step():
    s = reduced_state_at_depth(10)
    s_next = evolve_one_step(s)
    assert s_next.N == 11


def test_evolve_many_steps_length():
    s = reduced_state_at_depth(10)
    traj = evolve_many_steps(s, n_steps=20)
    assert len(traj) == 21  # initial + 20 steps
    assert traj[0].N == 10
    assert traj[-1].N == 30


def test_reduced_trajectory_matches_rule30():
    """Every reduced state's C IS the Rule 30 center bit at that depth."""
    from lattice_forge.block_tower import rule30_center_column
    bits = rule30_center_column(100)
    traj = reduced_trajectory(1, 100)
    for k, s in enumerate(traj):
        assert s.C == bits[k]


def test_verify_reduced_nbody_passes():
    r = verify_reduced_nbody(max_depth=256)
    assert r["status"] == "pass"
    assert r["chart_match_rate"] == 1.0
    assert r["arf_always_zero"]
    assert r["state_dimension_per_step"] == 5


def test_axis_distribution_matches_conjugate_triple():
    """Reduced n-body axis distribution = conjugate triple resolution
    depth distribution = (~22%, ~24%, ~27%, ~27%)."""
    r = verify_reduced_nbody(max_depth=256)
    dist = r["axis_distribution"]
    # All 4 axes appear with > 10% mass
    total = sum(dist.values())
    for axis in (0, 1, 2, 3):
        assert dist[axis] / total > 0.1


def test_reduction_factor_grows_with_depth():
    """Reduction factor = max_depth / 5 grows linearly with depth."""
    r_small = verify_reduced_nbody(max_depth=64)
    r_large = verify_reduced_nbody(max_depth=256)
    assert r_small["reduction_factor_at_max_depth"] < r_large["reduction_factor_at_max_depth"]
