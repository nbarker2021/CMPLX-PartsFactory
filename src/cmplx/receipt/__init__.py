"""
cmplx.receipt — Merkle-chained operation provenance.

The canonical receipt chain. Every meaningful operation in the
unified system mints a `Receipt`; receipts chain via `prev_hash`
into a Merkle-verifiable audit trail.

Historical 81-field union: ``_history_reference/Receipt_union.py``.
"""
from __future__ import annotations

import warnings

from .chain import ReceiptChain
from .dag import DagEdgeStore
from .provider import ReceiptProvider
from .types import (
    CANONICAL_TYPES,
    DAG_EDGE_TYPES,
    DagEdge,
    GENESIS_HASH,
    LEGACY_TYPE_ALIASES,
    Receipt,
    ReceiptType,
    compute_receipt_hash,
    is_canonical_type,
    normalize_receipt_type,
)

# Deprecation shims (one release)
def __getattr__(name: str):  # noqa: ANN001
    if name in (
        "write_receipt",
        "build_receipt_index",
        "verify_ledger",
        "ReceiptLedger",
        "new_key_b64",
        "new_run_id",
        "OperationReceipt",
        "ReceiptLedgerManager",
        "read_jsonl",
        "load_geolight",
        "load_toklight",
        "merge_timelines",
    ):
        warnings.warn(
            f"cmplx.receipt.{name} is deprecated; prefer ReceiptChain facade "
            f"or cmplx.receipt._persistence",
            DeprecationWarning,
            stacklevel=2,
        )
        if name == "write_receipt":
            from ._persistence.jsonl_run_ledger import write_receipt

            return write_receipt
        if name == "build_receipt_index":
            from ._persistence.jsonl_run_ledger import build_receipt_index

            return build_receipt_index
        if name == "verify_ledger":
            from ._persistence.jsonl_run_ledger import verify_ledger

            return verify_ledger
        if name in ("ReceiptLedger", "new_key_b64", "new_run_id"):
            from . import hmac_ledger as _hl

            return getattr(_hl, name)
        if name in ("OperationReceipt", "ReceiptLedgerManager"):
            from . import ledger_manager as _lm

            return getattr(_lm, name)
        if name in ("read_jsonl", "load_geolight", "load_toklight", "merge_timelines"):
            from . import receipts_bridge as _rb

            return getattr(_rb, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CANONICAL_TYPES",
    "DAG_EDGE_TYPES",
    "DagEdge",
    "GENESIS_HASH",
    "LEGACY_TYPE_ALIASES",
    "Receipt",
    "ReceiptType",
    "compute_receipt_hash",
    "is_canonical_type",
    "normalize_receipt_type",
    "ReceiptChain",
    "DagEdgeStore",
    "ReceiptProvider",
]
