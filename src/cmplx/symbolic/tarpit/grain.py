"""
Grain primitives — the irreducible 1D ribbon of the TarPit ecology.

Adapted from `evolving_tarpit/grain.py`. Pure-stdlib (no numpy);
vectors are tuples of floats. Same conceptual surface:

  - `DimensionalExtent` carries the extent vector + capacity bounds.
  - `Grain` is the bit-carrying irreducible unit with extent + bonds.
  - `Ribbon` is the explicit start→end form.
  - `GrainField` is the tape — a position-indexed collection of grains.
"""
from __future__ import annotations

import hashlib
import math
import random
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from . import _math as _m
from ._math import Vec


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GrainType(Enum):
    BIT = "bit"
    COMBINATOR = "combinator"
    MEDIATOR = "mediator"
    DUST = "dust"
    TRIAD = "triad"


# ---------------------------------------------------------------------------
# DimensionalExtent
# ---------------------------------------------------------------------------

_MASS_CAP = 0.999999  # reserve 1.0 for certified closure


@dataclass
class DimensionalExtent:
    """The extent vector of a grain plus its capacity bounds at this layer."""
    vector: Vec
    layer: int = 0
    L_max: float = 1.0
    A_max: float = 1.0
    V_max: float = 1.0

    def __post_init__(self) -> None:
        self.vector = _m.vec(self.vector)

    @property
    def norm(self) -> float:
        return _m.norm(self.vector)

    @property
    def mass_1d(self) -> float:
        if self.L_max <= 0:
            return 0.0
        raw = self.norm / self.L_max
        return min(raw, _MASS_CAP)

    def parallelogram_area(self, other: "DimensionalExtent") -> float:
        return _m.parallelogram_area(self.vector, other.vector)

    def is_materially_2d(self, other: "DimensionalExtent",
                         epsilon: float = 0.1) -> bool:
        a, b = self.norm, other.norm
        if a == 0 or b == 0:
            return False
        sin_theta = self.parallelogram_area(other) / (a * b)
        return abs(sin_theta) > epsilon

    def mass_2d(self, other: "DimensionalExtent") -> float:
        if self.A_max <= 0:
            return 0.0
        raw = self.parallelogram_area(other) / self.A_max
        return min(raw, _MASS_CAP)

    def with_vector(self, new_vector: Vec) -> "DimensionalExtent":
        return DimensionalExtent(
            vector=_m.vec(new_vector),
            layer=self.layer,
            L_max=self.L_max, A_max=self.A_max, V_max=self.V_max,
        )


# ---------------------------------------------------------------------------
# Grain
# ---------------------------------------------------------------------------

