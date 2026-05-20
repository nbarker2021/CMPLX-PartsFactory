"""
cmplx.receipt — Merkle-chained operation provenance.

The canonical receipt chain. Every meaningful operation in the
unified system mints a `Receipt`; receipts chain via `prev_hash`
into a Merkle-verifiable audit trail. The chain IS the blockchain.

See INTERFACE.md + BRIDGE.md alongside this package.

(Note: `Receipt.py` in this folder is the historical canonical
union from `place_canonicals.py` — 81 attrs across 15 variants —
preserved as reference but not part of the live API. Use
`cmplx.receipt.Receipt` from `types` for the runnable form.)
"""
from __future__ import annotations

from .chain import ReceiptChain
from .dag import DagEdgeStore
from .provider import ReceiptProvider
from .file_ledger import build_receipt_index, verify_ledger, write_receipt
from .hmac_ledger import ReceiptLedger, new_key_b64, new_run_id
from .ledger_manager import OperationReceipt, ReceiptLedgerManager
from .receipts_bridge import load_geolight, load_toklight, merge_timelines, read_jsonl
from .types import (
    CANONICAL_TYPES,
    DagEdge,
    GENESIS_HASH,
    Receipt,
    ReceiptType,
    compute_receipt_hash,
    is_canonical_type,
)

__all__ = [
    # types
    "CANONICAL_TYPES",
    "DagEdge",
    "GENESIS_HASH",
    "Receipt",
    "ReceiptType",
    "compute_receipt_hash",
    "is_canonical_type",
    # store
    "ReceiptChain",
    "DagEdgeStore",
    # provider
    "ReceiptProvider",
    # external JSONL bridges (GeoLight / TokLight)
    "read_jsonl",
    "load_geolight",
    "load_toklight",
    "merge_timelines",
    # escrow file/HMAC ledger
    "write_receipt",
    "build_receipt_index",
    "verify_ledger",
    "ReceiptLedger",
    "new_key_b64",
    "new_run_id",
    "OperationReceipt",
    "ReceiptLedgerManager",
]
