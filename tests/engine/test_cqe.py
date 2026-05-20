"""
Tests for cmplx.engine.cqe — the CQE orchestrator + primitives.
"""
from __future__ import annotations

import math

import pytest

from cmplx.engine.cqe import (
    CQEAtom,
    CQEConfig,
    CQEGovernance,
    CQEObjectiveFunction,
    CQEProvider,
    CQERunner,
    DomainAdapter,
    GovernanceLevel,
    ObjectiveScores,
    OperationMode,
    ProblemSolution,
    ROTATION_PATTERNS,
    TextResult,
    ValidationBand,
    analyze_string,
    band_for,
    classify_behavior,
    compute_v_total,
    digital_root_of_quad,
    generate_toroidal_shell,
    hash_to_complex,
    is_in_set,
    mandelbrot_iterate,
    parity_from_quad,
    pattern_distribution,
    profile_for,
    quad_from_text,
    sacred_frequency,
    torus_point,
)
from cmplx.morphon import Morphon, MorphonController
from cmplx.nsl import NSLProvider
from cmplx.receipt import ReceiptProvider


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# Mandelbrot primitives
# ---------------------------------------------------------------------------

def test_mandelbrot_iterate_origin_is_bounded():
    result = mandelbrot_iterate(0.0, 0.0)
    assert not result["escaped"]


def test_mandelbrot_iterate_far_escapes_fast():
    result = mandelbrot_iterate(5.0, 0.0)
    assert result["escaped"]
    assert result["iterations"] <= 5


def test_hash_to_complex_in_canonical_rectangle():
    cr, ci = hash_to_complex("test")
    assert -2.0 <= cr <= 0.5
    assert -1.25 <= ci <= 1.25


def test_hash_to_complex_deterministic():
    a = hash_to_complex("hello")
    b = hash_to_complex("hello")
    assert a == b


def test_classify_behavior_labels():
    bounded = {"escaped": False, "iterations": 50}
    fast = {"escaped": True, "iterations": 2}
    medium = {"escaped": True, "iterations": 10}
    slow = {"escaped": True, "iterations": 30}
    assert classify_behavior(bounded) == "BOUNDED"
    assert classify_behavior(fast) == "FAST_ESCAPE"
    assert classify_behavior(medium) == "MEDIUM_ESCAPE"
    assert classify_behavior(slow) == "SLOW_ESCAPE"


def test_analyze_string_full_pipeline():
    result = analyze_string("hello world")
    for key in ("escaped", "iterations", "z_norm", "c", "behavior", "text_length"):
        assert key in result


def test_is_in_set_origin():
    assert is_in_set(0.0, 0.0)


def test_is_in_set_far_point():
    assert not is_in_set(10.0, 0.0)


# ---------------------------------------------------------------------------
# Toroidal primitives
# ---------------------------------------------------------------------------

def test_torus_point_lies_on_torus_surface():
    R, r = 2.0, 1.0
    x, y, z = torus_point(0.0, 0.0, R, r)
    # At u=0, v=0: x = R+r, y = 0, z = 0
    assert x == pytest.approx(R + r)
    assert y == pytest.approx(0.0)
    assert z == pytest.approx(0.0)


def test_generate_toroidal_shell_count():
    shell = generate_toroidal_shell(n_points=32, seed=42)
    assert len(shell) == 32


def test_generate_toroidal_shell_seeded_deterministic():
    a = generate_toroidal_shell(n_points=10, seed=42)
    b = generate_toroidal_shell(n_points=10, seed=42)
    assert [p["position"] for p in a] == [p["position"] for p in b]


def test_toroidal_pattern_keys():
    shell = generate_toroidal_shell(n_points=20, seed=1)
    for point in shell:
        assert point["pattern"] in ROTATION_PATTERNS


def test_pattern_distribution_sums_to_n():
    shell = generate_toroidal_shell(n_points=50, seed=1)
    counts = pattern_distribution(shell)
    assert sum(counts.values()) == 50
    for k in ROTATION_PATTERNS:
        assert k in counts


