"""
Routing port provider stub (slot-15) — MDHG-backed until AGRM recompose lands.

Registers on ``MorphonController`` port ``routing``. Full TSP solve remains
in escrow (`staging/by-family/agrm/`); this stub exposes channel routing only.
"""
from __future__ import annotations

from typing import Any, Optional

from cmplx.morphon import Morphon


class AGRMRoutingProvider:
    """Minimal routing facade using MDHG ``channel_for``."""

    name: str = "agrm_routing_stub"

    def route_channel(self, morphon: Morphon) -> int:
        """Return DR channel for morphon via addressing port."""
        from cmplx.morphon import MorphonController

        addressing = MorphonController.get().get_provider("addressing")
        return addressing.channel_for(morphon)

    def solve(self, cities: list[tuple[float, float]], config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Placeholder — full AGRM TSP not yet promoted from escrow."""
        return {
            "status": "not_implemented",
            "message": "AGRM TSP solve deferred to escrow triage / recompose wave",
            "n_cities": len(cities),
        }

    @property
    def health(self) -> dict[str, Any]:
        return {"ok": True, "service": self.name, "mode": "mdhg_channel_stub"}
