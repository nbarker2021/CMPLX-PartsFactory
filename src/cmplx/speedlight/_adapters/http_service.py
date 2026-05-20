"""
SpeedLight HTTP adapter — thin FastAPI over SpeedlightProvider.

Port 8843 (ecosystem default). Mirrors receipt adapter pattern.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..provider import SpeedLightProvider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [speedlight] %(message)s")
logger = logging.getLogger("speedlight")

PORT = int(os.environ.get("PORT", "8843"))
_provider = SpeedLightProvider()

app = FastAPI(title="OpenCMPLX SpeedLight", description="Idempotent computation cache")


class CachePutRequest(BaseModel):
    key: str
    value: Any = None
    ttl: int = 3600


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", **(_provider.health)}


@app.post("/v1/cache")
def cache_put(body: CachePutRequest) -> Dict[str, Any]:
    _provider.put(body.key, body.value)
    return {"key": body.key, "stored": True, "ttl": body.ttl}


@app.get("/v1/cache/{key}")
def cache_get(key: str) -> Dict[str, Any]:
    val = _provider.get(key)
    if val is None:
        raise HTTPException(status_code=404, detail="not found")
    return {"key": key, "value": val}


@app.get("/v1/receipts/{receipt_id}")
def receipt_get(receipt_id: str) -> Dict[str, Any]:
    for task_id, comp in _provider.speedlight.receipt_cache.items():
        if comp.receipt_id == receipt_id or task_id == receipt_id:
            return comp.to_dict()
    raise HTTPException(status_code=404, detail="receipt not found")


def get_provider() -> SpeedLightProvider:
    return _provider
