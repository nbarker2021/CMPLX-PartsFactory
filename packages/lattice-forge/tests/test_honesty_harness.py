"""Smoke tests for honesty promotion harness."""

from __future__ import annotations

from lattice_forge.honesty_harness import run_open_claims_harness


def test_open_claims_harness_quick_passes():
    report = run_open_claims_harness(128, quick=True)
    assert report["overall_status"] == "pass"
    assert len(report["promotions"]) >= 3
    assert "rule30.prize.depth_only_shortcut" in report["still_conj"]
