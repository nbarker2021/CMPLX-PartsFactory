"""Bridge MMDB memory events to receipt spine (slot-01)."""
from __future__ import annotations

import os
from typing import Any, Optional


def mmdb_mint_receipt_enabled() -> bool:
    return os.environ.get("MMDB_MINT_RECEIPT", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def mint_mmdb_operation(
    op: str,
    payload: dict[str, Any],
    *,
    receipt_type: Optional[str] = None,
    atom_id: str = "",
) -> None:
    if not mmdb_mint_receipt_enabled():
        return
    from cmplx.receipt.types import ReceiptType

    if receipt_type is None:
        receipt_type = ReceiptType.POST.value if op == "store" else ReceiptType.PROCESS.value

    body = {"mmdb_op": op, **payload}
    operation = f"mmdb_{op}"
    try:
        from cmplx.morphon import MorphonController

        prov = MorphonController.get().get_provider("receipt")
        if prov is not None:
            prov.mint(
                receipt_type=receipt_type,
                atom_id=atom_id or op,
                operation=operation,
                payload=body,
            )
            return
    except Exception:
        pass
    from cmplx.receipt.chain import ReceiptChain

    ReceiptChain().mint(
        receipt_type=receipt_type,
        atom_id=atom_id or op,
        operation=operation,
        payload=body,
    )
