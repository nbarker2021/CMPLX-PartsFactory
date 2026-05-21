"""
HashLanesProvider — slot-16 thin port.

Lanes are content-addressed descriptors derived from MDHG hierarchical
addressing (channel, register, triad). Tour metadata comes from the
``routing`` port when cities are supplied.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional, Sequence

from cmplx.morphon import Morphon


def _lane_id(channel: int, register: str, triad: str) -> str:
    raw = f"{channel}:{register}:{triad}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


class HashLanesProvider:
    """Deterministic hash-lane routing over MDHG + optional TSP tour order."""

    name: str = "hash_lanes"

    def lane_for(self, morphon: Morphon) -> dict[str, Any]:
        from cmplx.morphon import MorphonController

        addressing = MorphonController.get().get_provider("addressing")
        hx, channel, register, triad = addressing.hierarchical_address(morphon)
        return {
            "lane_id": _lane_id(channel, register, triad),
            "dr_channel": channel,
            "hash_hex": hx,
            "register": register,
            "triad": triad,
            "morphon_id": morphon.id,
        }

    def lanes_for_morphons(self, morphons: Sequence[Morphon]) -> list[dict[str, Any]]:
        return [self.lane_for(m) for m in morphons]

    def tour_plan(
        self,
        cities: Sequence[tuple[float, float]],
        *,
        start: int = 0,
        labels: Optional[Sequence[str]] = None,
    ) -> dict[str, Any]:
        """Build lane hop order from routing TSP + per-city synthetic morphons."""
        from cmplx.morphon import Morphon, MorphonController

        routing = MorphonController.get().get_provider("routing")
        solve_out = routing.solve(list(cities), config={"start": start})
        tour = solve_out.get("tour") or []
        hops: list[dict[str, Any]] = []
        for idx in tour[:-1] if tour and tour[0] == tour[-1] else tour:
            if idx < 0 or idx >= len(cities):
                continue
            label = (labels[idx] if labels and idx < len(labels) else f"city-{idx}")
            m = Morphon.forge(payload={"city_index": idx, "label": label, "xy": cities[idx]})
            lane = self.lane_for(m)
            lane["tour_index"] = idx
            hops.append(lane)
        return {
            "status": "ok",
            "mode": "mdhg_lane_tour",
            "routing": solve_out,
            "hops": hops,
            "hop_count": len(hops),
        }

    @property
    def health(self) -> dict[str, Any]:
        return {"ok": True, "service": self.name, "mode": "mdhg_plus_routing"}
