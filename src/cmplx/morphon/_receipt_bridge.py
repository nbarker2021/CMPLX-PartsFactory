"""Bridge Morphon lifecycle to unified receipt spine (slot-01)."""
from __future__ import annotations

import os
from typing import Any, Optional


def morphon_mint_receipt_enabled() -> bool:
    return os.environ.get("MORPHON_MINT_RECEIPT", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def mint_morphon_event(
    event: str,
    *,
    morphon_id: str = "",
    receipt_type: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
) -> None:
    """Mint on receipt port when enabled (BIRTH / CROSSING / ASSIGN / GATE)."""
    if not morphon_mint_receipt_enabled():
        return
    from cmplx.receipt.types import ReceiptType

    if receipt_type is None:
        mapping = {
            "forge": ReceiptType.BIRTH.value,
            "transition": ReceiptType.CROSSING.value,
            "evolved_from": ReceiptType.BIRTH.value,
            "register": ReceiptType.ASSIGN.value,
            "gate_miss": ReceiptType.GATE.value,
            "admit_and_store": ReceiptType.PROCESS.value,
            "link_tarpit": ReceiptType.BOND.value,
            "combine": ReceiptType.BIRTH.value,
            "store": ReceiptType.PROCESS.value,
        }
        receipt_type = mapping.get(event, ReceiptType.PROCESS.value)

    body = {"morphon_event": event, **(detail or {})}
    try:
        from cmplx.morphon.controller import MorphonController

        prov = MorphonController.get().get_provider("receipt")
        if prov is not None:
            prov.mint(
                receipt_type=receipt_type,
                atom_id=morphon_id or event,
                operation=f"morphon_{event}",
                payload=body,
            )
            return
    except LookupError:
        pass
    except Exception:
        pass
    from cmplx.receipt.chain import ReceiptChain

    ReceiptChain().mint(
        receipt_type=receipt_type,
        atom_id=morphon_id or event,
        operation=f"morphon_{event}",
        payload=body,
    )
