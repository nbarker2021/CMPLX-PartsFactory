"""
Calibration target smoke tests.

Each of the 5 calibration targets must produce a non-empty receipt set and
maintain a stable pass rate. These tests run all targets and assert their
expected outcomes, locking in the G5 calibration suite as a regression net.
"""
from __future__ import annotations

import pytest

from calibration.targets.economic_phase_boundary import EconomicPhaseBoundaryCalibration
from calibration.targets.hundred_form_transition import HundredFormTransitionCalibration
from calibration.targets.quorum_consensus import QuorumConsensusCalibration
from calibration.targets.triadic_morphon import TriadicMorphonCalibration
from calibration.targets.wolfram_poc import WolframPocCalibration


def _override_ledger_dir(monkeypatch, tmp_path):
    from calibration import ledger as ledger_module
    monkeypatch.setattr(ledger_module, "_default_base_dir", lambda: tmp_path)


# Each row: (TargetClass, expected_claim_count, expected_pass_count)
# Updated as targets evolve; failures here are regressions.
_TARGETS = [
    (WolframPocCalibration, 7, 7),
    (QuorumConsensusCalibration, 6, 6),
    (EconomicPhaseBoundaryCalibration, 7, 7),
    (TriadicMorphonCalibration, 8, 8),
    (HundredFormTransitionCalibration, 7, 7),
]


@pytest.mark.parametrize(
    "target_class, expected_total, expected_passed",
    _TARGETS,
    ids=[t[0].target_name for t in _TARGETS],
)
def test_target_runs_and_passes_expected_claim_count(
    target_class, expected_total, expected_passed, tmp_path, monkeypatch,
):
    _override_ledger_dir(monkeypatch, tmp_path)
    target = target_class()
    result = target.run()
    assert result.total_claims == expected_total, (
        f"{target.target_name}: expected {expected_total} claims, "
        f"got {result.total_claims}"
    )
    assert result.passed_claims == expected_passed, (
        f"{target.target_name}: expected {expected_passed} passes, "
        f"got {result.passed_claims}. Per-claim: {result.summary_per_claim}"
    )
    assert result.ledger_path  # ledger persisted


def test_all_targets_together_pass(tmp_path, monkeypatch):
    """End-to-end: every target's claims pass against our substrate."""
    _override_ledger_dir(monkeypatch, tmp_path)
    results = []
    for target_class, _, _ in _TARGETS:
        results.append(target_class().run())

    total_claims = sum(r.total_claims for r in results)
    total_passed = sum(r.passed_claims for r in results)
    assert total_claims > 0
    assert total_passed == total_claims, (
        f"calibration suite has {total_claims - total_passed} failure(s); "
        f"per-target: {[(r.target_name, r.passed_claims, r.total_claims) for r in results]}"
    )


def test_substrate_e8_root_set_matches_poc_marquee_claim(tmp_path, monkeypatch):
    """The marquee G5 claim: substrate's E8 root set exactly matches the prior repo."""
    _override_ledger_dir(monkeypatch, tmp_path)
    result = WolframPocCalibration().run()
    assert result.summary_per_claim["substrate_root_set_matches_poc"] is True
