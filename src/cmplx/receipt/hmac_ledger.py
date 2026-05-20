"""
Deprecated: use ``cmplx.receipt._persistence.hmac_run``.
"""
from __future__ import annotations

import warnings

warnings.warn(
    "cmplx.receipt.hmac_ledger is deprecated; use cmplx.receipt._persistence.hmac_run",
    DeprecationWarning,
    stacklevel=2,
)

from ._persistence.hmac_run import ReceiptLedger, new_key_b64, new_run_id  # noqa: F401

__all__ = ["ReceiptLedger", "new_key_b64", "new_run_id"]
