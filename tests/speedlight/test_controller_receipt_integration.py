"""Controller + receipt spine integration for slot-04."""
from __future__ import annotations

from pathlib import Path

import pytest

from cmplx._adapters._runtime_stubs import ControllerContext
from cmplx.speedlight.controller_escrow import SpeedLightController


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "runs" / "run-1").mkdir(parents=True)
    return ws


def test_controller_writes_run_receipt_via_chain(workspace: Path, tmp_path: Path):
    run_dir = workspace / "runs" / "run-1"
    ctx = ControllerContext(workspace, "run-1", run_dir, step_id="s0")
    out = SpeedLightController().run(ctx, {"overlays": {}})
    receipt = out["receipt"]
    assert receipt.get("receipt_hash")
    assert receipt.get("controller") == "speedlight"
    ledger = run_dir / "ledger.jsonl"
    assert ledger.exists()
    assert ledger.read_text(encoding="utf-8").strip()
    assert out["index"].get("receipts")
    assert "ok" in out["verify"]
