#!/usr/bin/env python3
"""
OpenCMPLX Identity Service — Agent identity store with PG persistence.

Callsigns, access keys, session keys, SNAPDNA profiles, capability tiers.
Every agent has a unique identity.  Identity IS the coin body name.

5 capability tiers with tool gating:
  nascent    -> 3 tools,   epoch 0,  MI 0.0
  apprentice -> 8 tools,   epoch 1,  MI 0.1
  journeyman -> 15 tools,  epoch 3,  MI 0.3
  master     -> 30 tools,  epoch 10, MI 0.5
  architect  -> unlimited, epoch 25, MI 0.7

Receipt chain: every state change hashes the previous receipt.
PG-backed with in-memory cache.  Graceful fallback if PG unavailable.
"""
import hashlib
import json
import logging
import os
import secrets
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [identity] %(message)s")
logger = logging.getLogger("identity")

PORT = int(os.environ.get("PORT", "8000"))
PG_URL = os.environ.get("PG_URL", "postgresql://tmn2:tmn2_dev@tmn2-pg:5432/tmn2")

# ═══════════════════════════════════════════════════════════════════════
# PG Connection
# ═══════════════════════════════════════════════════════════════════════

import psycopg2

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
    except Exception as e:
        logger.warning("PG not available: %s", e)
        return None


_PG_COLS = [
    "agent_id", "name", "access_key", "session_key", "snap_dna",
    "tier", "karma", "coins", "epoch", "tick_count", "zero_coin_ticks",
    "created_at", "last_seen", "active", "receipt_chain", "capabilities",
]


