#!/usr/bin/env python3
"""
OpenCMPLX SpeedLight Service — Two-tier idempotent content-addressed cache

f(f(x)) = f(x) — zero recomputation cost.
Every computation receipted. Merkle-chained ledger.
Channel 3/6/9 governance: permissive/strict/idempotent.
Two-tier: in-memory LRU (OrderedDict, max 10000) + PG persistent cache.
ComputationReceipt: {receipt_hash, fn_name, task_hash, result_hash, hit, timestamp}.
"""
import hashlib
import json
import logging
import os
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [speedlight] %(message)s")
logger = logging.getLogger("speedlight")

PORT = int(os.environ.get("PORT", "8000"))
MAX_MEMORY_SIZE = int(os.environ.get("MAX_MEMORY_SIZE", "10000"))
PG_URL = os.environ.get("PG_URL", "")
GC_STALE_HOURS = int(os.environ.get("GC_STALE_HOURS", "72"))

# Channel governance: 3=permissive, 6=strict, 9=idempotent (priority cache)
CHANNEL_PRIORITY = {3: 1, 6: 2, 9: 3}
CHANNEL_LIMITS = {3: 1e3, 6: 0.1, 9: 1e-6}

app = FastAPI(title="OpenCMPLX SpeedLight", description="Two-tier idempotent content-addressed cache")

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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS speedlight_cache (
                    key         TEXT PRIMARY KEY,
                    value       JSONB,
                    task_hash   TEXT,
                    result_hash TEXT,
                    fn_name     TEXT DEFAULT '',
                    channel     INTEGER DEFAULT 3,
                    hits        INTEGER DEFAULT 0,
                    cost_seconds REAL DEFAULT 0.0,
                    created_at  DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
                    last_hit    DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_slc_task ON speedlight_cache(task_hash)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_slc_channel ON speedlight_cache(channel)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_slc_hits ON speedlight_cache(hits DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_slc_lasthit ON speedlight_cache(last_hit)")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS speedlight_receipts (
                    receipt_hash TEXT PRIMARY KEY,
                    fn_name     TEXT,
                    task_hash   TEXT,
                    result_hash TEXT,
                    hit         BOOLEAN DEFAULT FALSE,
                    channel     INTEGER DEFAULT 3,
                    created_at  DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_slr_task ON speedlight_receipts(task_hash)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_slr_time ON speedlight_receipts(created_at DESC)")
    except Exception as e:
        logger.warning("Table creation failed: %s", e)

# ─── Memory tier ─────────────────────────────────────────────────────────────
_cache: OrderedDict = OrderedDict()
_stats = {"hits": 0, "misses": 0, "time_saved": 0.0, "puts": 0,
          "memory_hits": 0, "pg_hits": 0, "gc_runs": 0, "gc_evicted": 0}
_ledger: List[Dict] = []
_ledger_head: str = "0" * 64

# ─── Models ──────────────────────────────────────────────────────────────────

class CacheRequest(BaseModel):
    task_id: str = ""
    key: str = ""
    content_hash: str = ""
    result: Any = None
    cost_seconds: float = 0.0
    channel: int = 3
    fn_name: str = ""

class BatchPutRequest(BaseModel):
    items: List[CacheRequest] = []

class ComputeRequest(BaseModel):
    task_id: str
    fn_name: str = ""
    result: Any = None
    cost_seconds: float = 0.0
    channel: int = 3

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _content_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8", errors="replace")).hexdigest()[:32]

def _make_receipt(fn_name: str, task_hash: str, result_hash: str, hit: bool, channel: int) -> Dict:
    global _ledger_head
    ts = time.time()
    entry = {"fn_name": fn_name, "task_hash": task_hash, "result_hash": result_hash,
             "hit": hit, "channel": channel, "prev": _ledger_head, "ts": ts}
    receipt_hash = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()[:32]
    entry["receipt_hash"] = receipt_hash
    _ledger_head = receipt_hash
    _ledger.append(entry)

    # Persist receipt to PG
    conn = _get_pg()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO speedlight_receipts (receipt_hash, fn_name, task_hash, result_hash, hit, channel, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (receipt_hash) DO NOTHING
                """, (receipt_hash, fn_name, task_hash, result_hash, hit, channel, ts))
        except Exception:
            pass

    return entry

def _is_priority_channel(channel: int) -> bool:
    return channel in (3, 6, 9)

def _get_from_pg(key: str) -> Optional[Dict]:
    conn = _get_pg()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT value, task_hash, result_hash, fn_name, channel, hits, cost_seconds FROM speedlight_cache WHERE key = %s", (key,))
            row = cur.fetchone()
            if row:
                # Update hit count
                cur.execute("UPDATE speedlight_cache SET hits = hits + 1, last_hit = %s WHERE key = %s", (time.time(), key))
                return {"result": row[0], "task_hash": row[1], "result_hash": row[2],
                        "fn_name": row[3], "channel": row[4], "hits": row[5] + 1,
                        "cost_seconds": row[6]}
    except Exception:
        pass
    return None

def _put_to_pg(key: str, value: Any, task_hash: str, result_hash: str, fn_name: str, channel: int, cost_seconds: float):
    conn = _get_pg()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO speedlight_cache (key, value, task_hash, result_hash, fn_name, channel, cost_seconds, created_at, last_hit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value, task_hash = EXCLUDED.task_hash,
                    result_hash = EXCLUDED.result_hash, last_hit = EXCLUDED.last_hit
            """, (key, json.dumps(value, default=str), task_hash, result_hash, fn_name,
                  channel, cost_seconds, time.time(), time.time()))
    except Exception:
        pass

def _put_memory(key: str, result: Any, cost_seconds: float, content_hash: str, channel: int, fn_name: str):
    _cache[key] = {"result": result, "cost_seconds": cost_seconds,
                   "content_hash": content_hash, "channel": channel,
                   "fn_name": fn_name, "cached_at": time.time(), "hits": 0}
    _cache.move_to_end(key)
    # Evict LRU, but prefer keeping priority channel entries
    while len(_cache) > MAX_MEMORY_SIZE:
        # Pop the oldest non-priority item, or oldest if all priority
        evicted = False
        for k in list(_cache.keys()):
            if not _is_priority_channel(_cache[k].get("channel", 3)):
                _cache.pop(k)
                evicted = True
                break
        if not evicted:
            _cache.popitem(last=False)

# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    _ensure_tables()
    logger.info("SpeedLight started, PG=%s, memory_max=%d",
                "connected" if _get_pg() else "unavailable", MAX_MEMORY_SIZE)

@app.get("/health")
def health():
    total = _stats["hits"] + _stats["misses"]
    hit_rate = _stats["hits"] / total * 100 if total else 0
    return {"ok": True, "service": "opencmplx-speedlight",
            "cached_entries": len(_cache), "hit_rate": round(hit_rate, 1),
            "time_saved": round(_stats["time_saved"], 2), "pg": _get_pg() is not None}

@app.get("/get/{key}")
def cache_get(key: str):
    """Get from cache: check memory tier, then PG tier."""
    # Tier 1: Memory
    if key in _cache:
        _stats["hits"] += 1
        _stats["memory_hits"] += 1
        entry = _cache[key]
        entry["hits"] = entry.get("hits", 0) + 1
        _stats["time_saved"] += entry.get("cost_seconds", 0)
        _cache.move_to_end(key)
        _make_receipt(entry.get("fn_name", ""), key, entry.get("content_hash", ""), True, entry.get("channel", 3))
        return {"hit": True, "tier": "memory", "key": key, "result": entry["result"],
                "cost_saved": entry.get("cost_seconds", 0), "hits": entry["hits"]}

    # Tier 2: PG
    pg_entry = _get_from_pg(key)
    if pg_entry:
        _stats["hits"] += 1
        _stats["pg_hits"] += 1
        _stats["time_saved"] += pg_entry.get("cost_seconds", 0)
        # Promote to memory
        _put_memory(key, pg_entry["result"], pg_entry.get("cost_seconds", 0),
                     pg_entry.get("result_hash", ""), pg_entry.get("channel", 3),
                     pg_entry.get("fn_name", ""))
        _make_receipt(pg_entry.get("fn_name", ""), key, pg_entry.get("result_hash", ""), True, pg_entry.get("channel", 3))
        return {"hit": True, "tier": "pg", "key": key, "result": pg_entry["result"],
                "cost_saved": pg_entry.get("cost_seconds", 0), "hits": pg_entry["hits"]}

    # Miss
    _stats["misses"] += 1
    _make_receipt("", key, "", False, 3)
    return {"hit": False, "key": key}

@app.post("/put")
def cache_put(req: CacheRequest):
    """Put into cache (memory + PG)."""
    key = req.key or req.task_id or _content_hash(json.dumps(req.result, default=str))
    task_hash = req.content_hash or _content_hash(key)
    result_hash = _content_hash(json.dumps(req.result, default=str))

    _put_memory(key, req.result, req.cost_seconds, task_hash, req.channel, req.fn_name)
    _put_to_pg(key, req.result, task_hash, result_hash, req.fn_name, req.channel, req.cost_seconds)
    _stats["puts"] += 1

    _make_receipt(req.fn_name, task_hash, result_hash, False, req.channel)

    return {"cached": True, "key": key, "tier": "both", "memory_entries": len(_cache)}

@app.post("/compute")
def cache_compute(req: ComputeRequest):
    """f(f(x))=f(x) idempotent compute. Check cache, return if hit, else store and return."""
    # Check memory
    if req.task_id in _cache:
        _stats["hits"] += 1
        _stats["memory_hits"] += 1
        entry = _cache[req.task_id]
        entry["hits"] = entry.get("hits", 0) + 1
        saved = entry.get("cost_seconds", 0)
        _stats["time_saved"] += saved
        _cache.move_to_end(req.task_id)
        _make_receipt(req.fn_name, req.task_id, entry.get("content_hash", ""), True, req.channel)
        return {"hit": True, "tier": "memory", "task_id": req.task_id,
                "result": entry["result"], "cost": 0.0, "cost_saved": saved,
                "idempotent": True}

    # Check PG
    pg_entry = _get_from_pg(req.task_id)
    if pg_entry:
        _stats["hits"] += 1
        _stats["pg_hits"] += 1
        _stats["time_saved"] += pg_entry.get("cost_seconds", 0)
        _put_memory(req.task_id, pg_entry["result"], pg_entry.get("cost_seconds", 0),
                     pg_entry.get("result_hash", ""), req.channel, req.fn_name)
        _make_receipt(req.fn_name, req.task_id, pg_entry.get("result_hash", ""), True, req.channel)
        return {"hit": True, "tier": "pg", "task_id": req.task_id,
                "result": pg_entry["result"], "cost": 0.0,
                "cost_saved": pg_entry.get("cost_seconds", 0), "idempotent": True}

    # Miss: store provided result
    _stats["misses"] += 1
    result_hash = _content_hash(json.dumps(req.result, default=str))
    _put_memory(req.task_id, req.result, req.cost_seconds, result_hash, req.channel, req.fn_name)
    _put_to_pg(req.task_id, req.result, req.task_id, result_hash, req.fn_name, req.channel, req.cost_seconds)
    _make_receipt(req.fn_name, req.task_id, result_hash, False, req.channel)

    return {"hit": False, "tier": "none", "task_id": req.task_id,
            "result": req.result, "cost": req.cost_seconds, "idempotent": False}

@app.get("/stats")
def cache_stats():
    """Hit/miss rates, tier breakdown, cache size."""
    total = _stats["hits"] + _stats["misses"]
    pg_size = 0
    conn = _get_pg()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM speedlight_cache")
                pg_size = cur.fetchone()[0]
        except Exception:
            pass

    return {
        "total_requests": total,
        "hits": _stats["hits"], "misses": _stats["misses"],
        "hit_rate": round(_stats["hits"] / total * 100, 2) if total else 0,
        "memory_hits": _stats["memory_hits"], "pg_hits": _stats["pg_hits"],
        "time_saved_seconds": round(_stats["time_saved"], 2),
        "puts": _stats["puts"],
        "memory_size": len(_cache), "memory_max": MAX_MEMORY_SIZE,
        "pg_size": pg_size,
        "ledger_length": len(_ledger), "ledger_head": _ledger_head,
        "gc_runs": _stats["gc_runs"], "gc_evicted": _stats["gc_evicted"],
        "channel_breakdown": _channel_breakdown(),
    }

def _channel_breakdown():
    breakdown = {}
    for entry in _cache.values():
        ch = entry.get("channel", 3)
        breakdown[ch] = breakdown.get(ch, 0) + 1
    return breakdown

@app.get("/ledger")
def get_ledger(limit: int = 20):
    """Recent computation receipts."""
    return {"receipts": _ledger[-limit:], "total": len(_ledger), "head": _ledger_head}

@app.post("/batch")
def batch_put(req: BatchPutRequest):
    """Batch put multiple items."""
    results = []
    for item in req.items:
        key = item.key or item.task_id or _content_hash(json.dumps(item.result, default=str))
        task_hash = item.content_hash or _content_hash(key)
        result_hash = _content_hash(json.dumps(item.result, default=str))
        _put_memory(key, item.result, item.cost_seconds, task_hash, item.channel, item.fn_name)
        _put_to_pg(key, item.result, task_hash, result_hash, item.fn_name, item.channel, item.cost_seconds)
        results.append({"key": key, "cached": True})
        _stats["puts"] += 1
    return {"cached": len(results), "results": results}

@app.post("/gc")
def garbage_collect():
    """Garbage collect stale entries from PG tier."""
    conn = _get_pg()
    if not conn:
        return {"gc": False, "reason": "PG unavailable"}
    cutoff = time.time() - (GC_STALE_HOURS * 3600)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM speedlight_cache WHERE last_hit < %s AND hits < 2", (cutoff,))
            stale_count = cur.fetchone()[0]
            cur.execute("DELETE FROM speedlight_cache WHERE last_hit < %s AND hits < 2", (cutoff,))
            _stats["gc_runs"] += 1
            _stats["gc_evicted"] += stale_count
            logger.info("GC: evicted %d stale entries (cutoff=%dh)", stale_count, GC_STALE_HOURS)
        return {"gc": True, "evicted": stale_count, "cutoff_hours": GC_STALE_HOURS}
    except Exception as e:
        return {"gc": False, "error": str(e)}

@app.get("/channel/{channel}")
def channel_policy(channel: int, dphi: float = 0.0):
    limit = CHANNEL_LIMITS.get(channel, 1e3)
    priority = CHANNEL_PRIORITY.get(channel, 0)
    return {"channel": channel, "dphi": dphi, "limit": limit,
            "allowed": dphi <= limit, "priority": priority,
            "governance": "priority_cache" if channel in (3, 6, 9) else "standard"}

@app.get("/status")
def status():
    total = _stats["hits"] + _stats["misses"]
    return {**_stats, "cached_entries": len(_cache), "max_size": MAX_MEMORY_SIZE,
            "total_requests": total, "ledger_length": len(_ledger), "ledger_head": _ledger_head}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
