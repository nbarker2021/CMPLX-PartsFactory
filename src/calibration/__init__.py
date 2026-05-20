"""
src/calibration/ — Reality calibration harness for the G5 gate.

Defined by docs/sub_frames/reality_calibration.md. The calibration suite
verifies that the cmplx substrate reproduces the observable behavior of
the prior CMPLX repos (CMPLX-1T, Wolfram study, CMPLX-Manny). It's meta
work — calibration uses cmplx to verify cmplx — so it lives outside the
cmplx tree.

Public surface:
    CalibrationLedger      — separate JSONL ledger w/ cross-reference to
                             cmplx.receipt
    CalibrationReceipt     — typed outcome record per claim
    CalibrationClaim       — (expected, tolerance, observed_fn) tuple
    CalibrationTarget      — orchestrator for a target's claim set
    CalibrationResult      — summary of a target run
"""
from __future__ import annotations

from .harness import (
    CalibrationClaim,
    CalibrationResult,
    CalibrationTarget,
    within_tolerance,
)
from .ledger import CalibrationLedger, CalibrationReceipt

__all__ = [
    "CalibrationClaim",
    "CalibrationLedger",
    "CalibrationReceipt",
    "CalibrationResult",
    "CalibrationTarget",
    "within_tolerance",
]
