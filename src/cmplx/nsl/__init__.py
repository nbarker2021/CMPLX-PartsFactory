"""
cmplx.nsl — Noether-Shannon-Landauer conservation scalar.

The 3-sector ΔΦ = ΔN + ΔI + ΔL conservation law. Every state change
in the unified system reports its NSL sectors; cumulative ΔΦ must
stay ≤ 0. The three sector triads (8-D each) together form a 24-D
Leech-lattice embedding.

See INTERFACE.md + BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .gate import GateDecision, GateMode, gate
from .ledger import NSLLedger, NSLReceipt
from .phi import (
    BOLTZMANN_K,
    COUPLING,
    DEFAULT_TEMPERATURE,
    TOLERANCE,
    delta_phi,
    enforce_conservation,
    is_conserved,
    landauer_cost,
    potential,
    shannon_bound,
)
from .agrm_legality import AGRMLegality
from .phi_computer import PhiComputer, PHI
from .phi_metric import PhiComponents, PhiMetric
from .provider import CheckResult, NSLProvider
from .sectors import LEECH_DIM, NSLSectors, NSLTriads, TRIAD_DIM

__all__ = [
    # phi primitives
    "BOLTZMANN_K", "COUPLING", "DEFAULT_TEMPERATURE", "TOLERANCE",
    "potential", "delta_phi", "shannon_bound", "landauer_cost",
    "enforce_conservation", "is_conserved",
    # sectors
    "LEECH_DIM", "NSLSectors", "NSLTriads", "TRIAD_DIM",
    # gate
    "GateDecision", "GateMode", "gate",
    # ledger
    "NSLLedger", "NSLReceipt",
    # provider
    "CheckResult", "NSLProvider",
    # escrow
    "PhiMetric", "PhiComponents", "AGRMLegality", "PhiComputer", "PHI",
]
