"""
Escrow merge (2026-05-19T00:00:31Z).
Source: ``CMPLX-history/staging/by-family/unclassified/partsfactory/gate.py``
Slot: ``slot-02-nsl-phi``
"""
#!/usr/bin/env python3
"""
OpenCMPLX Gate Service — Epoch gating + conservation checking

Every 300 epochs: capacity check → compress → contribute → merge → grow → restore.
Gate types: conservation (dphi>0), epoch (tick boundary), tier (capability locked),
            rate (too many ops/sec), quality (below threshold).
PG-backed conservation_checks table for audit trail.
"""
import hashlib
import json
import logging
import os
import time
import urllib.request
from typing import Any, Dict, List, Optional

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [gate] %(message)s")
logger = logging.getLogger("gate")

PORT = int(os.environ.get("PORT", "8000"))
IDENTITY_URL = os.environ.get("IDENTITY_URL", "http://tmn2-identity:8000")
CONSERVATION_URL = os.environ.get("CONSERVATION_URL", "http://tmn2-conservation:8000")
PG_URL = os.environ.get("PG_URL", "")

GATE_INTERVAL = 300
CAPACITY_THRESHOLD = 0.75
GROWTH_INCREMENT = 8
MAX_DIMS = 96
ALPHA = {"nascent": 0.30, "apprentice": 0.40, "journeyman": 0.50, "master": 0.60, "architect": 0.70}
RATE_LIMIT_PER_SEC = 50
QUALITY_THRESHOLD = 0.3

# Tier-locked operations: minimum tier required
TIER_LOCKS = {
    "spawn_child": "apprentice",
    "merge_brain": "journeyman",
    "federated_contribute": "journeyman",
    "create_coin": "master",
    "modify_daemon": "architect",
    "epoch_gate": "nascent",
    "board_post": "nascent",
    "bond_create": "apprentice",
}
TIER_ORDER = ["nascent", "apprentice", "journeyman", "master", "architect"]

app = FastAPI(title="OpenCMPLX Gate", description="Epoch gate — conservation + tier + rate + quality gating")

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