def _init_pg_tables():
    conn = _get_pg()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_identities (
                agent_id        TEXT PRIMARY KEY,
                name            TEXT,
                access_key      TEXT,
                session_key     TEXT,
                snap_dna        JSONB DEFAULT '[]'::jsonb,
                tier            TEXT DEFAULT 'nascent',
                karma           DOUBLE PRECISION DEFAULT 0,
                coins           DOUBLE PRECISION DEFAULT 10.0,
                epoch           INT DEFAULT 0,
                tick_count      INT DEFAULT 0,
                zero_coin_ticks INT DEFAULT 0,
                created_at      DOUBLE PRECISION,
                last_seen       DOUBLE PRECISION,
                active          BOOLEAN DEFAULT TRUE,
                receipt_chain   TEXT,
                capabilities    JSONB DEFAULT '{}'::jsonb
            )
        """)
        # Migrate from old schema if needed — add columns that may not exist
        for col, defn in [
            ("name", "TEXT"),
            ("coins", "DOUBLE PRECISION DEFAULT 10.0"),
            ("epoch", "INT DEFAULT 0"),
            ("tick_count", "INT DEFAULT 0"),
            ("zero_coin_ticks", "INT DEFAULT 0"),
            ("last_seen", "DOUBLE PRECISION"),
            ("active", "BOOLEAN DEFAULT TRUE"),
            ("receipt_chain", "TEXT"),
            ("capabilities", "JSONB DEFAULT '{}'::jsonb"),
        ]:
            try:
                cur.execute(f"ALTER TABLE agent_identities ADD COLUMN IF NOT EXISTS {col} {defn}")
            except Exception:
                pass
        logger.info("PG table agent_identities ensured")
    except Exception as e:
        logger.warning("PG table init failed: %s", e)


# ═══════════════════════════════════════════════════════════════════════
# Tier system — 5 levels with tool gating
# ═══════════════════════════════════════════════════════════════════════

TIERS = {
    "nascent":     {"max_tools": 3,  "epoch_req": 0,  "mi_threshold": 0.0},
    "apprentice":  {"max_tools": 8,  "epoch_req": 1,  "mi_threshold": 0.1},
    "journeyman":  {"max_tools": 15, "epoch_req": 3,  "mi_threshold": 0.3},
    "master":      {"max_tools": 30, "epoch_req": 10, "mi_threshold": 0.5},
    "architect":   {"max_tools": -1, "epoch_req": 25, "mi_threshold": 0.7},  # -1 = unlimited
}

TIER_ORDER = ["nascent", "apprentice", "journeyman", "master", "architect"]


def _next_tier(current: str) -> Optional[str]:
    """Return the next tier name, or None if already at max."""
    try:
        idx = TIER_ORDER.index(current)
        if idx + 1 < len(TIER_ORDER):
            return TIER_ORDER[idx + 1]
    except ValueError:
        pass
    return None


def _receipt_hash(prev: str, operation: str, ts: float) -> str:
    """Chain a receipt: SHA-256 of prev|operation|timestamp, truncated to 24 hex."""
    payload = f"{prev}|{operation}|{ts}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


# ═══════════════════════════════════════════════════════════════════════
# In-memory cache + PG persistence helpers
# ═══════════════════════════════════════════════════════════════════════

_identities: Dict[str, Dict] = {}


def _row_to_dict(cols: List[str], row: tuple) -> Dict:
    """Convert a PG row to a dict, deserializing JSON columns."""
    agent = dict(zip(cols, row))
    for jcol in ("snap_dna", "capabilities"):
        v = agent.get(jcol)
        if isinstance(v, str):
            try:
                agent[jcol] = json.loads(v)
            except Exception:
                pass
    return agent


def _save_agent(agent: Dict):
    """Persist agent to PG (primary) and memory cache."""
    aid = agent["agent_id"]
    _identities[aid] = agent
    conn = _get_pg()
    if not conn:
        return
    try:
        cur = conn.cursor()
        snap_dna = json.dumps(agent.get("snap_dna", []))
        capabilities = json.dumps(agent.get("capabilities", {}))
        cur.execute("""
            INSERT INTO agent_identities
                (agent_id, name, access_key, session_key, snap_dna, tier,
                 karma, coins, epoch, tick_count, zero_coin_ticks,
                 created_at, last_seen, active, receipt_chain, capabilities)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (agent_id) DO UPDATE SET
                name=EXCLUDED.name, access_key=EXCLUDED.access_key,
                session_key=EXCLUDED.session_key, snap_dna=EXCLUDED.snap_dna,
                tier=EXCLUDED.tier, karma=EXCLUDED.karma, coins=EXCLUDED.coins,
                epoch=EXCLUDED.epoch, tick_count=EXCLUDED.tick_count,
                zero_coin_ticks=EXCLUDED.zero_coin_ticks,
                last_seen=EXCLUDED.last_seen, active=EXCLUDED.active,
                receipt_chain=EXCLUDED.receipt_chain,
                capabilities=EXCLUDED.capabilities
        """, (
            aid, agent.get("name"), agent.get("access_key"),
            agent.get("session_key"), snap_dna,
            agent.get("tier", "nascent"),
            agent.get("karma", 0.0), agent.get("coins", 10.0),
            agent.get("epoch", 0), agent.get("tick_count", 0),
            agent.get("zero_coin_ticks", 0),
            agent.get("created_at"), agent.get("last_seen"),
            agent.get("active", True),
            agent.get("receipt_chain"),
            capabilities,
        ))
    except Exception as e:
        logger.warning("PG save failed for %s: %s", aid, e)


def _load_agent(agent_id: str) -> Optional[Dict]:
    """Load agent from memory cache first, then PG fallback."""
    if agent_id in _identities:
        return _identities[agent_id]
    conn = _get_pg()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM agent_identities WHERE agent_id = %s", (agent_id,))
            row = cur.fetchone()
            if row:
                cols = [d[0] for d in cur.description]
                agent = _row_to_dict(cols, row)
                _identities[agent_id] = agent
                return agent
        except Exception as e:
            logger.warning("PG load failed for %s: %s", agent_id, e)
    return None


def _load_all_agents(active_only: bool = False) -> List[Dict]:
    """Load all agents from PG (or memory fallback)."""
    conn = _get_pg()
    if conn:
        try:
            cur = conn.cursor()
            q = "SELECT * FROM agent_identities"
            if active_only:
                q += " WHERE active = TRUE"
            q += " ORDER BY created_at DESC NULLS LAST"
            cur.execute(q)
            cols = [d[0] for d in cur.description]
            results = []
            for row in cur.fetchall():
                agent = _row_to_dict(cols, row)
                _identities[agent["agent_id"]] = agent
                results.append(agent)
            return results
        except Exception as e:
            logger.warning("PG list failed: %s", e)
    return list(_identities.values())


def _load_cache_from_pg():
    """Warm the memory cache from PG on startup."""
    _load_all_agents()
    logger.info("Identity cache: %d agents loaded", len(_identities))


# ═══════════════════════════════════════════════════════════════════════
# FastAPI app
# ═══════════════════════════════════════════════════════════════════════

app = FastAPI(title="OpenCMPLX Identity",
              description="Agent identity store — PG-backed, tier-gated, receipt-chained")


# ── Request models ────────────────────────────────────────────────────

class IdentityRequest(BaseModel):
    agent_id: str = ""
    name: str = ""
    callsign: str = ""           # alias for name
    snapdna: List[str] = []
    domain: str = ""
    parent_id: str = ""
    coins: float = 10.0


class AuthRequest(BaseModel):
    agent_id: str
    access_key: str


class CoinUpdate(BaseModel):
    delta: float = 0.0
    reason: str = ""


class ReceiptRequest(BaseModel):
    operation: str
    input_hash: str = ""
    output_hash: str = ""
    delta_phi: float = 0.0


class AdvanceRequest(BaseModel):
    mi: float = 0.0


class KarmaUpdate(BaseModel):
    delta: float = 0.0
    reason: str = ""


class EpochUpdate(BaseModel):
    epoch: int = 0


# ── Startup ───────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    _init_pg_tables()
    _load_cache_from_pg()
    logger.info("Identity service started (PG=%s, agents=%d)",
                "connected" if _get_pg() else "unavailable", len(_identities))


# ── Health ────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    pg_ok = _get_pg() is not None
    active = sum(1 for a in _identities.values() if a.get("active", True))
    return {
        "ok": True, "service": "opencmplx-identity",
        "agents": len(_identities), "active": active,
        "pg": pg_ok, "tiers": list(TIERS.keys()),
    }


# ── Register ──────────────────────────────────────────────────────────

@app.post("/register")
def register(req: IdentityRequest):
    """Register a new agent identity.  Returns full identity record including access_key."""
    aid = req.agent_id or f"agent-{uuid.uuid4().hex[:8]}"
    now = time.time()
    access_key = secrets.token_hex(16)
    initial_receipt = _receipt_hash("genesis", "register", now)
    name = req.name or req.callsign or aid

    agent = {
        "agent_id": aid,
        "name": name,
        "access_key": access_key,
        "session_key": None,
        "snap_dna": req.snapdna,
        "domain": req.domain,
        "parent_id": req.parent_id,
        "tier": "nascent",
        "karma": 0.0,
        "coins": req.coins,
        "epoch": 0,
        "tick_count": 0,
        "zero_coin_ticks": 0,
        "created_at": now,
        "last_seen": now,
        "active": True,
        "receipt_chain": initial_receipt,
        "capabilities": {"max_tools": TIERS["nascent"]["max_tools"], "tier": "nascent"},
    }
    _save_agent(agent)
    logger.info("REGISTER: %s (name=%s, domain=%s, coins=%.1f)",
                aid, name, req.domain, req.coins)
    return agent


# ── Authenticate ──────────────────────────────────────────────────────

@app.post("/authenticate")
def authenticate(req: AuthRequest):
    """Authenticate agent with access_key.  Returns session_key if valid."""
    agent = _load_agent(req.agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")
    if not agent.get("active", True):
        raise HTTPException(403, "Agent deactivated")
    if agent.get("access_key") != req.access_key:
        raise HTTPException(401, "Invalid access key")

    session_key = secrets.token_hex(16)
    now = time.time()
    prev = agent.get("receipt_chain", "genesis")
    agent["session_key"] = session_key
    agent["last_seen"] = now
    agent["receipt_chain"] = _receipt_hash(prev, "authenticate", now)
    _save_agent(agent)
    logger.info("AUTH: %s session granted (tier=%s)", req.agent_id, agent["tier"])
    return {
        "agent_id": req.agent_id,
        "session_key": session_key,
        "tier": agent["tier"],
        "coins": agent.get("coins", 0.0),
        "receipt": agent["receipt_chain"],
    }


# ── Spawn session (internal, no access_key) ──────────────────────────

@app.post("/spawn/{agent_id}")
def spawn_session(agent_id: str):
    """Create a new session for an agent (internal service call)."""
    agent = _load_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")
    if not agent.get("active", True):
        raise HTTPException(403, "Agent deactivated")

    session_key = secrets.token_hex(16)
    now = time.time()
    prev = agent.get("receipt_chain", "genesis")
    agent["session_key"] = session_key
    agent["last_seen"] = now
    agent["receipt_chain"] = _receipt_hash(prev, "spawn", now)
    _save_agent(agent)
    return {
        "agent_id": agent_id,
        "session_key": session_key,
        "tier": agent["tier"],
        "receipt": agent["receipt_chain"],
    }


# ── Tier advancement ─────────────────────────────────────────────────

@app.post("/advance/{agent_id}")
def advance_tier(agent_id: str, req: AdvanceRequest):
    """Check if agent qualifies for tier advancement.

    Requires: epoch >= next tier epoch_req AND mi >= next tier mi_threshold.
    """
    agent = _load_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")

    current_tier = agent.get("tier", "nascent")
    next_t = _next_tier(current_tier)
    if not next_t:
        return {"agent_id": agent_id, "tier": current_tier, "advanced": False,
                "reason": "Already at maximum tier (architect)"}

    reqs = TIERS[next_t]
    epoch = agent.get("epoch", 0)
    mi = req.mi

    if epoch < reqs["epoch_req"]:
        return {"agent_id": agent_id, "tier": current_tier, "advanced": False,
                "reason": f"Epoch {epoch} < required {reqs['epoch_req']} for {next_t}"}
    if mi < reqs["mi_threshold"]:
        return {"agent_id": agent_id, "tier": current_tier, "advanced": False,
                "reason": f"MI {mi:.3f} < required {reqs['mi_threshold']} for {next_t}"}

    # Advance
    now = time.time()
    prev = agent.get("receipt_chain", "genesis")
    agent["tier"] = next_t
    agent["capabilities"] = {"max_tools": reqs["max_tools"], "tier": next_t}
    agent["last_seen"] = now
    agent["receipt_chain"] = _receipt_hash(prev, f"advance:{current_tier}->{next_t}", now)
    _save_agent(agent)
    logger.info("ADVANCE: %s %s -> %s (epoch=%d, mi=%.3f)",
                agent_id, current_tier, next_t, epoch, mi)
    return {
        "agent_id": agent_id, "old_tier": current_tier, "tier": next_t,
        "advanced": True, "max_tools": reqs["max_tools"],
        "receipt": agent["receipt_chain"],
    }


# ── Deactivation (death mechanics) ───────────────────────────────────

@app.post("/deactivate/{agent_id}")
def deactivate(agent_id: str):
    """Deactivate agent.  Preserves record but marks inactive (death)."""
    agent = _load_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")
    if not agent.get("active", True):
        return {"agent_id": agent_id, "deactivated": True, "already": True}

    now = time.time()
    prev = agent.get("receipt_chain", "genesis")
    agent["active"] = False
    agent["session_key"] = None
    agent["last_seen"] = now
    agent["receipt_chain"] = _receipt_hash(prev, "deactivate", now)
    _save_agent(agent)
    logger.info("DEACTIVATE: %s (tier=%s, karma=%.1f, coins=%.1f, ticks=%d)",
                agent_id, agent["tier"], agent.get("karma", 0),
                agent.get("coins", 0), agent.get("tick_count", 0))
    return {"agent_id": agent_id, "deactivated": True, "receipt": agent["receipt_chain"]}


# ── Reactivation ─────────────────────────────────────────────────────

@app.post("/reactivate/{agent_id}")
def reactivate(agent_id: str):
    """Reactivate a deactivated agent (respawn from death)."""
    agent = _load_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")
    if agent.get("active", True):
        return {"agent_id": agent_id, "reactivated": False, "reason": "Already active"}

    now = time.time()
    prev = agent.get("receipt_chain", "genesis")
    agent["active"] = True
    agent["last_seen"] = now
    agent["zero_coin_ticks"] = 0
    agent["receipt_chain"] = _receipt_hash(prev, "reactivate", now)
    _save_agent(agent)
    logger.info("REACTIVATE: %s", agent_id)
    return {"agent_id": agent_id, "reactivated": True, "receipt": agent["receipt_chain"]}


# ── Coin tracking ────────────────────────────────────────────────────

@app.post("/update_coins/{agent_id}")
def update_coins(agent_id: str, req: CoinUpdate):
    """Update agent coin balance.  Tracks zero-coin ticks for death trigger."""
    agent = _load_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")

    old_coins = agent.get("coins", 0.0)
    new_coins = max(0.0, old_coins + req.delta)
    agent["coins"] = new_coins

    # Death mechanics: track consecutive zero-coin ticks
    if new_coins <= 0.0:
        agent["zero_coin_ticks"] = agent.get("zero_coin_ticks", 0) + 1
    else:
        agent["zero_coin_ticks"] = 0

    now = time.time()
    prev = agent.get("receipt_chain", "genesis")
    agent["last_seen"] = now
    agent["receipt_chain"] = _receipt_hash(prev, f"coins:{req.delta:+.2f}", now)
    _save_agent(agent)

    return {
        "agent_id": agent_id,
        "old_coins": round(old_coins, 4),
        "new_coins": round(new_coins, 4),
        "delta": req.delta,
        "reason": req.reason,
        "zero_coin_ticks": agent["zero_coin_ticks"],
        "receipt": agent["receipt_chain"],
    }


# ── Karma tracking ───────────────────────────────────────────────────

@app.post("/update_karma/{agent_id}")
def update_karma(agent_id: str, req: KarmaUpdate):
    """Update agent karma.  Karma never goes below 0."""
    agent = _load_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")

    old_karma = agent.get("karma", 0.0)
    new_karma = max(0.0, old_karma + req.delta)
    agent["karma"] = new_karma

    now = time.time()
    prev = agent.get("receipt_chain", "genesis")
    agent["last_seen"] = now
    agent["receipt_chain"] = _receipt_hash(prev, f"karma:{req.delta:+.2f}", now)
    _save_agent(agent)

    return {
        "agent_id": agent_id,
        "old_karma": round(old_karma, 4),
        "new_karma": round(new_karma, 4),
        "delta": req.delta,
        "reason": req.reason,
        "receipt": agent["receipt_chain"],
    }


# ── Epoch update ─────────────────────────────────────────────────────

@app.post("/set_epoch/{agent_id}")
def set_epoch(agent_id: str, req: EpochUpdate):
    """Set agent epoch (called by spawn service epoch gate)."""
    agent = _load_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")

    old_epoch = agent.get("epoch", 0)
    agent["epoch"] = req.epoch
    now = time.time()
    prev = agent.get("receipt_chain", "genesis")
    agent["last_seen"] = now
    agent["receipt_chain"] = _receipt_hash(prev, f"epoch:{old_epoch}->{req.epoch}", now)
    _save_agent(agent)

    return {"agent_id": agent_id, "old_epoch": old_epoch, "epoch": req.epoch,
            "receipt": agent["receipt_chain"]}


# ── Tick ──────────────────────────────────────────────────────────────

@app.post("/tick/{agent_id}")
def tick(agent_id: str):
    """Increment tick counter, update last_seen.  Returns state summary."""
    agent = _load_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")

    agent["tick_count"] = agent.get("tick_count", 0) + 1
    agent["last_seen"] = time.time()
    _save_agent(agent)

    return {
        "agent_id": agent_id,
        "tick_count": agent["tick_count"],
        "tier": agent["tier"],
        "coins": agent.get("coins", 0.0),
        "karma": agent.get("karma", 0.0),
        "epoch": agent.get("epoch", 0),
        "zero_coin_ticks": agent.get("zero_coin_ticks", 0),
        "active": agent.get("active", True),
    }


# ── Receipt chain ────────────────────────────────────────────────────

@app.post("/receipt/{agent_id}")
def record_receipt(agent_id: str, req: ReceiptRequest):
    """Record a receipt for an agent action, extending the hash chain."""
    agent = _load_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")

    now = time.time()
    prev = agent.get("receipt_chain", "genesis")
    payload = f"{prev}|{req.operation}|{req.input_hash}|{req.output_hash}|{req.delta_phi}|{now}"
    new_receipt = hashlib.sha256(payload.encode()).hexdigest()[:24]

    agent["receipt_chain"] = new_receipt
    agent["last_seen"] = now
    _save_agent(agent)

    return {"agent_id": agent_id, "receipt": new_receipt, "operation": req.operation}


# ── Read endpoints ────────────────────────────────────────────────────

@app.get("/agent/{agent_id}")
def get_identity(agent_id: str):
    """Get agent identity (access_key redacted)."""
    agent = _load_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not registered")
    safe = {k: v for k, v in agent.items() if k != "access_key"}
    return safe


@app.get("/agents")
def list_agents(active_only: bool = False):
    """List all agents (summary view, no access_keys)."""
    agents = _load_all_agents(active_only=active_only)
    return [
        {
            "agent_id": a.get("agent_id"),
            "name": a.get("name"),
            "domain": a.get("domain"),
            "tier": a.get("tier"),
            "karma": a.get("karma", 0.0),
            "coins": a.get("coins", 0.0),
            "active": a.get("active", True),
            "epoch": a.get("epoch", 0),
            "tick_count": a.get("tick_count", 0),
        }
        for a in agents
    ]


@app.get("/tiers")
def get_tiers():
    """Return the tier definitions."""
    return TIERS


@app.get("/stats")
def stats():
    """Aggregate statistics across all agents."""
    agents = _load_all_agents()
    tier_counts: Dict[str, int] = {}
    total_coins = 0.0
    total_karma = 0.0
    active_count = 0
    for a in agents:
        t = a.get("tier", "nascent")
        tier_counts[t] = tier_counts.get(t, 0) + 1
        total_coins += a.get("coins", 0.0)
        total_karma += a.get("karma", 0.0)
        if a.get("active", True):
            active_count += 1
    return {
        "total": len(agents),
        "active": active_count,
        "tier_distribution": tier_counts,
        "total_coins": round(total_coins, 2),
        "total_karma": round(total_karma, 2),
    }


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
