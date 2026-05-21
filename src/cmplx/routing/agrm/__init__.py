"""
`agrm` family — composed canonicals (slot-15 routing).

``AGRMController`` is a place_canonicals merge stub; import may fail until
recomposed against MDHG + morphon ports.
"""
from __future__ import annotations

from . import _constants
from . import _functions

AGRMController = None
try:
    from .AGRMController import AGRMController as _AGRMController
    AGRMController = _AGRMController
except Exception:  # noqa: BLE001 — stub missing BaseController stack
    pass

__all__ = [
    "AGRMController",
    "_functions",
    "_constants",
]
