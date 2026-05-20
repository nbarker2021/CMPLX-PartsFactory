"""
Tests for cmplx.symbolic.tarpit — the Morphonic Ribbon Ecology.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from cmplx.symbolic.tarpit import (
    BondEngine,
    ComputationPhase,
    ComputationResult,
    DimensionalExtent,
    Dust,
    ErrorClass,
    ErrorWall,
    Grain,
    GrainField,
    GrainType,
    JotGrainEncoder,
    MirroredState,
    MirrorOperator,
    OutputWall,
    Ribbon,
    SKCombinator,
    TarpitEcology,
    Triad,
    WallEmitter,
)


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# DimensionalExtent
# ---------------------------------------------------------------------------

def test_extent_norm_zero():
    ext = DimensionalExtent(vector=(0.0,) * 8)
    assert ext.norm == 0.0
    assert ext.mass_1d == 0.0


def test_extent_mass_clipped_below_one():
    ext = DimensionalExtent(vector=(10.0,) * 8, L_max=1.0)
    assert ext.mass_1d < 1.0


def test_extent_parallelogram_area_orthogonal():
    a = DimensionalExtent(vector=(1.0, 0.0))
    b = DimensionalExtent(vector=(0.0, 1.0))
    assert a.parallelogram_area(b) == pytest.approx(1.0)


def test_extent_is_materially_2d_orthogonal():
    a = DimensionalExtent(vector=(1.0, 0.0))
    b = DimensionalExtent(vector=(0.0, 1.0))
    assert a.is_materially_2d(b)


def test_extent_is_not_2d_when_parallel():
    a = DimensionalExtent(vector=(1.0, 0.0))
    b = DimensionalExtent(vector=(2.0, 0.0))
    assert not a.is_materially_2d(b)


# ---------------------------------------------------------------------------
# Grain
# ---------------------------------------------------------------------------

def test_grain_default_value_is_bit():
    g = Grain(value=3)
    assert g.value == 1  # masked to single bit


def test_grain_flip_inverts_value_and_extends_lineage():
    g = Grain(value=0)
    f = g.flip()
    assert f.value == 1
    assert g.id in f.parent_ids


def test_grain_can_bond_with_2d():
    a = Grain(extent=DimensionalExtent(vector=(1.0, 0.0)))
    b = Grain(extent=DimensionalExtent(vector=(0.0, 1.0)))
    ok, mass = a.can_bond_with(b)
    assert ok is True
    assert mass >= 0


def test_grain_compute_hash_stable_across_calls():
    g = Grain()
    assert g.compute_hash() == g.compute_hash()


def test_grain_to_ribbon():
    g = Grain(value=1, extent=DimensionalExtent(vector=(1.0, 2.0)))
    r = g.to_ribbon()
    assert isinstance(r, Ribbon)
    assert r.value == 1
    assert r.end == (1.0, 2.0)


# ---------------------------------------------------------------------------
# GrainField
# ---------------------------------------------------------------------------

def test_field_create_and_get_grain():
    f = GrainField(dimension=8)
    g = f.create_grain(0, value=1)
    assert f.get_primary_grain(0) is g
    assert g.position == 0


def test_field_flip_current_creates_if_empty():
    f = GrainField()
    g = f.flip_current()
    assert g.value == 1
    # GrainField supports superposition (multiple grains per position),
    # so `g` is one of the grains at position 0, not necessarily primary.
    assert g in f.get_grains(0)


def test_field_pointer_movement():
    f = GrainField()
    f.move_pointer(3)
    assert f.pointer == 3
    f.move_pointer(-1)
    assert f.pointer == 2


def test_field_digital_root_range():
    f = GrainField()
    for _ in range(15):
        f.create_grain(0, value=1)
    dr = f.compute_digital_root()
    assert 0 <= dr <= 9


def test_field_observation_keys():
    f = GrainField(dimension=8, layer=2)
    obs = f.get_observation()
    for k in ("dimension", "layer", "time", "pointer", "total_grains",
              "digital_root", "L_max", "A_max", "V_max"):
        assert k in obs


# ---------------------------------------------------------------------------
# BondEngine
# ---------------------------------------------------------------------------

def test_bond_engine_creates_dust():
    eng = BondEngine()
    a = Grain(extent=DimensionalExtent(vector=(1.0, 0.0)))
    b = Grain(extent=DimensionalExtent(vector=(0.0, 1.0)))
    dust = eng.attempt_bond(a, b)
    assert isinstance(dust, Dust)
    assert dust.pole_a is a
    assert dust.pole_b is b
    assert dust.mediator is not None
    assert eng.bond_history == [dust]


def test_bond_engine_promotes_to_triad_when_closure():
    eng = BondEngine(epsilon=0.01)
    a = Grain(extent=DimensionalExtent(vector=(1.0, 0.0)))
    b = Grain(extent=DimensionalExtent(vector=(0.0, 1.0)))
    dust = eng.attempt_bond(a, b)
    triad = eng.promote_to_triad(dust)
    assert triad is not None
    assert len(triad.grains) == 3
    for g in triad.grains:
        assert any(t.startswith("triad:") for t in g.tags)


def test_bond_engine_statistics():
    eng = BondEngine()
    a = Grain(extent=DimensionalExtent(vector=(1.0, 0.0)))
    b = Grain(extent=DimensionalExtent(vector=(0.0, 1.0)))
    eng.attempt_bond(a, b)
    stats = eng.get_bond_statistics()
    assert stats["total_bonds"] == 1
    assert stats["avg_dimensional_demand"] > 0


# ---------------------------------------------------------------------------
# Walls
# ---------------------------------------------------------------------------

def test_output_wall_serializes_as_X_dot_digits():
    w = OutputWall(closure_count=3, residual_digits=[1, 2, 3])
    assert w.serialize() == "3.123"


def test_output_wall_mass_score_in_range():
    w = OutputWall(closure_count=0, residual_digits=[0, 0, 0])
    assert w.compute_mass_score() == 1.0
    w2 = OutputWall(closure_count=0, residual_digits=[9, 9, 9])
    assert w2.compute_mass_score() < 0.5


def test_error_wall_signature_hash_stable():
    w = ErrorWall(error_class=ErrorClass.BOND_FAILURE, stack_signature="abc")
    assert w.compute_signature_hash() == w.compute_signature_hash()


def test_wall_emitter_emits_output():
    emitter = WallEmitter()
    g = Grain(value=1)
    wall = emitter.emit_output(grains=[g], dusts=[], residuals=[0.5])
    assert wall in emitter.output_walls
    assert wall.grains == [g]


def test_wall_emitter_emits_error_with_mirror_for_capacity():
    emitter = WallEmitter()
    wall = emitter.emit_error(
        error_class=ErrorClass.CAPACITY_EXCEEDED,
        reproducer_grains=[], violated_invariants=["test"],
        context={},
    )
    assert wall.mirror_candidate is True


def test_wall_emitter_statistics():
    emitter = WallEmitter()
    emitter.emit_output(grains=[], dusts=[], residuals=[0.1])
    emitter.emit_error(ErrorClass.BOND_FAILURE, [], ["x"], {})
    stats = emitter.get_wall_statistics()
    assert stats["output_walls"] == 1
    assert stats["error_walls"] == 1
    assert stats["total_walls"] == 2


# ---------------------------------------------------------------------------
# MirrorOperator
# ---------------------------------------------------------------------------

def test_mirror_pole_inversion_negates_extent():
    op = MirrorOperator()
    g = Grain(extent=DimensionalExtent(vector=(1.0, 2.0, 3.0)))
    inverted = op.pole_inversion([g])
    assert inverted[0].extent.vector == (-1.0, -2.0, -3.0)
    assert g.id in inverted[0].parent_ids


def test_mirror_constraint_dualization():
    op = MirrorOperator()
    duals = op.constraint_dualization(["x <= 5", "max(y)"])
    assert "x >= 5" in duals
    assert any("min(y)" in d for d in duals)


def test_mirror_chamber_reflection_inverts_along_normal():
    op = MirrorOperator()
    g = Grain(extent=DimensionalExtent(vector=(1.0, 0.0)))
    reflected = op.chamber_reflection(g, boundary_normal=(1.0, 0.0))
    # reflection of (1,0) across hyperplane with normal (1,0) is (-1,0)
    assert reflected.extent.vector[0] == pytest.approx(-1.0)
    assert reflected.extent.vector[1] == pytest.approx(0.0)


def test_mirror_apply_returns_valid_state():
    op = MirrorOperator()
    err = ErrorWall(
        error_class=ErrorClass.CAPACITY_EXCEEDED,
        violated_invariants=["x <= 1"],
    )
    grains = [Grain(extent=DimensionalExtent(vector=(1.0, 0.0)))]
    state = op.apply_mirror(err, grains, time=5)
    assert isinstance(state, MirroredState)
    assert state.is_valid_bridge()


def test_mirror_apply_returns_none_for_empty():
    op = MirrorOperator()
    err = ErrorWall(error_class=ErrorClass.TIMEOUT)
    assert op.apply_mirror(err, [], time=0) is None


# ---------------------------------------------------------------------------
# Jot encoding
# ---------------------------------------------------------------------------

def test_jot_apply_bonds_neighbors():
    eng = BondEngine()
    enc = JotGrainEncoder(eng)
    f = GrainField()
    f.create_grain(0, value=1)
    f.create_grain(1, value=0)
    f = enc._execute_apply(f, step=0)
    assert len(eng.bond_history) == 1
    assert SKCombinator.S in enc.combinator_history


def test_jot_nest_extends_extent():
    eng = BondEngine()
    enc = JotGrainEncoder(eng)
    f = GrainField()
    g = f.create_grain(0, value=1)
    f = enc._execute_nest(f, step=0)
    # A COMBINATOR-typed grain was added at position 0 (it may not be
    # primary because of mass tie-breaking, but it must be present).
    grains_here = f.get_grains(0)
    assert any(gr.grain_type == GrainType.COMBINATOR for gr in grains_here)
    assert g.id in [pid for gr in grains_here for pid in gr.parent_ids]


def test_jot_interpret_bits_runs_program():
    eng = BondEngine()
    enc = JotGrainEncoder(eng)
    f = GrainField()
    f = enc.interpret_bits("0110", f)
    assert len(enc.combinator_history) == 4


# ---------------------------------------------------------------------------
# TarpitEcology — the provider
# ---------------------------------------------------------------------------

def test_ecology_runs_simple_bitchanger_program():
    eco = TarpitEcology(dimension=8, seed=42)
    result = eco.run("}}}")
    assert isinstance(result, ComputationResult)
    assert result.steps_executed == 3
    assert result.success is True


def test_ecology_emits_at_least_one_output_wall():
    eco = TarpitEcology(seed=42)
    result = eco.run("}+}")
    assert len(result.output_walls) >= 1


def test_ecology_loop_terminates():
    eco = TarpitEcology(seed=42, max_steps=200)
    # `[` with empty current grain → jump past `]` → terminate
    result = eco.run("[}}}]")
    assert result.steps_executed <= 200


def test_ecology_jot_program_bonds():
    eco = TarpitEcology(seed=42)
    result = eco.run("01010")
    assert result.bonds_formed >= 1


def test_ecology_reset_clears_state():
    eco = TarpitEcology(seed=42)
    eco.run("}}}")
    assert eco.step_count > 0
    eco.reset()
    assert eco.step_count == 0
    assert eco.result.steps_executed == 0


def test_ecology_timeout_emits_error_wall():
    eco = TarpitEcology(seed=42, max_steps=5)
    # An infinite loop on bit=1
    eco.run("+[]")
    # max_steps=5 will trip TIMEOUT before completion
    timeouts = [
        e for e in eco.result.error_walls
        if e.error_class == ErrorClass.TIMEOUT
    ]
    assert len(timeouts) >= 1


def test_ecology_infer_emergent_lattice_returns_label():
    eco = TarpitEcology(seed=42)
    eco.run("010101")
    inferred = eco.infer_emergent_lattice()
    assert "inferred_lattice" in inferred
    assert inferred["inferred_lattice"] in {
        "1D_Linear", "1D_Chain_with_Orthogonality", "2D_Grid",
    }


def test_ecology_statistics_keys():
    eco = TarpitEcology(seed=42)
    eco.run("}+}")
    stats = eco.get_statistics()
    for k in ("dimension", "steps", "phase", "digital_root", "grains",
              "bonds", "wall_stats"):
        assert k in stats


def test_ecology_evolve_returns_results():
    eco = TarpitEcology(seed=42)
    eco.load_program("}+}")
    results = eco.evolve(iterations=3, mutation_rate=1.0)
    assert len(results) == 3
    for r in results:
        assert isinstance(r, ComputationResult)


def test_ecology_phase_cycles_through_morsr():
    eco = TarpitEcology(seed=42)
    eco.run("}" * 50)
    # After 50 steps the phase should be defined and one of the four
    assert eco.current_phase in set(ComputationPhase)


def test_ecology_registers_on_symbolic_port():
    mc = MorphonController.get()
    eco = TarpitEcology(seed=42)
    mc.register("symbolic", eco)
    assert mc.get_provider("symbolic") is eco


def test_ecology_health_reports():
    eco = TarpitEcology(seed=42)
    eco.run("}+}")
    h = eco.health
    assert h["ok"] is True
    assert h["service"] == "tarpit_ecology"
