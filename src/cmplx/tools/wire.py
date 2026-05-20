"""Register Manus toolkit on the morphon controller mesh."""
from __future__ import annotations

from typing import Any, Optional

from cmplx.morphon.controller import MorphonController

from .provider import ManusToolsProvider


def register_default_toolkit(
    controller: Optional[MorphonController] = None,
) -> ManusToolsProvider:
    """Attach Manus tools to the ``engine`` provider when present."""
    mc = controller or MorphonController.get()
    manus = ManusToolsProvider()

    if mc.has("engine"):
        eng: Any = mc.get_provider("engine")
        eng.manus = manus  # type: ignore[attr-defined]
    else:
        # standalone registration bag on controller
        mc._manus_tools = manus  # type: ignore[attr-defined]

    return manus


def get_manus_tools(controller: Optional[MorphonController] = None) -> ManusToolsProvider:
    mc = controller or MorphonController.get()
    if mc.has("engine"):
        eng = mc.get_provider("engine")
        if hasattr(eng, "manus"):
            return eng.manus  # type: ignore[attr-defined]
    if hasattr(mc, "_manus_tools"):
        return mc._manus_tools  # type: ignore[attr-defined]
    return register_default_toolkit(mc)