def _ensure_table():
    conn = _get_pg()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conservation_checks (
                    check_id    TEXT PRIMARY KEY,
                    agent_id    TEXT NOT NULL,
                    operation   TEXT NOT NULL,
                    delta_phi   REAL DEFAULT 0.0,
                    gate_type   TEXT NOT NULL,
                    result      TEXT NOT NULL,
                    reason      TEXT,
                    metadata    JSONB DEFAULT '{}',
                    checked_at  DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cc_agent ON conservation_checks(agent_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cc_type  ON conservation_checks(gate_type)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cc_result ON conservation_checks(result)")
    except Exception as e:
        logger.warning("Table creation failed: %s", e)

# ─── HTTP helpers ─────────────────────────────────────────────────────────────

def _http_get(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None

def _http_post(url, data, timeout=10):
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None

# ─── In-memory stats ─────────────────────────────────────────────────────────
_stats = {"checked": 0, "passed": 0, "blocked": 0, "by_type": {}}
_rate_tracker: Dict[str, List[float]] = {}  # agent_id -> list of timestamps
_gate_history: List[Dict] = []

# ─── Gate rules ──────────────────────────────────────────────────────────────
GATE_RULES = [
    {"type": "conservation", "description": "ΔΦ must be ≤ 0 (conservation law)", "severity": "hard"},
    {"type": "epoch", "description": "Agent tick_count % 300 triggers epoch advancement", "severity": "soft"},
    {"type": "tier", "description": "Operation requires minimum tier level", "severity": "hard"},
    {"type": "rate", "description": f"Max {RATE_LIMIT_PER_SEC} operations/second per agent", "severity": "soft"},
    {"type": "quality", "description": f"Quality score must be ≥ {QUALITY_THRESHOLD}", "severity": "soft"},
]

# ─── Models ──────────────────────────────────────────────────────────────────

class GateCheckRequest(BaseModel):
    agent_id: str = ""
    operation: str = ""
    delta_phi: float = 0.0
    tier: str = "nascent"
    epoch: int = 0
    quality_score: float = 1.0
    capacity_score: float = 0.0
    dims: int = 24

class EpochCheckRequest(BaseModel):
    tick_count: int = 0
    capacity_score: float = 0.0
    dims: int = 24
    tier: str = "nascent"

# ─── Gate logic ──────────────────────────────────────────────────────────────

def _check_conservation(delta_phi: float) -> Optional[Dict]:
    if delta_phi > 0:
        return {"gated": True, "reason": f"ΔΦ={delta_phi:.6f} > 0 violates conservation", "gate_type": "conservation"}
    return None

def _check_tier(operation: str, agent_tier: str) -> Optional[Dict]:
    required = TIER_LOCKS.get(operation)
    if required is None:
        return None
    agent_rank = TIER_ORDER.index(agent_tier) if agent_tier in TIER_ORDER else 0
    required_rank = TIER_ORDER.index(required) if required in TIER_ORDER else 0
    if agent_rank < required_rank:
        return {"gated": True, "reason": f"Operation '{operation}' requires tier '{required}', agent is '{agent_tier}'", "gate_type": "tier"}
    return None

def _check_rate(agent_id: str) -> Optional[Dict]:
    now = time.time()
    timestamps = _rate_tracker.get(agent_id, [])
    # Keep only last second
    timestamps = [t for t in timestamps if now - t < 1.0]
    _rate_tracker[agent_id] = timestamps
    if len(timestamps) >= RATE_LIMIT_PER_SEC:
        return {"gated": True, "reason": f"Rate limit exceeded: {len(timestamps)}/{RATE_LIMIT_PER_SEC} ops/sec", "gate_type": "rate"}
    timestamps.append(now)
    return None

def _check_quality(quality_score: float) -> Optional[Dict]:
    if quality_score < QUALITY_THRESHOLD:
        return {"gated": True, "reason": f"Quality score {quality_score:.3f} below threshold {QUALITY_THRESHOLD}", "gate_type": "quality"}
    return None

def _check_epoch_identity(agent_id: str) -> Optional[Dict]:
    """Query identity service for agent epoch validity."""
    if not agent_id:
        return None
    info = _http_get(f"{IDENTITY_URL}/agent/{agent_id}")
    if info and info.get("status") == "suspended":
        return {"gated": True, "reason": f"Agent '{agent_id}' is suspended", "gate_type": "epoch"}
    return None

def _record_check(check_id: str, agent_id: str, operation: str, delta_phi: float, gate_type: str, result: str, reason: str):
    conn = _get_pg()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conservation_checks (check_id, agent_id, operation, delta_phi, gate_type, result, reason, checked_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (check_id) DO NOTHING
            """, (check_id, agent_id, operation, delta_phi, gate_type, result, reason, time.time()))
    except Exception as e:
        logger.warning("PG record failed: %s", e)

def _update_stats(gate_type: str, blocked: bool):
    _stats["checked"] += 1
    if blocked:
        _stats["blocked"] += 1
    else:
        _stats["passed"] += 1
    _stats["by_type"][gate_type] = _stats["by_type"].get(gate_type, 0) + 1

# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    _ensure_table()
    logger.info("Gate service started, PG=%s", "connected" if _get_pg() else "unavailable")

@app.get("/health")
def health():
    return {"ok": True, "service": "opencmplx-gate", "gates_processed": len(_gate_history),
            "stats": _stats, "pg": _get_pg() is not None}

@app.post("/check")
def check_gate(req: GateCheckRequest):
    check_id = hashlib.sha256(f"{req.agent_id}:{req.operation}:{time.time()}".encode()).hexdigest()[:24]

    # Run all gate checks in order of severity
    for checker, args in [
        (_check_conservation, (req.delta_phi,)),
        (_check_tier, (req.operation, req.tier)),
        (_check_rate, (req.agent_id,)),
        (_check_quality, (req.quality_score,)),
        (_check_epoch_identity, (req.agent_id,)),
    ]:
        result = checker(*args)
        if result:
            _update_stats(result["gate_type"], True)
            _record_check(check_id, req.agent_id, req.operation, req.delta_phi, result["gate_type"], "blocked", result["reason"])
            logger.info("GATE BLOCKED: %s op=%s type=%s", req.agent_id, req.operation, result["gate_type"])
            return {**result, "check_id": check_id}

    # All checks passed
    _update_stats("none", False)
    _record_check(check_id, req.agent_id, req.operation, req.delta_phi, "none", "passed", "all checks passed")

    # Check if epoch advancement is due
    epoch_due = req.epoch > 0 and req.epoch % GATE_INTERVAL == 0
    saturated = req.capacity_score >= CAPACITY_THRESHOLD
    should_advance = epoch_due and saturated
    new_dims = min(req.dims + GROWTH_INCREMENT, MAX_DIMS) if should_advance else req.dims
    alpha = ALPHA.get(req.tier, 0.30)

    response = {
        "gated": False, "reason": "all checks passed", "gate_type": "none",
        "check_id": check_id, "agent_id": req.agent_id,
        "epoch_due": epoch_due, "saturated": saturated, "should_advance": should_advance,
        "current_dims": req.dims, "new_dims": new_dims, "growth": new_dims - req.dims,
        "alpha": alpha, "tier": req.tier,
        "actions": ["compress", "contribute", "gather", "merge", "retrain", "grow", "restore"] if should_advance else [],
    }
    if should_advance:
        _gate_history.append(response)

    return response

@app.post("/epoch_check/{agent_id}")
def epoch_check(agent_id: str, req: EpochCheckRequest):
    due = req.tick_count > 0 and req.tick_count % GATE_INTERVAL == 0
    saturated = req.capacity_score >= CAPACITY_THRESHOLD
    should_advance = due and saturated
    new_dims = min(req.dims + GROWTH_INCREMENT, MAX_DIMS) if should_advance else req.dims
    alpha = ALPHA.get(req.tier, 0.30)

    result = {
        "agent_id": agent_id, "tick_count": req.tick_count,
        "due": due, "saturated": saturated, "should_advance": should_advance,
        "current_dims": req.dims, "new_dims": new_dims, "growth": new_dims - req.dims,
        "alpha": alpha, "tier": req.tier, "gate_interval": GATE_INTERVAL,
        "next_gate_at": ((req.tick_count // GATE_INTERVAL) + 1) * GATE_INTERVAL,
        "actions": ["compress", "contribute", "gather", "merge", "retrain", "grow", "restore"] if should_advance else [],
    }
    if should_advance:
        # Report to conservation service
        _http_post(f"{CONSERVATION_URL}/report", {
            "agent_id": agent_id, "service": "gate",
            "delta_phi": 0.0, "operation": "epoch_advance",
            "epoch": req.tick_count,
        })
    return result

@app.get("/rules")
def list_rules():
    return {
        "gate_rules": GATE_RULES,
        "tier_locks": TIER_LOCKS,
        "tier_order": TIER_ORDER,
        "gate_interval": GATE_INTERVAL,
        "capacity_threshold": CAPACITY_THRESHOLD,
        "rate_limit": RATE_LIMIT_PER_SEC,
        "quality_threshold": QUALITY_THRESHOLD,
        "growth_increment": GROWTH_INCREMENT,
        "max_dims": MAX_DIMS,
    }

@app.get("/stats")
def gate_stats():
    conn = _get_pg()
    pg_stats = {}
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT result, COUNT(*) FROM conservation_checks GROUP BY result")
                pg_stats = {row[0]: row[1] for row in cur.fetchall()}
                cur.execute("SELECT gate_type, COUNT(*) FROM conservation_checks GROUP BY gate_type")
                pg_stats["by_type_pg"] = {row[0]: row[1] for row in cur.fetchall()}
                cur.execute("SELECT COUNT(*) FROM conservation_checks")
                pg_stats["total_pg"] = cur.fetchone()[0]
        except Exception:
            pass
    return {
        "memory": _stats,
        "pg": pg_stats,
        "gate_history_length": len(_gate_history),
        "active_rate_trackers": len(_rate_tracker),
    }

@app.get("/history")
def gate_history(limit: int = 20):
    return _gate_history[-limit:]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
