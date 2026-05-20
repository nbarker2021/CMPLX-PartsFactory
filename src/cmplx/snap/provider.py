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

from typing import Any, Optional

from .gate369 import Body, EnneadPackage, Gate369Engine, Predicate
from .label import SNAPLabel
from .labeler import SNAPLabeler
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
        self.ledger.append("label", {
            "item_key": result.item_key,
            "label_count": len(result.all_labels),
        })
        return result

    def process_gate369(
        self,
        bodies: list[Body],
        predicates: list[Predicate],
        state: Optional[dict] = None,
    ) -> dict:
        trace = self.gate369.process(bodies, predicates, state)
        self.ledger.append("gate369", {
            "triad_size": len(trace["triad"]["members"]),
            "hexad_size": len(trace["hexad"]),
            "ennead_facets": len(trace["ennead"]["facets"]),
            "containment_c": trace["ennead"]["containment_c"],
            "crystallized": trace["ennead"]["crystallized"],
        })
        return trace

    def crystallize(self, ennead: EnneadPackage) -> SNAPTransaction:
        """Record that an ennead reached crystallization threshold.

        Returns the ledger transaction. The caller can then mint a
        `Crystal` via the `crystal` port (this engine does not do that
        directly to keep the dependency direction crystal → snap, not
        snap → crystal).
        """
        return self.ledger.append("crystallize", {
            "facets": [b.id for b in ennead.facets],
            "containment_c": ennead.containment_c,
            "lens": ennead.lens_name,
            "reversible": ennead.reversibility,
        })

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
