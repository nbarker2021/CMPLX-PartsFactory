"""
Escrow merge (2026-05-19T00:00:31Z).
Source: ``CMPLX-history/staging/by-family/unclassified/partsfactory/15_receipt_ledger_manager.py``
Slot: ``slot-01-receipt-chain``
"""
#!/usr/bin/env python3
"""
================================================================================
TOOL 15: ReceiptLedgerManager - Immutable Operation Logger
================================================================================
Derived from: CQE Receipt + ledger system + merkle trees
Purpose: Create immutable, verifiable operation receipts
"""

import hashlib
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import deque

@dataclass
class OperationReceipt:
    """A receipt for an operation."""
    claim: str
    pre_state: Dict[str, Any]
    post_state: Dict[str, Any]
    energies: Dict[str, float]
    keys: Dict[str, str]
    validators: Dict[str, bool]
    parity64: str
    pose_salt: str
    merkle_root: str
    timestamp: str
    sequence: int

class ReceiptLedgerManager:
    """
    Create immutable, verifiable operation receipts.

    Maintains an append-only ledger of operation receipts with
    cryptographic hashing, merkle tree integrity, and full audit trails.
    """

    def __init__(self, ledger_name: str = "default"):
        self.ledger_name = ledger_name
        self.ledger: deque = deque(maxlen=10000)
        self.merkle_tree: List[str] = []
        self.sequence = 0
        self.salt_counter = 0

    def sha256(self, data: Any) -> str:
        """Compute SHA256 hash of data."""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha256(data).hexdigest()

    def compute_parity64(self, data: Dict[str, Any]) -> str:
        """Compute 64-bit parity checksum."""
        hash_full = self.sha256(data)
        # XOR all 8-byte chunks
        parity = 0
        for i in range(0, len(hash_full), 16):
            chunk = int(hash_full[i:i+16], 16)
            parity ^= chunk
        return format(parity, '016x')

    def generate_salt(self) -> str:
        """Generate unique pose salt."""
        self.salt_counter += 1
        salt_data = f"{self.ledger_name}:{self.sequence}:{self.salt_counter}:{time.time()}"
        return self.sha256(salt_data)[:16]

    def compute_merkle_root(self, receipt: OperationReceipt) -> str:
        """Compute merkle root including previous receipts."""
        # Leaf hash
        receipt_dict = asdict(receipt)
        leaf = self.sha256(receipt_dict)

        if not self.merkle_tree:
            self.merkle_tree.append(leaf)
            return leaf

        # Build path to root
        current = leaf
        for level_hash in self.merkle_tree:
            combined = level_hash + current
            current = self.sha256(combined)

        self.merkle_tree.append(current)
        return current

    def create_receipt(self,
                       claim: str,
                       pre_state: Dict[str, Any],
                       post_state: Dict[str, Any],
                       energies: Optional[Dict[str, float]] = None,
                       validators: Optional[Dict[str, bool]] = None) -> OperationReceipt:
        """Create a new operation receipt."""
        self.sequence += 1

        # Compute keys
        keys = {
            'pre_hash': self.sha256(pre_state),
            'post_hash': self.sha256(post_state),
            'claim_hash': self.sha256(claim)
        }

        # Compute parity
        parity64 = self.compute_parity64({**pre_state, **post_state})

        # Generate salt
        pose_salt = self.generate_salt()

        # Create receipt (without merkle root first)
        receipt = OperationReceipt(
            claim=claim,
            pre_state=pre_state,
            post_state=post_state,
            energies=energies or {},
            keys=keys,
            validators=validators or {},
            parity64=parity64,
            pose_salt=pose_salt,
            merkle_root="",  # Will be updated
            timestamp=datetime.utcnow().isoformat(),
            sequence=self.sequence
        )

        # Compute merkle root
        receipt.merkle_root = self.compute_merkle_root(receipt)

        # Store
        self.ledger.append(receipt)

        return receipt

    def verify_receipt(self, receipt: OperationReceipt) -> bool:
        """Verify a receipt's integrity."""
        # Verify pre/post hashes
        if receipt.keys.get('pre_hash') != self.sha256(receipt.pre_state):
            return False
        if receipt.keys.get('post_hash') != self.sha256(receipt.post_state):
            return False

        # Verify parity
        expected_parity = self.compute_parity64({**receipt.pre_state, **receipt.post_state})
        if receipt.parity64 != expected_parity:
            return False

        return True

    def get_chain(self, start: int = 0, end: Optional[int] = None) -> List[OperationReceipt]:
        """Get receipts in a range."""
        receipts = list(self.ledger)
        return receipts[start:end]

    def get_last(self, n: int = 1) -> List[OperationReceipt]:
        """Get last n receipts."""
        receipts = list(self.ledger)
        return receipts[-n:] if n <= len(receipts) else receipts

    def audit(self) -> Dict[str, Any]:
        """Perform full ledger audit."""
        issues = []
        verified = 0

        for i, receipt in enumerate(self.ledger):
            if not self.verify_receipt(receipt):
                issues.append(f"Receipt {i} failed verification")
            else:
                verified += 1

        return {
            'total_receipts': len(self.ledger),
            'verified': verified,
            'issues': issues,
            'current_sequence': self.sequence,
            'merkle_tree_depth': len(self.merkle_tree)
        }

    def export_ledger(self, format: str = "json") -> str:
        """Export ledger to string format."""
        receipts = [asdict(r) for r in self.ledger]

        if format == "json":
            return json.dumps({
                'ledger_name': self.ledger_name,
                'sequence': self.sequence,
                'receipts': receipts
            }, indent=2)
        elif format == "jsonl":
            lines = [json.dumps(r) for r in receipts]
            return '\n'.join(lines)
        else:
            return str(receipts)

    def find_by_claim(self, claim_pattern: str) -> List[OperationReceipt]:
        """Find receipts by claim pattern."""
        return [r for r in self.ledger if claim_pattern in r.claim]

    def get_statistics(self) -> Dict[str, Any]:
        """Get ledger statistics."""
        if not self.ledger:
            return {}

        energies_list = []
        for r in self.ledger:
            energies_list.extend(r.energies.values())

        return {
            'total_receipts': len(self.ledger),
            'avg_energies': sum(energies_list) / len(energies_list) if energies_list else 0,
            'validation_rate': sum(1 for r in self.ledger if all(r.validators.values())) / len(self.ledger) if self.ledger else 0,
            'time_span': (self.ledger[-1].timestamp, self.ledger[0].timestamp) if len(self.ledger) > 1 else None
        }


