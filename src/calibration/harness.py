"""
CalibrationTarget / CalibrationClaim — orchestration for G5 reality calibration.

A target gathers a set of claims about a prior repo's behavior. Each claim
specifies an expected value, a tolerance, and an observed_fn that runs
through our substrate. The target's run() invokes each observed_fn,
compares against expected, mints a CalibrationReceipt, appends to a
CalibrationLedger, and returns a CalibrationResult.

The base class is deliberately minimal — subclasses define the claim set
and any harness-level setup (e.g., bootstrapping cmplx ports).
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .ledger import CalibrationLedger, CalibrationReceipt, _utc_now_iso


HARNESS_VERSION = "1.0"


# ─────────────────────────────────────────────────────────────────────
# Claim
# ─────────────────────────────────────────────────────────────────────

@dataclass
class CalibrationClaim:
    """One measurable claim a prior repo makes about substrate behavior.

    Fields:
        name: short identifier (e.g., "e8_root_count")
        expected: claimed value (number, list, dict)
        tolerance: acceptable delta. 0 (or 0.0) means exact match.
            Can be a dict for per-field tolerances on dict-valued claims.
        observed_fn: callable returning the observed value when invoked
            against the substrate. Takes no arguments — the harness sets
            up any context first (via ``target.setup()``).
        notes: optional human-readable context.
    """
    name: str
    expected: Any
    tolerance: Any
    observed_fn: Callable[[], Any]
    notes: str = ""


# ─────────────────────────────────────────────────────────────────────
# Tolerance evaluation
# ─────────────────────────────────────────────────────────────────────

def within_tolerance(
    observed: Any, expected: Any, tolerance: Any
) -> tuple[bool, Any]:
    """Check whether observed is within tolerance of expected.

    Returns (passed, delta). The shape of delta matches the shape of
    expected: scalar → scalar delta; dict → dict of per-field deltas;
    list → list of element deltas. ``"exact"`` indicates exact-equality
    comparison (tolerance == 0 path).

    Comparison rules:
      - numeric expected: ``passed = |observed - expected| ≤ tolerance``
      - exact-equality (tolerance == 0): ``passed = observed == expected``
        (covers strings, ints, bools, tuples — anything hashable-equal)
      - dict expected: per-field tolerance dict; missing keys default to 0
        (exact); pass iff every field passes.
      - list expected: element-wise; pass iff every element passes against
        a scalar tolerance (or a list of same length).
    """
    # Exact-equality short circuit.
    if _is_exact_tolerance(tolerance):
        if observed == expected:
            return True, "exact"
        return False, f"expected {expected!r}, got {observed!r}"

    # Dict comparison.
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            return False, f"observed is not a dict ({type(observed).__name__})"
        tol_dict = tolerance if isinstance(tolerance, dict) else {}
        deltas: dict[str, Any] = {}
        all_pass = True
        for k, exp_v in expected.items():
            obs_v = observed.get(k)
            tol_v = tol_dict.get(k, 0.0)
            sub_pass, sub_delta = within_tolerance(obs_v, exp_v, tol_v)
            deltas[k] = sub_delta
            all_pass = all_pass and sub_pass
        return all_pass, deltas

    # List comparison.
    if isinstance(expected, (list, tuple)):
        if not isinstance(observed, (list, tuple)) or len(observed) != len(expected):
            return False, f"observed length differs from expected"
        deltas_list = []
        all_pass = True
        for i, (obs_v, exp_v) in enumerate(zip(observed, expected)):
            tol_v = tolerance[i] if isinstance(tolerance, (list, tuple)) else tolerance
            sub_pass, sub_delta = within_tolerance(obs_v, exp_v, tol_v)
            deltas_list.append(sub_delta)
            all_pass = all_pass and sub_pass
        return all_pass, deltas_list

    # Numeric comparison.
    try:
        delta = abs(float(observed) - float(expected))
        passed = delta <= float(tolerance)
        return passed, delta
    except (TypeError, ValueError):
        # Non-numeric, non-exact path: fall back to equality.
        return observed == expected, ("exact" if observed == expected else "mismatch")


def _is_exact_tolerance(tolerance: Any) -> bool:
    """True iff the tolerance means 'exact match required'."""
    if tolerance is None:
        return True
    if isinstance(tolerance, (int, float)):
        return tolerance == 0
    return False


# ─────────────────────────────────────────────────────────────────────
# Target + result
# ─────────────────────────────────────────────────────────────────────

@dataclass
class CalibrationResult:
    """Summary of one CalibrationTarget.run() invocation."""
    target_name: str
    run_id: str
    ledger_path: str
    total_claims: int
    passed_claims: int
    failed_claims: int
    pass_rate: float
    all_passed: bool
    duration_ms: float
    summary_per_claim: dict[str, bool] = field(default_factory=dict)


class CalibrationTarget:
    """Base class for one calibration target.

    Subclass and override:
      - ``target_name`` (class attribute)
      - ``setup()`` — optional pre-run hook (e.g., bootstrap cmplx ports)
      - ``claims()`` — return the list of CalibrationClaim to evaluate
      - ``teardown()`` — optional post-run hook (cleanup)

    The base class provides ``run()`` orchestration: setup → for each
    claim, invoke observed_fn → evaluate tolerance → mint receipt → append
    to ledger → teardown → finalize ledger → return result.

    Failures don't abort the run — every claim is evaluated; the
    result aggregates pass/fail across all claims so partial-coverage
    diagnoses are still actionable.
    """

    target_name: str = "unnamed_target"
    harness_version: str = HARNESS_VERSION

    def setup(self) -> None:
        """Override to set up shared state before claims run."""
        return None

    def teardown(self) -> None:
        """Override to clean up after claims run."""
        return None

    def claims(self) -> list[CalibrationClaim]:
        """Return the list of claims for this target. Override in subclasses."""
        raise NotImplementedError

    def run(self, run_id: Optional[str] = None) -> CalibrationResult:
        """Execute the calibration run and return a result + persisted ledger."""
        t0 = time.time()
        ledger = CalibrationLedger.for_run(self.target_name, run_id=run_id)
        run_id = ledger.run_id

        head_before = self._current_receipt_head()
        try:
            self.setup()
            for claim in self.claims():
                receipt = self._evaluate_claim(claim, head_before)
                ledger.append(receipt)
        finally:
            self.teardown()

        path = ledger.finalize()
        duration_ms = (time.time() - t0) * 1000.0

        return CalibrationResult(
            target_name=self.target_name,
            run_id=run_id,
            ledger_path=str(path),
            total_claims=len(ledger.receipts),
            passed_claims=sum(1 for r in ledger.receipts if r.passed),
            failed_claims=sum(1 for r in ledger.receipts if not r.passed),
            pass_rate=ledger.summary["pass_rate"],
            all_passed=ledger.summary["all_passed"],
            duration_ms=duration_ms,
            summary_per_claim={r.claim_name: r.passed for r in ledger.receipts},
        )

    # ── Internals ──────────────────────────────────────────────

    def _evaluate_claim(
        self, claim: CalibrationClaim, head_before: str,
    ) -> CalibrationReceipt:
        """Invoke a claim's observed_fn, compare against expected, mint receipt."""
        t0 = time.time()
        try:
            observed = claim.observed_fn()
            err_note = ""
        except Exception as e:
            observed = None
            err_note = f"observed_fn raised: {type(e).__name__}: {e}"
        passed, delta = (
            within_tolerance(observed, claim.expected, claim.tolerance)
            if observed is not None or _is_exact_tolerance(claim.tolerance)
            else (False, err_note)
        )
        duration_ms = (time.time() - t0) * 1000.0
        head_after = self._current_receipt_head()

        notes = claim.notes
        if err_note:
            notes = (notes + " | " + err_note).strip(" |")

        return CalibrationReceipt(
            calibration_id=str(uuid.uuid4()),
            timestamp=_utc_now_iso(),
            target_name=self.target_name,
            claim_name=claim.name,
            expected=claim.expected,
            tolerance=claim.tolerance,
            observed=observed,
            delta=delta,
            passed=bool(passed),
            operational_chain_range=(head_before, head_after),
            harness_version=self.harness_version,
            notes=notes,
            duration_ms=duration_ms,
        )

    @staticmethod
    def _current_receipt_head() -> str:
        """Read the current cmplx.receipt chain head, or empty string if unregistered."""
        try:
            from cmplx.morphon import MorphonController
            provider = MorphonController.get().get_provider("receipt")
            return getattr(provider, "head", "") or ""
        except Exception:
            return ""
