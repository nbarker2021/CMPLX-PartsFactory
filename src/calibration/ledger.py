"""
CalibrationLedger — JSONL persistence + cross-reference to cmplx.receipt.

Separate ledger (not part of cmplx.receipt) because calibration is meta:
it's work *about* the substrate, not work the substrate does. Calibration
receipts cross-reference the cmplx.receipt chain via
``operational_chain_range = (head_before, head_after)`` so the two ledgers
stitch into one audit trail.

Receipts are JSONL files under ``data/calibration/<target>/<run_id>.jsonl``,
one receipt per line.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CalibrationReceipt:
    """One claim's outcome under a calibration run.

    See docs/sub_frames/reality_calibration.md §3 for the grammar contract.
    """

    calibration_id: str
    timestamp: str
    target_name: str
    claim_name: str
    expected: Any
    tolerance: Any  # float or dict[str, float]
    observed: Any
    delta: Any      # float, dict[str, float], or "exact" / "n/a"
    passed: bool
    operational_chain_range: tuple[str, str] = ("", "")
    harness_version: str = "1.0"
    notes: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["operational_chain_range"] = list(self.operational_chain_range)
        return d

    def to_json_line(self) -> str:
        return json.dumps(self.to_dict(), default=str, sort_keys=True)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CalibrationReceipt":
        ocr = d.get("operational_chain_range", ["", ""])
        d = {**d, "operational_chain_range": (ocr[0], ocr[1]) if len(ocr) >= 2 else ("", "")}
        return cls(**d)


class CalibrationLedger:
    """Append-only JSONL ledger for calibration receipts.

    Each ledger instance is bound to a single target + run combination.
    A target may have many runs (re-running calibration); each run gets
    its own file.

    Usage:

        ledger = CalibrationLedger.for_run("wolfram_poc")
        ledger.append(receipt)
        ledger.append(another_receipt)
        ledger.finalize()
        # → all receipts persisted to disk; ledger.path() points at the JSONL file
    """

    def __init__(self, target_name: str, run_id: Optional[str] = None,
                 base_dir: Optional[Path] = None) -> None:
        self.target_name = target_name
        self.run_id = run_id or str(uuid.uuid4())[:12]
        self.base_dir = base_dir or _default_base_dir()
        self._receipts: list[CalibrationReceipt] = []
        self._finalized = False

    @classmethod
    def for_run(
        cls,
        target_name: str,
        run_id: Optional[str] = None,
        base_dir: Optional[Path] = None,
    ) -> "CalibrationLedger":
        """Open a new ledger for one calibration run."""
        return cls(target_name=target_name, run_id=run_id, base_dir=base_dir)

    @classmethod
    def load(cls, path: Path) -> "CalibrationLedger":
        """Load a previously-finalized ledger from disk."""
        p = Path(path)
        target_name = p.parent.name
        run_id = p.stem
        ledger = cls(target_name=target_name, run_id=run_id, base_dir=p.parent.parent)
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                ledger._receipts.append(CalibrationReceipt.from_dict(json.loads(line)))
        ledger._finalized = True
        return ledger

    def append(self, receipt: CalibrationReceipt) -> None:
        if self._finalized:
            raise RuntimeError(
                f"calibration ledger for {self.target_name}/{self.run_id} "
                f"already finalized; create a new run for additional receipts"
            )
        self._receipts.append(receipt)

    def finalize(self) -> Path:
        """Write all receipts to disk and return the path."""
        path = self.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for r in self._receipts:
                f.write(r.to_json_line() + "\n")
        self._finalized = True
        return path

    def path(self) -> Path:
        return self.base_dir / self.target_name / f"{self.run_id}.jsonl"

    @property
    def receipts(self) -> list[CalibrationReceipt]:
        return list(self._receipts)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self._receipts) if self._receipts else False

    @property
    def summary(self) -> dict[str, Any]:
        total = len(self._receipts)
        passed = sum(1 for r in self._receipts if r.passed)
        return {
            "target": self.target_name,
            "run_id": self.run_id,
            "total_claims": total,
            "passed_claims": passed,
            "failed_claims": total - passed,
            "pass_rate": (passed / total) if total else 0.0,
            "all_passed": passed == total and total > 0,
        }

    def __repr__(self) -> str:
        s = self.summary
        return (
            f"<CalibrationLedger {self.target_name}/{self.run_id} "
            f"passed={s['passed_claims']}/{s['total_claims']}>"
        )


def _default_base_dir() -> Path:
    """Default ledger location: ``<repo>/data/calibration/``.

    Resolves to the repo root by walking up from this file (src/calibration/ledger.py).
    """
    here = Path(__file__).resolve()
    # here = src/calibration/ledger.py → repo_root = here.parents[2]
    repo_root = here.parents[2]
    return repo_root / "data" / "calibration"
