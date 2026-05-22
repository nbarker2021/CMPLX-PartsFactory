"""Bridge Forge overlay operations to the unified receipt spine (slot-01)."""
from __future__ import annotations

import os
from typing import Any, Optional


def forge_mint_receipt_enabled() -> bool:
    return os.environ.get("FORGE_MINT_RECEIPT", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def mint_forge_operation(
    op: str,
    payload: dict[str, Any],
    *,
    receipt_type: Optional[str] = None,
    atom_id: str = "",
) -> None:
    """Mint on receipt port when enabled. Maps verify outcomes to PROCESS/GATE."""
    if not forge_mint_receipt_enabled():
        return
    from cmplx.receipt.types import ReceiptType

    if receipt_type is None:
        status = str(payload.get("status", ""))
        if status == "fail":
            receipt_type = ReceiptType.GATE.value
        elif status.startswith("pass"):
            receipt_type = ReceiptType.PROCESS.value
        else:
            receipt_type = ReceiptType.PROCESS.value

    body = {"forge_op": op, **payload}
    try:
        from cmplx.morphon import MorphonController

        prov = MorphonController.get().get_provider("receipt")
        if prov is not None:
            prov.mint(
                receipt_type=receipt_type,
                atom_id=atom_id or op,
                operation=f"forge_{op}",
                payload=body,
            )
            return
    except Exception:
        pass
    from cmplx.receipt.chain import ReceiptChain

    ReceiptChain().mint(
        receipt_type=receipt_type,
        atom_id=atom_id or op,
        operation=f"forge_{op}",
        payload=body,
    )
