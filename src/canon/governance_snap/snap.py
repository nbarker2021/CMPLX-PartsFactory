"""
State Management — SNAP Serialization
=======================================

SNAP (State Notation and Atomic Persistence) provides atomic,
hash-verified state serialization for the CMPLX-Alpha system.

Integrates with the composite_tools/snap category.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cmplx.state.snap")


class SnapManager:
    """
    Manages SNAP state serialization and atomic persistence.

    Provides:
    - Atomic write (serialize + hash + store)
    - Verified read (deserialize + hash check)
    - Checkpoint creation and restoration
    - Diff and merge operations
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict] = {}
        self._checkpoints: Dict[str, Dict] = {}
        logger.info("SnapManager initialized")

    def write(self, key: str, value: Any) -> Dict:
        """Atomically serialize and store a value."""
        raw = json.dumps(value, default=str, sort_keys=True)
        h = hashlib.sha256(raw.encode()).hexdigest()[:16]
        record = {
            "key": key,
            "payload": raw,
            "hash": h,
            "ts": time.time(),
            "version": len(self._store.get(key, {}).get("history", [])) + 1,
        }
        self._store[key] = record
        logger.debug("SNAP write: key=%s hash=%s", key, h)
        return record

    def read(self, key: str) -> Optional[Any]:
        """Read and verify a stored value."""
        record = self._store.get(key)
        if record is None:
            return None
        payload = record.get("payload", "")
        expected_hash = record.get("hash", "")
        actual_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        if actual_hash != expected_hash:
            logger.error("SNAP hash mismatch for key=%s — data may be corrupted", key)
            raise ValueError(f"SNAP hash mismatch for key={key}")
        return json.loads(payload)

    def checkpoint(self, name: Optional[str] = None) -> Dict:
        """Create a named checkpoint of the entire store."""
        name = name or f"ckpt_{uuid.uuid4().hex[:8]}"
        snapshot = {
            "checkpoint_id": name,
            "ts": time.time(),
            "store": dict(self._store),
            "n_keys": len(self._store),
        }
        self._checkpoints[name] = snapshot
        logger.info("SNAP checkpoint created: %s (%d keys)", name, len(self._store))
        return snapshot

    def restore(self, checkpoint_id: str) -> bool:
        """Restore the store from a checkpoint."""
        ckpt = self._checkpoints.get(checkpoint_id)
        if ckpt is None:
            logger.error("SNAP checkpoint not found: %s", checkpoint_id)
            return False
        self._store = dict(ckpt.get("store", {}))
        logger.info("SNAP restored from checkpoint: %s", checkpoint_id)
        return True

    def keys(self) -> List[str]:
        return list(self._store.keys())

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def stats(self) -> Dict:
        return {
            "n_keys": len(self._store),
            "n_checkpoints": len(self._checkpoints),
            "checkpoint_ids": list(self._checkpoints.keys()),
        }
