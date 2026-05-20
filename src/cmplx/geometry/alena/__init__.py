"""
cmplx.geometry.alena — ALENA projection primitives.

The math layer every carrier and the routing/engine components share.
See INTERFACE.md and BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .ops import (
    ALENA,
    COUPLING,
    PHI,
    E8_NORM,
    fibonacci_radii,
)

__all__ = [
    "ALENA",
    "COUPLING",
    "PHI",
    "E8_NORM",
    "fibonacci_radii",
]
