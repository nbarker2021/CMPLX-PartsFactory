"""
Escrow merge (2026-05-19T00:00:31Z).
Source: ``CMPLX-history/staging/by-family/unclassified/partsfactory/receipt.py``
Slot: ``slot-01-receipt-chain``
"""
#!/usr/bin/env python3
"""
OpenCMPLX Receipt Service — Merkle-chained operation receipts

Every operation across every service produces a receipt.
Receipts chain via prev_hash. The chain IS the blockchain.
Receipt types: MINT, POST, BOND, PROCESS, ASSIGN, VOTE, BIRTH, DEATH, GATE, CROSSING.
PG-backed receipts + dag_edges tables (both exist in init-tmn2-pg.sql).
"""
import hashlib
import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [receipt] %(message)s")
logger = logging.getLogger("receipt")

PORT = int(os.environ.get("PORT", "8000"))
PG_URL = os.environ.get("PG_URL", "")

app = FastAPI(title="OpenCMPLX Receipt", description="Merkle-chained operation receipts")

RECEIPT_TYPES = ["MINT", "POST", "BOND", "PROCESS", "ASSIGN", "VOTE", "BIRTH", "DEATH", "GATE", "CROSSING"]

# ─── PG connection ────────────────────────────────────────────────────────────
_pg_conn = None

def _get_pg():
    global _pg_conn
    if not PG_URL:
        return None
    try:
        if _pg_conn is None or _pg_conn.closed:
            _pg_conn = psycopg2.connect(PG_URL)
            _pg_conn.autocommit = True
        return _pg_conn
    except Exception:
        return None

# ─── In-memory state ─────────────────────────────────────────────────────────
_chain: List[Dict] = []
_chain_head: str = "0" * 64
_index_by_id: Dict[str, Dict] = {}
_index_by_hash: Dict[str, Dict] = {}
_index_by_agent: Dict[str, List[str]] = {}
_index_by_type: Dict[str, List[str]] = {}
_index_by_atom: Dict[str, List[str]] = {}

# ─── Models ──────────────────────────────────────────────────────────────────

class ReceiptRequest(BaseModel):
    receipt_type: str = "PROCESS"
    agent_id: str = ""
    atom_id: str = ""
    operation: str = ""
    operator: str = ""
    payload: Dict = {}
    delta_phi: float = 0.0
    snap_labels: List[str] = []
    epoch: int = 0
    parent_hash: str = ""  # Explicit parent; if empty, uses chain head

class VerifyRequest(BaseModel):
    receipt_hash: str = ""
    max_depth: int = 100

class DagEdgeRequest(BaseModel):
    source_id: str
    target_id: str
    edge_type: str = "depends"
    weight: float = 1.0
    snap_overlap: List[str] = []

# ─── Core logic ──────────────────────────────────────────────────────────────

