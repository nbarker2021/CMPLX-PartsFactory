"""
Receipt HTTP adapter — thin FastAPI surface over ReceiptChain / ReceiptProvider.

Escrow source merged 2026-05-19; refactored 2026-05-20 to delegate to the
canonical in-process spine (no duplicate _chain globals).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from ..provider import ReceiptProvider
from ..types import CANONICAL_TYPES, Receipt, normalize_receipt_type

logging.basicConfig(level=logging.INFO, format="%(asctime)s [receipt] %(message)s")
logger = logging.getLogger("receipt")

PORT = int(os.environ.get("PORT", "8010"))
PG_URL = os.environ.get("PG_URL", "")
_STRICT = os.environ.get("RECEIPT_STRICT_TYPES", "0").strip() in ("1", "true", "yes")

app = FastAPI(title="OpenCMPLX Receipt", description="Merkle-chained operation receipts")
_provider = ReceiptProvider()

try:
    import psycopg2
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore[assignment]

_pg_conn = None


def _get_pg():
    global _pg_conn
    if not PG_URL or psycopg2 is None:
        return None
    try:
        if _pg_conn is None or _pg_conn.closed:
            _pg_conn = psycopg2.connect(PG_URL)
            _pg_conn.autocommit = True
        return _pg_conn
    except Exception:
        return None


def _receipt_to_dict(r: Receipt) -> Dict[str, Any]:
    d = r.to_dict()
    d["prev_hash"] = d.get("prev_hash", "")
    return d


class ReceiptRequest(BaseModel):
    receipt_type: str = "PROCESS"
    agent_id: str = ""
    atom_id: str = ""
    operation: str = ""
    operator: str = ""
    payload: Dict[str, Any] = {}
    delta_phi: float = 0.0
    snap_labels: List[str] = []
    epoch: int = 0
    parent_hash: str = ""


class VerifyRequest(BaseModel):
    receipt_hash: str = ""
    max_depth: int = 100


class DagEdgeRequest(BaseModel):
    source_id: str
    target_id: str
    edge_type: str = "depends"
    weight: float = 1.0
    snap_overlap: List[str] = []


def _persist_pg(receipt: Receipt) -> None:
    conn = _get_pg()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO receipts (
                    receipt_hash, atom_id, parent_hash, operation, operator,
                    delta_phi, metadata, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, to_timestamp(%s))
                ON CONFLICT (receipt_hash) DO NOTHING
                """,
                (
                    receipt.receipt_hash,
                    receipt.atom_id or None,
                    receipt.prev_hash,
                    receipt.operation,
                    receipt.operator,
                    receipt.delta_phi,
                    json.dumps(
                        {
                            "type": receipt.receipt_type,
                            "agent_id": receipt.agent_id,
                            "snap_labels": receipt.snap_labels,
                            "epoch": receipt.epoch,
                            "receipt_id": receipt.receipt_id,
                        }
                    ),
                    receipt.created_at,
                ),
            )
    except Exception as exc:
        logger.warning("PG insert failed: %s", exc)


@app.on_event("startup")
def startup() -> None:
    logger.info(
        "Receipt service started (chain delegate), PG=%s strict=%s",
        "connected" if _get_pg() else "unavailable",
        _STRICT,
    )


@app.get("/health")
def health() -> Dict[str, Any]:
    chain = _provider.chain
    return {
        "ok": True,
        "service": "opencmplx-receipt",
        "chain_length": chain.length,
        "head": chain.head[:16],
        "pg": _get_pg() is not None,
        "storage_mode": chain.storage_mode,
    }


@app.get("/status")
def status() -> Dict[str, Any]:
    s = _provider.chain.stats()
    return {
        "chain_length": s["length"],
        "head": s["head"],
        "agents": s["agents"],
        "atoms_tracked": s["atoms_tracked"],
        "types": s.get("by_type", {}),
    }


@app.post("/mint")
def mint_receipt(req: ReceiptRequest) -> Dict[str, Any]:
    try:
        rtype = normalize_receipt_type(req.receipt_type, strict=_STRICT)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    receipt = _provider.chain.mint(
        receipt_type=rtype,
        agent_id=req.agent_id,
        atom_id=req.atom_id,
        operation=req.operation,
        operator=req.operator,
        delta_phi=req.delta_phi,
        snap_labels=req.snap_labels,
        epoch=req.epoch,
        payload=req.payload,
        parent_hash=req.parent_hash,
    )
    _persist_pg(receipt)
    logger.info(
        "MINTED: %s type=%s atom=%s op=%s",
        receipt.receipt_hash[:16],
        rtype,
        req.atom_id,
        req.operation,
    )
    return _receipt_to_dict(receipt)


