"""
TarPit HTTP adapter — thin FastAPI over TarPitSymbolicProvider (port 8844).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cmplx.morphon import Morphon

from ..provider import TarPitSymbolicProvider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [tarpit] %(message)s")
logger = logging.getLogger("tarpit")

_provider = TarPitSymbolicProvider()


app = FastAPI(
    title="OpenCMPLX TarPit",
    description="Morphonic Ribbon Ecology — symbolic port (slot-18)",
    version="2026-05-21",
)


class RunRequest(BaseModel):
    program: str = Field(..., min_length=1)
    dimension: int = 8
    max_steps: int = 200
    mode: str = "etp"
    envelope_enabled: bool = False
    envelope_max_delta: float = 0.85


class EvolveRequest(BaseModel):
    program: str = Field(..., min_length=1)
    iterations: int = 5
    mutation_rate: float = 0.1


class DeriveRequest(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)
    morphon_id: str = ""


def get_provider() -> TarPitSymbolicProvider:
    return _provider


def reset_provider() -> TarPitSymbolicProvider:
    global _provider
    _provider = TarPitSymbolicProvider()
    return _provider


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", **_provider.health}


@app.get("/canonical-forms")
def canonical_forms() -> Dict[str, Any]:
    from ..canonical_forms import CANONICAL_ALIASES, CANONICAL_FORMS

    return {
        "forms": list(CANONICAL_FORMS),
        "aliases": dict(CANONICAL_ALIASES),
        "lexicon": _provider.aggregator.lexicon_export(),
    }


@app.post("/run")
def run_program(body: RunRequest) -> Dict[str, Any]:
    if not body.program.strip():
        raise HTTPException(status_code=400, detail="program required")
    from .._functions import RelativityEnvelope

    env = None
    if body.envelope_enabled:
        env = RelativityEnvelope(enabled=True, max_delta_component=body.envelope_max_delta)
    if body.mode in ("glyph", "jot", "evolve", "etp"):
        return _provider.execute_aggregated(
            body.program, mode=body.mode, envelope=env  # type: ignore[arg-type]
        )
    out = _provider.run_program(
        body.program,
        dimension=body.dimension,
        max_steps=body.max_steps,
        envelope=env,
    )
    return out


@app.post("/evolve")
def evolve_program(body: EvolveRequest) -> Dict[str, Any]:
    lineage = _provider.evolve_program(
        body.program,
        iterations=body.iterations,
        mutation_rate=body.mutation_rate,
    )
    return {"lineage": lineage, "canonical_form": "evolving_tarpit"}


@app.get("/sessions")
def list_sessions() -> Dict[str, Any]:
    return {"sessions": _provider.aggregator.list_sessions()}


@app.post("/ecology/evolve")
def ecology_evolve(body: EvolveRequest) -> Dict[str, Any]:
    eco = _provider.aggregator.ecology
    eco.load_program(body.program)
    results = eco.evolve(body.iterations, body.mutation_rate)
    return {"results": [r.to_dict() for r in results]}


@app.post("/derive")
def derive_morphon(body: DeriveRequest) -> Dict[str, Any]:
    m = Morphon.forge(payload=body.payload)
    report = _provider.derive(m)
    return {
        "summary": report.summary,
        "output_walls": len(report.output_walls),
        "error_walls": len(report.error_walls),
        "receipts": len(report.receipts),
    }


@app.post("/encode")
def encode_morphon(body: DeriveRequest) -> Dict[str, str]:
    m = Morphon.forge(payload=body.payload)
    return {"program": _provider.encode_to_etp(m)}


@app.get("/ecology/stats")
def ecology_stats() -> Dict[str, Any]:
    from ..ecology import TarpitEcology

    eco = TarpitEcology()
    return eco.get_statistics()
