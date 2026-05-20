"""Geometric Governance — Core CQE invariant engine.

Foundation of all expert operations. Every action must be validated
against registered invariants, recorded as boundary events with
cryptographic receipts, and tracked in the audit trail.
"""

from __future__ import annotations
import hashlib
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any

logger = logging.getLogger("governance")


class CQELawViolationError(Exception):
    """Raised when a CQE fundamental law is violated."""
    pass


class GeometricGovernanceError(Exception):
    """Raised when geometric governance constraints are violated."""
    pass


@dataclass(frozen=True)
class QuadraticInvariant:
    """Represents a quadratic invariant in the CQE system."""
    value: float
    tolerance: float = 1e-10
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_preserved(self, new_value: float) -> bool:
        return abs(self.value - new_value) <= self.tolerance

    def validate_preservation(self, new_value: float) -> None:
        if not self.is_preserved(new_value):
            raise CQELawViolationError(
                f"Quadratic Invariant violated: {self.value} -> {new_value}, "
                f"tolerance: {self.tolerance}"
            )


@dataclass(frozen=True)
class BoundaryEvent:
    """Represents a boundary event with entropy accounting and cryptographic receipt.

    Wave 0.4: ``generate_receipt`` now mints a CROSSING receipt through the
    unified receipt port (``MorphonController.get("receipt")``) when that
    port is registered. Falls back to the legacy local-hash form when the
    port is unregistered so this module remains usable in isolation.

    The return shape is unchanged (dict with the same keys) so existing
    callers are unaffected. ``receipt_hash`` now reflects the unified
    chain hash when port is registered, the legacy local SHA256 otherwise.
    """
    event_id: str
    timestamp: float
    entropy_delta: float
    receipt_data: Dict[str, Any]
    boundary_type: str

    def generate_receipt(self) -> Dict[str, Any]:
        # Try the unified receipt port first.
        unified_hash = self._try_mint_unified()
        if unified_hash is not None:
            return {
                "event_id": self.event_id,
                "timestamp": self.timestamp,
                "entropy_delta": self.entropy_delta,
                "boundary_type": self.boundary_type,
                "receipt_hash": unified_hash,
                "receipt_data": self.receipt_data,
            }
        # Fallback: legacy local hash so this module stays usable when the
        # receipt port hasn't been registered yet (early-boot, tests, etc.).
        receipt_str = f"{self.event_id}{self.timestamp}{self.entropy_delta}{self.boundary_type}"
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "entropy_delta": self.entropy_delta,
            "boundary_type": self.boundary_type,
            "receipt_hash": hashlib.sha256(receipt_str.encode()).hexdigest(),
            "receipt_data": self.receipt_data,
        }

    def _try_mint_unified(self) -> str | None:
        """Mint a CROSSING receipt on the unified ledger; return its hash.

        Returns None if the receipt port isn't registered or minting raises.
        Failures are intentionally swallowed — governance must keep working
        even when cmplx ports aren't wired (e.g., during unit tests that
        don't bootstrap the full controller).
        """
        try:
            from cmplx.morphon import MorphonController
            provider = MorphonController.get().get_provider("receipt")
            receipt = provider.mint_crossing(
                atom_id=self.event_id,
                boundary=self.boundary_type,
                payload={
                    "event_id": self.event_id,
                    "timestamp": self.timestamp,
                    "entropy_delta": self.entropy_delta,
                    "receipt_data": self.receipt_data,
                },
            )
            return getattr(receipt, "receipt_hash", None) or getattr(receipt, "hash", None)
        except Exception:
            return None


class GeometricGovernance:
    """Implements geometric governance principles.
    
    Core engine that:
    - Registers and validates quadratic invariants
    - Records boundary events with entropy accounting
    - Maintains a full audit trail of all operations
    """

    def __init__(self):
        self.invariants: Dict[str, QuadraticInvariant] = {}
        self.boundary_events: List[BoundaryEvent] = []
        self.audit_trail: List[Dict[str, Any]] = []

    def register_invariant(self, name: str, invariant: QuadraticInvariant) -> None:
        self.invariants[name] = invariant
        self.audit_trail.append({
            "action": "register_invariant",
            "invariant_name": name,
            "invariant_value": invariant.value,
            "timestamp": time.time(),
            "status": "registered",
        })

    def validate_operation(self, operation_name: str,
                           invariant_changes: Dict[str, float]) -> bool:
        try:
            for name, new_value in invariant_changes.items():
                if name in self.invariants:
                    self.invariants[name].validate_preservation(new_value)
            self.audit_trail.append({
                "operation": operation_name,
                "timestamp": time.time(),
                "status": "validated",
                "invariant_changes": invariant_changes,
            })
            return True
        except CQELawViolationError as e:
            self.audit_trail.append({
                "operation": operation_name,
                "timestamp": time.time(),
                "status": "violation",
                "error": str(e),
            })
            return False

    def record_boundary_event(self, event: BoundaryEvent) -> None:
        self.boundary_events.append(event)
        receipt = event.generate_receipt()
        self.audit_trail.append({
            "type": "boundary_event",
            "timestamp": time.time(),
            "receipt": receipt,
        })
