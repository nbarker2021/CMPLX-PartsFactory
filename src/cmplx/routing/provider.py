"""
Routing port provider (slot-15) — MDHG channel routing + TSP heuristic solve.

Staging refactored MDHG sweep controller loads optionally via ``staging_loader``.
"""
from __future__ import annotations

from typing import Any, Optional

from cmplx.morphon import Morphon

from .staging_loader import refactored_status, run_mdhg_sweep_probe
from .tsp_heuristic import nearest_neighbor_tour, tour_cost


class AGRMRoutingProvider:
    """Routing facade: MDHG channels + nearest-neighbor TSP tours."""

    name: str = "agrm_routing"

    def route_channel(self, morphon: Morphon) -> int:
        from cmplx.morphon import MorphonController

        addressing = MorphonController.get().get_provider("addressing")
        return addressing.channel_for(morphon)

    def solve(
        self,
        cities: list[tuple[float, float]],
        config: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        cfg = config or {}
        if len(cities) < 2:
            return {"status": "ok", "mode": "trivial", "tour": list(range(len(cities))), "cost": 0.0}
        start = int(cfg.get("start", 0))
        tour = nearest_neighbor_tour(cities, start=start)
        cost = tour_cost(cities, tour)
        out: dict[str, Any] = {
            "status": "ok",
            "mode": "nearest_neighbor",
            "tour": tour,
            "cost": cost,
            "n_cities": len(cities),
            "staging": refactored_status(),
        }
        if cfg.get("mdhg_sweep_probe"):
            out["mdhg_sweep"] = run_mdhg_sweep_probe(
                sweeps=int(cfg.get("sweeps", 1)),
                n=int(cfg.get("n", 200)),
                seed=int(cfg.get("seed", 0)),
            )
        return out

    @property
    def health(self) -> dict[str, Any]:
        st = refactored_status()
        return {
            "ok": True,
            "service": self.name,
            "mode": "nearest_neighbor_tsp",
            "staging_refactored": st,
        }
