"""Hash helpers for escrow bridges (replaces retooling.compat)."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def prefixed_id(prefix: str, digest: str, *, width: int = 16) -> str:
    return f"{prefix}_{digest[:width]}"


def deterministic_iso_from_hash(payload: dict[str, Any], *, key: str = "hash") -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256_hex(canonical)