def _mint(req: ReceiptRequest) -> Dict:
    global _chain_head
    receipt_id = str(uuid.uuid4())[:16]
    ts = time.time()
    parent = req.parent_hash if req.parent_hash else _chain_head
    operator = req.operator or req.agent_id

    # Compute receipt_hash = SHA256(parent_hash:operation:atom_id:timestamp)
    hash_input = f"{parent}:{req.operation}:{req.atom_id}:{ts}"
    receipt_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    receipt = {
        "receipt_id": receipt_id, "receipt_hash": receipt_hash,
        "receipt_type": req.receipt_type, "agent_id": req.agent_id,
        "atom_id": req.atom_id, "operation": req.operation,
        "operator": operator, "delta_phi": req.delta_phi,
        "snap_labels": req.snap_labels, "epoch": req.epoch,
        "prev_hash": parent, "created_at": ts,
        "chain_index": len(_chain),
        "source_tag": f"{req.agent_id}@epoch{req.epoch}::receipt::{receipt_id}",
    }

    # Memory indexes
    _chain.append(receipt)
    _chain_head = receipt_hash
    _index_by_id[receipt_id] = receipt
    _index_by_hash[receipt_hash] = receipt
    _index_by_agent.setdefault(req.agent_id, []).append(receipt_id)
    _index_by_type.setdefault(req.receipt_type, []).append(receipt_id)
    if req.atom_id:
        _index_by_atom.setdefault(req.atom_id, []).append(receipt_id)

    # Persist to PG receipts table
    conn = _get_pg()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO receipts (receipt_hash, atom_id, parent_hash, operation, operator, delta_phi, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, to_timestamp(%s))
                    ON CONFLICT (receipt_hash) DO NOTHING
                """, (receipt_hash, req.atom_id or None, parent, req.operation,
                      operator, req.delta_phi,
                      json.dumps({"type": req.receipt_type, "agent_id": req.agent_id,
                                  "snap_labels": req.snap_labels, "epoch": req.epoch}),
                      ts))
        except Exception as e:
            logger.warning("PG insert failed: %s", e)

    return receipt

def _walk_chain(start_hash: str, max_depth: int = 100) -> List[Dict]:
    """Walk receipt chain backwards from start_hash."""
    chain = []
    current = start_hash
    seen = set()
    for _ in range(max_depth):
        if current in seen or current == "0" * 64:
            break
        seen.add(current)
        receipt = _index_by_hash.get(current)
        if not receipt:
            # Try PG
            conn = _get_pg()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT receipt_hash, atom_id, parent_hash, operation, operator, delta_phi, metadata, created_at FROM receipts WHERE receipt_hash = %s", (current,))
                        row = cur.fetchone()
                        if row:
                            receipt = {"receipt_hash": row[0], "atom_id": row[1], "prev_hash": row[2],
                                       "operation": row[3], "operator": row[4], "delta_phi": row[5],
                                       "metadata": row[6], "created_at": str(row[7])}
                except Exception:
                    pass
            if not receipt:
                break
        chain.append(receipt)
        current = receipt.get("prev_hash", "")
    return chain

# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    logger.info("Receipt service started, PG=%s", "connected" if _get_pg() else "unavailable")

@app.get("/health")
def health():
    return {"ok": True, "service": "opencmplx-receipt", "chain_length": len(_chain),
            "head": _chain_head[:16], "pg": _get_pg() is not None}

@app.get("/status")
def status():
    return {"chain_length": len(_chain), "head": _chain_head,
            "agents": len(_index_by_agent), "atoms_tracked": len(_index_by_atom),
            "types": {t: len(_index_by_type.get(t, [])) for t in RECEIPT_TYPES}}

@app.post("/mint")
def mint_receipt(req: ReceiptRequest):
    if req.receipt_type not in RECEIPT_TYPES:
        raise HTTPException(400, f"Invalid receipt type. Must be one of: {RECEIPT_TYPES}")
    receipt = _mint(req)
    logger.info("MINTED: %s type=%s atom=%s op=%s", receipt["receipt_hash"][:16],
                req.receipt_type, req.atom_id, req.operation)
    return receipt

@app.post("/verify")
def verify_receipt(req: VerifyRequest):
    """Verify a receipt chain by walking parents back to genesis."""
    if not req.receipt_hash:
        # Verify entire in-memory chain
        prev = "0" * 64
        breaks = []
        for i, r in enumerate(_chain):
            if r["prev_hash"] != prev:
                breaks.append({"index": i, "expected": prev[:16], "got": r["prev_hash"][:16]})
            prev = r["receipt_hash"]
        return {"valid": len(breaks) == 0, "length": len(_chain),
                "head": _chain_head, "breaks": breaks[:10]}

    chain = _walk_chain(req.receipt_hash, req.max_depth)
    reaches_genesis = chain and chain[-1].get("prev_hash", "") == "0" * 64
    return {
        "receipt_hash": req.receipt_hash,
        "chain_depth": len(chain),
        "reaches_genesis": reaches_genesis,
        "chain": [{"hash": r["receipt_hash"][:16], "op": r.get("operation"), "atom": r.get("atom_id")} for r in chain],
    }

@app.get("/chain/{atom_id}")
def get_atom_chain(atom_id: str):
    """Get full receipt chain for an atom."""
    receipt_ids = _index_by_atom.get(atom_id, [])
    receipts = [_index_by_id[rid] for rid in receipt_ids if rid in _index_by_id]

    # Also check PG
    pg_receipts = []
    conn = _get_pg()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT receipt_hash, parent_hash, operation, operator, delta_phi, metadata, created_at
                    FROM receipts WHERE atom_id = %s ORDER BY created_at
                """, (atom_id,))
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
def recent_receipts(limit: int = 20, offset: int = 0):
    """Recent receipts with pagination."""
    start = max(0, len(_chain) - limit - offset)
    end = max(0, len(_chain) - offset)
    return {"receipts": _chain[start:end], "total": len(_chain), "limit": limit, "offset": offset}

