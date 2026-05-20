"""Bridge SNAP operations to the unified receipt spine (slot-01)."""
from __future__ import annotations

import os
from typing import Any, Optional


def snap_mint_receipt_enabled() -> bool:
    return os.environ.get("SNAP_MINT_RECEIPT", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def mint_snap_operation(
    op: str,
    payload: dict[str, Any],
    *,
    receipt_type: Optional[str] = None,
    atom_id: str = "",
) -> None:
    """Mint on receipt port when enabled. Frame: POST label, GATE gate fail."""
    if not snap_mint_receipt_enabled():
        return
    from cmplx.receipt.types import ReceiptType

    if receipt_type is None:
        if op == "label":
            receipt_type = ReceiptType.POST.value
        elif op == "gate369" and not payload.get("crystallized", True):
            receipt_type = ReceiptType.GATE.value
        else:
            receipt_type = ReceiptType.PROCESS.value

    body = {"snap_op": op, **payload}
    if "snap_tx_hash" not in body and payload.get("tx_hash"):
        body["snap_tx_hash"] = payload["tx_hash"]
    try:
        from cmplx.morphon import MorphonController

        prov = MorphonController.get().get_provider("receipt")
        if prov is not None:
            prov.mint(
                receipt_type=receipt_type,
                atom_id=atom_id or op,
                operation=f"snap_{op}",
                payload=body,
            )
            return
    except Exception:
        pass
    from cmplx.receipt.chain import ReceiptChain

    ReceiptChain().mint(
        receipt_type=receipt_type,
        atom_id=atom_id or op,
        operation=f"snap_{op}",
        payload=body,
    )
