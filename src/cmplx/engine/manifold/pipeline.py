"""
Registry-only manifold pipeline — no hinge_controller dependency.

Uses ``ManusToolsProvider`` for domain adaptation and optional NSL gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from cmplx.tools.manus import CMPLXToolRegistry, load_manifest_v3
from cmplx.nsl.phi import delta_phi, potential


@dataclass
class ManifoldItem:
    tool_id: str
    domain: str
    rails: Dict[str, np.ndarray]
    vector_24d: np.ndarray
    label: str = ""
    admitted: bool = True
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ManifoldPipeline:
    """Lightweight SUBMIT path: adapt → label → conservation check."""

    def __init__(self, registry: Optional[CMPLXToolRegistry] = None) -> None:
        self.registry = registry or CMPLXToolRegistry()
        self.manifest = load_manifest_v3()

    def process(
        self,
        tool_id: str,
        raw: Dict[str, Any],
        *,
        phi_before: Optional[np.ndarray] = None,
        phi_after: Optional[np.ndarray] = None,
        eversion: bool = False,
    ) -> ManifoldItem:
        domain = tool_id
        for t in self.manifest.get("tools", []):
            if t.get("tool_id") == tool_id:
                domain = t.get("tool_id", tool_id).split("_", 1)[0]
                break
        rails = self.registry.adapt(tool_id, raw)
        v24 = np.concatenate([rails["alpha"], rails["beta"], rails["gamma"]])
        item = ManifoldItem(
            tool_id=tool_id,
            domain=domain,
            rails=rails,
            vector_24d=v24,
            label=self._auto_label(tool_id, v24),
        )
        if phi_before is not None and phi_after is not None:
            d = delta_phi(phi_before, phi_after)
            if d > 0.03:
                item.admitted = False
                item.reason = f"delta_phi={d:.4f}>0.03"
        item.metadata["phi_before"] = float(potential(phi_before)) if phi_before is not None else None
        item.metadata["phi_after"] = float(potential(phi_after)) if phi_after is not None else None

        if eversion:
            item = self._apply_eversion(item, raw)

        return item

    def _apply_eversion(self, item: ManifoldItem, raw: Dict[str, Any]) -> ManifoldItem:
        """Tempering pass: Morphonic eversion + BRS commit gate on raw payload."""
        try:
            from cmplx.engine.eversion.network import MorphonicEversionNetwork

            net = MorphonicEversionNetwork(n_domains=3)
            ev = net.forward(raw, domain_id=0)
            item.metadata["eversion"] = {
                "committed": ev.get("committed"),
                "brs_all_pass": ev.get("brs_all_pass"),
                "cumulative_delta_phi": ev.get("cumulative_delta_phi"),
                "genus": ev.get("genus"),
                "snap_key": (ev.get("snap_key") or "")[:16],
            }
            if not ev.get("committed", False):
                item.admitted = False
                item.reason = item.reason or "eversion_not_committed"
        except Exception as exc:
            item.metadata["eversion_error"] = str(exc)
        return item

    def _auto_label(self, tool_id: str, v24: np.ndarray) -> str:
        dr = int(np.sum(np.abs(v24) > 0.1)) % 9 or 1
        short = tool_id.replace("T", "").split("_")[0][:12]
        return f"SNAP:{short}:DR{dr}"

    def batch(self, items: List[tuple[str, Dict[str, Any]]]) -> List[ManifoldItem]:
        return [self.process(tid, raw) for tid, raw in items]
