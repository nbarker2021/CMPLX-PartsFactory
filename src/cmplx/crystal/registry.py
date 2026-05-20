"""
CrystalRegistry — the `crystal` port provider.

Holds data crystals + tool crystals in-process. Mints Crystals,
attaches E8Nodes (with snap_labels + mdhg_address + e8_coords), and
exposes resonance-based queries (`vibrate`).

Persistence to MMDB is optional and goes through the `memory` port
when registered (lazy lookup so the registry runs standalone too).
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from .fabric import ATOM_LEVELS, DEFAULT_FABRIC, LevelConfig, assign_address
from .types import (
    Crystal,
    E8Node,
    ToolCrystal,
)

class CrystalRegistry:
    """In-process registry of data crystals + tool crystals.

    Register on the `crystal` port:
        MorphonController.get().register("crystal", CrystalRegistry())
    """

    name: str = "crystal_registry"

    def __init__(self) -> None:
        self._crystals: dict[str, Crystal] = {}
        self._nodes_by_crystal: dict[str, list[E8Node]] = {}
        self._tools: dict[str, ToolCrystal] = {}

    def _snap_engine(self) -> Any:
        """Resolve SNAP via morphon port, else in-process fallback."""
        try:
            from cmplx.morphon import MorphonController

            ctrl = MorphonController.get()
            if ctrl.has("snap"):
                return ctrl.get_provider("snap")
        except Exception:
            pass
        try:
            from cmplx.snap import SNAPEngine

            return SNAPEngine()
        except Exception:
            return None

    def _snap_labels_for(
        self,
        content: str,
        *,
        key: str = "",
        content_type: str = "atom",
        labels: Optional[list[str]] = None,
    ) -> list[str]:
        if labels is not None:
            return list(labels)
        engine = self._snap_engine()
        if engine is None:
            return []
        item_key = key or (content[:32] if content else "node")
        snap_label = engine.label(
            content,
            key=item_key,
            context={"content_type": content_type},
        )
        return list(snap_label.all_labels)

    # ── Data crystal CRUD ───────────────────────────────────────────────

    def create(
        self,
        name: str,
        crystal_type: str = "knowledge",
        e8_seed: Optional[list[float]] = None,
        meaning_depth: int = 3,
        level_count: int = 6,
        owner: str = "",
    ) -> Crystal:
        from .fabric import e8_seed_from_name, MEANING_LEVELS
        seed = e8_seed if e8_seed else e8_seed_from_name(name)
        levels = DEFAULT_FABRIC[:level_count] if level_count <= 10 else DEFAULT_FABRIC
        crystal = Crystal(
            name=name,
            crystal_type=crystal_type,
            e8_root=list(seed),
            meaning_levels=list(MEANING_LEVELS[:meaning_depth]),
            level_config=[asdict(lvl) for lvl in levels],
            owner=owner,
        )
        self._crystals[crystal.crystal_id] = crystal
        self._nodes_by_crystal[crystal.crystal_id] = []
        return crystal

    def add_node(
        self,
        crystal_id: str,
        content: str,
        content_type: str = "atom",
        e8_coords: Optional[list[float]] = None,
        labels: Optional[list[str]] = None,
    ) -> E8Node:
        crystal = self._crystals.get(crystal_id)
        if crystal is None:
            raise LookupError(f"crystal not found: {crystal_id}")

        if crystal.level_config:
            levels = tuple(LevelConfig(**lvl) for lvl in crystal.level_config)
        else:
            levels = ATOM_LEVELS

        coords = list(e8_coords) if e8_coords else list(crystal.e8_root)
        snap_labels = self._snap_labels_for(
            content,
            key=content[:32] if content else "",
            content_type=content_type,
            labels=labels,
        )
        mdhg = assign_address(
            content=content,
            e8_coords=coords,
            entry_type=content_type,
            labels=snap_labels,
            levels=levels,
        )
        node = E8Node(
            crystal_id=crystal_id,
            content=content,
            content_type=content_type,
            e8_coords=coords,
            snap_labels=snap_labels,
            mdhg_address=mdhg,
        )
        self._nodes_by_crystal[crystal_id].append(node)
        crystal.node_count += 1
        crystal.total_mass += node.mass
        crystal.extend_receipt(f"node:{node.node_id}")
        return node

    def mount_ennead(
        self,
        crystal_id: str,
        ennead: Any,
        *,
        record_crystallize: bool = True,
    ) -> list[E8Node]:
        """Mount Gate369 ennead facets as nodes; optional SNAP crystallize ledger op."""
        engine = self._snap_engine()
        if record_crystallize and engine is not None:
            engine.crystallize(ennead)
        nodes: list[E8Node] = []
        for body in getattr(ennead, "facets", ()) or ():
            payload = getattr(body, "payload", None)
            content = str(payload if payload is not None else getattr(body, "id", ""))
            nodes.append(
                self.add_node(
                    crystal_id,
                    content=content,
                    content_type="ennead_facet",
                    labels=None,
                )
            )
        return nodes

    def mount_triad(
        self,
        crystal_id: str,
        triad: Any,
        *,
        record_bond: bool = True,
    ) -> list[E8Node]:
        """Mount TarPit ``Triad`` grains as crystal nodes (glyphic_tarpit bond path)."""
        if record_bond:
            from cmplx.symbolic.tarpit._receipt_bridge import mint_tarpit_operation

            mint_tarpit_operation(
                "triad",
                {"triad_id": getattr(triad, "id", ""), "grains": len(getattr(triad, "grains", []))},
                atom_id=getattr(triad, "id", "triad"),
            )
        nodes: list[E8Node] = []
        for grain in getattr(triad, "grains", ()) or ():
            content = str(getattr(grain, "id", ""))
            tags = list(getattr(grain, "tags", []) or [])
            nodes.append(
                self.add_node(
                    crystal_id,
                    content=content,
                    content_type="triad_grain",
                    labels=tags or None,
                )
            )
        return nodes

    def get(self, crystal_id: str) -> Optional[Crystal]:
        return self._crystals.get(crystal_id)

    def nodes_of(self, crystal_id: str) -> list[E8Node]:
        return list(self._nodes_by_crystal.get(crystal_id, ()))

    def list(self, state: Optional[str] = None) -> list[Crystal]:
        if state is None:
            return list(self._crystals.values())
        return [c for c in self._crystals.values() if c.state == state]

    def commit(self, crystal_id: str) -> dict:
        crystal = self._crystals.get(crystal_id)
        if crystal is None:
            raise LookupError(f"crystal not found: {crystal_id}")
        crystal.state = "committed"
        crystal.extend_receipt("commit")
        return {"crystal_id": crystal_id, "state": "committed",
                "nodes": crystal.node_count}

    def activate(self, crystal_id: str) -> dict:
        crystal = self._crystals.get(crystal_id)
        if crystal is None:
            raise LookupError(f"crystal not found: {crystal_id}")
        crystal.state = "active"
        crystal.extend_receipt("activate")
        return {"crystal_id": crystal_id, "state": "active"}

    # ── Tool crystal CRUD ───────────────────────────────────────────────

    def register_tool(self, tool: ToolCrystal) -> ToolCrystal:
        if tool.name in self._tools:
            raise RuntimeError(f"tool crystal {tool.name!r} already registered")
        self._tools[tool.name] = tool
        return tool

    def get_tool(self, name: str) -> Optional[ToolCrystal]:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolCrystal]:
        return list(self._tools.values())

    # ── Resonance query ────────────────────────────────────────────────

    def vibrate(self, crystal_id: str, frequency: float,
                tolerance: float = 0.1) -> list[E8Node]:
        """Return nodes whose first e8_coord is within `tolerance` of
        `frequency`. The minimum-viable form of resonance querying —
        richer versions (E8 dot-product, leech distance) plug in later.
        """
        nodes = self._nodes_by_crystal.get(crystal_id, [])
        return [
            n for n in nodes
            if n.e8_coords and abs(n.e8_coords[0] - frequency) <= tolerance
        ]

    # ── Reporting ──────────────────────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": "crystal_registry",
            "crystals": len(self._crystals),
            "tools": len(self._tools),
            "total_nodes": sum(c.node_count for c in self._crystals.values()),
        }

    def __repr__(self) -> str:
        return (
            f"<CrystalRegistry crystals={len(self._crystals)} "
            f"tools={len(self._tools)}>"
        )
