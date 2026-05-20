"""
cmplx.geometry — the lattice projections morphons inhabit.

Provides the `geometry` port on MorphonController. See INTERFACE.md and
BRIDGE.md alongside this package for the contract.

Sub-packages:
    cmplx.geometry.e8       — 8-D E8 lattice (used by the port + extended)
    cmplx.geometry.leech    — 24-D Leech-space encoding
    cmplx.geometry.niemeier — 24 Niemeier lattices (extended; not yet used by port)
"""
from __future__ import annotations

from .provider import Geometry
from .e8 import E8
from .leech import Leech

__all__ = ["Geometry", "E8", "Leech"]
