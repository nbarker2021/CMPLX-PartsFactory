"""
MORSRProvider — the `diagnostic` port provider.

Bundles `MORSREngine` (pulse cycle) + `CompleteTraversal` (240-node
mode) + `SonarScan` (ping mode) into one composite provider. Register
on the `diagnostic` port:

    MorphonController.get().register("diagnostic", MORSRProvider())
"""
from __future__ import annotations

from typing import Optional

from cmplx.nsl import NSLProvider

from .operators import OperatorRegistry
from .overlay import Overlay
from .pulse import MORSREngine, MORSRPolicy, Region
from .sonar import SonarScan, SonarScanResult
from .traversal import CompleteTraversal, TraversalResult, TraversalStrategy


class MORSRProvider:
    """Composite MORSR provider: pulse + traversal + sonar."""

    name: str = "morsr_provider"

    def __init__(
        self,
        engine: Optional[MORSREngine] = None,
        traversal: Optional[CompleteTraversal] = None,
        sonar: Optional[SonarScan] = None,
        nsl: Optional[NSLProvider] = None,
    ) -> None:
        nsl = nsl or NSLProvider()
        self.engine = engine or MORSREngine(nsl=nsl)
        self.traversal = traversal or CompleteTraversal(nsl=nsl)
        self.sonar = sonar or SonarScan()
        # Shared NSL for all three modes
        if engine is None:
            self.engine.nsl = nsl
        if traversal is None:
            self.traversal.nsl = nsl
        self.nsl = nsl

    # ── Mode 1: pulse cycle ──────────────────────────────────────────

    def pulse(self, seed: Overlay) -> Region:
        return self.engine.pulse(seed)

    # ── Mode 2: complete traversal ───────────────────────────────────

    def traverse(
        self,
        initial: Overlay,
        strategy: TraversalStrategy = TraversalStrategy.SYSTEMATIC,
    ) -> TraversalResult:
        return self.traversal.explore(initial, strategy)

    # ── Mode 3: sonar scan ───────────────────────────────────────────

    def scan(
        self,
        source,
        radius: float = 5.0,
    ) -> SonarScanResult:
        return self.sonar.ping(source, radius=radius)

    # ── Convenience: register an atom in the sonar field ─────────────

    def register_atom(
        self,
        atom_id: str,
        e8_coords,
        labels: Optional[list[str]] = None,
    ):
        return self.sonar.register_atom(atom_id, e8_coords, labels)

    # ── Operator registration ────────────────────────────────────────

    def add_operator(self, name: str, fn) -> None:
        self.engine.operators.add(name, fn)

    @property
    def operators(self) -> OperatorRegistry:
        return self.engine.operators

    @property
    def policy(self) -> MORSRPolicy:
        return self.engine.policy

    # ── Reporting ────────────────────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": "morsr_provider",
            "operators": len(self.engine.operators),
            "handshakes_recorded": len(self.engine.log),
            "atoms_registered": self.sonar.atom_count,
            "traversal_roots": len(self.traversal.roots),
            "nsl_cumulative_dphi": self.nsl.ledger.cumulative,
        }

    def __repr__(self) -> str:
        return (
            f"<MORSRProvider ops={len(self.engine.operators)} "
            f"atoms={self.sonar.atom_count}>"
        )
