"""
Escrow merge (2026-05-19T00:00:31Z).
Source: ``CMPLX-history/staging/by-family/unclassified/partsfactory/speedlight_controller.py``
Slot: ``slot-04-speedlight-worldline``
"""
from __future__ import annotations

from typing import Any, Dict

from cmplx._adapters._runtime_stubs import BaseController, ControllerContext, canon_artifacts
from cmplx.receipt.chain import ReceiptChain
from cmplx.receipt._persistence.jsonl_run_ledger import build_receipt_index, verify_ledger


class SpeedLightController(BaseController):
    name = "speedlight"

    def run(self, ctx: ControllerContext, params: Dict[str, Any]) -> Dict[str, Any]:
        chain = ReceiptChain()
        ledger_path = ctx.run_dir / "ledger.jsonl"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not ledger_path.exists():
            ledger_path.write_text("", encoding="utf-8")

        ledger_snapshot_rel = "speedlight/ledger_snapshot.jsonl"
        ledger_snapshot_path = ctx.run_dir / "artifacts" / ledger_snapshot_rel
        ledger_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_snapshot_path.write_text(ledger_path.read_text(encoding="utf-8"), encoding="utf-8")

        artifacts = canon_artifacts([
            {"path": ledger_snapshot_rel, "role": "speedlight_ledger_snapshot"},
        ])

        receipt = chain.write_run_receipt(
            workspace=ctx.workspace,
            run_id=ctx.run_id,
            step_id=ctx.step_id,
            controller=self.name,
            inputs={"params": params},
            outputs={"controller_run": True},
            artifacts=artifacts,
            overlays=params.get("overlays"),
            extra={"meta_controller": True},
        )
        idx = build_receipt_index(ctx.workspace, ctx.run_id)
        ver = verify_ledger(ctx.workspace, ctx.run_id)
        return {"receipt": receipt, "index": idx, "verify": ver}