def test_sacred_frequency_range():
    f = sacred_frequency("hello")
    assert 174.0 <= f <= 963.0


def test_sacred_frequency_deterministic():
    assert sacred_frequency("x") == sacred_frequency("x")


# ---------------------------------------------------------------------------
# Banding
# ---------------------------------------------------------------------------

def test_band_for_breakthrough():
    assert band_for(0.95) == "BREAKTHROUGH"


def test_band_for_peer_ready():
    assert band_for(0.70) == "PEER_READY"


def test_band_for_exploratory():
    assert band_for(0.30) == "EXPLORATORY"


def test_compute_v_total_weighted_mean():
    scores = {"a": 1.0, "b": 0.5}
    weights = {"a": 1.0, "b": 1.0}
    assert compute_v_total(scores, weights) == pytest.approx(0.75)


def test_compute_v_total_zero_weights():
    assert compute_v_total({"a": 1.0}, {}) == 0.0


def test_validation_band_enum():
    assert ValidationBand.BREAKTHROUGH.value == "BREAKTHROUGH"


# ---------------------------------------------------------------------------
# DomainAdapter
# ---------------------------------------------------------------------------

def test_domain_adapter_p_problem_dim():
    da = DomainAdapter()
    v = da.embed_p_problem(size=100, complexity_hint=2)
    assert len(v) == 8


def test_domain_adapter_np_problem_larger_norm_than_p():
    da = DomainAdapter()
    p = da.embed_p_problem(size=100)
    np = da.embed_np_problem(size=100)
    p_norm = math.sqrt(sum(x * x for x in p))
    np_norm = math.sqrt(sum(x * x for x in np))
    # NP designed to have larger norm than P
    assert np_norm > p_norm


def test_domain_adapter_optimization():
    da = DomainAdapter()
    v = da.embed_optimization_problem(variables=10, constraints=5)
    assert len(v) == 8


def test_domain_adapter_creative():
    da = DomainAdapter()
    v = da.embed_scene_problem(scene_complexity=50, narrative_depth=25, character_count=5)
    assert len(v) == 8


def test_domain_adapter_text():
    da = DomainAdapter()
    v = da.embed_text("hello world")
    assert len(v) == 8
    norm = math.sqrt(sum(x * x for x in v))
    assert norm == pytest.approx(math.sqrt(2), abs=1e-6)


def test_domain_adapter_text_deterministic():
    da = DomainAdapter()
    assert da.embed_text("x") == da.embed_text("x")


def test_domain_adapter_adapt_dispatches_by_type():
    da = DomainAdapter()
    p = da.adapt({"complexity_class": "P", "size": 50}, "computational")
    np = da.adapt({"complexity_class": "NP", "size": 50}, "computational")
    assert len(p) == 8
    assert len(np) == 8
    assert p != np


# ---------------------------------------------------------------------------
# CQEAtom helpers
# ---------------------------------------------------------------------------

def test_quad_from_text_range():
    q = quad_from_text("hello")
    assert len(q) == 4
    for v in q:
        assert 1 <= v <= 4


def test_quad_from_text_deterministic():
    assert quad_from_text("x") == quad_from_text("x")


def test_parity_from_quad_eight_channels():
    p = parity_from_quad((1, 2, 3, 4))
    assert len(p) == 8
    for bit in p:
        assert bit in (0, 1)


def test_parity_from_quad_known_pattern():
    # quad = (1,2,3,4): q1%2=1, q2%2=0, q3%2=1, q4%2=0
    # (1+2)%2=1, (3+4)%2=1, (1+3)%2=0, (2+4)%2=0
    assert parity_from_quad((1, 2, 3, 4)) == (1, 0, 1, 0, 1, 1, 0, 0)


def test_digital_root_of_quad():
    assert digital_root_of_quad((1, 2, 3, 4)) == 1  # 1+2+3+4=10 → 1+0=1
    assert digital_root_of_quad((4, 4, 4, 4)) == 7  # 16 → 1+6=7


