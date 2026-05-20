"""
Gate modes — how a component handles a positive-ΔΦ candidate.

Three canonical modes, from `block1_leech_decomposition.yml:83`:

  - ΠG (GOVERN)    — reject if ΔΦ > 0
  - ΠE (AMORTIZE)  — allow with amortization against a budget
  - ΠB (SIGNAL)    — signal but don't reject

A component picks a mode based on its risk profile: governance gates
use GOVERN; engines with energy budgets use AMORTIZE; passive
monitors use SIGNAL.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .phi import TOLERANCE
from .sectors import NSLSectors


class GateMode(str, Enum):
    GOVERN = "govern"        # ΠG — reject if ΔΦ > 0
    AMORTIZE = "amortize"    # ΠE — allow with budget
    SIGNAL = "signal"        # ΠB — signal only


@dataclass(frozen=True)
class GateDecision:
    accepted: bool
    reason: str
    delta_phi: float
    remaining_budget: float = 0.0


def gate(
    sectors: NSLSectors,
    mode: GateMode = GateMode.GOVERN,
    budget: float = 0.0,
    tolerance: float = TOLERANCE,
) -> GateDecision:
    """Apply the chosen gate to an `NSLSectors` candidate.

    Returns a `GateDecision` with `accepted`, a reason string, the
    candidate's `delta_phi`, and (for AMORTIZE) the remaining budget.
    """
    dphi = sectors.total

    if dphi <= tolerance:
        return GateDecision(
            accepted=True,
            reason="conserved",
            delta_phi=dphi,
            remaining_budget=budget,
        )

    # dphi > 0 — non-conservation candidate
    if mode == GateMode.GOVERN:
        return GateDecision(
            accepted=False,
            reason="rejected_govern",
            delta_phi=dphi,
            remaining_budget=budget,
        )

    if mode == GateMode.AMORTIZE:
        if dphi <= budget + tolerance:
            return GateDecision(
                accepted=True,
                reason="amortized",
                delta_phi=dphi,
                remaining_budget=budget - dphi,
            )
        return GateDecision(
            accepted=False,
            reason="budget_exceeded",
            delta_phi=dphi,
            remaining_budget=budget,
        )

    if mode == GateMode.SIGNAL:
        return GateDecision(
            accepted=True,
            reason="signaled_violation",
            delta_phi=dphi,
            remaining_budget=budget,
        )

    raise ValueError(f"unknown gate mode: {mode!r}")
