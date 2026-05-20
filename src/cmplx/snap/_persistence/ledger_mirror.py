"""
In-process SNAP ledger mirror.

Canonical audit trail for cross-slot wiring is the receipt port
(see ``_receipt_bridge``). This module documents the mirror role only.
"""
from __future__ import annotations

from ..ledger import SNAPLedger, SNAPTransaction

__all__ = ["SNAPLedger", "SNAPTransaction"]
