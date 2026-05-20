"""TMN2 Identity Service — Agent identity store with PG persistence.

Port of TMN2 identity.py. Agent registration, authentication,
tier advancement (nascent→architect), coin/karma tracking,
and receipt-chained state changes.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import time
import uuid
from typing import Any, Optional

logger = logging.getLogger("services.identity")

PORT = int(os.environ.get("PORT", "8000"))
PG_URL = os.environ.get("PG_URL", "postgresql://tmn2:tmn2_dev@host.docker.internal:5432/tmn2")

TIERS: dict[str, dict] = {
    "nascent":     {"max_tools": 3,  "epoch_req": 0,  "mi_threshold": 0.0},
    "apprentice":  {"max_tools": 8,  "epoch_req": 1,  "mi_threshold": 0.1},
    "journeyman":  {"max_tools": 15, "epoch_req": 3,  "mi_threshold": 0.3},
    "master":      {"max_tools": 30, "epoch_req": 10, "mi_threshold": 0.5},
    "architect":   {"max_tools": -1, "epoch_req": 25, "mi_threshold": 0.7},
}
TIER_ORDER = ["nascent", "apprentice", "journeyman", "master", "architect"]

_PG_COLS = [
    "agent_id", "name", "access_key", "session_key", "snap_dna",
    "tier", "karma", "coins", "epoch", "tick_count", "zero_coin_ticks",
    "created_at", "last_seen", "active", "receipt_chain", "capabilities",
]


def _next_tier(current: str) -> Optional[str]:
    try:
        idx = TIER_ORDER.index(current)
        if idx + 1 < len(TIER_ORDER):
            return TIER_ORDER[idx + 1]
    except ValueError:
        pass
    return None


def _receipt_hash(prev: str, operation: str, ts: float) -> str:
    payload = f"{prev}|{operation}|{ts}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


class TMN2IdentityService:
    """TMN2 Agent Identity Store.

    PG-backed agent registry with 5-tier capability system,
    authentication, coin/karma economics, death mechanics,
    and receipt-chained state history.
    """

    def __init__(self, pg_url: str = "", governance=None):
        self._governance = governance
        self._pg_url = pg_url or PG_URL
        self._pg_conn = None
        self._identities: dict[str, dict] = {}
        self._init_pg_tables()
        self._load_cache_from_pg()

    def _get_pg(self):
        if not self._pg_url:
            return None
        try:
            import psycopg2
            if self._pg_conn is None or self._pg_conn.closed:
                self._pg_conn = psycopg2.connect(self._pg_url)
                self._pg_conn.autocommit = True
            return self._pg_conn
        except Exception as e:
            logger.warning("PG not available: %s", e)
            return None

    def _init_pg_tables(self):
        conn = self._get_pg()
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
            for col, defn in [
                ("name", "TEXT"), ("coins", "DOUBLE PRECISION DEFAULT 10.0"),
                ("epoch", "INT DEFAULT 0"), ("tick_count", "INT DEFAULT 0"),
                ("zero_coin_ticks", "INT DEFAULT 0"), ("last_seen", "DOUBLE PRECISION"),
                ("active", "BOOLEAN DEFAULT TRUE"), ("receipt_chain", "TEXT"),
                ("capabilities", "JSONB DEFAULT '{}'::jsonb"),
            ]:
                try:
                    cur.execute(f"ALTER TABLE agent_identities ADD COLUMN IF NOT EXISTS {col} {defn}")
                except Exception:
                    pass
            logger.info("PG table agent_identities ensured")
        except Exception as e:
            logger.warning("PG table init failed: %s", e)

    def _row_to_dict(self, cols: list[str], row: tuple) -> dict:
        agent = dict(zip(cols, row))
        for jcol in ("snap_dna", "capabilities"):
            v = agent.get(jcol)
            if isinstance(v, str):
                try:
                    agent[jcol] = json.loads(v)
                except Exception:
                    pass
        return agent

    def _save_agent(self, agent: dict):
        aid = agent["agent_id"]
        self._identities[aid] = agent
        conn = self._get_pg()
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
                agent.get("receipt_chain"), capabilities,
            ))
        except Exception as e:
            logger.warning("PG save failed for %s: %s", aid, e)

    def _load_agent(self, agent_id: str) -> Optional[dict]:
        if agent_id in self._identities:
            return self._identities[agent_id]
        conn = self._get_pg()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM agent_identities WHERE agent_id = %s", (agent_id,))
                row = cur.fetchone()
                if row:
                    cols = [d[0] for d in cur.description]
                    agent = self._row_to_dict(cols, row)
                    self._identities[agent_id] = agent
                    return agent
            except Exception as e:
                logger.warning("PG load failed for %s: %s", agent_id, e)
        return None

    def _load_all_agents(self, active_only: bool = False) -> list[dict]:
        conn = self._get_pg()
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
                    agent = self._row_to_dict(cols, row)
                    self._identities[agent["agent_id"]] = agent
                    results.append(agent)
                return results
            except Exception as e:
                logger.warning("PG list failed: %s", e)
        return list(self._identities.values())

    def _load_cache_from_pg(self):
        self._load_all_agents()
        logger.info("Identity cache: %d agents loaded", len(self._identities))

    # ── Public API ───────────────────────────────────────────

    def register(self, agent_id: str = "", name: str = "",
                 callsign: str = "", snapdna: list[str] = None,
                 domain: str = "", parent_id: str = "",
                 coins: float = 10.0) -> dict:
        aid = agent_id or f"agent-{uuid.uuid4().hex[:8]}"
        now = time.time()
        access_key = secrets.token_hex(16)
        initial_receipt = _receipt_hash("genesis", "register", now)
        name = name or callsign or aid

        agent = {
            "agent_id": aid, "name": name, "access_key": access_key,
            "session_key": None, "snap_dna": snapdna or [],
            "domain": domain, "parent_id": parent_id,
            "tier": "nascent", "karma": 0.0, "coins": coins, "epoch": 0,
            "tick_count": 0, "zero_coin_ticks": 0,
            "created_at": now, "last_seen": now, "active": True,
            "receipt_chain": initial_receipt,
            "capabilities": {"max_tools": TIERS["nascent"]["max_tools"],
                             "tier": "nascent"},
        }
        self._save_agent(agent)
        logger.info("REGISTER: %s (name=%s, domain=%s, coins=%.1f)",
                    aid, name, domain, coins)

        if self._governance:
            from governance.engine import BoundaryEvent
            self._governance.record_boundary_event(BoundaryEvent(
                event_id=f"identity-register-{aid}",
                timestamp=now, entropy_delta=0.0,
                receipt_data={"agent_id": aid, "tier": "nascent"},
                boundary_type="identity_register",
            ))

        return agent

    def authenticate(self, agent_id: str, access_key: str) -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")
        if not agent.get("active", True):
            raise ValueError("Agent deactivated")
        if agent.get("access_key") != access_key:
            raise ValueError("Invalid access key")

        session_key = secrets.token_hex(16)
        now = time.time()
        prev = agent.get("receipt_chain", "genesis")
        agent["session_key"] = session_key
        agent["last_seen"] = now
        agent["receipt_chain"] = _receipt_hash(prev, "authenticate", now)
        self._save_agent(agent)
        logger.info("AUTH: %s session granted (tier=%s)", agent_id, agent["tier"])
        return {
            "agent_id": agent_id, "session_key": session_key,
            "tier": agent["tier"], "coins": agent.get("coins", 0.0),
            "receipt": agent["receipt_chain"],
        }

    def spawn_session(self, agent_id: str) -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")
        if not agent.get("active", True):
            raise ValueError("Agent deactivated")

        session_key = secrets.token_hex(16)
        now = time.time()
        prev = agent.get("receipt_chain", "genesis")
        agent["session_key"] = session_key
        agent["last_seen"] = now
        agent["receipt_chain"] = _receipt_hash(prev, "spawn", now)
        self._save_agent(agent)
        return {
            "agent_id": agent_id, "session_key": session_key,
            "tier": agent["tier"], "receipt": agent["receipt_chain"],
        }

    def advance_tier(self, agent_id: str, mi: float = 0.0) -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")

        current_tier = agent.get("tier", "nascent")
        next_t = _next_tier(current_tier)
        if not next_t:
            return {"agent_id": agent_id, "tier": current_tier, "advanced": False,
                    "reason": "Already at maximum tier (architect)"}

        reqs = TIERS[next_t]
        epoch = agent.get("epoch", 0)

        if epoch < reqs["epoch_req"]:
            return {"agent_id": agent_id, "tier": current_tier, "advanced": False,
                    "reason": f"Epoch {epoch} < required {reqs['epoch_req']} for {next_t}"}
        if mi < reqs["mi_threshold"]:
            return {"agent_id": agent_id, "tier": current_tier, "advanced": False,
                    "reason": f"MI {mi:.3f} < required {reqs['mi_threshold']} for {next_t}"}

        now = time.time()
        prev = agent.get("receipt_chain", "genesis")
        agent["tier"] = next_t
        agent["capabilities"] = {"max_tools": reqs["max_tools"], "tier": next_t}
        agent["last_seen"] = now
        agent["receipt_chain"] = _receipt_hash(prev, f"advance:{current_tier}->{next_t}", now)
        self._save_agent(agent)
        logger.info("ADVANCE: %s %s -> %s (epoch=%d, mi=%.3f)",
                    agent_id, current_tier, next_t, epoch, mi)
        return {
            "agent_id": agent_id, "old_tier": current_tier, "tier": next_t,
            "advanced": True, "max_tools": reqs["max_tools"],
            "receipt": agent["receipt_chain"],
        }

    def deactivate(self, agent_id: str) -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")
        if not agent.get("active", True):
            return {"agent_id": agent_id, "deactivated": True, "already": True}

        now = time.time()
        prev = agent.get("receipt_chain", "genesis")
        agent["active"] = False
        agent["session_key"] = None
        agent["last_seen"] = now
        agent["receipt_chain"] = _receipt_hash(prev, "deactivate", now)
        self._save_agent(agent)
        logger.info("DEACTIVATE: %s (tier=%s, karma=%.1f, coins=%.1f, ticks=%d)",
                    agent_id, agent["tier"], agent.get("karma", 0),
                    agent.get("coins", 0), agent.get("tick_count", 0))
        return {"agent_id": agent_id, "deactivated": True,
                "receipt": agent["receipt_chain"]}

    def reactivate(self, agent_id: str) -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")
        if agent.get("active", True):
            return {"agent_id": agent_id, "reactivated": False,
                    "reason": "Already active"}

        now = time.time()
        prev = agent.get("receipt_chain", "genesis")
        agent["active"] = True
        agent["last_seen"] = now
        agent["zero_coin_ticks"] = 0
        agent["receipt_chain"] = _receipt_hash(prev, "reactivate", now)
        self._save_agent(agent)
        logger.info("REACTIVATE: %s", agent_id)
        return {"agent_id": agent_id, "reactivated": True,
                "receipt": agent["receipt_chain"]}

    def update_coins(self, agent_id: str, delta: float = 0.0,
                     reason: str = "") -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")

        old_coins = agent.get("coins", 0.0)
        new_coins = max(0.0, old_coins + delta)
        agent["coins"] = new_coins

        if new_coins <= 0.0:
            agent["zero_coin_ticks"] = agent.get("zero_coin_ticks", 0) + 1
        else:
            agent["zero_coin_ticks"] = 0

        now = time.time()
        prev = agent.get("receipt_chain", "genesis")
        agent["last_seen"] = now
        agent["receipt_chain"] = _receipt_hash(prev, f"coins:{delta:+.2f}", now)
        self._save_agent(agent)

        return {
            "agent_id": agent_id, "old_coins": round(old_coins, 4),
            "new_coins": round(new_coins, 4), "delta": delta,
            "reason": reason, "zero_coin_ticks": agent["zero_coin_ticks"],
            "receipt": agent["receipt_chain"],
        }

    def update_karma(self, agent_id: str, delta: float = 0.0,
                     reason: str = "") -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")

        old_karma = agent.get("karma", 0.0)
        new_karma = max(0.0, old_karma + delta)
        agent["karma"] = new_karma

        now = time.time()
        prev = agent.get("receipt_chain", "genesis")
        agent["last_seen"] = now
        agent["receipt_chain"] = _receipt_hash(prev, f"karma:{delta:+.2f}", now)
        self._save_agent(agent)

        return {
            "agent_id": agent_id, "old_karma": round(old_karma, 4),
            "new_karma": round(new_karma, 4), "delta": delta,
            "reason": reason, "receipt": agent["receipt_chain"],
        }

    def set_epoch(self, agent_id: str, epoch: int = 0) -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")

        old_epoch = agent.get("epoch", 0)
        agent["epoch"] = epoch
        now = time.time()
        prev = agent.get("receipt_chain", "genesis")
        agent["last_seen"] = now
        agent["receipt_chain"] = _receipt_hash(prev, f"epoch:{old_epoch}->{epoch}", now)
        self._save_agent(agent)

        return {"agent_id": agent_id, "old_epoch": old_epoch, "epoch": epoch,
                "receipt": agent["receipt_chain"]}

    def tick(self, agent_id: str) -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")

        agent["tick_count"] = agent.get("tick_count", 0) + 1
        agent["last_seen"] = time.time()
        self._save_agent(agent)

        return {
            "agent_id": agent_id, "tick_count": agent["tick_count"],
            "tier": agent["tier"], "coins": agent.get("coins", 0.0),
            "karma": agent.get("karma", 0.0), "epoch": agent.get("epoch", 0),
            "zero_coin_ticks": agent.get("zero_coin_ticks", 0),
            "active": agent.get("active", True),
        }

    def record_receipt(self, agent_id: str, operation: str = "",
                       input_hash: str = "", output_hash: str = "",
                       delta_phi: float = 0.0) -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")

        now = time.time()
        prev = agent.get("receipt_chain", "genesis")
        payload = f"{prev}|{operation}|{input_hash}|{output_hash}|{delta_phi}|{now}"
        new_receipt = hashlib.sha256(payload.encode()).hexdigest()[:24]

        agent["receipt_chain"] = new_receipt
        agent["last_seen"] = now
        self._save_agent(agent)

        return {"agent_id": agent_id, "receipt": new_receipt,
                "operation": operation}

    def get_identity(self, agent_id: str) -> dict:
        agent = self._load_agent(agent_id)
        if not agent:
            raise ValueError("Agent not registered")
        safe = {k: v for k, v in agent.items() if k != "access_key"}
        safe["_tier_info"] = TIERS.get(agent.get("tier", "nascent"), {})
        return safe

    def list_agents(self, active_only: bool = False) -> list[dict]:
        agents = self._load_all_agents(active_only=active_only)
        return [
            {
                "agent_id": a.get("agent_id"), "name": a.get("name"),
                "domain": a.get("domain"), "tier": a.get("tier"),
                "karma": a.get("karma", 0.0), "coins": a.get("coins", 0.0),
                "active": a.get("active", True), "epoch": a.get("epoch", 0),
                "tick_count": a.get("tick_count", 0),
            }
            for a in agents
        ]

    @property
    def tiers(self) -> dict:
        return TIERS

    @property
    def stats(self) -> dict:
        agents = self._load_all_agents()
        tier_counts: dict[str, int] = {}
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
            "total": len(agents), "active": active_count,
            "tier_distribution": tier_counts,
            "total_coins": round(total_coins, 2),
            "total_karma": round(total_karma, 2),
        }

    @property
    def health(self) -> dict:
        pg_ok = self._get_pg() is not None
        active = sum(1 for a in self._identities.values() if a.get("active", True))
        return {
            "ok": True, "service": "tmn2-identity",
            "agents": len(self._identities), "active": active,
            "pg": pg_ok, "tiers": list(TIERS.keys()),
        }
