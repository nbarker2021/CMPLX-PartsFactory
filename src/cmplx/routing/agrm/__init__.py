"""
`agrm` family — routing support (slot-15).

Use ``cmplx.routing.provider.AGRMRoutingProvider`` on the ``routing`` port.
Use ``cmplx.routing.staging_loader`` for the escrowed refactored MDHG build.

The composed merge artifact lives in ``_composed_DO_NOT_IMPORT.py`` — do not import.
"""
from __future__ import annotations

from . import _constants
from . import _functions

__all__ = [
    "_functions",
    "_constants",
]
