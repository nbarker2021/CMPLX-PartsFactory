"""SpawnService — Agent birth, death, epoch gate. Full lifecycle orchestrator."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

import psycopg2

from governance.engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("spawn_service")

_host = "host.docker.internal"

PORT = int(os.environ.get("PORT", "8000"))
IDENTITY_URL = os.environ.get("IDENTITY_URL", f"http://{_host}:8004")
BRAIN_URL = os.environ.get("BRAIN_URL", f"http://{_host}:8008")
MINT_URL = os.environ.get("MINT_URL", f"http://{_host}:8003")
COOP_URL = os.environ.get("COOP_URL", f"http://{_host}:8005")
BOARD_URL = os.environ.get("BOARD_URL", f"http://{_host}:8000")
PG_URL = os.environ.get("PG_URL", f"postgresql://tmn2:tmn2_dev@{_host}:5432/tmn2")

SHELL_WEIGHTS = {0: 1.0, 1: 0.5, 2: 0.25, 3: 0.125}
DEATH_TICK_THRESHOLD = 100
EPOCH_TICK_INTERVAL = 300

DOMAIN_TO_DEPT = {
    "geometry": "geometry", "tarpit": "computation", "snap": "code",
    "agent": "agents", "physics": "physics", "economics": "economy",
    "code": "code", "philosophy": "reasoning", "scanner": "intake",
    "training": "training", "reasoning": "reasoning", "governance": "governance",
}


def assign_shell(parent_depth: int) -> int:
    return min(parent_depth + 1, 3)


def _post(url: str, path: str, data: dict, timeout: int = 10) -> Optional[dict]:
    try:
        import urllib.request
        body = json.dumps(data).encode()
        req = urllib.request.Request(
            f"{url}{path}", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        logger.warning("POST %s%s failed: %s", url, path, exc)
        return None


def _get(url: str, path: str, timeout: int = 10) -> Optional[dict]:
    try:
        import urllib.request
        req = urllib.request.Request(f"{url}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        logger.warning("GET %s%s failed: %s", url, path, exc)
        return None


class SpawnService:
    """Agent lifecycle orchestrator: birth, death, epoch gate."""

    def __init__(self, governance: Optional[GeometricGovernance] = None):
        self.governance = governance
        self._pg_conn = None
        self._births: List[Dict] = []
        self._lock = threading.Lock()

    def _get_pg(self):
        if not PG_URL:
            return None
        try:
            if self._pg_conn is None or self._pg_conn.closed:
                self._pg_conn = psycopg2.connect(PG_URL)
                self._pg_conn.autocommit = True
            return self._pg_conn
        except Exception as e:
            logger.warning("PG not available: %s", e)
            return None

    def init_pg_tables(self):
        conn = self._get_pg()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS spawn_births (
                    child_id TEXT PRIMARY KEY, parent_id TEXT, domain TEXT, name TEXT,
                    shell INT DEFAULT 0, coin_name TEXT, born_at DOUBLE PRECISION,
                    died_at DOUBLE PRECISION, alive BOOLEAN DEFAULT TRUE,
                    birth_record JSONB DEFAULT '{}'::jsonb)
            """)
            logger.info("PG table spawn_births ensured")
        except Exception as e:
            logger.warning("PG table init failed: %s", e)

    def _save_birth(self, record: Dict):
        self._births.append(record)
        conn = self._get_pg()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO spawn_births
                    (child_id, parent_id, domain, name, shell, coin_name, born_at, alive, birth_record)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (child_id) DO UPDATE SET
                    alive=EXCLUDED.alive, birth_record=EXCLUDED.birth_record
            """, (record["child_id"], record.get("parent_id"), record.get("domain"),
                  record.get("name"), record.get("shell", 0), record.get("coin_name"),
                  record.get("born_at"), record.get("alive", True), json.dumps(record)))
        except Exception as e:
            logger.warning("PG save birth failed: %s", e)

    def _mark_death(self, child_id: str):
        conn = self._get_pg()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("UPDATE spawn_births SET alive = FALSE, died_at = %s WHERE child_id = %s",
                        (time.time(), child_id))
        except Exception as e:
            logger.warning("PG mark death failed: %s", e)

    # ── Birth ───────────────────────────────────────────────────────────

    def birth(self, parent_id: str = "", domain: str = "", name: str = "",
              callsign: str = "", snapdna: List[str] = None,
              escrow_merit: float = 10.0, domain_boost: str = "") -> Dict[str, Any]:
        child_id = f"agent-{uuid.uuid4().hex[:8]}"
        now = time.time()
        agent_name = name or callsign or child_id
        steps: Dict[str, Any] = {}

        identity_resp = _post(IDENTITY_URL, "/register", {
            "agent_id": child_id, "name": agent_name, "callsign": agent_name,
            "snapdna": snapdna or [], "domain": domain, "parent_id": parent_id,
            "coins": escrow_merit,
        })
        steps["identity"] = identity_resp or {"error": "identity service unavailable"}
        access_key = (identity_resp or {}).get("access_key")

        brain_resp = _post(BRAIN_URL, "/register", {
            "agent_id": child_id, "domain": domain, "parent_id": parent_id,
            "domain_boost": domain_boost, "snapdna": snapdna or [],
        })
        steps["brain"] = brain_resp or {"error": "brain service unavailable"}

        parent_shell = 0
        if parent_id:
            parent_info = _get(IDENTITY_URL, f"/agent/{parent_id}")
            if parent_info:
                parent_shell = parent_info.get("shell", 0)
        child_shell = assign_shell(parent_shell)
        shell_weight = SHELL_WEIGHTS.get(child_shell, 0.125)
        steps["shell"] = {"depth": child_shell, "weight": shell_weight, "parent_shell": parent_shell}

        coin_name = f"{domain.upper()}_{child_id[-8:]}" if domain else child_id
        mint_resp = _post(MINT_URL, "/mint", {
            "agent_id": child_id, "coin_name": coin_name, "domain": domain,
            "initial_value": escrow_merit * shell_weight, "snapdna": snapdna or [],
        })
        steps["mint"] = mint_resp or {"error": "mint service unavailable"}

        department = DOMAIN_TO_DEPT.get(domain, "meta")
        coop_resp = _post(COOP_URL, "/register", {
            "agent_id": child_id, "snapdna": snapdna or [],
            "department": department, "karma": 0.0, "epoch": 0,
        })
        steps["coop"] = coop_resp or {"error": "coop service unavailable"}

        birth_record = {
            "child_id": child_id, "parent_id": parent_id, "domain": domain,
            "name": agent_name, "snapdna": snapdna or [],
            "escrow_merit": escrow_merit, "shell": child_shell,
            "shell_weight": shell_weight, "coin_name": coin_name,
            "born_at": now, "alive": True, "steps": steps, "access_key": access_key,
        }
        self._save_birth(birth_record)

        _post(BOARD_URL, "/post", {
            "board": "agent-work", "author": "spawn-service",
            "title": f"Birth: {agent_name} ({child_id})",
            "body": json.dumps({
                "event": "birth", "child_id": child_id, "parent_id": parent_id,
                "domain": domain, "shell": child_shell,
            }),
            "labels": ["event_birth", f"domain_{domain}"],
        })

        if self.governance:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"birth-{child_id}", timestamp=now, entropy_delta=-escrow_merit * shell_weight,
                receipt_data={"child_id": child_id, "domain": domain, "shell": child_shell},
                boundary_type="spawn_birth",
            ))

        logger.info("BIRTH: %s (parent=%s, domain=%s, shell=%d, coins=%.1f)",
                     child_id, parent_id or "none", domain, child_shell, escrow_merit)
        return birth_record

    # ── Death ───────────────────────────────────────────────────────────

    def death(self, agent_id: str, reason: str = "zero_coins_100_ticks") -> Dict[str, Any]:
        now = time.time()
        steps: Dict[str, Any] = {}
        deact_resp = _post(IDENTITY_URL, f"/deactivate/{agent_id}", {})
        steps["identity"] = deact_resp or {"error": "identity deactivation failed"}
        archive_resp = _post(BRAIN_URL, f"/archive/{agent_id}", {})
        steps["brain"] = archive_resp or {"error": "brain archive failed"}
        remove_resp = _post(COOP_URL, f"/remove/{agent_id}", {})
        steps["coop"] = remove_resp or {"error": "coop removal failed"}
        obit_resp = _post(BOARD_URL, "/post", {
            "board": "agent-work", "author": "spawn-service",
            "title": f"Death: {agent_id}",
            "body": json.dumps({"event": "death", "agent_id": agent_id, "reason": reason, "died_at": now}),
            "labels": ["event_death"],
        })
        steps["board"] = obit_resp or {"error": "board post failed"}
        self._mark_death(agent_id)
        logger.info("DEATH: %s (reason=%s)", agent_id, reason)
        return {"agent_id": agent_id, "died_at": now, "reason": reason, "steps": steps}

    # ── Epoch Gate ──────────────────────────────────────────────────────

    def epoch_gate(self, agent_id: str, tick_count: int = 0, mi: float = 0.0) -> Dict[str, Any]:
        if tick_count <= 0 or tick_count % EPOCH_TICK_INTERVAL != 0:
            return {
                "agent_id": agent_id, "gate_triggered": False,
                "tick_count": tick_count,
                "next_gate_at": ((tick_count // EPOCH_TICK_INTERVAL) + 1) * EPOCH_TICK_INTERVAL,
            }
        new_epoch = tick_count // EPOCH_TICK_INTERVAL
        steps: Dict[str, Any] = {}
        epoch_resp = _post(IDENTITY_URL, f"/set_epoch/{agent_id}", {"epoch": new_epoch})
        steps["set_epoch"] = epoch_resp or {"error": "epoch update failed"}
        advance_resp = _post(IDENTITY_URL, f"/advance/{agent_id}", {"mi": mi})
        steps["advance"] = advance_resp or {"error": "advance check failed"}
        advanced = (advance_resp or {}).get("advanced", False)
        new_tier = (advance_resp or {}).get("tier", "unknown")
        _post(BOARD_URL, "/post", {
            "board": "agent-work", "author": "spawn-service",
            "title": f"Epoch gate: {agent_id} -> epoch {new_epoch}",
            "body": json.dumps({
                "event": "epoch_gate", "agent_id": agent_id,
                "epoch": new_epoch, "tick_count": tick_count,
                "advanced": advanced, "tier": new_tier,
            }),
            "labels": ["event_epoch_gate"],
        })
        logger.info("EPOCH GATE: %s epoch=%d, advanced=%s, tier=%s", agent_id, new_epoch, advanced, new_tier)
        return {
            "agent_id": agent_id, "gate_triggered": True, "epoch": new_epoch,
            "tick_count": tick_count, "advanced": advanced, "tier": new_tier, "steps": steps,
        }

    # ── Death check ─────────────────────────────────────────────────────

    def check_death(self, agent_id: str) -> Dict[str, Any]:
        agent_info = _get(IDENTITY_URL, f"/agent/{agent_id}")
        if not agent_info:
            return {"agent_id": agent_id, "should_die": False, "error": "agent not found"}
        zero_ticks = agent_info.get("zero_coin_ticks", 0)
        coins = agent_info.get("coins", 0.0)
        active = agent_info.get("active", True)
        if not active:
            return {"agent_id": agent_id, "should_die": False, "already_dead": True}
        if coins <= 0.0 and zero_ticks >= DEATH_TICK_THRESHOLD:
            death_result = self.death(agent_id, reason=f"zero_coins_{zero_ticks}_ticks")
            return {"agent_id": agent_id, "should_die": True, "zero_ticks": zero_ticks, "death_result": death_result}
        return {"agent_id": agent_id, "should_die": False, "coins": coins, "zero_ticks": zero_ticks, "death_threshold": DEATH_TICK_THRESHOLD}

    # ── List / Get ──────────────────────────────────────────────────────

    def list_births(self, limit: int = 50, alive_only: bool = False) -> List[Dict]:
        conn = self._get_pg()
        if conn:
            try:
                cur = conn.cursor()
                q = "SELECT child_id, parent_id, domain, name, shell, coin_name, born_at, died_at, alive FROM spawn_births"
                if alive_only:
                    q += " WHERE alive = TRUE"
                q += " ORDER BY born_at DESC LIMIT %s"
                cur.execute(q, (limit,))
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
            except Exception as e:
                logger.warning("PG list births failed: %s", e)
        result = self._births[-limit:]
        if alive_only:
            result = [b for b in result if b.get("alive", True)]
        return result

    def get_birth(self, child_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_pg()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT birth_record FROM spawn_births WHERE child_id = %s", (child_id,))
                row = cur.fetchone()
                if row:
                    rec = row[0]
                    return rec if isinstance(rec, dict) else json.loads(rec)
            except Exception as e:
                logger.warning("PG get birth failed: %s", e)
        for b in self._births:
            if b.get("child_id") == child_id:
                return b
        return None

    def health(self) -> Dict[str, Any]:
        pg_ok = self._get_pg() is not None
        return {"ok": True, "service": "opencmplx-spawn", "births": len(self._births), "pg": pg_ok}
