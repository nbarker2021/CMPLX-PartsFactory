"""
Bounded HF training window — explicit opt-in only.

Phase A: admit-mask substrate loop + job report JSON.
Phase B: optional ``CMPLX_HF_MODEL`` lazy forward (mockable in CI).
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from .hf_on_demand import hf_lane_from_env
from .hf_adapter import TrainerHarnessSketch

_TRAIN_WINDOW_ENV = "CMPLX_TRAIN_WINDOW"
_TRAIN_ON_VALUES = frozenset({"1", "true", "yes", "on"})
_HF_MODEL_ENV = "CMPLX_HF_MODEL"
_REPORT_DIR = Path(__file__).resolve().parents[4] / "data" / "train_windows"


def train_window_from_env() -> bool:
    """True when ``CMPLX_HF_LANE=train`` or ``CMPLX_TRAIN_WINDOW`` is on."""
    if hf_lane_from_env() == "train":
        return True
    raw = os.environ.get(_TRAIN_WINDOW_ENV, "0").strip().lower()
    return raw in _TRAIN_ON_VALUES


def hf_model_from_env() -> Optional[str]:
    raw = os.environ.get(_HF_MODEL_ENV, "").strip()
    return raw or None


def load_tokens_from_db(db_path: str | Path, *, limit: int = 500) -> list[str]:
    path = Path(db_path)
    if not path.is_file():
        return []
    conn = sqlite3.connect(str(path))
    try:
        rows = conn.execute(
            "SELECT DISTINCT concat FROM token_bonds ORDER BY concat LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [str(r[0]) for r in rows if r[0]]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def load_tokens_from_file(path: str | Path) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip()]


def resolve_train_tokens(
    *,
    crystal_bundle: Path,
    dataset: str = "identity_review",
    tokens_file: Optional[str | Path] = None,
    db_path: Optional[str | Path] = None,
    limit: int = 500,
) -> list[str]:
    if tokens_file:
        return load_tokens_from_file(tokens_file)
    bundle = Path(crystal_bundle)
    db = Path(db_path) if db_path else bundle / "token_index.sqlite"
    if db.is_file():
        tokens = load_tokens_from_db(db, limit=limit)
        if tokens:
            return tokens
    if dataset == "identity_review":
        resolved = bundle.resolve()
        if resolved.name.endswith(".crystal") or (resolved / "token_index.sqlite").is_file():
            repo = resolved.parent.parent if resolved.parent.name == "crystals" else resolved.parent
        elif len(resolved.parents) > 1:
            repo = resolved.parents[1]
        else:
            repo = resolved.parent
        fallback = repo / "data" / "token_index_identity_review.sqlite"
        if fallback.is_file():
            return load_tokens_from_db(fallback, limit=limit)
    return []


def _hf_train_step_stub(*, model_name: str, tokens: Sequence[str]) -> dict[str, Any]:
    """Lazy HF boundary — imports only when model env is set."""
    try:
        import torch  # noqa: F401
    except ImportError:
        return {"hf": False, "reason": "torch_not_installed", "model": model_name}
    return {
        "hf": True,
        "model": model_name,
        "batch_size": len(tokens),
        "loss_stub": 0.0,
        "note": "phase_b_stub_forward",
    }


@dataclass
class TrainWindowConfig:
    """Operator-tunable bounded train loop."""

    crystal_bundle: Path
    tokens: Sequence[str] = field(default_factory=list)
    max_steps: int = 10
    wall_clock_budget_sec: float = 120.0
    db_path: Optional[str] = None
    dataset: str = "identity_review"
    tokens_file: Optional[str] = None
    dry_run: bool = False
    allow_mutations: bool = False
    report_dir: Path = field(default_factory=lambda: _REPORT_DIR)

    def __post_init__(self) -> None:
        self.crystal_bundle = Path(self.crystal_bundle)
        self.report_dir = Path(self.report_dir)
        if self.max_steps < 1:
            raise ValueError("max_steps must be >= 1")


@dataclass
class TrainWindowResult:
    ran: bool
    steps_completed: int = 0
    admitted_total: int = 0
    rejected_total: int = 0
    elapsed_sec: float = 0.0
    reason: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    report_path: Optional[str] = None
    dry_run: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "ran": self.ran,
            "steps_completed": self.steps_completed,
            "admitted_total": self.admitted_total,
            "rejected_total": self.rejected_total,
            "elapsed_sec": self.elapsed_sec,
            "reason": self.reason,
            "steps": self.steps,
            "report_path": self.report_path,
            "dry_run": self.dry_run,
        }


def write_job_report(result: TrainWindowResult, config: TrainWindowConfig) -> Path:
    config.report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = config.report_dir / f"{stamp}.json"
    payload = {
        "timestamp": stamp,
        "crystal": str(config.crystal_bundle),
        "dataset": config.dataset,
        "hf_model": hf_model_from_env(),
        "allow_mutations": config.allow_mutations,
        "result": result.as_dict(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def run_train_window(
    config: TrainWindowConfig,
    *,
    force: bool = False,
) -> TrainWindowResult:
    """
    Run a bounded admit-mask train loop when the train window is enabled.

    ``force=True`` bypasses env gates (tests only).
    """
    if not force and not config.dry_run and not train_window_from_env():
        return TrainWindowResult(ran=False, reason="train_window_off")

    tokens = list(config.tokens)
    if not tokens:
        tokens = resolve_train_tokens(
            crystal_bundle=config.crystal_bundle,
            dataset=config.dataset,
            tokens_file=config.tokens_file,
            db_path=config.db_path,
        )

    plan = {
        "token_count": len(tokens),
        "max_steps": config.max_steps,
        "wall_clock_budget_sec": config.wall_clock_budget_sec,
        "hf_model": hf_model_from_env(),
    }
    if config.dry_run:
        return TrainWindowResult(
            ran=False,
            reason="dry_run",
            dry_run=True,
            steps=[{"plan": plan}],
        )

    harness = TrainerHarnessSketch(
        crystal_bundle=config.crystal_bundle,
        tokens=tokens,
        max_steps=config.max_steps,
    )
    model_name = hf_model_from_env()
    started = time.monotonic()
    steps_out: list[dict[str, Any]] = []
    admitted_total = 0
    rejected_total = 0
    completed = 0

    for step_idx in range(config.max_steps):
        elapsed = time.monotonic() - started
        if elapsed >= config.wall_clock_budget_sec:
            result = TrainWindowResult(
                ran=True,
                steps_completed=completed,
                admitted_total=admitted_total,
                rejected_total=rejected_total,
                elapsed_sec=elapsed,
                reason="wall_clock_budget",
                steps=steps_out,
            )
            report = write_job_report(result, config)
            result.report_path = str(report)
            return result
        batch = tokens[step_idx % len(tokens) :] if tokens else []
        if tokens:
            batch = [tokens[step_idx % len(tokens)]]
        payload = harness.stub_train_step(batch if batch else None)
        payload["step"] = step_idx
        admitted = int(payload.get("admitted", 0))
        batch_size = int(payload.get("batch_size", 0))
        rejected_total += max(0, batch_size - admitted)
        admitted_total += admitted
        if model_name:
            payload["hf_step"] = _hf_train_step_stub(model_name=model_name, tokens=batch or tokens[:8])
        steps_out.append(payload)
        completed += 1

    result = TrainWindowResult(
        ran=True,
        steps_completed=completed,
        admitted_total=admitted_total,
        rejected_total=rejected_total,
        elapsed_sec=time.monotonic() - started,
        reason="max_steps",
        steps=steps_out,
    )
    report = write_job_report(result, config)
    result.report_path = str(report)
    return result


__all__ = [
    "TrainWindowConfig",
    "TrainWindowResult",
    "hf_model_from_env",
    "load_tokens_from_db",
    "load_tokens_from_file",
    "resolve_train_tokens",
    "run_train_window",
    "train_window_from_env",
    "write_job_report",
]
