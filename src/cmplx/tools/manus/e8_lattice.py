"""E8 lattice shim for Manus instruments (CMPLXUNI ``cmplx.mdhg.e8_lattice`` API)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from cmplx.primitives.core import generate_e8_roots


@dataclass
class E8Root:
    index: int
    coords: tuple[float, ...]


class E8Lattice:
    """Minimal lattice surface matching Manus instrument expectations."""

    def __init__(self) -> None:
        self._roots = generate_e8_roots()

    def get_roots(self) -> List[E8Root]:
        return [E8Root(i, tuple(float(x) for x in r)) for i, r in enumerate(self._roots)]
