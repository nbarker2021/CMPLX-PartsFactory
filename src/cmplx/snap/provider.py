"""
SNAPEngine — the `snap` port provider.

Bundles the four SNAP subsystems (Labeler, LensBank, Gate369Engine,
Ledger) and exposes a single point that auto-receipts the operations
it runs:

  - `engine.label(item, key)` → records `op=label`
  - `engine.process_gate369(bodies, predicates)` → records
    `op=gate369` with the ennead containment metric
  - `engine.crystallize(ennead)` → records `op=crystallize` (the moment
    a sufficiently-contained ennead is ready to mint a Crystal)

Consumers may bypass the engine and use the subsystems directly — but
they then lose the ledger entry for that step.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .gate369 import Body, EnneadPackage, Gate369Engine, Predicate
from .label import SNAPLabel
from .labeler import SNAPLabeler
from ._receipt_bridge import mint_snap_operation
from .ledger import SNAPLedger, SNAPTransaction
from .lenses import LensBank


class SNAPEngine:
    """The composite SNAP provider.

    Register on the `snap` port:
        MorphonController.get().register("snap", SNAPEngine())
    """

    name: str = "snap_engine"

    def __init__(
        self,
        labeler: Optional[SNAPLabeler] = None,
        lens_bank: Optional[LensBank] = None,
        ledger: Optional[SNAPLedger] = None,
    ) -> None:
        self.labeler = labeler or SNAPLabeler()
        self.lens_bank = lens_bank or LensBank()
        self.gate369 = Gate369Engine(lens_bank=self.lens_bank)
        self.ledger = ledger or SNAPLedger()

    # ── Operations (with ledger receipts) ─────────────────────────────

    def label(self, item: Any, key: str = "",
              context: Optional[dict] = None) -> SNAPLabel:
        result = self.labeler.label(item, key, context)
        payload = {
            "item_key": result.item_key,
            "label_count": len(result.all_labels),
        }
        tx = self.ledger.append("label", payload)
        mint_snap_operation(
            "label", {**payload, "tx_hash": tx.hash}, atom_id=result.item_key
        )
        return result

    def process_gate369(
        self,
        bodies: list[Body],
        predicates: list[Predicate],
        state: Optional[dict] = None,
    ) -> dict:
        trace = self.gate369.process(bodies, predicates, state)
        payload = {
            "triad_size": len(trace["triad"]["members"]),
            "hexad_size": len(trace["hexad"]),
            "ennead_facets": len(trace["ennead"]["facets"]),
            "containment_c": trace["ennead"]["containment_c"],
            "crystallized": trace["ennead"]["crystallized"],
        }
        tx = self.ledger.append("gate369", payload)
        mint_snap_operation("gate369", {**payload, "tx_hash": tx.hash})
        return trace

    def crystallize(self, ennead: EnneadPackage) -> SNAPTransaction:
        """Record that an ennead reached crystallization threshold.

        Returns the ledger transaction. The caller can then mint a
        `Crystal` via the `crystal` port (this engine does not do that
        directly to keep the dependency direction crystal → snap, not
        snap → crystal).
        """
        payload = {
            "facets": [b.id for b in ennead.facets],
            "containment_c": ennead.containment_c,
            "lens": ennead.lens_name,
            "reversible": ennead.reversibility,
            "crystallized": ennead.containment_c > 0.7,
        }
        tx = self.ledger.append("crystallize", payload)
        mint_snap_operation("crystallize", {**payload, "tx_hash": tx.hash})
        return tx

    def mint_run_snapshot(
        self,
        workspace: Path,
        run_id: str,
        step_id: str,
        *,
        inputs: Optional[dict] = None,
        mirror_to_receipt_port: bool = True,
    ) -> dict:
        """Persist run-level snapshot via receipt spine JSONL ledger."""
        from cmplx.receipt.chain import ReceiptChain

        outputs = {
            "ledger_length": self.ledger.length,
            "ledger_head": self.ledger.head,
            "ledger_ok": self.ledger.verify(),
        }
        run_receipt = ReceiptChain().write_run_receipt(
            workspace=workspace,
            run_id=run_id,
            step_id=step_id,
            controller="snap",
            inputs=inputs or {},
            outputs=outputs,
            artifacts=[],
            extra={"snapshot": True, "snap_entries": self.ledger.to_dict_list()},
        )
        if mirror_to_receipt_port:
            mint_snap_operation(
                "run_snapshot",
                outputs,
                receipt_type="PROCESS",
                atom_id=run_id,
            )
        return run_receipt

    def ledger_export(self) -> dict:
        return {
            "length": self.ledger.length,
            "head": self.ledger.head,
            "verified": self.ledger.verify(),
            "entries": self.ledger.to_dict_list(),
        }

    # ── Reporting ─────────────────────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": "snap_engine",
            "rules": self.labeler.rule_count,
            "lenses": len(self.lens_bank.names()),
            "ledger_length": self.ledger.length,
        }

    def __repr__(self) -> str:
        return (
            f"<SNAPEngine rules={self.labeler.rule_count} "
            f"lenses={len(self.lens_bank.names())} "
            f"ledger={self.ledger.length}>"
        )
