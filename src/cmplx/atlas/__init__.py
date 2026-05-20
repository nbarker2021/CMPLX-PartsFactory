"""
cmplx.atlas — Mandelbrot deployment boundary + Julia c-assignment.

Parent frame slots 26 (atlas-mandelbrot) + 27 (julia-c-assignment).

Each Morphon IS a Julia set with fixed c (Observer-Julia Correspondence).
The Atlas package keeps the Morphon-Mandelbrot Isomorphism honest:
  - ``derive_c(morphon)`` — Julia c-value derivation from Morphon identity
  - ``is_in_mandelbrot(c)`` — membership test for the deployment boundary
  - ``AtlasProvider`` — port-provider that wires both into the cmplx mesh

See INTERFACE.md alongside.
"""
from __future__ import annotations

from .julia import derive_c
from .mandelbrot import escape_time, is_in_mandelbrot
from .provider import AtlasProvider

__all__ = [
    "AtlasProvider",
    "derive_c",
    "escape_time",
    "is_in_mandelbrot",
]
