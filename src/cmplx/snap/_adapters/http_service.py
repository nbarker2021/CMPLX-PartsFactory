"""
SNAP HTTP adapter — thin FastAPI over SNAPEngine (ecosystem port 8823).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..gate369 import Body, Predicate
from ..label import SNAPRole
from ..provider import SNAPEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [snap] %(message)s")
logger = logging.getLogger("snap")

_engine = SNAPEngine()

app = FastAPI(
    title="OpenCMPLX SNAP",
    description="Labels, lenses, Gate369, ledger (slot-17)",
    version="2026-05-21-deep",
)


class Gate369Request(BaseModel):
    items: List[str] = Field(default_factory=list)
    context: str = ""
    bodies: List[str] = Field(default_factory=list)
    predicates: List[str] = Field(default_factory=list)


class StratifyRequest(BaseModel):
    concept: str
    depth: int = 3


class LabelRequest(BaseModel):
    item: Any = None
    key: str = ""


class LensEvaluateRequest(BaseModel):
    state: Dict[str, Any] = Field(default_factory=dict)
    lens: str = "base"
    before: Dict[str, Any] = Field(default_factory=dict)
    after: Dict[str, Any] = Field(default_factory=dict)


class RunSnapshotRequest(BaseModel):
    workspace: str
    run_id: str
    step_id: str = "snap-0"
    inputs: Dict[str, Any] = Field(default_factory=dict)


def get_engine() -> SNAPEngine:
    return _engine


def reset_engine() -> SNAPEngine:
    """Test helper: fresh in-process engine."""
    global _engine
    _engine = SNAPEngine()
    return _engine


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", **_engine.health}


@app.get("/taxonomy")
def taxonomy() -> Dict[str, Any]:
    return {
        "roles": [r.value for r in SNAPRole],
        "lenses": _engine.lens_bank.names(),
        "rules": _engine.labeler.rule_count,
    }


@app.get("/angles")
def angles() -> Dict[str, Any]:
    return {
        "angles": [
            "structural",
            "semantic",
            "quality",
            "risk",
            "domain",
            "polarity",
            "containment",
            "reversibility",
        ]
    }


@app.get("/ledger")
def ledger_get() -> Dict[str, Any]:
    return _engine.ledger_export()


@app.get("/ledger/verify")
def ledger_verify() -> Dict[str, Any]:
    return {"ok": _engine.ledger.verify(), "length": _engine.ledger.length}


@app.post("/gate369")
def gate369(body: Gate369Request) -> Dict[str, Any]:
    if body.bodies:
        bodies = [Body(id=b, payload={}) for b in body.bodies]
        preds = [Predicate(name=p) for p in body.predicates] or [Predicate(name="pass")]
    elif body.items:
        bodies = [Body(id=str(i), payload={"v": it}) for i, it in enumerate(body.items)]
        preds = [Predicate(name="pass")]
    else:
        raise HTTPException(status_code=400, detail="items or bodies required")
    return _engine.process_gate369(bodies, preds, {"context": body.context})


@app.post("/triad")
def triad(body: Gate369Request) -> Dict[str, Any]:
    if not body.items and not body.bodies:
        raise HTTPException(status_code=400, detail="items required")
    ids = body.bodies or body.items
    bodies = [Body(id=str(i), payload={"v": x}) for i, x in enumerate(ids[:9])]
    preds = [Predicate(name="pass")]
    trace = _engine.gate369.triad(bodies, preds, {})
    return {"members": [b.id for b in trace.members], "delta_u": trace.delta_u}


@app.post("/stratify")
def stratify(body: StratifyRequest) -> Dict[str, Any]:
    lbl = _engine.label(body.concept, key=body.concept[:32])
    return {"concept": body.concept, "depth": body.depth, "labels": lbl.to_dict()}


@app.post("/evaluate_lenses")
def evaluate_lenses(body: LensEvaluateRequest) -> Dict[str, Any]:
    lens = _engine.lens_bank.get(body.lens) or _engine.lens_bank.get("base")
    if lens is None:
        raise HTTPException(status_code=400, detail="unknown lens")
    return {
        "lens": lens.name,
        "verdict": lens.evaluate(body.state),
        "reward": lens.score_reward(body.before, body.after),
    }


@app.post("/v1/label")
def label_post(body: LabelRequest) -> Dict[str, Any]:
    lbl = _engine.label(body.item, key=body.key)
    return lbl.to_dict()


@app.post("/v1/run-snapshot")
def run_snapshot(body: RunSnapshotRequest) -> Dict[str, Any]:
    ws = Path(body.workspace)
    if not ws.is_absolute():
        ws = Path.cwd() / ws
    (ws / "runs" / body.run_id).mkdir(parents=True, exist_ok=True)
    return _engine.mint_run_snapshot(
        ws, body.run_id, body.step_id, inputs=body.inputs
    )


@app.post("/tick")
def tick() -> Dict[str, Any]:
    """Lightweight pulse — labels engine health dimensions."""
    _engine.label("tick", key="tick")
    return {"ok": True, "ledger_length": _engine.ledger.length}
