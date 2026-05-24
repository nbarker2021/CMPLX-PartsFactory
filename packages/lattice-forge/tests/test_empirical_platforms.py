"""Smoke tests for empirical platform manifest and runners."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
SCRIPTS = PKG / "scripts"


def test_materialize_manifest():
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "materialize_empirical_platforms.py")],
        cwd=PKG,
        capture_output=True,
        text=True,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(PKG / "src")},
    )
    assert proc.returncode == 0, proc.stderr
    manifest = PKG / "empirical" / "platforms.manifest.jsonl"
    assert manifest.is_file()
    rows = [json.loads(l) for l in manifest.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) >= 20
    ids = {r["claim_id"] for r in rows}
    assert "T1" in ids
    assert "rule30.prize.depth_only_shortcut" in ids


def test_run_claim_t1_quick():
    subprocess.run(
        [sys.executable, str(SCRIPTS / "materialize_empirical_platforms.py")],
        cwd=PKG,
        check=True,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(PKG / "src")},
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "run_empirical_matrix.py"), "--quick", "--claim", "T1"],
        cwd=PKG,
        capture_output=True,
        text=True,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(PKG / "src")},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "pass" in proc.stdout
