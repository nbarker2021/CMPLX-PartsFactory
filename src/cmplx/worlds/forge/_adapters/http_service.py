"""
Lattice Forge HTTP adapter — thin FastAPI over WorldsForgeProvider (slot-19, :8845).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
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


class WitnessClassifyRequest(BaseModel):
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    morphism_id: Optional[str] = None


class WitnessRegimeARequest(BaseModel):
    n: int = Field(..., ge=1)
    max_depth: int = 4096
    base_page: int = 64


class WitnessProofBundleRequest(BaseModel):
    max_depth: int = 128
    page_count: int = 2
    page_size: int = 128
    block_size: int = 8
    max_order: int = 4
    verify: bool = True


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


def _witness_mint(op: str, payload: dict[str, Any]) -> None:
    from .._receipt_bridge import mint_forge_operation

    mint_forge_operation(op, payload)


try:
    from lattice_forge.witness.api import create_witness_router

    app.include_router(
        create_witness_router(
            get_provider().forge,
            provider=get_provider(),
            mint_fn=_witness_mint,
        )
    )
except ImportError:
    logger.info("witness router unavailable — install lattice-forge[witness]")


_DEPRECATION = {"Deprecation": "true", "Link": '</witness/regime-a/query>; rel="successor-version"'}


@app.post("/witness/classify-ledger")
def witness_classify_ledger_deprecated(body: WitnessClassifyRequest) -> JSONResponse:
    """Deprecated alias — use POST /witness/classify."""
    payload = get_provider().witness_classify(**body.model_dump(), mint_receipt=True)
    return JSONResponse(payload, headers=_DEPRECATION)


@app.post("/witness/regime-a/query-mint")
def witness_regime_a_query_mint_deprecated(body: WitnessRegimeARequest) -> JSONResponse:
    """Deprecated alias — use POST /witness/regime-a/query."""
    payload = get_provider().witness_regime_a_query(**body.model_dump(), mint_receipt=True)
    return JSONResponse(payload, headers=_DEPRECATION)


@app.post("/witness/proof-bundle-mint")
def witness_proof_bundle_mint_deprecated(body: WitnessProofBundleRequest) -> JSONResponse:
    """Deprecated alias — use POST /witness/proof-bundle."""
    payload = get_provider().witness_proof_bundle(**body.model_dump(), mint_receipt=True)
    return JSONResponse(payload, headers=_DEPRECATION)
