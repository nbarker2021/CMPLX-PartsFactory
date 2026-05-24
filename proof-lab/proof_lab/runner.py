"""Subprocess runners for proven (library) validation."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.environ.get("PROOF_LAB_ROOT", Path(__file__).resolve().parents[2]))
PKG = ROOT / "packages" / "lattice-forge"
ARTIFACTS = ROOT / "proof-lab" / "artifacts"


@dataclass
class StepResult:
    name: str
    ok: bool
    exit_code: int
    detail: str = ""


def _run(cmd: list[str], *, cwd: Path | None = None) -> StepResult:
    name = cmd[0] if cmd else "empty"
    proc = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
    )
    detail = (proc.stdout or "")[-4000:] + (proc.stderr or "")[-2000:]
    return StepResult(name=name, ok=proc.returncode == 0, exit_code=proc.returncode, detail=detail)


def run_pytest() -> StepResult:
    return _run(
        [
            "python",
            "-m",
            "pytest",
            str(PKG / "tests"),
            str(ROOT / "tests" / "worlds" / "test_forge_provider.py"),
            "-q",
            "--tb=short",
        ],
    )


def run_proofs_quick() -> StepResult:
    report = PKG / "proofs_report.json"
    return _run(
        ["python", str(PKG / "scripts" / "run_all_proofs.py"), "--quick", "--output", str(report)],
        cwd=PKG,
    )


def run_falsify_tier_a(*, quick: bool = True) -> StepResult:
    cmd = ["lattice-forge", "falsify", "--tier-a"]
    if quick:
        cmd.append("--quick")
    return _run(cmd)


def regression_check() -> StepResult:
    report_path = PKG / "proofs_report.json"
    expected_path = PKG / "expected_outputs.json"
    if not report_path.is_file() or not expected_path.is_file():
        return StepResult("regression", False, 1, "missing proofs_report or expected_outputs")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    mismatches: list[str] = []
    for key, exp in expected.get("expected_proofs", {}).items():
        act = report.get("proofs", {}).get(key)
        if not act:
            mismatches.append(f"{key} missing")
            continue
        if exp.get("status") and act.get("status") != exp.get("status"):
            mismatches.append(f"{key} status {act.get('status')} != {exp.get('status')}")
    if report.get("overall_status") != "pass":
        mismatches.append("overall_status not pass")
    return StepResult(
        "regression",
        not mismatches,
        0 if not mismatches else 1,
        "; ".join(mismatches) or "ok",
    )


def run_formal_bundle() -> dict:
    steps = [run_pytest(), run_proofs_quick(), regression_check(), run_falsify_tier_a()]
    return {
        "ok": all(s.ok for s in steps),
        "steps": [{"name": s.name, "ok": s.ok, "exit_code": s.exit_code, "detail": s.detail} for s in steps],
    }
