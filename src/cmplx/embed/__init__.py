"""
cmplx.embed — 4-Embed Model decomposition.

Provides the `embed` port on MorphonController. Decomposes a morphon
into the four typed channels (Constraint, State, Evidence, Operator) of
the 4-Embed Model. See INTERFACE.md alongside.

Sub-frame slot — parent frame Slot 19.
"""
from __future__ import annotations

from .provider import FourEmbedProvider

__all__ = ["FourEmbedProvider"]