@app.get("/receipt/{receipt_id}")
def get_receipt(receipt_id: str):
    if receipt_id not in _index_by_id:
        raise HTTPException(404, "Receipt not found")
    return _index_by_id[receipt_id]

@app.get("/agent/{agent_id}")
def get_agent_receipts(agent_id: str, limit: int = 20):
    ids = _index_by_agent.get(agent_id, [])
    return [_index_by_id[rid] for rid in ids[-limit:]]

@app.get("/stats")
def receipt_stats():
    """Receipt statistics: total, by operation, chain depth histogram."""
    # Chain depth per atom
    depth_histogram = {}
    for atom_id, rids in _index_by_atom.items():
        depth = len(rids)
        bucket = str(depth) if depth <= 10 else "10+"
        depth_histogram[bucket] = depth_histogram.get(bucket, 0) + 1

    # By operation
    op_counts: Dict[str, int] = {}
    for r in _chain:
        op = r.get("operation", "unknown")
        op_counts[op] = op_counts.get(op, 0) + 1

    # PG stats
    pg_stats = {}
    conn = _get_pg()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM receipts")
                pg_stats["total"] = cur.fetchone()[0]
                cur.execute("SELECT operation, COUNT(*) FROM receipts GROUP BY operation ORDER BY COUNT(*) DESC LIMIT 20")
                pg_stats["by_operation"] = {r[0]: r[1] for r in cur.fetchall()}
        except Exception:
            pass

    return {
        "total_memory": len(_chain),
        "head": _chain_head[:16],
        "by_type": {t: len(_index_by_type.get(t, [])) for t in RECEIPT_TYPES},
        "by_operation": op_counts,
        "atoms_with_receipts": len(_index_by_atom),
        "agents_with_receipts": len(_index_by_agent),
        "chain_depth_histogram": depth_histogram,
        "pg": pg_stats,
    }

@app.post("/dag_edge")
def create_dag_edge(req: DagEdgeRequest):
    """Create DAG edge between atoms based on SNAP label overlap."""
    conn = _get_pg()
    if not conn:
        return {"stored": False, "reason": "PG unavailable", "edge": req.dict()}
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO dag_edges (source_id, target_id, edge_type, weight, created_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (source_id, target_id, edge_type) DO UPDATE SET weight = EXCLUDED.weight
            """, (req.source_id, req.target_id, req.edge_type, req.weight))
        logger.info("DAG edge: %s -[%s]-> %s (weight=%.3f, overlap=%d labels)",
                     req.source_id, req.edge_type, req.target_id, req.weight, len(req.snap_overlap))
        return {"stored": True, "source": req.source_id, "target": req.target_id,
                "edge_type": req.edge_type, "weight": req.weight,
                "snap_overlap": req.snap_overlap}
    except Exception as e:
        logger.warning("DAG edge failed: %s", e)
        raise HTTPException(500, f"DAG edge creation failed: {e}")

@app.get("/dag/{atom_id}")
def get_dag_edges(atom_id: str):
    """Get all DAG edges for an atom (both outgoing and incoming)."""
    conn = _get_pg()
    if not conn:
        return {"atom_id": atom_id, "outgoing": [], "incoming": []}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT source_id, target_id, edge_type, weight FROM dag_edges WHERE source_id = %s", (atom_id,))
            outgoing = [{"source": r[0], "target": r[1], "type": r[2], "weight": r[3]} for r in cur.fetchall()]
            cur.execute("SELECT source_id, target_id, edge_type, weight FROM dag_edges WHERE target_id = %s", (atom_id,))
            incoming = [{"source": r[0], "target": r[1], "type": r[2], "weight": r[3]} for r in cur.fetchall()]
        return {"atom_id": atom_id, "outgoing": outgoing, "incoming": incoming}
    except Exception:
        return {"atom_id": atom_id, "outgoing": [], "incoming": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