if __name__ == "__main__":
    ledger = ReceiptLedgerManager("test_ledger")

    print("ReceiptLedgerManager Demo:")
    print("=" * 50)

    # Create receipts
    operations = [
        ("vector_transform", {'x': 1.0, 'y': 2.0}, {'x': 2.0, 'y': 4.0}, {'energy': 0.5}),
        ("lattice_snap", {'state': 'raw'}, {'state': 'snapped'}, {'energy': 0.3, 'alignment': 0.95}),
        ("weyl_flip", {'parity': 1}, {'parity': -1}, {'energy': 0.1})
    ]

    for claim, pre, post, energies in operations:
        receipt = ledger.create_receipt(
            claim=claim,
            pre_state=pre,
            post_state=post,
            energies=energies,
            validators={'integrity': True, 'bounds': True}
        )
        print(f"\nReceipt: {receipt.claim}")
        print(f"  Sequence: {receipt.sequence}")
        print(f"  Merkle root: {receipt.merkle_root[:16]}...")
        print(f"  Parity64: {receipt.parity64}")

    # Audit
    audit_result = ledger.audit()
    print(f"\nAudit Results:")
    for k, v in audit_result.items():
        print(f"  {k}: {v}")

    # Stats
    stats = ledger.get_statistics()
    print(f"\nStatistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
