"""
Crystal dataclasses — data crystals + tool crystals.

Two surfaces:
  - `Crystal` + `E8Node`: knowledge units mounted on the 10-level fabric.
  - `ToolCrystal` + `ToolAtom`: tools-as-crystals with 4 bonded atoms.

Both share the receipt_chain provenance idea and the
`snap_labels + e8_coords + mdhg_address` triple.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Optional

from cmplx.geometry.alena import COUPLING

from .fabric import (
    DEFAULT_FABRIC,
    LevelConfig,
    MEANING_LEVELS,
    e8_seed_from_name,
)


# ---------------------------------------------------------------------------
# Tool-crystal enums (from cmplx_pending/tmn/BlockType.py + CompositionRule.py)
# ---------------------------------------------------------------------------

class BlockType(str, Enum):
    INPUT = "INPUT"
    TRANSFORM = "TRANSFORM"
    BOUNDARY = "BOUNDARY"
    OUTPUT = "OUTPUT"


class CompositionRule(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    RECURSIVE = "recursive"


# ---------------------------------------------------------------------------
# Data crystal: Crystal + E8Node
# ---------------------------------------------------------------------------

@dataclass
class Crystal:
    """A knowledge crystal mounted on the 10-level fabric.

    Identity (`crystal_id`) is auto-generated; `e8_root` is the seed
    coordinate that anchors the crystal in the lattice; `receipt_chain`
    is a sha256 chain extended every time a node is added.
    """
    crystal_id: str = ""
    name: str = ""
    crystal_type: str = "knowledge"
    state: str = "growing"  # growing | committed | active
    e8_root: list[float] = field(default_factory=lambda: [0.0] * 8)
    meaning_levels: list[str] = field(default_factory=lambda: list(MEANING_LEVELS[:3]))
    level_config: list[dict] = field(default_factory=list)
    owner: str = ""
    snap_address: str = ""
    receipt_chain: str = ""
    created_at: float = 0.0
    node_count: int = 0
    total_mass: float = 0.0

    def __post_init__(self) -> None:
        if not self.crystal_id:
            self.crystal_id = uuid.uuid4().hex[:12]
        if not self.created_at:
            self.created_at = time.time()
        if not self.receipt_chain:
            self.receipt_chain = hashlib.sha256(
                f"crystal:{self.crystal_id}".encode()
            ).hexdigest()[:32]
        if not self.snap_address:
            self.snap_address = f"crystal://{self.name or self.crystal_id}"

    def extend_receipt(self, tag: str) -> str:
        """Hash the current receipt_chain with a new tag; update + return."""
        self.receipt_chain = hashlib.sha256(
            f"{self.receipt_chain}:{tag}:{time.time_ns()}".encode()
        ).hexdigest()[:32]
        return self.receipt_chain

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class E8Node:
    """A single point inside a crystal — carries every binding at once.

    `snap_labels` come from `cmplx.snap`; `mdhg_address` from
    `cmplx.crystal.fabric.assign_address` (or the richer
    `cmplx.addressing.mdhg` when promoted); `e8_coords` from
    `cmplx.geometry.e8` / `alena.project_to_channels`.
    """
    node_id: str = ""
    crystal_id: str = ""
    content: str = ""
    content_type: str = "atom"
    e8_coords: list[float] = field(default_factory=lambda: [0.0] * 8)
    snap_labels: list[str] = field(default_factory=list)
    mdhg_address: dict = field(default_factory=dict)
    importance: float = 0.5
    meaning_level: int = 0
    mass: float = 0.0
    created_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.node_id:
            self.node_id = f"node-{uuid.uuid4().hex[:8]}"
        if not self.created_at:
            self.created_at = time.time()
        if not self.mass:
            self.mass = len(self.snap_labels) * COUPLING

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Tool crystal: ToolAtom + ToolCrystal
# (canonical forms from cmplx_pending/tmn/{ToolAtom,ToolCrystal}.py)
# ---------------------------------------------------------------------------

@dataclass
class ToolAtom:
    """One of the four blocks of a ToolCrystal.

    Default `laws = ["delta_phi_le_0", "receipt_required"]` — the
    conservation requirements every tool atom must satisfy.
    """
    atom_id: str
    block_type: BlockType
    tool_name: str
    handler: Optional[Callable] = field(default=None, repr=False)
    param_schema: dict[str, Any] = field(default_factory=dict)
    output_desc: str = ""
    laws: list[str] = field(default_factory=lambda: ["delta_phi_le_0", "receipt_required"])
    snap_labels: list[str] = field(default_factory=list)
    e8_coords: list[float] = field(default_factory=lambda: [0.0] * 8)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "atom_id": self.atom_id,
            "block_type": self.block_type.value,
            "tool_name": self.tool_name,
            "param_schema": self.param_schema,
            "output_desc": self.output_desc,
            "laws": self.laws,
            "snap_labels": self.snap_labels,
            "e8_coords": self.e8_coords,
            "description": self.description,
        }


@dataclass
class ToolCrystal:
    """A tool expressed as a crystal with n=4 bonded atoms.

    The crystal IS the tool definition AND the handler AND the schema.
    Bonds compose tool crystals into pipelines.
    """
    name: str
    description: str = ""
    category: str = "general"
    input_atom: Optional[ToolAtom] = None
    transform_atom: Optional[ToolAtom] = None
    boundary_atom: Optional[ToolAtom] = None
    output_atom: Optional[ToolAtom] = None
    bonds: list[tuple[str, CompositionRule]] = field(default_factory=list)
    resonance: str = ""
    e8_coords: list[float] = field(default_factory=lambda: [0.0] * 8)

    def __post_init__(self) -> None:
        if not self.resonance:
            self.resonance = self._compute_resonance()
        if not self.e8_coords or all(c == 0 for c in self.e8_coords):
            self.e8_coords = e8_seed_from_name(self.name)
        if not self.input_atom:
            self._default_blocks()

    def _compute_resonance(self) -> str:
        payload = json.dumps(
            {"name": self.name, "category": self.category,
             "desc": self.description[:64]},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:24]

    def _default_blocks(self) -> None:
        base = f"{self.name}_"
        self.input_atom = ToolAtom(
            atom_id=base + "input",
            block_type=BlockType.INPUT,
            tool_name=self.name,
            description=f"Input constraints for {self.name}",
        )
        self.boundary_atom = ToolAtom(
            atom_id=base + "boundary",
            block_type=BlockType.BOUNDARY,
            tool_name=self.name,
            laws=["delta_phi_le_0", "receipt_required"],
            description=f"Conservation boundary for {self.name}",
        )
        self.output_atom = ToolAtom(
            atom_id=base + "output",
            block_type=BlockType.OUTPUT,
            tool_name=self.name,
            description=f"Output type for {self.name}",
        )

    def configure(
        self,
        handler: Callable,
        param_schema: dict[str, Any],
        output_desc: str = "",
        snap_labels: Optional[list[str]] = None,
        e8_coords: Optional[list[float]] = None,
        laws: Optional[list[str]] = None,
    ) -> "ToolCrystal":
        """Set the TRANSFORM atom handler and configure INPUT/OUTPUT schemas."""
        self.transform_atom = ToolAtom(
            atom_id=f"{self.name}_transform",
            block_type=BlockType.TRANSFORM,
            tool_name=self.name,
            handler=handler,
            description=self.description,
            snap_labels=snap_labels or [],
            e8_coords=e8_coords or self.e8_coords,
        )
        if self.input_atom:
            self.input_atom.param_schema = param_schema
        if self.output_atom and output_desc:
            self.output_atom.output_desc = output_desc
        if self.boundary_atom and laws:
            self.boundary_atom.laws = laws
        if e8_coords:
            self.e8_coords = e8_coords
        return self

    def add_bond(self, target_crystal_name: str, rule: CompositionRule) -> "ToolCrystal":
        self.bonds.append((target_crystal_name, rule))
        return self

    def to_mcp_schema(self) -> dict:
        """Export as MCP Tool schema (wire-protocol compatible)."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_atom.param_schema if self.input_atom else {},
        }

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "resonance": self.resonance,
            "e8_coords": self.e8_coords,
            "atoms": {
                "input": self.input_atom.to_dict() if self.input_atom else None,
                "transform": self.transform_atom.to_dict() if self.transform_atom else None,
                "boundary": self.boundary_atom.to_dict() if self.boundary_atom else None,
                "output": self.output_atom.to_dict() if self.output_atom else None,
            },
            "bonds": [(t, r.value) for t, r in self.bonds],
        }
