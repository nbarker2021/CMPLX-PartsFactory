"""ReceiptLedger — token-domain receipt index over the unified cmplx ledger.

Wave 0.3: this module no longer maintains its own SHA-256 hash chain.
All receipts are minted via ``MorphonController.get("receipt")``; this
class keeps the convenience indexes (by_expert, by_type, by_time) and
exposes the legacy dict-shaped return for backwards compatibility with
existing callers. The 7 wallet receipt types (MINT/BURN/EARN/SPEND/
TRANSFER/STAKE/REWARD) become ``operation_kind`` labels in the unified
receipt payload.

When the ``receipt`` port is unregistered (rare; only during isolated
tests or pre-bootstrap code), the ledger falls back to a local SHA-256
chain identical to the pre-Wave-0.3 behavior. The fallback exists for
robustness; normal runtime always uses the unified port.
"""

from __future__ import annotations
import hashlib
import json
import time
import uuid
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("wallet.receipts")

GENESIS_HASH = "0" * 64
RECEIPT_TYPES = ["MINT", "BURN", "EARN", "SPEND", "TRANSFER", "STAKE", "REWARD"]


class ReceiptLedger:
    def __init__(self, governance=None):
        # `governance` parameter is preserved for backwards compatibility
        # but no longer used internally (Wave 0.3 — main governance handles
        # any governance-level concerns; wallet just emits receipts).
        self.governance = governance
        self.chain: List[Dict[str, Any]] = []
        self.chain_head: str = GENESIS_HASH
        self._index_by_id: Dict[str, Dict[str, Any]] = {}
        self._index_by_hash: Dict[str, Dict[str, Any]] = {}
        self._index_by_expert: Dict[str, List[str]] = {}
        self._index_by_type: Dict[str, List[str]] = {}

    def record(self, expert_id: str, receipt_type: str, amount: float,
               operation: str, balance_before: float = None,
               balance_after: float = None,
               counterparty: str = None,
               payload: Dict[str, Any] = None,
               parent_hash: str = None) -> Dict[str, Any]:
        if receipt_type not in RECEIPT_TYPES:
            raise ValueError(f"Invalid receipt type: {receipt_type}. Must be one of {RECEIPT_TYPES}")

        ts = time.time()
        parent = parent_hash or self.chain_head

        # Try the unified receipt port first.
        unified = self._mint_unified(
            expert_id=expert_id,
            receipt_type=receipt_type,
            amount=amount,
            operation=operation,
            balance_before=balance_before,
            balance_after=balance_after,
            counterparty=counterparty,
            payload=payload,
        )
        if unified is not None:
            receipt_id = unified["receipt_id"]
            receipt_hash = unified["receipt_hash"]
        else:
            # Fallback: legacy local SHA-256 chain.
            receipt_id = str(uuid.uuid4())[:16]
            hash_input = f"{parent}:{expert_id}:{operation}:{amount}:{ts}"
            receipt_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        receipt = {
            "receipt_id": receipt_id,
            "receipt_hash": receipt_hash,
            "receipt_type": receipt_type,
            "expert_id": expert_id,
            "amount": amount,
            "operation": operation,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "counterparty": counterparty,
            "payload": payload or {},
            "prev_hash": parent,
            "chain_index": len(self.chain),
            "created_at": ts,
        }

        self.chain.append(receipt)
        self.chain_head = receipt_hash
        self._index_by_id[receipt_id] = receipt
        self._index_by_hash[receipt_hash] = receipt
        self._index_by_expert.setdefault(expert_id, []).append(receipt_id)
        self._index_by_type.setdefault(receipt_type, []).append(receipt_id)

        logger.debug("Receipt %s: %s %.4f for %s", receipt_hash[:16], receipt_type, amount, expert_id)
        return receipt

    def _mint_unified(
        self,
        *,
        expert_id: str,
        receipt_type: str,
        amount: float,
        operation: str,
        balance_before: float | None,
        balance_after: float | None,
        counterparty: str | None,
        payload: Dict[str, Any] | None,
    ) -> Optional[Dict[str, str]]:
        """Mint a PROCESS receipt via the unified port; return id+hash.

        Returns None when the receipt port isn't registered or minting raises.
        Exceptions are swallowed — wallet operations must keep working even
        when the unified ledger is offline.
        """
        try:
            from cmplx.morphon import MorphonController
            provider = MorphonController.get().get_provider("receipt")
            rec = provider.mint(
                receipt_type="process",  # PROCESS in the unified grammar
                agent_id=expert_id,
                atom_id=expert_id,
                operation=operation,
                payload={
                    "operation_kind": receipt_type,  # wallet's 7 types as label
                    "amount": amount,
                    "balance_before": balance_before,
                    "balance_after": balance_after,
                    "counterparty": counterparty,
                    **(payload or {}),
                },
            )
            return {
                "receipt_id": getattr(rec, "receipt_id", "") or "",
                "receipt_hash": getattr(rec, "receipt_hash", "") or getattr(rec, "hash", "") or "",
            }
        except Exception:
            return None

    def verify_chain(self, start_hash: str = None,
                     max_depth: int = 1000) -> Dict[str, Any]:
        start = start_hash or self.chain_head
        current = start
        seen = set()
        breaks = []
        depth = 0
        while current != GENESIS_HASH and depth < max_depth:
            if current in seen:
                breaks.append({"index": depth, "issue": "cycle_detected"})
                break
            seen.add(current)
            receipt = self._index_by_hash.get(current)
            if not receipt:
                breaks.append({"index": depth, "issue": "missing_receipt"})
                break
            expected_prev = receipt.get("prev_hash", "")
            if expected_prev != GENESIS_HASH and expected_prev not in self._index_by_hash:
                breaks.append({
                    "index": depth,
                    "issue": "parent_not_found",
                    "expected_parent": expected_prev[:16],
                })
            current = expected_prev
            depth += 1
        return {
            "valid": len(breaks) == 0,
            "chain_depth": depth,
            "reaches_genesis": current == GENESIS_HASH,
            "breaks": breaks[:10],
            "head": self.chain_head[:16],
        }

    def get_by_expert(self, expert_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        ids = self._index_by_expert.get(expert_id, [])
        return [self._index_by_id[rid] for rid in ids[-limit:]]

    def get_by_type(self, receipt_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        ids = self._index_by_type.get(receipt_type, [])
        return [self._index_by_id[rid] for rid in ids[-limit:]]

    def get_by_time(self, start_time: float, end_time: float,
                    expert_id: str = None) -> List[Dict[str, Any]]:
        results = []
        for receipt in reversed(self.chain):
            if receipt["created_at"] < start_time:
                continue
            if receipt["created_at"] > end_time:
                continue
            if expert_id and receipt["expert_id"] != expert_id:
                continue
            results.append(receipt)
        return results

    def get_by_hash(self, receipt_hash: str) -> Optional[Dict[str, Any]]:
        return self._index_by_hash.get(receipt_hash)

    def get_by_id(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        return self._index_by_id.get(receipt_id)

    def walk_chain(self, start_hash: str, max_depth: int = 100) -> List[Dict[str, Any]]:
        chain = []
        current = start_hash
        seen = set()
        for _ in range(max_depth):
            if current in seen or current == GENESIS_HASH:
                break
            seen.add(current)
            receipt = self._index_by_hash.get(current)
            if not receipt:
                break
            chain.append(receipt)
            current = receipt["prev_hash"]
        return chain

    def get_stats(self) -> Dict[str, Any]:
        expert_counts = {}
        for r in self.chain:
            expert_counts[r["expert_id"]] = expert_counts.get(r["expert_id"], 0) + 1
        return {
            "total_receipts": len(self.chain),
            "head": self.chain_head[:16],
            "by_type": {t: len(self._index_by_type.get(t, [])) for t in RECEIPT_TYPES},
            "unique_experts": len(self._index_by_expert),
            "unique_hashes": len(self._index_by_hash),
            "total_amount": sum(r["amount"] for r in self.chain),
            "experts": {
                eid: {"receipt_count": cnt, "last_receipt": self.get_by_expert(eid, 1)[0].get("created_at") if self.get_by_expert(eid, 1) else None}
                for eid, cnt in sorted(expert_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            },
        }
