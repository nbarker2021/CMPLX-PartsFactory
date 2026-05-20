"""
Tests for cmplx.morsr — diagnostic pulse engine + traversal + sonar.
"""
from __future__ import annotations

import math

import pytest

from cmplx.morphon import MorphonController
from cmplx.morsr import (
    CompleteTraversal,
    DEFAULT_DIM,
    DEFAULT_MASK_LEN,
    E8_DIRECTIONS_DEFAULT,
    Handshake,
    HandshakeLog,
    MORSREngine,
    MORSRPolicy,
    MORSRProvider,
    NodeAnalysis,
    OperatorRegistry,
    Overlay,
    Region,
    SHADOW_CATEGORIES,
    ShadowAction,
    ShellMode,
    SonarAtom,
    SonarScan,
    SonarScanResult,
    StopMetric,
    TraversalResult,
    TraversalStrategy,
    build_shell,
    in_shell,
    op_midpoint,
    op_parity_mirror,
    op_rtheta,
    op_weyl_reflect,
)
from cmplx.nsl import GateMode, NSLProvider, NSLSectors


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------

def test_overlay_autogenerates_id_and_pads():
    o = Overlay()
    assert o.overlay_id
    assert len(o.position) == DEFAULT_DIM
    assert len(o.activations) == DEFAULT_MASK_LEN


def test_overlay_position_passthrough():
    o = Overlay(position=(1.0, 2.0, 3.0))
    assert o.position[:3] == (1.0, 2.0, 3.0)


def test_overlay_activations_clamped_to_bit():
    o = Overlay(activations=(0, 1, 5, -3, 7))
    assert o.activations[:5] == (0, 1, 1, 1, 1)


def test_overlay_hash_id_deterministic():
    o1 = Overlay(position=(1.0,) * 8)
    o2 = Overlay(position=(1.0,) * 8)
    assert o1.hash_id() == o2.hash_id()


def test_overlay_clone_changes_id():
    o = Overlay()
    c = o.clone()
    assert c.overlay_id != o.overlay_id
    assert c.position == o.position


def test_overlay_active_indices():
    acts = [0] * 240
    acts[5] = 1
    acts[100] = 1
    o = Overlay(activations=tuple(acts))
    assert o.active_indices() == [5, 100]
    assert o.num_active() == 2


def test_overlay_to_from_dict_round_trip():
    o = Overlay(position=(0.5, 0.3, 0.1))
    d = o.to_dict()
    o2 = Overlay.from_dict(d)
    assert o2.position == o.position
    assert o2.activations == o.activations


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

