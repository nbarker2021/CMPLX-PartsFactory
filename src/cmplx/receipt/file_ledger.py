"""
Deprecated: use ``cmplx.receipt._persistence.jsonl_run_ledger`` or ``ReceiptChain.write_run_receipt``.
"""
from __future__ import annotations

import warnings

warnings.warn(
    "cmplx.receipt.file_ledger is deprecated; use ReceiptChain.write_run_receipt "
    "or cmplx.receipt._persistence.jsonl_run_ledger",
    DeprecationWarning,
    stacklevel=2,
)

from ._persistence.jsonl_run_ledger import (  # noqa: F401
    build_receipt_index,
    canonical_json,
    merkle_root_hex,
    receipt_schema_version,
    sha256_bytes,
    sha256_file,
    verify_artifact_provenance,
    verify_ledger,
    write_receipt,
    write_receipt_ctx,
)

__all__ = [
    "build_receipt_index",
    "canonical_json",
    "merkle_root_hex",
    "receipt_schema_version",
    "sha256_bytes",
    "sha256_file",
    "verify_artifact_provenance",
    "verify_ledger",
    "write_receipt",
    "write_receipt_ctx",
]
