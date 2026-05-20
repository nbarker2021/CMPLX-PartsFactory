"""Receipt signing helpers for run JSONL ledger."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Optional, Tuple


def _keys_path(workspace: Path) -> Path:
    return workspace / ".receipt" / "signing_keys.json"


def _load_or_create_key(workspace: Path, key_id: str = "default") -> Tuple[str, bytes]:
    path = _keys_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {}
    if key_id not in data:
        if os.environ.get("CQE_DETERMINISTIC_TIME") == "1":
            raw = b"deterministic-test-signing-key-32b!"
        else:
            raw = os.urandom(32)
        data[key_id] = base64.b64encode(raw).decode("ascii")
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    raw = base64.b64decode(data[key_id].encode("ascii"))
    return key_id, raw


def sign_receipt_hash(workspace: Path, receipt_hash: str, key_id: str = "default") -> Tuple[str, str]:
    """Return (signing_key_id, signature_b64) for a receipt hash."""
    kid, key = _load_or_create_key(workspace, key_id)
    mac = hmac.new(key, receipt_hash.encode("utf-8"), hashlib.sha256).digest()
    return kid, base64.b64encode(mac).decode("ascii")


def verify_receipt_signature(
    workspace: Path,
    signing_key_id: str,
    receipt_hash: str,
    signature_b64: str,
    *,
    signed_at_utc: Optional[str] = None,
) -> bool:
    del signed_at_utc  # reserved for future key rotation
    path = _keys_path(workspace)
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_b64 = data.get(signing_key_id)
    if not raw_b64:
        return False
    key = base64.b64decode(raw_b64.encode("ascii"))
    mac = hmac.new(key, receipt_hash.encode("utf-8"), hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("ascii")
    return hmac.compare_digest(expected, signature_b64)
