"""
Morphon helpers for transform corpus ingest.

Wires ``MorphonController.store`` / ``fetch`` when the memory port is
registered, and ``combine_pair(..., inherit_link)`` for consecutive
8-char segments in the same chunk.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from cmplx.morphon import Morphon, MorphonController
from cmplx.morphon.combinations import CombineMethod, combine_pair


def try_store(morphon: Morphon) -> Morphon:
    """Persist when ``memory`` port is registered; no-op otherwise."""
    ctrl = MorphonController.get()
    if ctrl.has("memory"):
        return ctrl.store(morphon)
    return morphon


def bond_inherit_link(left: Morphon, right: Morphon) -> Morphon:
    """Explicit ``morphon_tarpit`` inheritance when either side is linked."""
    bonded = combine_pair(left, right, CombineMethod.INHERIT_LINK)
    assert isinstance(bonded, Morphon)
    return try_store(bonded)


def forge_ingest_morphon(
    payload: Mapping[str, Any],
    *,
    prev: Optional[Morphon] = None,
    store: bool = True,
    bond_with_prev: bool = True,
) -> tuple[Morphon, Optional[Morphon]]:
    """Forge a segment morphon; optionally store and bond to *prev*."""
    morphon = Morphon.forge(dict(payload))
    if store:
        morphon = try_store(morphon)
    bond: Optional[Morphon] = None
    if prev is not None and bond_with_prev:
        bond = bond_inherit_link(prev, morphon)
    return morphon, bond
