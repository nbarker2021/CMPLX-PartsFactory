"""cmplx.geometry.leech — 24-D content-addressed Leech-space encoding."""
from __future__ import annotations

from .embed import (
    Leech,
    DIMENSION,
    LEECH_PREFIX,
    leech_point_for,
    leech_point_from_payload,
)

__all__ = [
    "Leech",
    "DIMENSION",
    "LEECH_PREFIX",
    "leech_point_for",
    "leech_point_from_payload",
]
