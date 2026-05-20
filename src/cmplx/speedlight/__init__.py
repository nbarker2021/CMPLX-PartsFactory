"""
cmplx.speedlight — the unified idempotent computation cache.

`f(f(x)) = f(x)`. Once a result is cached at a task's address, it
is never recomputed. Every result lives at an MDHG-shaped address
(`planet.city.building.floor.room.atom`) so neighbor queries become
prefix queries and proximity queries become E8 geometry.

See INTERFACE.md + BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .atlas_o8 import curvature, embed_E8, extract_O8
from .address import (
    ASPECTS,
    PLANETS,
    address_prefix,
    aspect_key,
    compute_mdhg_address,
    parse_address,
)
from .cache import SpeedLight, SpeedLightDistributed
from .equivalence import EquivalenceLearner, Prototype, cosine_similarity
from .index import GlobalIndex, IndexEntry
from .provider import SpeedLightProvider
from .receipt import ComputationReceipt, ReceiptStore
from .tiers import TwoTierCache
from .worldline import WorldlineCache

__all__ = [
    # address
    "ASPECTS", "PLANETS", "address_prefix", "aspect_key",
    "compute_mdhg_address", "parse_address",
    # cache
    "SpeedLight", "SpeedLightDistributed",
    # equivalence
    "EquivalenceLearner", "Prototype", "cosine_similarity",
    # index
    "GlobalIndex", "IndexEntry",
    # provider
    "SpeedLightProvider",
    # receipt
    "ComputationReceipt", "ReceiptStore",
    # tiers
    "TwoTierCache",
    # worldline
    "WorldlineCache",
  # escrow
    "embed_E8", "extract_O8", "curvature",
]
