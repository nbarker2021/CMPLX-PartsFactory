"""cmplx.geometry.e8 — 8-D content-addressed E8 projection + helpers."""
from __future__ import annotations

from .embed import (
    E8,
    DIMENSION,
    e8_coordinates_for,
    e8_coordinates_from_payload,
    e8_roots,
    nearest_root,
)

__all__ = [
    "E8",
    "DIMENSION",
    "e8_coordinates_for",
    "e8_coordinates_from_payload",
    "e8_roots",
    "nearest_root",
]
