"""
MDHG routing bridge for TarPit tape cells.

Maps tape payloads to crystal ``assign_address`` hierarchy (planet/slot +
fabric levels). Live remote MDHG service wiring is deferred; this module
is the in-process routing contract.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from cmplx.crystal.fabric import assign_address

from .mdhg_tape import TarpitMDHGTape


def route_tape_cell(
    payload: Dict[str, Any],
    *,
    e8_coords: Optional[List[float]] = None,
    labels: Optional[List[str]] = None,
    entry_type: str = "tape_cell",
) -> Dict[str, Any]:
    """Assign fabric MDHG address for a tape cell payload."""
    content = payload.get("glyph", "") or payload.get("content", "")
    if not content:
        content = str(payload.get("atom_id", payload.get("slot", "")))
    coords = list(e8_coords or payload.get("e8_coords") or [0.0] * 8)[:8]
    addr = assign_address(
        content=content,
        e8_coords=coords,
        entry_type=entry_type,
        labels=labels or payload.get("tags"),
        content_hash=payload.get("content_hash", ""),
    )
    planet = addr.get("Planet") or addr.get("planet") or "alpha"
    return {
        "mdhg_address": addr.get("full", ""),
        "levels": addr,
        "planet_id": str(planet).lower().replace(" ", "_"),
        "digital_root": addr.get("digital_root"),
    }


def bind_tape_cell(
    tape: TarpitMDHGTape,
    payload: Dict[str, Any],
    *,
    position: Optional[Tuple[str, int]] = None,
    e8_coords: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Write cell to tape with MDHG routing metadata attached."""
    routing = route_tape_cell(payload, e8_coords=e8_coords)
    enriched = dict(payload)
    enriched["mdhg_address"] = routing["mdhg_address"]
    enriched["mdhg_levels"] = routing["levels"]
    if position is None:
        position = (routing["planet_id"], tape.pointer[1])
    result = tape.write_cell(enriched, position=position)
    return {"written": result, "routing": routing, "pointer": tape.pointer}
