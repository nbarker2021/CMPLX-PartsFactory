"""
Lattice Forge HTTP adapter — thin FastAPI over WorldsForgeProvider (slot-19, :8845).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ..provider import WorldsForgeProvider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [forge] %(message)s")
logger = logging.getLogger("forge")

_provider = WorldsForgeProvider()

app = FastAPI(
    title="OpenCMPLX Lattice Forge",
    description="Rule 30 witness + proof obligation ledger (slot-19 worlds)",
    version="2026-05-21-dual-home",
)


class ProofObligationsRequest(BaseModel):
    max_depth: int = 128
    page_count: int = 2
    page_size: int = 128
    block_size: int = 8
    max_order: int = 4


def get_provider() -> WorldsForgeProvider:
    return _provider


def reset_provider(root: Optional[str] = None) -> WorldsForgeProvider:
    """Test helper: fresh in-process provider."""
    global _provider
    _provider = WorldsForgeProvider(root=root)
    return _provider


@app.get("/health")
def health() -> Dict[str, Any]:
    return get_provider().health()


@app.get("/status")
def status() -> Dict[str, Any]:
    return get_provider().status()


@app.post("/rule30/proof-obligations")
def rule30_proof_obligations(body: ProofObligationsRequest) -> Dict[str, Any]:
    return get_provider().rule30_proof_obligations(**body.model_dump())


@app.post("/rule30/verify-proof-obligations")
def verify_rule30_proof_obligations(body: ProofObligationsRequest) -> Dict[str, Any]:
    return get_provider().verify_rule30_proof_obligations(**body.model_dump())


@app.post("/morphonics/verify")
def verify_morphonics() -> Dict[str, Any]:
    return get_provider().verify_morphonics()
