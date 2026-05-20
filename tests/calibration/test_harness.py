"""
Calibration harness tests.

Verifies the G5 infrastructure itself — ledger persistence, tolerance
evaluation, target orchestration, and the wolfram_poc target's first
run integrity.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from calibration import (
    CalibrationClaim,
    CalibrationLedger,
    CalibrationReceipt,
    CalibrationTarget,
    within_tolerance,
)


# ─────────────────────────────────────────────────────────────────────
# within_tolerance
# ─────────────────────────────────────────────────────────────────────

class TestWithinTolerance:
    def test_scalar_exact_match_passes(self):
        passed, delta = within_tolerance(5, 5, 0)
        assert passed is True
        assert delta == "exact"

    def test_scalar_exact_mismatch_fails(self):
        passed, _ = within_tolerance(5, 6, 0)
        assert passed is False

    def test_scalar_within_tolerance_passes(self):
        passed, delta = within_tolerance(5.05, 5.0, 0.1)
        assert passed is True
        assert abs(delta - 0.05) < 1e-9

    def test_scalar_outside_tolerance_fails(self):
        passed, delta = within_tolerance(5.5, 5.0, 0.1)
        assert passed is False
        assert delta > 0.1

    def test_bool_exact(self):
        assert within_tolerance(True, True, 0)[0] is True
        assert within_tolerance(False, True, 0)[0] is False

    def test_string_exact(self):
        assert within_tolerance("hello", "hello", 0)[0] is True
        assert within_tolerance("hi", "hello", 0)[0] is False

    def test_dict_all_fields_pass(self):
        expected = {"a": 1.0, "b": 2.0}
        observed = {"a": 1.05, "b": 1.95}
        tol = {"a": 0.1, "b": 0.1}
        passed, deltas = within_tolerance(observed, expected, tol)
        assert passed is True
        assert "a" in deltas
        assert "b" in deltas

    def test_dict_one_field_fails(self):
        expected = {"a": 1.0, "b": 2.0}
        observed = {"a": 1.05, "b": 5.0}  # b is way off
        tol = {"a": 0.1, "b": 0.1}
        passed, _ = within_tolerance(observed, expected, tol)
        assert passed is False

    def test_list_elementwise_pass(self):
        passed, _ = within_tolerance([1.0, 2.0, 3.0], [1.05, 2.05, 2.95], 0.1)
        assert passed is True


# ─────────────────────────────────────────────────────────────────────
# CalibrationLedger
# ─────────────────────────────────────────────────────────────────────

class TestCalibrationLedger:
    def test_ledger_empty_summary(self, tmp_path):
        ledger = CalibrationLedger.for_run("test_target", base_dir=tmp_path)
        s = ledger.summary
        assert s["total_claims"] == 0
        assert s["all_passed"] is False  # vacuous: no claims means not "all passed"

    def test_ledger_append_and_summary(self, tmp_path):
        ledger = CalibrationLedger.for_run("test_target", base_dir=tmp_path)
        ledger.append(_make_receipt("test_target", "claim_a", True))
        ledger.append(_make_receipt("test_target", "claim_b", False))
        ledger.append(_make_receipt("test_target", "claim_c", True))
        s = ledger.summary
        assert s["total_claims"] == 3
        assert s["passed_claims"] == 2
        assert s["failed_claims"] == 1
        assert abs(s["pass_rate"] - 2 / 3) < 1e-9
        assert s["all_passed"] is False

    def test_ledger_finalize_writes_jsonl(self, tmp_path):
        ledger = CalibrationLedger.for_run("test_target", base_dir=tmp_path)
        ledger.append(_make_receipt("test_target", "claim_a", True))
        ledger.append(_make_receipt("test_target", "claim_b", True))
        path = ledger.finalize()
        assert path.exists()
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        first = json.loads(lines[0])
        assert first["claim_name"] == "claim_a"
        assert first["passed"] is True

    def test_finalize_then_append_raises(self, tmp_path):
        ledger = CalibrationLedger.for_run("test_target", base_dir=tmp_path)
        ledger.append(_make_receipt("test_target", "claim_a", True))
        ledger.finalize()
        with pytest.raises(RuntimeError, match="already finalized"):
            ledger.append(_make_receipt("test_target", "claim_b", True))

    def test_ledger_load_round_trip(self, tmp_path):
        ledger = CalibrationLedger.for_run("test_target", base_dir=tmp_path)
        ledger.append(_make_receipt("test_target", "claim_a", True))
        ledger.append(_make_receipt("test_target", "claim_b", False))
        path = ledger.finalize()
        loaded = CalibrationLedger.load(path)
        assert loaded.summary["total_claims"] == 2
        assert loaded.summary["passed_claims"] == 1
        assert loaded.receipts[0].claim_name == "claim_a"

    def test_ledger_path_structure(self, tmp_path):
        ledger = CalibrationLedger.for_run(
            "my_target", run_id="abc123", base_dir=tmp_path,
        )
        assert ledger.path() == tmp_path / "my_target" / "abc123.jsonl"


# ─────────────────────────────────────────────────────────────────────
# CalibrationTarget base
# ─────────────────────────────────────────────────────────────────────

class _SimplePassingTarget(CalibrationTarget):
    target_name = "simple_pass"

    def claims(self):
        return [
            CalibrationClaim(name="trivial", expected=1, tolerance=0, observed_fn=lambda: 1),
            CalibrationClaim(name="float_close", expected=3.14, tolerance=0.01,
                             observed_fn=lambda: 3.141),
        ]


class _SimpleFailingTarget(CalibrationTarget):
    target_name = "simple_fail"

    def claims(self):
        return [
            CalibrationClaim(name="will_pass", expected=10, tolerance=0,
                             observed_fn=lambda: 10),
            CalibrationClaim(name="will_fail", expected=10, tolerance=0,
                             observed_fn=lambda: 11),
        ]


class _RaisingTarget(CalibrationTarget):
    target_name = "raising"

    def claims(self):
        return [
            CalibrationClaim(name="boom", expected=1, tolerance=0,
                             observed_fn=lambda: (_ for _ in ()).throw(RuntimeError("boom"))),
        ]


class TestCalibrationTarget:
    def test_passing_target(self, tmp_path, monkeypatch):
        _override_ledger_dir(monkeypatch, tmp_path)
        target = _SimplePassingTarget()
        result = target.run()
        assert result.all_passed is True
        assert result.total_claims == 2
        assert result.passed_claims == 2

    def test_failing_target_records_both_outcomes(self, tmp_path, monkeypatch):
        _override_ledger_dir(monkeypatch, tmp_path)
        target = _SimpleFailingTarget()
        result = target.run()
        assert result.all_passed is False
        assert result.passed_claims == 1
        assert result.failed_claims == 1
        assert result.summary_per_claim["will_pass"] is True
        assert result.summary_per_claim["will_fail"] is False

    def test_raising_observed_fn_records_failure_not_exception(self, tmp_path, monkeypatch):
        _override_ledger_dir(monkeypatch, tmp_path)
        target = _RaisingTarget()
        # Should NOT raise — calibration captures exceptions in notes.
        result = target.run()
        assert result.failed_claims == 1
        assert result.all_passed is False


# ─────────────────────────────────────────────────────────────────────
# wolfram_poc end-to-end smoke
# ─────────────────────────────────────────────────────────────────────

class TestWolframPocCalibration:
    def test_wolfram_poc_all_claims_pass(self, tmp_path, monkeypatch):
        """First reality calibration — substrate E8 matches POC E8."""
        _override_ledger_dir(monkeypatch, tmp_path)
        from calibration.targets.wolfram_poc import WolframPocCalibration
        target = WolframPocCalibration()
        result = target.run()
        # Headline assertion: all 7 claims pass.
        assert result.all_passed is True, (
            f"calibration failed; per-claim: {result.summary_per_claim}"
        )
        # Sanity on counts.
        assert result.total_claims == 7
        assert result.passed_claims == 7

    def test_wolfram_poc_substrate_root_set_matches_poc(self, tmp_path, monkeypatch):
        """The marquee claim: our 240 E8 roots == POC's 240 E8 roots."""
        _override_ledger_dir(monkeypatch, tmp_path)
        from calibration.targets.wolfram_poc import WolframPocCalibration
        target = WolframPocCalibration()
        result = target.run()
        assert result.summary_per_claim["substrate_root_set_matches_poc"] is True


# ─────────────────────────────────────────────────────────────────────
# Test utilities
# ─────────────────────────────────────────────────────────────────────

def _make_receipt(target_name: str, claim_name: str, passed: bool) -> CalibrationReceipt:
    from datetime import datetime, timezone
    return CalibrationReceipt(
        calibration_id=f"test-{claim_name}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        target_name=target_name,
        claim_name=claim_name,
        expected=1,
        tolerance=0,
        observed=1 if passed else 0,
        delta="exact" if passed else 1,
        passed=passed,
    )


def _override_ledger_dir(monkeypatch, tmp_path):
    """Redirect CalibrationLedger's default base_dir to tmp_path for tests."""
    from calibration import ledger as ledger_module
    monkeypatch.setattr(ledger_module, "_default_base_dir", lambda: tmp_path)
