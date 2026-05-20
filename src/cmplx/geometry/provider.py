"""
Geometry — the provider that bridges geometry operations through the
morphon controller.

Implements both `e8_coordinates(morphon)` and `leech_point(morphon)` by
delegating to the sub-packages.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .e8 import e8_coordinates_for
from .leech import leech_point_for

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


class Geometry:
    """Stateless geometry provider. Register on the `geometry` port.

    >>> from cmplx.morphon import MorphonController
    >>> from cmplx.geometry import Geometry
    >>> MorphonController.get().register("geometry", Geometry())
    """

    def e8_coordinates(self, morphon: "Morphon") -> tuple[float, ...]:
        return e8_coordinates_for(morphon)

    def leech_point(self, morphon: "Morphon") -> str:
        return leech_point_for(morphon)
