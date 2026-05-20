"""
SNAPLedger + SNAPTransaction — append-only provenance chain.

Every meaningful SNAP operation (label, gate, ennead crystallization)
appends a transaction. Each transaction's hash chains onto the
previous one, so any tamper breaks `verify()`.

This is the SNAP half of the spine — Crystal's `receipt_chain`
extends from this. When `cmplx.engine.cqe` lands, its `delta_phi ≤ 0`
boundary check writes its own receipts into the same ledger.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class SNAPTransaction:
    """One entry in the ledger. Immutable once minted."""
    tx_id: str
    op: str
    payload: dict
    prev_hash: str
    hash: str
    timestamp: float


def _compute_hash(prev_hash: str, op: str, payload: dict, tx_id: str,
                  timestamp: float) -> str:
    serialized = json.dumps({
        "tx_id": tx_id,
        "op": op,
        "payload": payload,
        "prev_hash": prev_hash,
        "timestamp": timestamp,
    }, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SNAPLedger:
    """Append-only chained ledger of SNAP operations."""

    name: str = "snap_ledger"
    GENESIS_HASH: str = "0" * 64

    def __init__(self) -> None:
        self._entries: list[SNAPTransaction] = []

    def append(self, op: str, payload: dict) -> SNAPTransaction:
        prev = self._entries[-1].hash if self._entries else self.GENESIS_HASH
        tx_id = uuid.uuid4().hex[:12]
        ts = time.time()
        h = _compute_hash(prev, op, payload, tx_id, ts)
        tx = SNAPTransaction(
            tx_id=tx_id, op=op, payload=dict(payload),
            prev_hash=prev, hash=h, timestamp=ts,
        )
        self._entries.append(tx)
        return tx

    def verify(self) -> bool:
        """Walk the chain. Return True iff every hash recomputes."""
        prev = self.GENESIS_HASH
        for tx in self._entries:
            expected = _compute_hash(prev, tx.op, tx.payload, tx.tx_id, tx.timestamp)
            if expected != tx.hash or tx.prev_hash != prev:
                return False
            prev = tx.hash
        return True

    @property
    def length(self) -> int:
        return len(self._entries)

    @property
    def head(self) -> str:
        """Tip of the chain (or genesis hash if empty)."""
        return self._entries[-1].hash if self._entries else self.GENESIS_HASH

    def entries(self) -> list[SNAPTransaction]:
        return list(self._entries)

    def to_dict_list(self) -> list[dict]:
        return [asdict(tx) for tx in self._entries]

    def __repr__(self) -> str:
        return f"<SNAPLedger length={self.length} head={self.head[:8]}...>"
