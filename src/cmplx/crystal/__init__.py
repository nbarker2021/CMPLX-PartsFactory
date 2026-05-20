"""
cmplx.crystal — the composite primitive that binds SNAP + MDHG + E8.

See INTERFACE.md + BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .fabric import (
    ATOM_LEVELS,
    CITY_MAP,
    DEFAULT_FABRIC,
    HashAlgo,
    LevelConfig,
    MEANING_LEVELS,
    PLANET_NAMES,
    assign_address,
    digital_root,
    e8_seed_from_name,
    golay_encode,
    julia_iterate,
    project_to_leech,
)
from .registry import CrystalRegistry
from .types import (
    BlockType,
    CompositionRule,
    Crystal,
    E8Node,
    ToolAtom,
    ToolCrystal,
)

__all__ = [
    # fabric
    "ATOM_LEVELS",
    "CITY_MAP",
    "DEFAULT_FABRIC",
    "HashAlgo",
    "LevelConfig",
    "MEANING_LEVELS",
    "PLANET_NAMES",
    "assign_address",
    "digital_root",
    "e8_seed_from_name",
    "golay_encode",
    "julia_iterate",
    "project_to_leech",
    # types
    "BlockType",
    "CompositionRule",
    "Crystal",
    "E8Node",
    "ToolAtom",
    "ToolCrystal",
    # registry
    "CrystalRegistry",
]