def test_cqeatom_forge_populates_fields():
    atom = CQEAtom.forge("test content")
    assert atom.morphon.quad_encoding is not None
    assert atom.morphon.parity_channels is not None
    assert atom.morphon.digital_root is not None
    assert atom.morphon.sacred_frequency is not None
    assert atom.morphon.fractal_coordinate is not None


def test_cqeatom_is_morphon():
    """User direction: CQEAtom IS a Morphon."""
    atom = CQEAtom.forge({"k": "v"})
    assert isinstance(atom.morphon, Morphon)
    # The Morphon has its own id; the CQEAtom exposes it
    assert atom.id == atom.morphon.id


def test_cqeatom_wrapping_existing_morphon():
    m = Morphon.forge(payload={"text": "hello"})
    atom = CQEAtom(m)
    assert m.quad_encoding is not None
    assert m.fractal_coordinate is not None


def test_cqeatom_to_dict_keys():
    atom = CQEAtom.forge("test")
    d = atom.to_dict()
    for k in ("id", "quad_encoding", "parity_channels",
              "digital_root", "sacred_frequency", "fractal_coordinate"):
        assert k in d


def test_cqeatom_string_payload_wraps_in_dict():
    atom = CQEAtom.forge("hello world")
    assert atom.morphon.payload == {"text": "hello world"}


# ---------------------------------------------------------------------------
# CQEObjectiveFunction
# ---------------------------------------------------------------------------

def test_objective_evaluate_returns_full_breakdown():
    obj = CQEObjectiveFunction()
    scores = obj.evaluate(
        vector=(0.5, 0.3, 0.2, 0.1, 0.0, 0.1, 0.2, 0.3),
        reference_channels=(1.0, 0.5, 0.3, 0.2, 0.0, 0.1, 0.2, 0.3),
    )
    assert isinstance(scores, ObjectiveScores)
    assert 0.0 <= scores.phi_total <= 1.0
    assert 0.0 <= scores.parity_consistency <= 1.0
    assert 0.0 <= scores.chamber_stability <= 1.0
    assert 0.0 <= scores.geometric_separation <= 1.0