@dataclass
class Grain:
    """The irreducible 1D-ribbon unit."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    grain_type: GrainType = GrainType.BIT
    value: int = 0
    extent: DimensionalExtent = field(
        default_factory=lambda: DimensionalExtent(vector=tuple(0.0 for _ in range(8)))
    )
    position: int = 0
    observation_count: int = 0
    birth_time: int = 0
    parent_ids: list[str] = field(default_factory=list)
    certificates: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    associations: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.value = self.value & 1

    @property
    def mass(self) -> float:
        return self.extent.mass_1d

    def flip(self) -> "Grain":
        return Grain(
            id=uuid.uuid4().hex[:8],
            grain_type=self.grain_type,
            value=1 - self.value,
            extent=self.extent.with_vector(self.extent.vector),
            position=self.position,
            observation_count=self.observation_count + 1,
            birth_time=self.birth_time + 1,
            parent_ids=[self.id],
            certificates={**self.certificates, "flipped_from": self.id},
            tags=list(self.tags),
            associations=dict(self.associations),
        )

    def observe(self, observer_id: str = "default") -> "Grain":
        self.observation_count += 1
        self.certificates[f"observed_by_{observer_id}"] = self.observation_count
        return self

    def can_bond_with(self, other: "Grain", epsilon: float = 0.1) -> tuple[bool, float]:
        """Return (is_2d_emergent, mass) for a candidate bond."""
        if self.extent.is_materially_2d(other.extent, epsilon):
            return True, self.extent.mass_2d(other.extent)
        return False, min(self.mass, other.mass)

    def compute_hash(self) -> str:
        content = f"{self.id}:{self.value}:{self.position}:{self.extent.norm:.6f}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_ribbon(self) -> "Ribbon":
        return Ribbon(
            grain_id=self.id,
            start=_m.zeros(len(self.extent.vector)),
            end=self.extent.vector,
            value=self.value,
        )

    def __repr__(self) -> str:
        return f"Grain({self.id}:{self.value}@{self.position},m={self.mass:.3f})"


# ---------------------------------------------------------------------------
# Ribbon
# ---------------------------------------------------------------------------

@dataclass
class Ribbon:
    """Explicit ribbon: directed segment start → end in V_W."""
    grain_id: str
    start: Vec
    end: Vec
    value: int = 0

    def __post_init__(self) -> None:
        self.start = _m.vec(self.start)
        self.end = _m.vec(self.end)

    @property
    def vector(self) -> Vec:
        return _m.sub(self.end, self.start)

    @property
    def length(self) -> float:
        return _m.norm(self.vector)

    def intersects(self, other: "Ribbon", tolerance: float = 1e-6) -> bool:
        """Coarse non-parallel test. Two ribbons whose extent vectors
        are colinear are treated as non-intersecting; otherwise they
        may intersect."""
        v1 = self.vector
        v2 = other.vector
        area = _m.parallelogram_area(v1, v2)
        return area > tolerance

    def __repr__(self) -> str:
        return f"Ribbon({self.grain_id}:len={self.length:.3f})"


# ---------------------------------------------------------------------------
# GrainField — the tape
# ---------------------------------------------------------------------------

class GrainField:
    """The tape: a position-indexed collection of grains.

    Holds the brainfuck-style pointer, evolves through time, and
    bookkeeping for composite structures (Dust / Triad — held opaquely
    in `composites`, populated by `BondEngine`).
    """

    def __init__(self, dimension: int = 8, layer: int = 0,
                 rng: Optional[random.Random] = None) -> None:
        self.dimension = dimension
        self.layer = layer
        self.grains: dict[int, list[Grain]] = {}
        self.composites: list[Any] = []
        self.pointer: int = 0
        self.time: int = 0
        self.L_max = 1.0 * (2 ** layer)
        self.A_max = 1.0 * (4 ** layer)
        self.V_max = 1.0 * (8 ** layer)
        self._rng = rng or random.Random()

    def get_grains(self, position: int) -> list[Grain]:
        return self.grains.get(position, [])

    def get_primary_grain(self, position: int) -> Optional[Grain]:
        gs = self.get_grains(position)
        return max(gs, key=lambda g: g.mass) if gs else None

    def set_grain(self, position: int, grain: Grain) -> None:
        bucket = self.grains.setdefault(position, [])
        grain.position = position
        grain.extent.L_max = self.L_max
        grain.extent.A_max = self.A_max
        grain.extent.V_max = self.V_max
        grain.birth_time = self.time
        bucket.append(grain)

    def create_grain(self, position: int, value: int = 0) -> Grain:
        direction = _m.random_unit_vec(self.dimension, self._rng)
        extent = DimensionalExtent(
            vector=_m.scale(direction, 0.5),
            layer=self.layer,
            L_max=self.L_max, A_max=self.A_max, V_max=self.V_max,
        )
        g = Grain(value=value, extent=extent, position=position)
        self.set_grain(position, g)
        return g

    def move_pointer(self, delta: int) -> None:
        self.pointer += delta

    def get_current_grain(self) -> Optional[Grain]:
        return self.get_primary_grain(self.pointer)

    def flip_current(self) -> Grain:
        g = self.get_current_grain()
        if g is None:
            g = self.create_grain(self.pointer, 0)
        flipped = g.flip()
        self.set_grain(self.pointer, flipped)
        return flipped

    def compute_digital_root(self) -> int:
        total = sum(g.value for grains in self.grains.values() for g in grains)
        while total >= 10:
            total = sum(int(d) for d in str(total))
        return total

    def compute_field_entropy(self) -> float:
        if not self.grains:
            return 0.0
        counts = [len(g) for g in self.grains.values()]
        if not counts:
            return 0.0
        avg = sum(counts) / len(counts)
        return math.log1p(avg) / 10.0

    def step_time(self) -> None:
        self.time += 1

    def all_grains(self) -> list[Grain]:
        return [g for grains in self.grains.values() for g in grains]

    def get_observation(self) -> dict:
        total = sum(len(g) for g in self.grains.values())
        return {
            "dimension": self.dimension,
            "layer": self.layer,
            "time": self.time,
            "pointer": self.pointer,
            "total_grains": total,
            "occupied_positions": len(self.grains),
            "digital_root": self.compute_digital_root(),
            "entropy": self.compute_field_entropy(),
            "composites": len(self.composites),
            "L_max": self.L_max,
            "A_max": self.A_max,
            "V_max": self.V_max,
        }
