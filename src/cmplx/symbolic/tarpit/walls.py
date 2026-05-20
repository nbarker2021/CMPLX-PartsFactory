"""
Two wall languages — OutputWall, ErrorWall — plus MirrorOperator
and WallEmitter.

Adapted from `evolving_tarpit/walls.py`. Same surface, pure-stdlib
math (vectors as tuples).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from . import _math as _m
from .bond import Dust
from .grain import DimensionalExtent, Grain


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WallType(Enum):
    OUTPUT = "output"
    ERROR = "error"


class ErrorClass(Enum):
    CAPACITY_EXCEEDED = "capacity_exceeded"
    INVARIANT_VIOLATION = "invariant_violation"
    BOND_FAILURE = "bond_failure"
    MIRROR_REQUIRED = "mirror_required"
    TIMEOUT = "timeout"
    INVALID_STATE = "invalid_state"


# ---------------------------------------------------------------------------
# OutputWall — (X, ⟨d₁…dₖ⟩, R_open, cert)
# ---------------------------------------------------------------------------

@dataclass
class OutputWall:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    closure_count: int = 0
    residual_digits: list[int] = field(default_factory=list)
    residual_set: list[Any] = field(default_factory=list)
    certificates: dict[str, Any] = field(default_factory=dict)
    grains: list[Grain] = field(default_factory=list)
    dusts: list[Dust] = field(default_factory=list)
    emission_time: int = 0

    def __post_init__(self) -> None:
        self.residual_digits = [d % 10 for d in self.residual_digits]

    def serialize(self) -> str:
        """X.d₁d₂…dₖ — coded report, not a float."""
        digits_str = "".join(str(d) for d in self.residual_digits)
        return f"{self.closure_count}.{digits_str}"

    def compute_mass_score(self) -> float:
        """Lower residual = higher quality. Returns score in [0, 1]."""
        if not self.residual_digits:
            return 1.0
        weights = [10 ** (-i) for i in range(len(self.residual_digits))]
        weighted = sum(d * w for d, w in zip(self.residual_digits, weights))
        max_w = sum(9 * w for w in weights)
        return 1.0 - (weighted / max_w if max_w > 0 else 0.0)

    def __repr__(self) -> str:
        return f"OutputWall({self.id}: {self.serialize()})"


# ---------------------------------------------------------------------------
# ErrorWall — (class, stack_sig, G*, ΔI, actions, obligations)
# ---------------------------------------------------------------------------

@dataclass
class ErrorWall:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    error_class: ErrorClass = ErrorClass.INVALID_STATE
    stack_signature: str = ""
    reproducer_grains: list[Grain] = field(default_factory=list)
    violated_invariants: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    witness_obligations: list[str] = field(default_factory=list)
    mirror_candidate: bool = False
    emission_time: int = 0
    context: dict[str, Any] = field(default_factory=dict)

    def compute_signature_hash(self) -> int:
        content = f"{self.error_class.value}:{self.stack_signature}"
        return hash(content) % (2 ** 32)

    def __repr__(self) -> str:
        return f"ErrorWall({self.id}: {self.error_class.value})"


# ---------------------------------------------------------------------------
# MirroredState + MirrorOperator
# ---------------------------------------------------------------------------

@dataclass
class MirroredState:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    source_error: Optional[ErrorWall] = None
    mirror_type: str = ""
    counter_grains: list[Grain] = field(default_factory=list)
    new_mediator: Optional[Grain] = None
    certificates: dict[str, Any] = field(default_factory=dict)
    creation_time: int = 0

    def is_valid_bridge(self) -> bool:
        return (
            len(self.counter_grains) > 0
            and self.new_mediator is not None
            and bool(self.certificates.get("stability_check"))
        )


class MirrorOperator:
    """Mirror bundle: pole inversion, constraint dualization,
    chamber reflection."""

    def __init__(self) -> None:
        self.mirror_history: list[MirroredState] = []

    def pole_inversion(self, grains: list[Grain]) -> list[Grain]:
        out: list[Grain] = []
        for g in grains:
            new_extent = g.extent.with_vector(_m.neg(g.extent.vector))
            out.append(Grain(
                value=g.value,
                extent=new_extent,
                parent_ids=[g.id],
                certificates={"pole_inversion": True},
            ))
        return out

    @staticmethod
    def constraint_dualization(constraints: list[str]) -> list[str]:
        dual: list[str] = []
        for c in constraints:
            lc = c.lower()
            if "<=" in c:
                dual.append(c.replace("<=", ">="))
            elif ">=" in c:
                dual.append(c.replace(">=", "<="))
            elif "max" in lc:
                dual.append(lc.replace("max", "min"))
            elif "min" in lc:
                dual.append(lc.replace("min", "max"))
            else:
                dual.append(f"NOT({c})")
        return dual

    def chamber_reflection(self, grain: Grain,
                           boundary_normal) -> Grain:
        reflected = _m.reflect(grain.extent.vector, boundary_normal)
        new_extent = grain.extent.with_vector(reflected)
        return Grain(
            value=grain.value,
            extent=new_extent,
            parent_ids=[grain.id],
            certificates={
                "chamber_reflection": True,
                "boundary_normal": list(boundary_normal),
            },
        )

    def apply_mirror(self, error_wall: ErrorWall,
                     grains: list[Grain],
                     time: int = 0) -> Optional[MirroredState]:
        if not grains:
            return None
        inverted = self.pole_inversion(grains)
        duals = self.constraint_dualization(error_wall.violated_invariants)

        new_mediator: Optional[Grain] = None
        if inverted:
            avg = _m.mean([g.extent.vector for g in inverted])
            med_extent = inverted[0].extent.with_vector(avg)
            new_mediator = Grain(
                value=grains[0].value if grains else 0,
                extent=med_extent,
                certificates={
                    "mirrored_mediator": True,
                    "dual_constraints": duals,
                },
            )

        state = MirroredState(
            source_error=error_wall,
            mirror_type="full_bundle",
            counter_grains=inverted,
            new_mediator=new_mediator,
            certificates={
                "pole_inversion": True,
                "constraint_dualization": duals,
                "stability_check": True,
            },
            creation_time=time,
        )
        self.mirror_history.append(state)
        return state

    @staticmethod
    def can_bridge_back(mirrored: MirroredState, _original_state: Any = None) -> bool:
        return mirrored.is_valid_bridge()


# ---------------------------------------------------------------------------
# WallEmitter — solver emits walls; ecology interprets them
# ---------------------------------------------------------------------------

class WallEmitter:
    def __init__(self) -> None:
        self.output_walls: list[OutputWall] = []
        self.error_walls: list[ErrorWall] = []
        self.wall_counter: int = 0

    def emit_output(self, grains: list[Grain], dusts: list[Dust],
                    residuals: list[Any], time: int = 0) -> OutputWall:
        digits: list[int] = []
        for r in residuals[:5]:
            if isinstance(r, (int, float)):
                digits.append(int(r * 10) % 10)
        while len(digits) < 3:
            digits.append(0)
        wall = OutputWall(
            closure_count=len(dusts),
            residual_digits=digits,
            residual_set=list(residuals),
            grains=list(grains),
            dusts=list(dusts),
            emission_time=time,
            certificates={
                "wall_number": self.wall_counter,
                "grain_count": len(grains),
                "dust_count": len(dusts),
            },
        )
        self.output_walls.append(wall)
        self.wall_counter += 1
        return wall

    def emit_error(self, error_class: ErrorClass,
                   reproducer_grains: list[Grain],
                   violated_invariants: list[str],
                   context: dict[str, Any],
                   time: int = 0) -> ErrorWall:
        stack_sig = (
            f"{error_class.value}_{len(reproducer_grains)}_{len(violated_invariants)}"
        )
        suggested: list[str] = []
        mirror = False
        if error_class == ErrorClass.CAPACITY_EXCEEDED:
            suggested = ["spawn_higher_support", "promote_to_next_layer"]
            mirror = True
        elif error_class == ErrorClass.INVARIANT_VIOLATION:
            suggested = ["relax_constraints", "mirror_chamber"]
            mirror = True
        elif error_class == ErrorClass.BOND_FAILURE:
            suggested = ["retry_bond", "alternate_mediator"]
        elif error_class == ErrorClass.MIRROR_REQUIRED:
            suggested = ["mirror_chamber"]
            mirror = True
        else:
            suggested = ["inspect_grains", "reset_field"]

        wall = ErrorWall(
            error_class=error_class,
            stack_signature=stack_sig,
            reproducer_grains=list(reproducer_grains),
            violated_invariants=list(violated_invariants),
            suggested_actions=suggested,
            mirror_candidate=mirror,
            emission_time=time,
            context=dict(context),
        )
        self.error_walls.append(wall)
        self.wall_counter += 1
        return wall

    def get_wall_statistics(self) -> dict:
        avg = 0.0
        if self.output_walls:
            avg = sum(w.compute_mass_score() for w in self.output_walls) / len(self.output_walls)
        return {
            "total_walls": self.wall_counter,
            "output_walls": len(self.output_walls),
            "error_walls": len(self.error_walls),
            "avg_output_mass": avg,
            "mirror_candidates": sum(1 for w in self.error_walls if w.mirror_candidate),
        }