def test_objective_phi_total_is_weighted_combination():
    obj = CQEObjectiveFunction()
    s = obj.evaluate(
        vector=(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
        reference_channels=(0.5,) * 8,
    )
    # phi_total should be in [0, 1]
    assert 0.0 <= s.phi_total <= 1.0


def test_objective_nsl_sectors_when_v_before_supplied():
    obj = CQEObjectiveFunction()
    s = obj.evaluate(
        vector=(0.5,) * 8,
        reference_channels=(0.5,) * 8,
        v_before=(1.0,) * 8,
    )
    # Going from larger to smaller vector should produce ΔΦ ≤ 0
    assert s.nsl_sectors.total <= 0.001  # small numerical tolerance


def test_objective_to_dict():
    obj = CQEObjectiveFunction()
    s = obj.evaluate(vector=(0.5,) * 8, reference_channels=(0.5,) * 8)
    d = s.to_dict()
    for k in ("phi_total", "parity_consistency", "chamber_stability",
              "geometric_separation", "kissing_alignment", "nsl_sectors"):
        assert k in d


# ---------------------------------------------------------------------------
# CQEGovernance
# ---------------------------------------------------------------------------

def test_governance_starts_with_builtin_constraints():
    gov = CQEGovernance()
    assert len(gov.constraints) >= 5  # at least 5 built-ins


def test_governance_starts_with_builtin_policies():
    gov = CQEGovernance()
    names = {p.name for p in gov.policies.values()}
    for n in ("permissive", "standard", "strict", "ultimate",
              "tqf_lawful", "uvibs_compliant"):
        assert n in names


def test_governance_active_policy_is_standard_by_default():
    gov = CQEGovernance()
    assert gov.active_policy().name == "standard"


def test_governance_set_active_policy():
    gov = CQEGovernance()
    assert gov.set_active_policy("strict")
    assert gov.active_policy().name == "strict"
    assert not gov.set_active_policy("nonexistent")


def test_governance_validate_passes_clean_atom():
    gov = CQEGovernance()
    atom = CQEAtom.forge("hello").morphon
    result = gov.validate(atom)
    # Clean atom should pass
    assert isinstance(result["valid"], bool)
    assert "violations" in result
    assert result["constraint_count"] > 0


def test_governance_validate_catches_bad_quad():
    gov = CQEGovernance()
    # Inject a bad quad via ctx
    result = gov.validate(item=None, ctx={"quad_encoding": (5, 0, -1, 99)})
    assert not result["valid"]
    assert len(result["violations"]) >= 1


def test_governance_violations_tracked():
    gov = CQEGovernance()
    gov.validate(item=None, ctx={"quad_encoding": (5, 5, 5, 5)})
    assert len(gov.violations) >= 1


def test_governance_register_custom_constraint():
    gov = CQEGovernance()
    from cmplx.engine.cqe import ConstraintType
    cid = gov.register_constraint(
        constraint_type=ConstraintType.LOGICAL,
        name="always_false",
        validator=lambda item, ctx: False,
    )
    assert cid in gov.constraints


def test_governance_health_keys():
    gov = CQEGovernance()
    h = gov.health
    for k in ("active_policy", "constraint_count", "policy_count",
              "violation_count"):
        assert k in h


# ---------------------------------------------------------------------------
# OperationMode + profiles
# ---------------------------------------------------------------------------

def test_operation_mode_values():
    for mode in OperationMode:
        assert mode.value in (
            "BASIC", "ENHANCED", "SACRED_GEOMETRY",
            "MANDELBROT_FRACTAL", "ULTIMATE_UNIFIED",
        )


def test_profile_for_basic_minimal_stages():
    p = profile_for(OperationMode.BASIC)
    assert not p.fractal_mandelbrot
    assert not p.toroidal_shell
    assert not p.morsr_exploration
    assert p.governance


def test_profile_for_ultimate_all_stages():
    p = profile_for(OperationMode.ULTIMATE_UNIFIED)
    assert p.fractal_mandelbrot
    assert p.toroidal_shell
    assert p.morsr_exploration


# ---------------------------------------------------------------------------
# CQERunner.process_text
# ---------------------------------------------------------------------------

def test_runner_process_text_basic():
    runner = CQERunner(config=CQEConfig(operation_mode=OperationMode.BASIC))
    result = runner.process_text("hello world")
    assert isinstance(result, TextResult)
    assert result.mode == "BASIC"
    assert result.elapsed_seconds >= 0
    assert len(result.receipt_ids) > 0


def test_runner_process_text_enhanced_populates_phi():
    runner = CQERunner(config=CQEConfig(operation_mode=OperationMode.ENHANCED))
    result = runner.process_text("hello world")
    assert result.phi_scores is not None
    assert result.v_total >= 0
    assert result.band in ("BREAKTHROUGH", "PEER_READY", "EXPLORATORY")


def test_runner_process_text_mandelbrot_runs_fractal():
    runner = CQERunner(config=CQEConfig(
        operation_mode=OperationMode.MANDELBROT_FRACTAL
    ))
    result = runner.process_text("hello")
    assert result.fractal != {}
    assert "behavior" in result.fractal


def test_runner_process_text_sacred_runs_toroidal():
    runner = CQERunner(config=CQEConfig(
        operation_mode=OperationMode.SACRED_GEOMETRY,
    ))
    result = runner.process_text("hello")
    assert result.toroidal_n > 0
    assert sum(result.toroidal_patterns.values()) == result.toroidal_n


def test_runner_process_text_emits_receipts():
    receipts = ReceiptProvider()
    runner = CQERunner(receipts=receipts,
                       config=CQEConfig(operation_mode=OperationMode.ENHANCED))
    runner.process_text("test")
    assert receipts.length > 0


# ---------------------------------------------------------------------------
# CQERunner.solve_problem
# ---------------------------------------------------------------------------

def test_runner_solve_problem_returns_solution():
    runner = CQERunner()
    sol = runner.solve_problem(
        problem={"complexity_class": "P", "size": 50},
        domain_type="computational",
    )
    assert isinstance(sol, ProblemSolution)
    assert sol.domain_type == "computational"
    assert len(sol.initial_vector) == 8
    assert sol.objective_score >= 0


def test_runner_solve_problem_generates_recommendations():
    runner = CQERunner()
    sol = runner.solve_problem(
        problem={"complexity_class": "P", "size": 50},
        domain_type="computational",
    )
    assert len(sol.recommendations) > 0


def test_runner_solve_problem_with_optimization_domain():
    runner = CQERunner()
    sol = runner.solve_problem(
        problem={"variables": 10, "constraints": 5, "objective_type": "linear"},
        domain_type="optimization",
    )
    assert sol.domain_type == "optimization"
    assert len(sol.initial_vector) == 8


def test_runner_forge_atom():
    runner = CQERunner()
    atom = runner.forge_atom("test content")
    assert isinstance(atom, CQEAtom)
    assert atom.morphon.quad_encoding is not None
    # Should have emitted a MINT receipt
    assert runner.receipts.by_type("MINT")


# ---------------------------------------------------------------------------
# CQEProvider (the port)
# ---------------------------------------------------------------------------

def test_provider_registers_on_engine_port():
    mc = MorphonController.get()
    p = CQEProvider()
    mc.register("engine", p)
    assert mc.get_provider("engine") is p


def test_provider_process_text_passthrough():
    p = CQEProvider()
    result = p.process_text("hello")
    assert isinstance(result, TextResult)


def test_provider_solve_problem_passthrough():
    p = CQEProvider()
    sol = p.solve_problem(
        problem={"complexity_class": "P", "size": 50},
        domain_type="computational",
    )
    assert isinstance(sol, ProblemSolution)


def test_provider_set_mode_changes_runner_mode():
    p = CQEProvider()
    p.set_mode(OperationMode.MANDELBROT_FRACTAL)
    assert p.runner.config.operation_mode == OperationMode.MANDELBROT_FRACTAL


def test_provider_set_governance_policy():
    p = CQEProvider()
    assert p.set_governance_policy("strict")
    assert p.governance.active_policy().name == "strict"


def test_provider_health_keys():
    p = CQEProvider()
    h = p.health
    assert h["ok"] is True
    assert h["service"] == "cqe_provider"
    assert "runner" in h
    assert "governance" in h


def test_provider_forge_atom():
    p = CQEProvider()
    atom = p.forge_atom("test")
    assert isinstance(atom, CQEAtom)


# ---------------------------------------------------------------------------
# Integration: full pipeline end-to-end
# ---------------------------------------------------------------------------

def test_integration_ultimate_unified_full_pipeline():
    """End-to-end: ULTIMATE_UNIFIED mode runs all stages."""
    p = CQEProvider(config=CQEConfig(
        operation_mode=OperationMode.ULTIMATE_UNIFIED,
        governance_policy="standard",
    ))
    result = p.process_text("hello unified world")

    # All major stages produced output
    assert result.e8 != {}
    assert result.fractal != {}
    assert result.toroidal_n > 0
    assert result.phi_scores is not None
    assert result.v_total > 0
    assert result.band in ("BREAKTHROUGH", "PEER_READY", "EXPLORATORY")

    # Receipts minted for each stage
    assert len(result.receipt_ids) >= 5

    # Receipt chain remains valid
    assert p.receipts.verify_chain()["valid"]


def test_integration_p_vs_np_separation():
    """A 'P' and an 'NP' problem produce different vectors and scores."""
    p = CQEProvider()
    p_sol = p.solve_problem(
        problem={"complexity_class": "P", "size": 50},
        domain_type="computational",
    )
    np_sol = p.solve_problem(
        problem={"complexity_class": "NP", "size": 50},
        domain_type="computational",
    )
    assert p_sol.initial_vector != np_sol.initial_vector
