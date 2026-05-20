"""
HMAC JSONL master ledger (escrow from partsfactory/ledger.py).

Canonical location; ``cmplx.receipt.hmac_ledger`` re-exports with deprecation.
"""
from __future__ import annotations

import base64
import hashlib
import hmac as hmac_lib
import json
import os
import threading
import time
import uuid

_lock = threading.Lock()


def _canon(o: object) -> str:
    return json.dumps(o, sort_keys=True, separators=(",", ":"))


def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _hmac_sig(key_b64: str, msg: str) -> str:
    key = base64.b64decode(key_b64.encode("ascii"))
    mac = hmac_lib.new(key, msg.encode("utf-8"), digestmod=hashlib.sha256).digest()
    return "H:" + base64.b64encode(mac).decode("ascii")


class ReceiptLedger:
    """Append-only JSONL ledger with hash chain + HMAC signature."""

    def __init__(self, root_dir: str, key_b64: str):
        self.root_dir = root_dir
        self.key_b64 = key_b64
        os.makedirs(root_dir, exist_ok=True)
        self.path = os.path.join(root_dir, "master.jsonl")

    def _last_hash(self) -> str | None:
        try:
            with open(self.path, "rb") as f:
                lines = f.read().splitlines()
            if not lines:
                return None
            rec = json.loads(lines[-1].decode("utf-8"))
            return rec.get("hash")
        except FileNotFoundError:
            return None

    def append(self, record: dict) -> dict:
        record = dict(record)
        record["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        record["prev"] = self._last_hash()
        payload = _canon(record)
        record["hash"] = "h:" + _sha256_hex(payload.encode("utf-8"))
        record["sig"] = _hmac_sig(self.key_b64, payload)
        with _lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, separators=(",", ":")) + "\n")
        return record

    def verify(self) -> dict:
        try:
            with open(self.path, "rb") as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            return {"ok": True, "count": 0}
        prev = None
        for i, raw in enumerate(lines):
            rec = json.loads(raw.decode("utf-8"))
            canon = {k: v for k, v in rec.items() if k not in ("hash", "sig")}
            payload = _canon(canon)
            if rec.get("prev") != prev:
                return {"ok": False, "at": i, "err": "prev_mismatch"}
            if rec.get("hash") != "h:" + _sha256_hex(payload.encode("utf-8")):
                return {"ok": False, "at": i, "err": "hash_mismatch"}
            if rec.get("sig") != _hmac_sig(self.key_b64, payload):
                return {"ok": False, "at": i, "err": "sig_mismatch"}
            prev = rec.get("hash")
        return {"ok": True, "count": len(lines)}

    def close(self) -> None:
        return


def new_key_b64() -> str:
    return base64.b64encode(os.urandom(32)).decode("ascii")


def new_run_id(prefix: str = "civ") -> str:
    return f"{prefix}:{uuid.uuid4().hex[:12]}"


__all__ = ["ReceiptLedger", "new_key_b64", "new_run_id"]