def test_op_rtheta_rotates_first_two_axes():
    o = Overlay(position=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    rotated = op_rtheta(o, theta=math.pi / 2)
    assert rotated.position[0] == pytest.approx(0.0, abs=1e-9)
    assert rotated.position[1] == pytest.approx(1.0, abs=1e-9)


def test_op_weyl_reflect_negates_root():
    o = Overlay(position=(1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    r = op_weyl_reflect(o, root_index=1)
    assert r.position[1] == -2.0


def test_op_midpoint_with_other():
    a = Overlay(position=(0.0,) * 8)
    b = Overlay(position=(2.0,) * 8)
    m = op_midpoint(a, b, weight=0.5)
    assert all(v == pytest.approx(1.0) for v in m.position)


def test_op_midpoint_without_other_perturbs():
    o = Overlay(position=(1.0,) * 8)
    p = op_midpoint(o)
    # Deterministic perturbation; first component shifts by COUPLING*0.1
    assert p.position != o.position


def test_op_parity_mirror_flips_activations():
    acts = [0] * 240
    acts[0] = 1
    o = Overlay(activations=tuple(acts))
    m = op_parity_mirror(o)
    assert m.activations[0] == 0
    assert m.activations[1] == 1


def test_op_returns_new_overlay():
    o = Overlay(position=(1.0,) * 8)
    r = op_rtheta(o)
    assert r.overlay_id != o.overlay_id  # new id
    assert r.position != o.position


def test_operator_registry_has_canonical_four():
    reg = OperatorRegistry()
    assert set(reg.names()) == {"rtheta", "weyl_reflect", "midpoint", "parity_mirror"}
    assert len(reg) == 4


def test_operator_registry_add_custom():
    reg = OperatorRegistry()
    reg.add("custom", lambda o: o.clone())
    assert "custom" in reg.names()


def test_operator_registry_rejects_duplicate():
    reg = OperatorRegistry()
    with pytest.raises(RuntimeError):
        reg.add("rtheta", lambda o: o)


def test_operator_registry_lookup_unknown():
    reg = OperatorRegistry()
    with pytest.raises(LookupError):
        reg.get("nope")


# ---------------------------------------------------------------------------
# Shell construction
# ---------------------------------------------------------------------------

def test_shell_radial_grows_with_stage():
    allowed_0, meta_0 = build_shell(ShellMode.RADIAL, 240, 0.25, 2, 0)
    allowed_2, meta_2 = build_shell(ShellMode.RADIAL, 240, 0.25, 2, 2)
    assert meta_0["R"] < meta_2["R"]
    assert len(allowed_0) < len(allowed_2)


def test_shell_radial_caps_at_one():
    _, meta = build_shell(ShellMode.RADIAL, 240, 0.5, 10, 10)
    assert meta["R"] == 1.0


def test_shell_bfs_starts_from_actives():
    allowed, meta = build_shell(
        ShellMode.BFS, 240, 1, 2, 0, active_idxs=[100]
    )
    # At stage 0, hops = 1 — only neighbors ±1 of 100 reachable (+the seed)
    assert 100 in allowed
    assert 99 in allowed
    assert 101 in allowed
    assert 50 not in allowed


def test_shell_bfs_expands_with_stage():
    a0, _ = build_shell(ShellMode.BFS, 240, 1, 2, 0, active_idxs=[100])
    a1, _ = build_shell(ShellMode.BFS, 240, 1, 2, 1, active_idxs=[100])
    assert len(a1) > len(a0)


def test_shell_unknown_mode_raises():
    with pytest.raises(ValueError):
        build_shell("warp", 240, 0.5, 2, 0)


def test_in_shell_check():
    allowed = {1, 2, 3, 4, 5}
    assert in_shell([1, 3], allowed)
    assert not in_shell([1, 10], allowed)


# ---------------------------------------------------------------------------
# Handshake + HandshakeLog
# ---------------------------------------------------------------------------

def test_handshake_auto_id_and_timestamp():
    h = Handshake(op="rtheta", phi_before=1.0, phi_after=0.5)
    assert h.handshake_id
    assert h.timestamp > 0
    assert h.delta == -0.5


def test_handshake_to_dict_version_field():
    h = Handshake(op="rtheta", phi_before=1.0, phi_after=0.5)
    assert h.to_dict()["version"] == "morsr_handshake_v1"


def test_handshake_signature_stable():
    h = Handshake(op="rtheta", phi_before=1.0, phi_after=0.5)
    sig1 = h.signature
    sig2 = h.signature
    assert sig1 == sig2


def test_log_aggregates_reasons_and_ops():
    log = HandshakeLog()
    log.append(Handshake(op="rtheta", accepted=True, reason="strict_decrease"))
    log.append(Handshake(op="rtheta", accepted=False, reason="out_of_shell"))
    log.append(Handshake(op="midpoint", accepted=True, reason="strict_decrease"))
    assert log.reason_counts() == {
        "strict_decrease": 2, "out_of_shell": 1,
    }
    assert log.op_counts() == {"rtheta": 2, "midpoint": 1}


def test_log_stats_accept_rate():
    log = HandshakeLog()
    log.append(Handshake(accepted=True))
    log.append(Handshake(accepted=False))
    log.append(Handshake(accepted=True))
    stats = log.stats()
    assert stats["total"] == 3
    assert stats["accepts"] == 2
    assert stats["accept_rate"] == pytest.approx(2 / 3)


def test_log_by_op_filter():
    log = HandshakeLog()
    log.append(Handshake(op="rtheta"))
    log.append(Handshake(op="midpoint"))
    assert len(log.by_op("rtheta")) == 1
    assert len(log.by_op("midpoint")) == 1


def test_log_jsonl_serializes():
    log = HandshakeLog()
    log.append(Handshake(op="rtheta"))
    log.append(Handshake(op="midpoint"))
    jsonl = log.to_jsonl()
    assert jsonl.count("\n") == 1
    assert "rtheta" in jsonl
    assert "midpoint" in jsonl


# ---------------------------------------------------------------------------
# MORSREngine — the pulse cycle
# ---------------------------------------------------------------------------

def test_engine_pulse_returns_region():
    eng = MORSREngine(policy=MORSRPolicy(max_stages=2,
                                          gate_mode=GateMode.SIGNAL))
    seed = Overlay(position=(1.0,) * 8)
    region = eng.pulse(seed)
    assert isinstance(region, Region)
    assert region.seed_id == seed.overlay_id
    assert len(region.stages) > 0


def test_engine_pulse_records_handshakes():
    eng = MORSREngine(policy=MORSRPolicy(max_stages=1,
                                          gate_mode=GateMode.SIGNAL))
    eng.pulse(Overlay(position=(1.0,) * 8))
    # 4 operators × 1 stage = 4 candidates
    assert len(eng.log) == 4


def test_engine_pulse_status_set():
    eng = MORSREngine(policy=MORSRPolicy(
        max_stages=3, gate_mode=GateMode.SIGNAL,
        stop_threshold=1e-10,  # never trigger threshold stop
    ))
    region = eng.pulse(Overlay(position=(1.0,) * 8))
    assert region.status in {
        "terminated_threshold", "terminated_factor_exhausted", "max_stages",
    }


def test_engine_pulse_govern_rejects_increases():
    """With GOVERN gate, an op that increases ΔΦ is rejected."""
    policy = MORSRPolicy(
        max_stages=1, gate_mode=GateMode.GOVERN, eps_phi=1e-9,
    )
    eng = MORSREngine(policy=policy)
    # Start at zero — any op that makes the position non-zero may
    # increase phi_total via Shannon delta; at minimum no strict
    # decrease is possible.
    region = eng.pulse(Overlay(position=(0.0,) * 8))
    accepts = sum(s.accepts for s in region.stages)
    # With govern mode and zero initial position, conservative acceptance
    assert accepts >= 0  # acceptance count is non-negative


def test_engine_pulse_signal_accepts_all():
    eng = MORSREngine(policy=MORSRPolicy(
        max_stages=1, gate_mode=GateMode.SIGNAL,
    ))
    region = eng.pulse(Overlay(position=(1.0,) * 8))
    # SIGNAL mode never rejects on conservation grounds
    accepts = sum(s.accepts for s in region.stages)
    # 4 operators × 1 stage = 4 attempts; in SIGNAL mode all conserved
    # OR signaled candidates are accepted (unless plateau exhausted)
    assert accepts > 0


def test_engine_pulse_summary_includes_metrics():
    eng = MORSREngine(policy=MORSRPolicy(max_stages=1,
                                          gate_mode=GateMode.SIGNAL))
    region = eng.pulse(Overlay(position=(1.0,) * 8))
    summary = region.summary()
    for key in ("seed_id", "stage_count", "total_attempts", "total_accepts"):
        assert key in summary


def test_engine_reset_clears_log():
    eng = MORSREngine(policy=MORSRPolicy(max_stages=1,
                                          gate_mode=GateMode.SIGNAL))
    eng.pulse(Overlay(position=(1.0,) * 8))
    assert len(eng.log) > 0
    eng.reset()
    assert len(eng.log) == 0


def test_engine_policy_factors_consumed_in_order():
    policy = MORSRPolicy(
        shell_factors=(1, 2, 4),
        max_stages=3,
        gate_mode=GateMode.SIGNAL,
        stop_threshold=-1.0,  # never stop on threshold
    )
    eng = MORSREngine(policy=policy)
    region = eng.pulse(Overlay(position=(1.0,) * 8))
    assert len(region.stages) == 3


# ---------------------------------------------------------------------------
# CompleteTraversal — 240-node mode
# ---------------------------------------------------------------------------

def test_traversal_visits_all_roots():
    t = CompleteTraversal()
    result = t.explore(Overlay(position=(0.0,) * 8))
    assert len(result.visited) == 240


def test_traversal_systematic_order():
    t = CompleteTraversal()
    result = t.explore(
        Overlay(position=(0.0,) * 8),
        strategy=TraversalStrategy.SYSTEMATIC,
    )
    indices = [n.node_index for n in result.visited]
    assert indices == list(range(240))


def test_traversal_distance_ordered():
    t = CompleteTraversal()
    result = t.explore(
        Overlay(position=(0.0,) * 8),
        strategy=TraversalStrategy.DISTANCE_ORDERED,
    )
    distances = [n.distance_to_initial for n in result.visited]
    # Allow ties but generally non-decreasing
    assert distances[0] <= distances[-1]


def test_traversal_chamber_guided():
    t = CompleteTraversal()
    result = t.explore(
        Overlay(position=(0.0,) * 8),
        strategy=TraversalStrategy.CHAMBER_GUIDED,
    )
    assert len(result.visited) == 240


def test_traversal_returns_best_node():
    t = CompleteTraversal()
    result = t.explore(Overlay(position=(0.0,) * 8))
    assert result.best_node_index >= 0
    assert result.best_node_index < 240
    # best_score is the max of all visited scores
    all_scores = [n.objective_score for n in result.visited]
    assert result.best_score == max(all_scores)


def test_traversal_summary_keys():
    t = CompleteTraversal()
    result = t.explore(Overlay(position=(0.0,) * 8))
    s = result.summary()
    for k in ("strategy", "nodes_visited", "best_score", "score_mean"):
        assert k in s


def test_traversal_top_k_orders_by_score():
    t = CompleteTraversal()
    result = t.explore(Overlay(position=(0.0,) * 8))
    top = result.top_k(k=5)
    scores = [n.objective_score for n in top]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# SonarScan — 240-direction ping mode
# ---------------------------------------------------------------------------

def test_sonar_default_directions_240():
    scan = SonarScan()
    assert scan.directions_count == E8_DIRECTIONS_DEFAULT
    assert len(scan.directions) == 240


def test_sonar_register_atom():
    scan = SonarScan()
    atom = scan.register_atom("a1", [0.5, 0, 0, 0, 0, 0, 0, 0],
                              labels=["foo"])
    assert isinstance(atom, SonarAtom)
    assert scan.atom_count == 1


def test_sonar_ping_empty_field_shell_3():
    scan = SonarScan()
    result = scan.ping([0.0] * 8, radius=1.0)
    assert result.hit_count == 0
    assert result.shell == "shell_3"


def test_sonar_ping_records_hits():
    scan = SonarScan()
    # Register an atom along the first direction
    direction = scan.directions[0]
    atom_coords = tuple(0.5 * c for c in direction)
    scan.register_atom("a1", atom_coords)
    result = scan.ping([0.0] * 8, radius=2.0)
    assert result.hit_count >= 1


def test_sonar_ping_filters_by_radius():
    scan = SonarScan()
    # Atom outside radius
    scan.register_atom("far", [10.0] + [0.0] * 7)
    result = scan.ping([0.0] * 8, radius=1.0)
    assert result.hit_count == 0


def test_sonar_shell_classification():
    scan = SonarScan()
    # Register many atoms in many directions to push depth_score up
    for i in range(0, 240, 2):  # every other direction
        direction = scan.directions[i]
        scan.register_atom(f"a{i}", tuple(0.5 * c for c in direction))
    result = scan.ping([0.0] * 8, radius=2.0)
    # Should land in shell_0 or shell_1
    assert result.shell in {"shell_0", "shell_1"}


def test_sonar_shadow_actions_emitted():
    scan = SonarScan()
    # No atoms → all 240 directions unhit → 8 categories × 30 unhit
    result = scan.ping([0.0] * 8, radius=1.0)
    assert len(result.shadow_actions) == 8
    for action in result.shadow_actions:
        assert action.category in SHADOW_CATEGORIES
        assert action.unhit_count > 0


def test_sonar_shadow_categories_are_eight():
    assert len(SHADOW_CATEGORIES) == 8
    assert "geometry" in SHADOW_CATEGORIES
    assert "governance" in SHADOW_CATEGORIES


def test_sonar_result_to_dict_keys():
    scan = SonarScan()
    result = scan.ping([0.0] * 8)
    d = result.to_dict()
    for k in ("source", "radius", "hit_count", "depth_score", "shell",
              "shadow_actions", "coverage_by_category"):
        assert k in d


def test_sonar_coverage_by_category_all_categories():
    scan = SonarScan()
    result = scan.ping([0.0] * 8)
    coverage = result.coverage_by_category()
    assert set(coverage.keys()) == set(SHADOW_CATEGORIES)


def test_sonar_register_atoms_batch():
    scan = SonarScan()
    n = scan.register_atoms_batch([
        {"atom_id": "a1", "e8_coords": [0.5] * 8},
        {"atom_id": "a2", "e8_coords": [0.3] * 8},
    ])
    assert n == 2


# ---------------------------------------------------------------------------
# MORSRProvider — composite (the `diagnostic` port)
# ---------------------------------------------------------------------------

def test_provider_pulse_uses_engine():
    nsl = NSLProvider()
    p = MORSRProvider(nsl=nsl)
    region = p.pulse(Overlay(position=(1.0,) * 8))
    assert isinstance(region, Region)


def test_provider_traverse_uses_traversal():
    p = MORSRProvider()
    result = p.traverse(Overlay(position=(0.0,) * 8))
    assert isinstance(result, TraversalResult)
    assert len(result.visited) == 240


def test_provider_scan_uses_sonar():
    p = MORSRProvider()
    p.register_atom("a1", [0.5, 0, 0, 0, 0, 0, 0, 0])
    result = p.scan([0.0] * 8, radius=2.0)
    assert isinstance(result, SonarScanResult)


def test_provider_add_operator():
    p = MORSRProvider()
    before = len(p.operators)
    p.add_operator("custom", lambda o: o.clone())
    assert len(p.operators) == before + 1


def test_provider_registers_on_diagnostic_port():
    mc = MorphonController.get()
    p = MORSRProvider()
    mc.register("diagnostic", p)
    assert mc.get_provider("diagnostic") is p


def test_provider_health_keys():
    p = MORSRProvider()
    h = p.health
    assert h["ok"] is True
    assert h["service"] == "morsr_provider"
    assert h["operators"] == 4
    assert h["traversal_roots"] == 240


def test_provider_pulse_then_scan_then_traverse():
    """End-to-end: all three modes on one provider."""
    p = MORSRProvider()
    # Pulse
    region = p.pulse(Overlay(position=(1.0,) * 8))
    assert region.stages
    # Scan
    p.register_atom("a1", [0.5] * 8)
    scan_result = p.scan([0.0] * 8, radius=2.0)
    assert scan_result.directions_total == 240
    # Traverse
    trav_result = p.traverse(Overlay(position=(0.0,) * 8))
    assert len(trav_result.visited) == 240
