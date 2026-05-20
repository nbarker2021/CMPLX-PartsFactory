"""
cmplx.constraints.aletheia — conservation-law admission for morphons.

Provides the `constraints` port on MorphonController. See INTERFACE.md
and BRIDGE.md for the contract.
"""
from __future__ import annotations

from .aletheia import (
    Aletheia,
    ConservationLaw,
    LawResult,
    RejectionError,
)
from .dimensional_enforcement import DimensionalEnforcementEngine
from .intent_slicer import Agent, Intent, IntentSlicer
from .report_bridge import ingest_aletheia_report
from .laws import (
    PayloadIsMappingLaw,
    PayloadNotEmptyLaw,
    PayloadSizeLimitLaw,
    StateTransitionWellFormedLaw,
    NoForbiddenKeysLaw,
    default_law_set,
)

__all__ = [
    "Aletheia",
    "ConservationLaw",
    "LawResult",
    "RejectionError",
    "PayloadIsMappingLaw",
    "PayloadNotEmptyLaw",
    "PayloadSizeLimitLaw",
    "StateTransitionWellFormedLaw",
    "NoForbiddenKeysLaw",
    "default_law_set",
    "DimensionalEnforcementEngine",
    "ingest_aletheia_report",
    "Intent",
    "Agent",
    "IntentSlicer",
]
