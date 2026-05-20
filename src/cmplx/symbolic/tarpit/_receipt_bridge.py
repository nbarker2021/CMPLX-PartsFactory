"""Bridge TarPit operations to the unified receipt spine (slot-01)."""
from __future__ import annotations

import os
from typing import Any, Optional


def tarpit_mint_receipt_enabled() -> bool:
    return os.environ.get("TARPIT_MINT_RECEIPT", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def mint_tarpit_operation(
    op: str,
    payload: dict[str, Any],
    *,
    receipt_type: Optional[str] = None,
    atom_id: str = "",
) -> None:
    """Mint on receipt port when enabled. Frame: BIRTH/BOND/CROSSING + ETP steps."""
    if not tarpit_mint_receipt_enabled():
        return
    from cmplx.receipt.types import ReceiptType

    if receipt_type is None:
        mapping = {
            "grain": ReceiptType.BIRTH.value,
            "bond": ReceiptType.BOND.value,
            "triad": ReceiptType.BOND.value,
            "mirror": ReceiptType.CROSSING.value,
            "etp_step": ReceiptType.PROCESS.value,
        }
        receipt_type = mapping.get(op, ReceiptType.PROCESS.value)
        if op == "etp_step":
            if payload.get("error_class"):
                receipt_type = ReceiptType.DEATH.value
            elif not payload.get("envelope_ok", True):
                receipt_type = ReceiptType.GATE.value

    body = {"tarpit_op": op, **payload}
    try:
        from cmplx.morphon import MorphonController

        prov = MorphonController.get().get_provider("receipt")
        if prov is not None:
            prov.mint(
                receipt_type=receipt_type,
                atom_id=atom_id or op,
                operation=f"tarpit_{op}",
                payload=body,
            )
            return
    except Exception:
        pass
    from cmplx.receipt.chain import ReceiptChain

    ReceiptChain().mint(
        receipt_type=receipt_type,
        atom_id=atom_id or op,
        operation=f"tarpit_{op}",
        payload=body,
    )
