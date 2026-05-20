"""
Wave 0.3 + 0.4 tests — wallet receipts and governance BoundaryEvent migration
to the unified receipt port.

Verifies:
  0.3:
    - ReceiptLedger.record() returns a dict in the legacy shape.
    - When `receipt` port is registered, the dict's `receipt_hash` is the
      unified chain hash (not the legacy local SHA-256).
    - When `receipt` port is unregistered, the ledger falls back to the
      legacy local SHA-256 chain (existing tests don't break).
    - MintService.__init__ accepts governance=None.
    - Wallet operations work without a governance instance.
  0.4:
    - BoundaryEvent.generate_receipt() returns a dict in the legacy shape.
    - When `receipt` port is registered, the dict's `receipt_hash` is the
      unified chain hash.
    - When `receipt` port is unregistered, it returns the legacy local hash.
    - The chain length on the receipt port grows after each BoundaryEvent
      receipt is generated.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from runtime.cmplx_bootstrap import register_all


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# Wave 0.4: BoundaryEvent.generate_receipt routes through receipt port
# ---------------------------------------------------------------------------

def test_boundary_event_falls_back_when_receipt_port_unregistered():
    """When no receipt port → legacy local SHA-256 hash."""
    from governance.engine import BoundaryEvent
    event = BoundaryEvent(
        event_id="test_event",
        timestamp=1234567890.0,
        entropy_delta=0.1,
        receipt_data={"key": "value"},
        boundary_type="test_boundary",
    )
    receipt = event.generate_receipt()
    assert "receipt_hash" in receipt
    assert receipt["event_id"] == "test_event"
    assert receipt["boundary_type"] == "test_boundary"
    # Legacy hash is just SHA256 of concatenated fields.
    import hashlib
    expected = hashlib.sha256(
        f"{event.event_id}{event.timestamp}{event.entropy_delta}{event.boundary_type}".encode()
    ).hexdigest()
    assert receipt["receipt_hash"] == expected


def test_boundary_event_mints_via_receipt_port_when_registered():
    """When receipt port is registered → unified chain hash."""
    register_all()
    receipt_provider = MorphonController.get().get_provider("receipt")
    chain_length_before = receipt_provider.length

    from governance.engine import BoundaryEvent
    event = BoundaryEvent(
        event_id="test_event",
        timestamp=1234567890.0,
        entropy_delta=0.1,
        receipt_data={"key": "value"},
        boundary_type="test_boundary",
    )
    receipt = event.generate_receipt()

    # Chain grew by exactly one.
    assert receipt_provider.length == chain_length_before + 1
    # The receipt's hash is reachable via the receipt port.
    found = receipt_provider.by_hash(receipt["receipt_hash"])
    assert found is not None
    assert found.atom_id == "test_event"


def test_governance_record_boundary_event_still_works_after_unified_routing():
    """Existing GeometricGovernance.record_boundary_event path still functions."""
    register_all()
    from governance.engine import GeometricGovernance, BoundaryEvent
    gov = GeometricGovernance()
    event = BoundaryEvent(
        event_id="evt_1",
        timestamp=1234567890.0,
        entropy_delta=0.05,
        receipt_data={},
        boundary_type="audit",
    )
    gov.record_boundary_event(event)
    assert len(gov.boundary_events) == 1
    assert len(gov.audit_trail) == 1


# ---------------------------------------------------------------------------
# Wave 0.3: ReceiptLedger routes through receipt port
# ---------------------------------------------------------------------------

def test_receipt_ledger_record_returns_legacy_dict_shape():
    from wallet.receipts import ReceiptLedger
    ledger = ReceiptLedger()
    receipt = ledger.record(
        expert_id="expert_1",
        receipt_type="MINT",
        amount=50.0,
        operation="create_expert",
    )
    # Legacy dict keys preserved
    for key in (
        "receipt_id", "receipt_hash", "receipt_type", "expert_id",
        "amount", "operation", "prev_hash", "chain_index", "created_at"
    ):
        assert key in receipt
    assert receipt["receipt_type"] == "MINT"
    assert receipt["amount"] == 50.0


def test_receipt_ledger_uses_unified_port_when_registered():
    register_all()
    from wallet.receipts import ReceiptLedger
    receipt_provider = MorphonController.get().get_provider("receipt")
    chain_before = receipt_provider.length

    ledger = ReceiptLedger()
    receipt = ledger.record(
        expert_id="expert_1",
        receipt_type="MINT",
        amount=50.0,
        operation="create_expert",
    )

    # The unified chain grew by one.
    assert receipt_provider.length == chain_before + 1
    # The receipt hash returned is reachable via the unified port.
    found = receipt_provider.by_hash(receipt["receipt_hash"])
    assert found is not None
    assert found.agent_id == "expert_1"


def test_wallet_record_uses_unified_port():
    """Port path sets payload.wallet_op (completion pass 2026-05-21)."""
    register_all()
    from wallet.receipts import ReceiptLedger

    ledger = ReceiptLedger()
    ledger.record(
        expert_id="expert_wallet",
        receipt_type="SPEND",
        amount=3.0,
        operation="pay",
    )
    provider = MorphonController.get().get_provider("receipt")
    recent = provider.chain.recent(limit=1)
    assert recent
    assert recent[0].payload.get("wallet_op") == "SPEND"
    assert recent[0].payload.get("amount") == 3.0


def test_receipt_ledger_falls_back_to_legacy_chain_without_port():
    """When `receipt` port isn't registered, ReceiptLedger keeps working
    with a local SHA-256 chain (matches pre-Wave-0.3 behavior)."""
    from wallet.receipts import ReceiptLedger, GENESIS_HASH
    ledger = ReceiptLedger()
    r1 = ledger.record(expert_id="e1", receipt_type="MINT", amount=10.0, operation="op")
    r2 = ledger.record(expert_id="e1", receipt_type="EARN", amount=5.0, operation="op")
    assert r1["prev_hash"] == GENESIS_HASH
    assert r2["prev_hash"] == r1["receipt_hash"]
    assert ledger.chain_head == r2["receipt_hash"]


def test_receipt_ledger_rejects_invalid_type():
    from wallet.receipts import ReceiptLedger
    ledger = ReceiptLedger()
    with pytest.raises(ValueError, match="Invalid receipt type"):
        ledger.record(
            expert_id="e1",
            receipt_type="NOT_A_REAL_TYPE",
            amount=1.0,
            operation="op",
        )


def test_receipt_ledger_indexes_by_expert_and_type():
    from wallet.receipts import ReceiptLedger
    ledger = ReceiptLedger()
    ledger.record(expert_id="e1", receipt_type="MINT", amount=10.0, operation="op1")
    ledger.record(expert_id="e1", receipt_type="EARN", amount=5.0, operation="op2")
    ledger.record(expert_id="e2", receipt_type="MINT", amount=20.0, operation="op3")

    e1_receipts = ledger.get_by_expert("e1")
    assert len(e1_receipts) == 2

    mint_receipts = ledger.get_by_type("MINT")
    assert len(mint_receipts) == 2


# ---------------------------------------------------------------------------
# Wave 0.3b: MintService accepts governance=None (signature-only test)
# ---------------------------------------------------------------------------

def test_mint_service_constructor_accepts_governance_none():
    """MintService init signature accepts governance=None.

    Full end-to-end mint_tokens tests require an ExpertWallet SQLite setup
    that's beyond Wave 0.3's scope; the signature check + the receipts-side
    tests above are sufficient for this gate.
    """
    from wallet.mint import MintService
    # No wallet, no governance — just verify __init__ accepts these.
    mint = MintService(governance=None, wallet=None)
    assert mint.governance is None
    assert mint.wallet is None


def test_mint_service_init_skips_invariant_registration_when_governance_none():
    """Without governance, MintService.__init__ shouldn't try to register
    invariants on a None object."""
    from wallet.mint import MintService
    # If governance is None and code is broken, init raises AttributeError.
    # Success here = init returned without exception.
    mint = MintService(governance=None, wallet=None)
    assert mint._invariant_token == "total_supply_invariant"
