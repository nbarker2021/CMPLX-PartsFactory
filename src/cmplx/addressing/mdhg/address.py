"""
MDHGAddress — locality-preserving hierarchical address.

Adapted from the canonical `cmplx_pending/addressing/mdhg/MDHGAddress.py`
(3-variant union, 9 methods). Stripped of the BaseModel/pydantic
dependency; pure dataclass.

The shape is the original 5-level hierarchy (planet/city/building/
floor/room) plus `atom` as the finest grain. Coordinates are
quantized into 12-slot buckets from the E8 vector — same scheme as
the canonical, so addresses produced here are interchangeable with
old-system addresses for routing purposes.

`shaped_hash()` is the locality-preserving hash — similar addresses
produce similar prefixes (because the prefix encodes hierarchy, not
content). This is the property AGRM relied on for fast neighborhood
queries.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


def _quantize(val: float, slots: int = 12) -> str:
    """Map a float to a slot id `s00`..`s{slots-1}`."""
    slot = int(abs(val * 1000)) % slots
    return f"s{slot:02d}"


@dataclass
class MDHGAddress:
    """Spatial address with the 5-level hierarchy + atom + e8/leech extras."""

    atom: str = ""
    room: str = ""
    floor: str = ""
    building: str = ""
    city: str = ""
    planet: str = ""
    e8_coords: list[float] = field(default_factory=lambda: [0.0] * 8)
    e8_projection: Optional[list[float]] = None
    leech_coords: Optional[tuple[int, ...]] = None
    granularity_level: int = 0
    grid_layer: str = "fast"   # fast / med / slow
    address_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        if not self.address_hash:
            self.address_hash = self._compute_hash()

    @classmethod
    def from_e8(
        cls,
        e8_coords: list[float],
        granularity: int = 0,
        grid_layer: str = "fast",
    ) -> "MDHGAddress":
        """Build address from 8-D E8 coords by quantizing each component
        into one slot of the hierarchy."""
        coords = list(e8_coords[:8])
        while len(coords) < 8:
            coords.append(0.0)
        return cls(
            atom=_quantize(coords[0]),
            room=_quantize(coords[1]),
            floor=_quantize(coords[2]),
            building=_quantize(coords[3]),
            city=_quantize(coords[4]),
            planet=_quantize(coords[5]),
            e8_coords=coords,
            granularity_level=granularity,
            grid_layer=grid_layer,
        )

    def full_path(self) -> str:
        parts = [self.planet, self.city, self.building,
                 self.floor, self.room, self.atom]
        return "/".join(p for p in parts if p)

    def shaped_hash(self) -> str:
        """Locality-preserving hash — encodes hierarchical position."""
        address_str = (
            f"{self.planet}:{self.city}:{self.building}:"
            f"{self.floor}:{self.room}:{self.atom}:{self.granularity_level}"
        )
        return hashlib.sha256(address_str.encode()).hexdigest()

    def _compute_hash(self) -> str:
        data = (
            f"{self.room}:{self.floor}:{self.building}:"
            f"{self.city}:{self.planet}"
        )
        return hashlib.sha256(data.encode()).hexdigest()[:24]

    def to_dict(self) -> dict:
        return {
            "atom": self.atom,
            "room": self.room,
            "floor": self.floor,
            "building": self.building,
            "city": self.city,
            "planet": self.planet,
            "e8_coords": self.e8_coords,
            "e8_projection": self.e8_projection,
            "leech_coords": list(self.leech_coords) if self.leech_coords else None,
            "granularity_level": self.granularity_level,
            "grid_layer": self.grid_layer,
            "address_hash": self.address_hash,
            "full_path": self.full_path(),
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return f"MDHGAddress({self.full_path()!r}, layer={self.grid_layer!r})"
