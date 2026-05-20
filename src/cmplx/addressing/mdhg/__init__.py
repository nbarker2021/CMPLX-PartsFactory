"""
cmplx.addressing.mdhg — Multi-Dimensional Hash Graph.

Two surfaces:

  - Channel-1-9 digital-root addressing (the runnable contract for the
    `addressing` port on `MorphonController`).

  - Locality-preserving hierarchical addresses (`MDHGAddress`) +
    multi-scale admission with drift tracking (`MDHGMultiScale`,
    `LayerCache`, `SlotRecord`) — promoted from
    `composed_mdhg_v3.py` (8720-line historical monolith).

See INTERFACE.md and BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .address import MDHGAddress
from .hash import (
    MDHG,
    Channel,
    Triad,
    digital_root,
    digital_root_hex,
)
from .multiscale import (
    DEFAULT_BINS,
    LAYERS,
    LayerCache,
    MDHGMultiScale,
    QUANT_DIMS,
    SlotRecord,
    quantize_24,
    slot_id_from_q24,
)
from .provider import MDHGAddressingProvider

__all__ = [
    # Channel-1-9 addressing
    "MDHG",
    "Channel",
    "Triad",
    "digital_root",
    "digital_root_hex",
    # Hierarchical addresses
    "MDHGAddress",
    # Multi-scale admission
    "DEFAULT_BINS",
    "LAYERS",
    "LayerCache",
    "MDHGMultiScale",
    "QUANT_DIMS",
    "SlotRecord",
    "quantize_24",
    "slot_id_from_q24",
    # Provider facade
    "MDHGAddressingProvider",
]
