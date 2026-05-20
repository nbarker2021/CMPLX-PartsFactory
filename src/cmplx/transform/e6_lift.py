"""
E6 plot → E8 lift witnesses for linked translation pairs.

Embedding is documented NSL 6D slice + NLAECNF E8 coords (not foreign LLM).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from cmplx.primitives.core import NLAECNFChain


@dataclass
class GeometryWitness:
    concat: str
    snap_key: str
    e6_coords: tuple[float, ...]
    e8_coords: tuple[float, ...]
    translation_key: str = ""
    stream: str = "en"

    def as_dict(self) -> dict[str, Any]:
        return {
            "concat": self.concat,
            "snap_key": self.snap_key,
            "translation_key": self.translation_key,
            "stream": self.stream,
            "e6_coords": list(self.e6_coords),
            "e8_coords": list(self.e8_coords),
        }


def e6_slice_from_e8(e8: tuple[float, ...]) -> tuple[float, ...]:
    """Project 8D E8 witness to 6D Spin(6) slice (first six coords)."""
    if len(e8) < 6:
        padded = tuple(float(x) for x in e8) + (0.0,) * (6 - len(e8))
        return padded[:6]
    return tuple(float(c) for c in e8[:6])


def lift_concat(
    concat: str,
    *,
    translation_key: str = "",
    stream: str = "en",
) -> GeometryWitness:
    canonical = NLAECNFChain.full_chain(concat)
    e8 = tuple(float(c) for c in canonical["e8_coords"])
    return GeometryWitness(
        concat=concat,
        snap_key=str(canonical["snap_key"]),
        e6_coords=e6_slice_from_e8(e8),
        e8_coords=e8,
        translation_key=translation_key,
        stream=stream,
    )


def e8_distance(e8_a: tuple[float, ...], e8_b: tuple[float, ...]) -> float:
    return sum((float(a) - float(b)) ** 2 for a, b in zip(e8_a, e8_b)) ** 0.5


def lift_linked_pair(
    concat_en: str,
    concat_native: str,
    *,
    translation_key: str,
    tolerance: float = 1e-3,
) -> dict[str, Any]:
    """Lift EN + native; report whether E8 coords align within tolerance."""
    w_en = lift_concat(concat_en, translation_key=translation_key, stream="en")
    w_nat = lift_concat(concat_native, translation_key=translation_key, stream="native")
    dist = e8_distance(w_en.e8_coords, w_nat.e8_coords)
    return {
        "en": w_en.as_dict(),
        "native": w_nat.as_dict(),
        "e8_distance": dist,
        "tolerance": tolerance,
        "aligned": dist <= tolerance,
    }


def linked_pair_within_tolerance(
    concat_en: str,
    concat_native: str,
    *,
    translation_key: str = "",
    tolerance: float = 1e-3,
) -> bool:
    """Return True when linked EN/native E8 witnesses are within ``tolerance``."""
    return lift_linked_pair(
        concat_en,
        concat_native,
        translation_key=translation_key,
        tolerance=tolerance,
    )["aligned"]


__all__ = [
    "GeometryWitness",
    "e6_slice_from_e8",
    "e8_distance",
    "lift_concat",
    "lift_linked_pair",
    "linked_pair_within_tolerance",
]
