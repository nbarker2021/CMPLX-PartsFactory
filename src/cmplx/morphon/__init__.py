"""
cmplx.morphon — the atomic-and-outer-bound primitive of the unified
system.

See INTERFACE.md and BRIDGE.md alongside this package for the full
contract. This is the first component built under the new "parts-
plugged-into-a-designed-system" approach.

Public surface:
    Morphon            — the unit type
    MorphonState       — lifecycle Enum
    Receipt            — append-only history entry
    MorphonController  — bridge runtime; other components register here
    register, get_provider — module-level shortcuts to the controller
"""
from __future__ import annotations

from .state import MorphonState, can_transition, assert_transition, is_terminal
from .morphon import Morphon, Receipt
from .controller import (
    MorphonController,
    AddressingProvider,
    AtlasProvider,
    GeometryProvider,
    MemoryProvider,
    ConstraintsProvider,
    EmbedProvider,
    EngineProvider,
    FourEmbedView,
    SymbolicProvider,
    SymbolicReport,
    TransportProvider,
    KNOWN_PORTS,
    register,
    get_provider,
)

__all__ = [
    "Morphon",
    "MorphonState",
    "Receipt",
    "MorphonController",
    "AddressingProvider",
    "AtlasProvider",
    "GeometryProvider",
    "MemoryProvider",
    "ConstraintsProvider",
    "EmbedProvider",
    "EngineProvider",
    "FourEmbedView",
    "SymbolicProvider",
    "SymbolicReport",
    "TransportProvider",
    "KNOWN_PORTS",
    "register",
    "get_provider",
    "can_transition",
    "assert_transition",
    "is_terminal",
]
