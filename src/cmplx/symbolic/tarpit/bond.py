"""
Bond chemistry — Dust, Triad, BondEngine.

When two grains bond, the engine constructs poles, finds a canonical
mediator, and produces a `Dust` triple `(a, b, mediator, certificates)`.
If the dust passes closure checks, it can be promoted to a `Triad` —
a stabilized higher-order form.

Adapted from `evolving_tarpit/bond_chemistry.py`. The exemplar uses
numpy; this version uses the pure-stdlib `_math` helpers.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from . import _math as _m
from .grain import DimensionalExtent, Grain, GrainType


# ---------------------------------------------------------------------------
# Dust + Triad
# ---------------------------------------------------------------------------

@dataclass
class Dust:
    """A minimal composite: two bonded grains + a mediator."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    pole_a: Optional[Grain] = None
    pole_b: Optional[Grain] = None
    mediator: Optional[Grain] = None
    certificates: dict[str, Any] = field(default_factory=dict)
    creation_time: int = 0

    def members(self) -> list[Grain]:
        return [g for g in (self.pole_a, self.pole_b, self.mediator) if g is not None]

    def compute_signature(self) -> str:
        ids = ":".join(g.id for g in self.members())
        return hashlib.sha256(ids.encode()).hexdigest()[:16]


@dataclass
class Triad:
    """A stabilized 3-body composite produced from a closure-checked Dust."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    grains: list[Grain] = field(default_factory=list)
    closure_score: float = 0.0
    invariant_hash: str = ""
    certificates: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.invariant_hash and self.grains:
            ids = ":".join(g.id for g in self.grains)
            self.invariant_hash = hashlib.sha256(ids.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# BondEngine
# ---------------------------------------------------------------------------

class BondEngine:
    """Bonds grains, produces Dust, promotes Dust to Triads."""

    def __init__(self, epsilon: float = 0.1) -> None:
        self.epsilon = epsilon
        self.bond_history: list[Dust] = []
        self.triad_history: list[Triad] = []

    def attempt_bond(self, a: Grain, b: Grain) -> Optional[Dust]:
        """Try to bond a pair. Returns a Dust on success."""
        # Build a mediator at the midpoint
        if not a.extent.vector or not b.extent.vector:
            return None
        mid_vec = _m.midpoint(a.extent.vector, b.extent.vector)
        mediator_extent = DimensionalExtent(
            vector=mid_vec,
            layer=a.extent.layer,
            L_max=a.extent.L_max, A_max=a.extent.A_max, V_max=a.extent.V_max,
        )
        mediator = Grain(
            grain_type=GrainType.MEDIATOR,
            value=a.value ^ b.value,
            extent=mediator_extent,
            parent_ids=[a.id, b.id],
            certificates={"bonded_from": [a.id, b.id]},
        )
        is_2d, mass = a.can_bond_with(b, self.epsilon)
        dust = Dust(
            pole_a=a, pole_b=b, mediator=mediator,
            certificates={
                "epsilon": self.epsilon,
                "is_2d_emergent": is_2d,
                "bond_mass": mass,
            },
        )
        self.bond_history.append(dust)
        return dust

    def check_closure(self, dust: Dust) -> bool:
        """Closure test: dust must have all three members and the bond
        mass must be at least the COUPLING constant (the floor for a
        meaningful triad)."""
        if not dust or len(dust.members()) < 3:
            return False
        mass = dust.certificates.get("bond_mass", 0.0)
        return mass >= 0.03  # COUPLING

    def promote_to_triad(self, dust: Dust) -> Optional[Triad]:
        """If `dust` passes closure, return the Triad form."""
        if not self.check_closure(dust):
            return None
        triad = Triad(
            grains=dust.members(),
            closure_score=dust.certificates.get("bond_mass", 0.0),
            certificates={"promoted_from": dust.id, **dust.certificates},
        )
        # Tag the constituent grains as part of a triad
        for g in triad.grains:
            g.tags.append(f"triad:{triad.id}")
        self.triad_history.append(triad)
        return triad

    def get_bond_statistics(self) -> dict:
        if not self.bond_history:
            return {
                "total_bonds": 0,
                "triads_formed": 0,
                "avg_dimensional_demand": 0.0,
                "avg_mass": 0.0,
                "2d_emergent_fraction": 0.0,
            }
        masses = [d.certificates.get("bond_mass", 0.0) for d in self.bond_history]
        twod = [1 for d in self.bond_history
                if d.certificates.get("is_2d_emergent")]
        # demand proxy: how often 2D emerged (1 = always 2D)
        avg_demand = 1.0 + len(twod) / len(self.bond_history)
        return {
            "total_bonds": len(self.bond_history),
            "triads_formed": len(self.triad_history),
            "avg_dimensional_demand": avg_demand,
            "avg_mass": sum(masses) / len(masses),
            "2d_emergent_fraction": len(twod) / len(self.bond_history),
        }
