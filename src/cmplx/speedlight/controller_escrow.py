"""
Escrow merge (2026-05-19T00:00:31Z).
Source: ``CMPLX-history/staging/by-family/unclassified/partsfactory/speedlight_controller.py``
Slot: ``slot-04-speedlight-worldline``
"""
from __future__ import annotations
from typing import Any, Dict

from cmplx._adapters._runtime_stubs import BaseController, ControllerContext
from cmplx.receipt.file_ledger import write_receipt, build_receipt_index, verify_ledger
from cmplx._adapters._runtime_stubs import canon_artifacts

class SpeedLightController(BaseController):
    name = "speedlight"

    def run(self, ctx: ControllerContext, params: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure SpeedLight ledger exists for this run.
        ledger_path = ctx.run_dir / "ledger.jsonl"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not ledger_path.exists():
            ledger_path.write_text("", encoding="utf-8")
        # Meta-controller: index + verify (SpeedLight-style observability)
        idx = build_receipt_index(ctx.workspace, ctx.run_id)
        ver = verify_ledger(ctx.workspace, ctx.run_id)

        # IMPORTANT: never hash ledger.jsonl directly inside a receipt that will
        # append to that same ledger. Take a stable snapshot first.
        ledger_snapshot_rel = "speedlight/ledger_snapshot.jsonl"
        ledger_snapshot_path = ctx.run_dir / "artifacts" / ledger_snapshot_rel
        ledger_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_snapshot_path.write_text(ledger_path.read_text(encoding="utf-8"), encoding="utf-8")

        # Canonical artifacts live under ctx.run_dir (runs/<run_id>/...)
        artifacts = canon_artifacts([
            {"path": ledger_snapshot_rel, "role": "speedlight_ledger_snapshot"},
            {"path": "receipt_index.json", "role": "speedlight_index"},
            {"path": "ledger_verify.json", "role": "speedlight_verify"},
        ], base_dir=ctx.run_dir)

        receipt = write_receipt(
            workspace=ctx.workspace,
            run_id=ctx.run_id,
            step_id=ctx.step_id,
            controller=self.name,
            inputs={"params": params},
            outputs={"index_count": len(idx.get("receipts", [])), "verify_ok": ver.get("ok", False)},
            artifacts=artifacts,
            overlays=params.get("overlays"),
            extra={"meta_controller": True},
        )
        return {"receipt": receipt, "index": idx, "verify": ver}
