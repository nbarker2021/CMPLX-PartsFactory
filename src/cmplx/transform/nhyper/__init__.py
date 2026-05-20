"""
NHyperTower minimal API — promoted interfaces (body still escrow in pending file).

Full combinatorial tower remains in ``src/cmplx_pending/n/NHyperTower.py`` until
explicit promotion approval; this package wires level builders to ``superperm_n``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from cmplx.primitives.superperm import superperm_n, superperm_length

from ..nhyper_tower import nhyper_active_n


@dataclass
class NHyperLevelSpec:
    tower_level: int
    active_n: int
    sp_length: int
    status: str = "minimal_api"

    def as_dict(self) -> dict[str, Any]:
        return {
            "tower_level": self.tower_level,
            "active_n": self.active_n,
            "sp_length": self.sp_length,
            "status": self.status,
        }


def level_spec(tower_level: int) -> NHyperLevelSpec:
    """Resolve tower level to superpermutation schedule (n = level + 4 for 0..4)."""
    n = nhyper_active_n(tower_level)
    return NHyperLevelSpec(
        tower_level=tower_level,
        active_n=n,
        sp_length=superperm_length(n),
    )


def superperm_for_level(tower_level: int) -> str:
    """Load validated superpermutation string for a tower level."""
    return superperm_n(nhyper_active_n(tower_level))


def build_level_hook(tower_level: int, *, partial: Optional[str] = None) -> dict[str, Any]:
    """
    Minimal level builder hook for compose pipelines (no Cartesian product).

    Returns schedule metadata only; mutations stay in ``IndexSupervisor``.
    """
    spec = level_spec(tower_level)
    return {
        "level": spec.as_dict(),
        "superpermutation_preview": superperm_for_level(tower_level)[:32] + "...",
        "partial_seed": partial,
    }


__all__ = [
    "NHyperLevelSpec",
    "build_level_hook",
    "level_spec",
    "superperm_for_level",
]
