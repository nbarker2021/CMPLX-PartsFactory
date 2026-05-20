"""
cmplx.transport.pixel — RGB pixel-block carrier for morphons.

One implementation of the broader `cmplx.transport.carrier` framework.
See INTERFACE.md and BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .pixel import BLOCK_SIZE, PixelCarrier, PixelFrame

__all__ = ["BLOCK_SIZE", "PixelCarrier", "PixelFrame"]
