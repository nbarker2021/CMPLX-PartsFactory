"""
cmplx.transport.video — VideoCarrier stub.

A `Carrier` that will encode a morphon as a sequence of video frames,
using GVS-style toroidal flow (poloidal / toroidal / meridional /
helical rotation modes) to render time-varying glyphs on top of the
pixel-block layout.

This package currently exposes the **interface only** so the rest of
the DAG can reference it. The implementation will land alongside
`cmplx.geometry.toroidal` (planned) and the WorldForge port.
"""
from __future__ import annotations

from .video import VideoCarrier, VideoFrame

__all__ = ["VideoCarrier", "VideoFrame"]
