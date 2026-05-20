"""Receipt signing helpers (escrow file_ledger dependency)."""
from __future__ import annotations

import hashlib
import hmac
from typing import Optional


def sign_receipt_hash(payload_hash: str, key: bytes) -> str:
    return hmac.new(key, payload_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_receipt_signature(payload_hash: str, signature: str, key: bytes) -> bool:
    expected = sign_receipt_hash(payload_hash, key)
    return hmac.compare_digest(expected, signature)
