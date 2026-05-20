"""
Escrow merge (2026-05-19T00:00:31Z).
Source: ``CMPLX-history/staging/by-family/unclassified/partsfactory/conservation.py``
Slot: ``slot-03-aletheia-law-chain``
"""
#!/usr/bin/env python3
"""
OpenCMPLX Conservation Service — ΔΦ = ΔN + ΔI + ΔL enforcement

Tracks conservation across ALL services. Every operation reports its ΔΦ.
Cumulative ΔΦ must remain ≤ 0. Violation = system halt on that path.
Three sectors: Noether (symmetry), Shannon (information), Landauer (erasure).
The conservation law IS the stop condition IS palindromic closure.
PG-backed conservation_ledger for persistent audit trail.
"""
import json
import logging
import os
import time
import urllib.request
from typing import Any, Dict, List, Optional

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [conservation] %(message)s")
logger = logging.getLogger("conservation")

PORT = int(os.environ.get("PORT", "8000"))
COUPLING = float(os.environ.get("COUPLING", "0.030076"))
PG_URL = os.environ.get("PG_URL", "")

app = FastAPI(title="OpenCMPLX Conservation", description="ΔΦ = ΔN + ΔI + ΔL enforcement")

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

def _ensure_tables():
    conn = _get_pg()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            # Extended ledger for per-operation tracking
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conservation_entries (
                    entry_id    SERIAL PRIMARY KEY,
                    atom_id     TEXT,
                    agent_id    TEXT NOT NULL,
                    service     TEXT,
                    operation   TEXT NOT NULL,
                    delta_phi   REAL NOT NULL DEFAULT 0.0,
                    delta_n     REAL DEFAULT 0.0,
                    delta_i     REAL DEFAULT 0.0,
                    delta_l     REAL DEFAULT 0.0,
                    cumulative  REAL NOT NULL DEFAULT 0.0,
                    violation   BOOLEAN DEFAULT FALSE,
                    epoch       INTEGER DEFAULT 0,
                    created_at  DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ce_agent ON conservation_entries(agent_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ce_service ON conservation_entries(service)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ce_violation ON conservation_entries(violation)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ce_time ON conservation_entries(created_at DESC)")
    except Exception as e:
        logger.warning("Table creation failed: %s", e)

# ─── In-memory state ─────────────────────────────────────────────────────────
_ledger: List[Dict] = []
_cumulative_dphi: float = 0.0
_violations: int = 0
_per_agent: Dict[str, float] = {}
_per_service: Dict[str, float] = {}
_per_operation: Dict[str, float] = {}
_per_agent_violations: Dict[str, int] = {}
_total_checks: int = 0

# ─── Models ──────────────────────────────────────────────────────────────────

class ConservationReport(BaseModel):
    agent_id: str = ""
    service: str = ""
    atom_id: str = ""
    delta_phi: float = 0.0
    delta_n: float = 0.0
    delta_i: float = 0.0
    delta_l: float = 0.0
    operation: str = ""
    epoch: int = 0

class BatchReport(BaseModel):
    operations: List[ConservationReport] = []

# ─── Core logic ──────────────────────────────────────────────────────────────

def _process_report(req: ConservationReport) -> Dict:
    global _cumulative_dphi, _violations, _total_checks
    _total_checks += 1

    entry = {
        "agent_id": req.agent_id, "service": req.service, "atom_id": req.atom_id,
        "delta_phi": req.delta_phi, "delta_n": req.delta_n,
        "delta_i": req.delta_i, "delta_l": req.delta_l,
        "operation": req.operation, "epoch": req.epoch,
        "timestamp": time.time(),
        "cumulative_before": _cumulative_dphi,
    }

    _cumulative_dphi += req.delta_phi
    entry["cumulative_after"] = _cumulative_dphi

    _per_agent[req.agent_id] = _per_agent.get(req.agent_id, 0) + req.delta_phi
    _per_service[req.service] = _per_service.get(req.service, 0) + req.delta_phi
    _per_operation[req.operation] = _per_operation.get(req.operation, 0) + req.delta_phi

    is_violation = req.delta_phi > 0
    if is_violation:
        _violations += 1
        _per_agent_violations[req.agent_id] = _per_agent_violations.get(req.agent_id, 0) + 1
        entry["violation"] = True
        logger.warning("CONSERVATION VIOLATION: ΔΦ=%.4f from %s/%s op=%s",
                       req.delta_phi, req.agent_id, req.service, req.operation)
    else:
        entry["violation"] = False

    _ledger.append(entry)

    # Persist to PG
    conn = _get_pg()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conservation_entries
                        (atom_id, agent_id, service, operation, delta_phi, delta_n, delta_i, delta_l, cumulative, violation, epoch, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (req.atom_id or None, req.agent_id, req.service, req.operation,
                      req.delta_phi, req.delta_n, req.delta_i, req.delta_l,
                      _cumulative_dphi, is_violation, req.epoch, time.time()))
        except Exception as e:
            logger.warning("PG insert failed: %s", e)

    # Update conservation_ledger summary row
    _update_summary_row()

    return entry

def _update_summary_row():
    conn = _get_pg()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE conservation_ledger SET
                    cumulative_dphi = %s,
                    tick_dphi = %s,
                    violation_count = %s,
                    checked_at = %s
                WHERE id = (SELECT MIN(id) FROM conservation_ledger)
            """, (_cumulative_dphi, _ledger[-1]["delta_phi"] if _ledger else 0.0,
                  _violations, time.time()))
    except Exception:
        pass

# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    _ensure_tables()
    logger.info("Conservation service started, PG=%s, coupling=%.6f",
                "connected" if _get_pg() else "unavailable", COUPLING)

@app.get("/health")
def health():
    return {"ok": True, "service": "opencmplx-conservation",
            "cumulative_dphi": round(_cumulative_dphi, 6), "violations": _violations,
            "total_checks": _total_checks, "pg": _get_pg() is not None}

@app.post("/check")
def check_conservation(req: ConservationReport):
    """Check delta_phi for an operation and update cumulative."""
    return _process_report(req)

@app.post("/report")
def report_conservation(req: ConservationReport):
    """Alias for /check — backward compatibility."""
    return _process_report(req)

@app.post("/batch")
def batch_check(req: BatchReport):
    """Batch check multiple operations."""
    results = []
    violations = 0
    for op in req.operations:
        result = _process_report(op)
        results.append(result)
        if result.get("violation"):
            violations += 1
    return {
        "processed": len(results),
        "violations": violations,
        "cumulative_dphi": round(_cumulative_dphi, 6),
        "results": results,
    }

@app.get("/ledger")
def get_ledger(limit: int = 20, source: str = "memory"):
    """Recent conservation ledger entries. source=pg reads from database."""
    if source == "pg":
        conn = _get_pg()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT entry_id, atom_id, agent_id, service, operation, delta_phi,
                               delta_n, delta_i, delta_l, cumulative, violation, epoch, created_at
                        FROM conservation_entries ORDER BY entry_id DESC LIMIT %s
                    """, (limit,))
                    cols = [d[0] for d in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
            except Exception:
                pass
    return _ledger[-limit:]

@app.get("/stats")
def stats():
    """Detailed stats by agent, by operation type, by time period."""
    conn = _get_pg()
    pg_stats = {}
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*), SUM(delta_phi), SUM(CASE WHEN violation THEN 1 ELSE 0 END) FROM conservation_entries")
                row = cur.fetchone()
                pg_stats["total_entries"] = row[0]
                pg_stats["total_dphi"] = round(row[1] or 0, 6)
                pg_stats["total_violations"] = row[2]
                cur.execute("SELECT agent_id, SUM(delta_phi), COUNT(*) FROM conservation_entries GROUP BY agent_id ORDER BY SUM(delta_phi)")
                pg_stats["by_agent"] = [{"agent_id": r[0], "dphi": round(r[1], 6), "count": r[2]} for r in cur.fetchall()]
                cur.execute("SELECT operation, SUM(delta_phi), COUNT(*) FROM conservation_entries GROUP BY operation ORDER BY COUNT(*) DESC LIMIT 20")
                pg_stats["by_operation"] = [{"operation": r[0], "dphi": round(r[1], 6), "count": r[2]} for r in cur.fetchall()]
        except Exception:
            pass

    return {
        "cumulative_dphi": round(_cumulative_dphi, 6),
        "total_checks": _total_checks,
        "violations": _violations,
        "conservation_valid": _violations == 0,
        "coupling": COUPLING,
        "by_agent": {k: round(v, 6) for k, v in sorted(_per_agent.items(), key=lambda x: x[1])},
        "by_service": {k: round(v, 6) for k, v in _per_service.items()},
        "by_operation": {k: round(v, 6) for k, v in _per_operation.items()},
        "agent_violations": _per_agent_violations,
        "pg": pg_stats,
    }

@app.post("/audit")
def audit():
    """Full conservation audit: sum all entries, verify cumulative chain."""
    running = 0.0
    errors = []
    for i, entry in enumerate(_ledger):
        expected_before = running
        if abs(entry.get("cumulative_before", expected_before) - expected_before) > 1e-8:
            errors.append({"index": i, "expected": expected_before,
                           "got": entry.get("cumulative_before"), "agent_id": entry.get("agent_id")})
        running += entry.get("delta_phi", 0.0)

    # Cross-check with PG
    pg_sum = None
    conn = _get_pg()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT SUM(delta_phi), COUNT(*) FROM conservation_entries")
                row = cur.fetchone()
                pg_sum = {"sum": round(row[0] or 0, 6), "count": row[1]}
        except Exception:
            pass

    drift = abs(running - _cumulative_dphi)
    return {
        "valid": len(errors) == 0 and drift < 1e-8,
        "memory_cumulative": round(_cumulative_dphi, 6),
        "recomputed_cumulative": round(running, 6),
        "drift": drift,
        "chain_errors": errors[:20],
        "total_entries": len(_ledger),
        "pg_cross_check": pg_sum,
    }

@app.get("/agent/{agent_id}")
def agent_conservation(agent_id: str):
    return {
        "agent_id": agent_id,
        "cumulative_dphi": round(_per_agent.get(agent_id, 0), 6),
        "violations": _per_agent_violations.get(agent_id, 0),
    }

@app.get("/surplus")
def surplus():
    return {
        "surplus": round(abs(_cumulative_dphi), 6),
        "spendable": _cumulative_dphi < 0,
        "coupling": COUPLING,
        "conservation_valid": _violations == 0,
    }

@app.get("/status")
def status():
    return {
        "cumulative_dphi": round(_cumulative_dphi, 6),
        "entries": len(_ledger),
        "violations": _violations,
        "agents_tracked": len(_per_agent),
        "services_tracked": len(_per_service),
        "operations_tracked": len(_per_operation),
        "coupling": COUPLING,
        "conservation_valid": _violations == 0,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
