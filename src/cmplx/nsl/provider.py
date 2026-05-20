"""
NSLProvider — the `conservation` port provider.

Bundles the `NSLLedger` with a default `GateMode` and provides the
one-call helpers any component uses:

    >>> nsl = NSLProvider()
    >>> result = nsl.check_and_record(v_before, v_after, agent_id="...")
    >>> if result.accepted:
    ...     proceed()
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from .gate import GateDecision, GateMode, gate
from .ledger import NSLLedger, NSLReceipt
from .phi import (
    DEFAULT_TEMPERATURE,
    TOLERANCE,
    delta_phi,
    enforce_conservation,
    landauer_cost,
    potential,
    shannon_bound,
)
from .sectors import NSLSectors, NSLTriads


@dataclass
class CheckResult:
    """Combined output of a `check_and_record` call."""
    decision: GateDecision
    receipt: NSLReceipt
    sectors: NSLSectors

    @property
    def accepted(self) -> bool:
        return self.decision.accepted

    @property
    def delta_phi(self) -> float:
        return self.decision.delta_phi


class NSLProvider:
    """The `conservation` port provider.

    Register on the port:
        MorphonController.get().register("conservation", NSLProvider())
    """

    name: str = "nsl_provider"

    def __init__(
        self,
        ledger: Optional[NSLLedger] = None,
        triads: Optional[NSLTriads] = None,
        default_mode: GateMode = GateMode.GOVERN,
        default_budget: float = 0.0,
        tolerance: float = TOLERANCE,
    ) -> None:
        self.ledger = ledger or NSLLedger()
        self.triads = triads or NSLTriads()
        self.default_mode = default_mode
        self.default_budget = default_budget
        self.tolerance = tolerance

    # ── Compute helpers ───────────────────────────────────────────────

    @staticmethod
    def potential(v: Sequence[float]) -> float:
        return potential(v)

    @staticmethod
    def delta_phi(v_before: Sequence[float], v_after: Sequence[float]) -> float:
        return delta_phi(v_before, v_after)

    @staticmethod
    def shannon_bound(v: Sequence[float]) -> float:
        return shannon_bound(v)

    @staticmethod
    def landauer_cost(d_phi: float, temperature: float = DEFAULT_TEMPERATURE) -> float:
        return landauer_cost(d_phi, temperature)

    def compute_sectors(
        self,
        v_before: Sequence[float],
        v_after: Sequence[float],
    ) -> NSLSectors:
        """Three-sector breakdown.

        - `dN` — Noether sector via inner product with `triads.noether`.
        - `dI` — Shannon delta: `H(after) - H(before)`.
        - `dL` — Landauer sector via inner product with `triads.landauer`,
          scaled by COUPLING for consistency with the canonical form.

        If `triads.noether` is the zero vector (default state), the
        Noether sector is 0 and ΔΦ collapses to (shannon + landauer +
        the geometric potential delta is reported separately via
        `delta_phi()`).
        """
        delta_vec = tuple(
            float(a) - float(b) for a, b in zip(v_after, v_before)
        )
        # Score the change vector through the triads
        triad_scores = self.triads.score(delta_vec)
        # Shannon: explicit bit-delta
        d_shannon = shannon_bound(v_after) - shannon_bound(v_before)
        # Combine: triad-noether for symmetry, true Shannon delta for info,
        # triad-landauer for erasure (already COUPLING-scaled in the triad)
        return NSLSectors(
            dN=triad_scores.dN,
            dI=d_shannon,
            dL=triad_scores.dL,
        )

    # ── Gate ──────────────────────────────────────────────────────────

    def gate(
        self,
        sectors: NSLSectors,
        mode: Optional[GateMode] = None,
        budget: Optional[float] = None,
    ) -> GateDecision:
        return gate(
            sectors,
            mode=mode or self.default_mode,
            budget=self.default_budget if budget is None else budget,
            tolerance=self.tolerance,
        )

    # ── Combined check + record ──────────────────────────────────────

    def check_and_record(
        self,
        v_before: Sequence[float],
        v_after: Sequence[float],
        agent_id: str = "",
        service: str = "",
        atom_id: str = "",
        operation: str = "",
        epoch: int = 0,
        mode: Optional[GateMode] = None,
        budget: Optional[float] = None,
    ) -> CheckResult:
        sectors = self.compute_sectors(v_before, v_after)
        decision = self.gate(sectors, mode, budget)
        receipt = NSLReceipt(
            sectors=sectors,
            delta_phi=sectors.total,
            agent_id=agent_id,
            service=service,
            atom_id=atom_id,
            operation=operation,
            epoch=epoch,
        )
        self.ledger.append(receipt)
        return CheckResult(decision=decision, receipt=receipt, sectors=sectors)

    # ── Adjustment helper ────────────────────────────────────────────

    def enforce(
        self,
        v_before: Sequence[float],
        v_after: Sequence[float],
    ) -> tuple[tuple[float, ...], bool]:
        return enforce_conservation(v_before, v_after, tolerance=self.tolerance)

    # ── Reporting ─────────────────────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": "nsl_provider",
            "default_mode": self.default_mode.value,
            "default_budget": self.default_budget,
            "ledger": self.ledger.stats(),
        }

    def __repr__(self) -> str:
        return (
            f"<NSLProvider mode={self.default_mode.value} "
            f"ledger_entries={len(self.ledger)} "
            f"cumulative={self.ledger.cumulative:.6f}>"
        )