@app.post("/verify")
def verify_receipt(req: VerifyRequest) -> Dict[str, Any]:
    result = _provider.verify(req.receipt_hash, req.max_depth)
    if req.receipt_hash and "chain" in result:
        return result
    if not req.receipt_hash:
        return {
            "valid": result.get("valid", False),
            "length": result.get("length", 0),
            "head": result.get("head", ""),
            "breaks": result.get("breaks", []),
        }
    return result


@app.get("/chain/{atom_id}")
def get_atom_chain(atom_id: str) -> Dict[str, Any]:
    receipts = [_receipt_to_dict(r) for r in _provider.chain_for_atom(atom_id)]
    pg_receipts: List[Dict[str, Any]] = []
    conn = _get_pg()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT receipt_hash, parent_hash, operation, operator,
                           delta_phi, metadata, created_at
                    FROM receipts WHERE atom_id = %s ORDER BY created_at
                    """,
                    (atom_id,),
                )
                cols = [d[0] for d in cur.description]
                pg_receipts = [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception:
            pass
    return {
        "atom_id": atom_id,
        "memory_receipts": receipts,
        "pg_receipts": pg_receipts,
        "total": len(receipts) + len(pg_receipts),
    }


@app.get("/recent")
def recent_receipts(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    receipts = [_receipt_to_dict(r) for r in _provider.recent(limit, offset)]
    return {
        "receipts": receipts,
        "total": _provider.length,
        "limit": limit,
        "offset": offset,
    }


@app.get("/receipt/{receipt_id}")
def get_receipt(receipt_id: str) -> Dict[str, Any]:
    r = _provider.by_id(receipt_id)
    if r is None:
        raise HTTPException(404, "Receipt not found")
    return _receipt_to_dict(r)


@app.get("/agent/{agent_id}")
def get_agent_receipts(agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    return [_receipt_to_dict(r) for r in _provider.by_agent(agent_id, limit)]


@app.get("/stats")
def receipt_stats() -> Dict[str, Any]:
    base = _provider.chain.stats()
    op_counts: Dict[str, int] = {}
    for r in _provider.chain.all():
        op = r.operation or "unknown"
        op_counts[op] = op_counts.get(op, 0) + 1
    pg_stats: Dict[str, Any] = {}
    conn = _get_pg()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM receipts")
                pg_stats["total"] = cur.fetchone()[0]
        except Exception:
            pass
    return {
        "total_memory": base["length"],
        "head": base["head"][:16] if base["head"] else "",
        "by_type": base.get("by_type", {}),
        "by_operation": op_counts,
        "atoms_with_receipts": base.get("atoms_tracked", 0),
        "agents_with_receipts": base.get("agents", 0),
        "chain_depth_histogram": base.get("depth_histogram", {}),
        "pg": pg_stats,
        "canonical_types": list(CANONICAL_TYPES),
    }


@app.post("/dag_edge")
def create_dag_edge(req: DagEdgeRequest) -> Dict[str, Any]:
    edge = _provider.add_edge(
        req.source_id,
        req.target_id,
        edge_type=req.edge_type,
        weight=req.weight,
        snap_overlap=req.snap_overlap,
    )
    conn = _get_pg()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO dag_edges (source_id, target_id, edge_type, weight, created_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (source_id, target_id, edge_type)
                    DO UPDATE SET weight = EXCLUDED.weight
                    """,
                    (req.source_id, req.target_id, req.edge_type, req.weight),
                )
            return {
                "stored": True,
                "source": req.source_id,
                "target": req.target_id,
                "edge_type": req.edge_type,
                "weight": req.weight,
                "snap_overlap": req.snap_overlap,
            }
        except Exception as exc:
            logger.warning("DAG edge PG failed: %s", exc)
    return {
        "stored": True,
        "memory_only": True,
        "edge": edge.to_dict(),
    }


@app.get("/dag/{atom_id}")
def get_dag_edges(atom_id: str) -> Dict[str, Any]:
    mem = _provider.edges_of(atom_id)
    conn = _get_pg()
    if not conn:
        return {"atom_id": atom_id, "outgoing": mem.get("outgoing", []), "incoming": mem.get("incoming", [])}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_id, target_id, edge_type, weight FROM dag_edges WHERE source_id = %s",
                (atom_id,),
            )
            outgoing = [
                {"source": r[0], "target": r[1], "type": r[2], "weight": r[3]}
                for r in cur.fetchall()
            ]
            cur.execute(
                "SELECT source_id, target_id, edge_type, weight FROM dag_edges WHERE target_id = %s",
                (atom_id,),
            )
            incoming = [
                {"source": r[0], "target": r[1], "type": r[2], "weight": r[3]}
                for r in cur.fetchall()
            ]
        return {"atom_id": atom_id, "outgoing": outgoing, "incoming": incoming}
    except Exception:
        return {"atom_id": atom_id, "outgoing": mem.get("outgoing", []), "incoming": mem.get("incoming", [])}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
