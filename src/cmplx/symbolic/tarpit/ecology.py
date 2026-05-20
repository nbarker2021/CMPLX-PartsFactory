"""
TarpitEcology — the main integration + `symbolic` port provider.

The ecology binds GrainField + BondEngine + WallEmitter + MirrorOperator
+ JotGrainEncoder into one runnable. Programs are strings over the
8-char alphabet `}<>+[]01` (see INTERFACE.md). Each step either
mutates the grain field, attempts a bond, or terminates the program.

`run(program)` returns a `ComputationResult` summarizing the walls,
dusts/triads, digital root, and final mass.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .bond import BondEngine, Dust, Triad
from .grain import GrainField
from .jot import JotGrainEncoder
from .walls import (
    ErrorClass,
    ErrorWall,
    MirrorOperator,
    OutputWall,
    WallEmitter,
)


# Instruction alphabet
_INSTRUCTIONS = frozenset("}<>+[]01")


class ComputationPhase(Enum):
    OBSERVE = "observe"
    REFLECT = "reflect"
    SYNTHESIZE = "synthesize"
    RECURSE = "recurse"


@dataclass
class ComputationResult:
    program: str = ""
    grain_field: Optional[GrainField] = None
    output_walls: list[OutputWall] = field(default_factory=list)
    error_walls: list[ErrorWall] = field(default_factory=list)
    dusts: list[Dust] = field(default_factory=list)
    triads: list[Triad] = field(default_factory=list)
    steps_executed: int = 0
    bonds_formed: int = 0
    mirrors_applied: int = 0
    success: bool = False
    final_digital_root: int = 0
    final_mass: float = 0.0

    def to_dict(self) -> dict:
        return {
            "program": self.program,
            "success": self.success,
            "steps": self.steps_executed,
            "bonds": self.bonds_formed,
            "mirrors": self.mirrors_applied,
            "output_walls": len(self.output_walls),
            "error_walls": len(self.error_walls),
            "dusts": len(self.dusts),
            "triads": len(self.triads),
            "digital_root": self.final_digital_root,
            "final_mass": self.final_mass,
        }


class TarpitEcology:
    """The TarPit ecology — register on `symbolic`."""

    name: str = "tarpit_ecology"

    def __init__(
        self,
        dimension: int = 8,
        layer: int = 0,
        max_steps: int = 10_000,
        epsilon: float = 0.1,
        seed: Optional[int] = None,
    ) -> None:
        self.dimension = dimension
        self.layer = layer
        self.max_steps = max_steps
        self.epsilon = epsilon
        self._rng = random.Random(seed)

        self.field = GrainField(dimension=dimension, layer=layer, rng=self._rng)
        self.bond_engine = BondEngine(epsilon=epsilon)
        self.wall_emitter = WallEmitter()
        self.mirror_operator = MirrorOperator()
        self.jot_encoder = JotGrainEncoder(self.bond_engine)

        self.current_phase = ComputationPhase.OBSERVE
        self.step_count = 0
        self.instruction_pointer = 0
        self.program = ""

        self.result = ComputationResult()

    # ── Program lifecycle ─────────────────────────────────────────────

    def load_program(self, program: str) -> None:
        self.program = program
        self.instruction_pointer = 0

    def reset(self) -> None:
        self.field = GrainField(dimension=self.dimension, layer=self.layer, rng=self._rng)
        self.bond_engine = BondEngine(epsilon=self.epsilon)
        self.wall_emitter = WallEmitter()
        self.mirror_operator = MirrorOperator()
        self.jot_encoder = JotGrainEncoder(self.bond_engine)
        self.current_phase = ComputationPhase.OBSERVE
        self.step_count = 0
        self.instruction_pointer = 0
        self.result = ComputationResult()

    # ── Step + dispatch ───────────────────────────────────────────────

    def step(self) -> bool:
        if self.instruction_pointer >= len(self.program):
            return False
        if self.step_count >= self.max_steps:
            self._emit_error(ErrorClass.TIMEOUT, "Maximum steps exceeded")
            return False

        instr = self.program[self.instruction_pointer]
        try:
            if instr == "}":
                self._exec_flip_right()
            elif instr == "<":
                self._exec_move_left()
            elif instr == ">":
                self._exec_move_right()
            elif instr == "+":
                self._exec_flip()
            elif instr == "[":
                self._exec_loop_start()
                self.step_count += 1
                self.field.step_time()
                self._update_phase()
                return True
            elif instr == "]":
                self._exec_loop_end()
                self.step_count += 1
                self.field.step_time()
                self._update_phase()
                return True
            elif instr == "0":
                self.field = self.jot_encoder._execute_apply(self.field, self.step_count)
            elif instr == "1":
                self.field = self.jot_encoder._execute_nest(self.field, self.step_count)
        except Exception as exc:
            self._emit_error(ErrorClass.INVALID_STATE, str(exc))

        self.instruction_pointer += 1
        self.step_count += 1
        self.field.step_time()
        self._update_phase()
        return True

    # ── Individual ops ────────────────────────────────────────────────

    def _exec_flip_right(self) -> None:
        g = self.field.get_current_grain()
        if g is None:
            self.field.create_grain(self.field.pointer, value=1)
        else:
            self.field.set_grain(self.field.pointer, g.flip())
        self.field.move_pointer(1)

    def _exec_move_left(self) -> None:
        self.field.move_pointer(-1)

    def _exec_move_right(self) -> None:
        self.field.move_pointer(1)

    def _exec_flip(self) -> None:
        g = self.field.get_current_grain()
        if g is None:
            self.field.create_grain(self.field.pointer, value=1)
        else:
            self.field.set_grain(self.field.pointer, g.flip())

    def _exec_loop_start(self) -> None:
        g = self.field.get_current_grain()
        if g is None or g.value == 0:
            # Jump past matching ]
            depth = 1
            self.instruction_pointer += 1
            while self.instruction_pointer < len(self.program) and depth > 0:
                c = self.program[self.instruction_pointer]
                if c == "[":
                    depth += 1
                elif c == "]":
                    depth -= 1
                if depth > 0:
                    self.instruction_pointer += 1
            # Land on the matching `]`, then advance past it
            self.instruction_pointer += 1
        else:
            self.instruction_pointer += 1

    def _exec_loop_end(self) -> None:
        g = self.field.get_current_grain()
        if g is not None and g.value == 1:
            # Jump back to matching `[`
            depth = 1
            self.instruction_pointer -= 1
            while self.instruction_pointer >= 0 and depth > 0:
                c = self.program[self.instruction_pointer]
                if c == "]":
                    depth += 1
                elif c == "[":
                    depth -= 1
                if depth > 0:
                    self.instruction_pointer -= 1
            self.instruction_pointer += 1  # land just after `[`
        else:
            self.instruction_pointer += 1

    # ── Phase + error ─────────────────────────────────────────────────

    def _update_phase(self) -> None:
        phases = list(ComputationPhase)
        self.current_phase = phases[(self.step_count // 10) % len(phases)]

    def _emit_error(self, error_class: ErrorClass, message: str) -> None:
        cur = self.field.get_current_grain()
        wall = self.wall_emitter.emit_error(
            error_class=error_class,
            reproducer_grains=[cur] if cur is not None else [],
            violated_invariants=[message],
            context={"step": self.step_count, "pointer": self.field.pointer},
            time=self.step_count,
        )
        self.result.error_walls.append(wall)
        if wall.mirror_candidate:
            self._attempt_mirror(wall)

    def _attempt_mirror(self, error_wall: ErrorWall) -> None:
        grains = self.field.all_grains()
        mirrored = self.mirror_operator.apply_mirror(
            error_wall, grains, time=self.step_count
        )
        if mirrored is not None and mirrored.is_valid_bridge():
            for g in mirrored.counter_grains[:2]:
                self.field.set_grain(self.field.pointer, g)
            self.result.mirrors_applied += 1

    # ── Run + finalize ────────────────────────────────────────────────

    def run(self, program: Optional[str] = None) -> ComputationResult:
        if program is not None:
            self.load_program(program)
        while self.step():
            pass
        self._finalize()
        return self.result

    def _finalize(self) -> None:
        # Collect composites
        dusts = [c for c in self.field.composites if isinstance(c, Dust)]
        triads_from_field = [c for c in self.field.composites if isinstance(c, Triad)]
        # Promote any closure-checked dusts not yet promoted
        promoted: list[Triad] = []
        for d in dusts:
            if self.bond_engine.check_closure(d):
                t = self.bond_engine.promote_to_triad(d)
                if t is not None:
                    promoted.append(t)
        self.result.dusts = dusts
        self.result.triads = list({t.id: t for t in (triads_from_field + promoted)}.values())

        grains = self.field.all_grains()
        residuals = [g.mass for g in grains]
        wall = self.wall_emitter.emit_output(
            grains=grains,
            dusts=self.result.dusts,
            residuals=residuals,
            time=self.step_count,
        )
        self.result.output_walls.append(wall)

        self.result.program = self.program
        self.result.grain_field = self.field
        self.result.steps_executed = self.step_count
        self.result.bonds_formed = len(self.bond_engine.bond_history)
        self.result.success = len(self.result.error_walls) == 0
        self.result.final_digital_root = self.field.compute_digital_root()
        self.result.final_mass = (
            sum(g.mass for g in grains) / len(grains) if grains else 0.0
        )

    # ── Evolution ─────────────────────────────────────────────────────

    def evolve(self, iterations: int = 10,
               mutation_rate: float = 0.1) -> list[ComputationResult]:
        results: list[ComputationResult] = []
        current = self.program
        for i in range(iterations):
            if i > 0 and self._rng.random() < mutation_rate:
                current = self._mutate_program(current)
            self.reset()
            r = self.run(current)
            results.append(r)
            if r.final_mass > 0.5 and r.success:
                current = r.program
        return results

    def _mutate_program(self, program: str) -> str:
        ops = "}<>+[]01"
        if not program:
            return "0"
        kind = self._rng.choice(("insert", "delete", "substitute"))
        if kind == "insert":
            pos = self._rng.randint(0, len(program))
            ch = self._rng.choice(ops)
            return program[:pos] + ch + program[pos:]
        if kind == "delete" and len(program) > 1:
            pos = self._rng.randint(0, len(program) - 1)
            return program[:pos] + program[pos + 1:]
        pos = self._rng.randint(0, len(program) - 1)
        ch = self._rng.choice(ops)
        return program[:pos] + ch + program[pos + 1:]

    # ── Reporting ─────────────────────────────────────────────────────

    def get_statistics(self) -> dict:
        return {
            "dimension": self.dimension,
            "layer": self.layer,
            "steps": self.step_count,
            "phase": self.current_phase.value,
            "digital_root": self.field.compute_digital_root(),
            "field_entropy": self.field.compute_field_entropy(),
            "grains": sum(len(g) for g in self.field.grains.values()),
            "bonds": len(self.bond_engine.bond_history),
            "wall_stats": self.wall_emitter.get_wall_statistics(),
            "mirror_history": len(self.mirror_operator.mirror_history),
        }

    def infer_emergent_lattice(self) -> dict:
        stats = self.bond_engine.get_bond_statistics()
        demand = stats.get("avg_dimensional_demand", 0.0)
        if demand > 1.8:
            lattice = "2D_Grid"
        elif demand > 1.3:
            lattice = "1D_Chain_with_Orthogonality"
        else:
            lattice = "1D_Linear"
        return {
            "inferred_lattice": lattice,
            "bond_stats": stats,
            "digital_root": self.field.compute_digital_root(),
            "mass_distribution": "high" if stats.get("avg_mass", 0.0) > 0.5 else "low",
        }

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": "tarpit_ecology",
            "dimension": self.dimension,
            "layer": self.layer,
            "grains": sum(len(g) for g in self.field.grains.values()),
            "bonds": len(self.bond_engine.bond_history),
            "triads": len(self.bond_engine.triad_history),
            "walls": self.wall_emitter.wall_counter,
        }

    def __repr__(self) -> str:
        return (
            f"<TarpitEcology dim={self.dimension} layer={self.layer} "
            f"steps={self.step_count}>"
        )
