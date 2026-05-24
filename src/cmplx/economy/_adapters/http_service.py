"""Economy HTTP adapter — thin FastAPI over EconomyProvider.

Port 8845 (ecosystem default, one above SpeedLight). Mirrors the
receipt/speedlight adapter pattern.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..provider import EconomyProvider
from ..state import CommissionStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [economy] %(message)s")
logger = logging.getLogger("economy")

PORT = int(os.environ.get("PORT", "8845"))
_provider = EconomyProvider()

app = FastAPI(title="OpenCMPLX Economy", description="Agent marketplace and resource economy")


class MintRequest(BaseModel):
    agent_id: str
    amount: float


class TransferRequest(BaseModel):
    from_id: str
    to_id: str
    amount: float


class CommissionRequest(BaseModel):
    requester: str
    task: str
    reward: float
    snap_labels: List[str] = []
    deadline_hours: float = 24.0


@app.get("/health")
def health() -> Dict[str, Any]:
    return _provider.health()


@app.get("/balance/{agent_id}")
def balance(agent_id: str) -> Dict[str, Any]:
    bal = _provider.balance(agent_id)
    return {"agent_id": agent_id, "debt": bal.debt, "in_default": bal.in_default}


@app.post("/mint")
def mint(req: MintRequest) -> Dict[str, Any]:
    bal = _provider.mint(req.agent_id, req.amount)
    return {"agent_id": req.agent_id, "debt": bal.debt}


@app.post("/transfer")
def transfer(req: TransferRequest) -> Dict[str, Any]:
    ok, reason = _provider.transfer(req.from_id, req.to_id, req.amount)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    return {"from_id": req.from_id, "to_id": req.to_id, "amount": req.amount}


@app.post("/commission")
def create_commission(req: CommissionRequest) -> Dict[str, Any]:
    comm = _provider.create_commission(
        req.requester,
        req.task,
        req.reward,
        req.snap_labels,
        req.deadline_hours,
    )
    return {
        "commission_id": comm.commission_id,
        "status": comm.status.value,
        "reward": comm.reward,
    }


@app.get("/commissions")
def list_commissions(status: Optional[str] = None) -> List[Dict[str, Any]]:
    s = CommissionStatus(status) if status else None
    return [
        {
            "commission_id": c.commission_id,
            "requester": c.requester,
            "task": c.task,
            "reward": c.reward,
            "status": c.status.value,
        }
        for c in _provider.list_commissions(s)
    ]
