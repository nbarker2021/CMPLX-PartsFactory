"""Run JSONL ledger tests — _persistence/jsonl_run_ledger + ReceiptChain facade."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from cmplx.receipt import ReceiptChain
from cmplx.receipt._persistence import hmac_run, jsonl_run_ledger


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    os.environ["CQE_DETERMINISTIC_TIME"] = "1"
    (tmp_path / "schemas").mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_write_run_receipt_roundtrip(workspace: Path):
    chain = ReceiptChain()
    rec = chain.write_run_receipt(
        workspace,
        run_id="run1",
        step_id="s1",
        controller="test_ctrl",
        inputs={"a": 1},
        outputs={"b": 2},
        artifacts=[],
    )
    assert rec["run_id"] == "run1"
    ledger = workspace / "runs" / "run1" / "ledger.jsonl"
    assert ledger.exists()
    lines = ledger.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["receipt_hash"] == rec["receipt_hash"]


def test_verify_run_ledger_ok(workspace: Path):
    chain = ReceiptChain()
    chain.write_run_receipt(
        workspace,
        run_id="run2",
        step_id="s1",
        controller="ctrl",
        inputs={},
        outputs={},
        artifacts=[],
    )
    report = chain.verify_run_ledger(workspace, "run2")
    assert report["ok"] is True


def test_verify_run_ledger_detects_break(workspace: Path):
    chain = ReceiptChain()
    chain.write_run_receipt(
        workspace,
        run_id="run3",
        step_id="s1",
        controller="ctrl",
        inputs={},
        outputs={},
        artifacts=[],
    )
    ledger = workspace / "runs" / "run3" / "ledger.jsonl"
    lines = ledger.read_text(encoding="utf-8").splitlines()
    bad = json.loads(lines[0])
    bad["receipt_hash"] = "0" * 64
    ledger.write_text(json.dumps(bad) + "\n", encoding="utf-8")
    report = chain.verify_run_ledger(workspace, "run3")
    assert report["ok"] is False


def test_hmac_ledger_roundtrip(tmp_path: Path):
    key = hmac_run.new_key_b64()
    ledger = hmac_run.ReceiptLedger(str(tmp_path / "hmac"), key)
    ledger.append({"op": "test", "n": 1})
    ledger.append({"op": "test", "n": 2})
    result = ledger.verify()
    assert result["ok"] is True
    assert result["count"] == 2


def test_jsonl_module_direct(workspace: Path):
    rec = jsonl_run_ledger.write_receipt(
        workspace,
        run_id="direct",
        step_id="s0",
        controller="ctrl",
        inputs={},
        outputs={},
        artifacts=[],
    )
    assert "receipt_id" in rec
