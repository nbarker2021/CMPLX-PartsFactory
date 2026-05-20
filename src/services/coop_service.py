"""CoopService — Agent matching, activity management, 12 departments."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import time
from typing import Any, Dict, List, Optional, Set

import psycopg2

from governance.engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("coop_service")

_host = "host.docker.internal"

PORT = int(os.environ.get("PORT", "8000"))
PG_URL = os.environ.get("PG_URL", f"postgresql://tmn2:tmn2_dev@{_host}:5432/tmn2")
BOARD_URL = os.environ.get("BOARD_URL", f"http://{_host}:8000")
PIPELINE_URL = os.environ.get("PIPELINE_URL", f"http://{_host}:8001")
ARENA_URL = os.environ.get("ARENA_URL", f"http://{_host}:8009")
IDENTITY_URL = os.environ.get("IDENTITY_URL", f"http://{_host}:8004")
INGRESS_URL = os.environ.get("INGRESS_URL", f"http://{_host}:8010")
MINT_URL = os.environ.get("MINT_URL", f"http://{_host}:8003")

DEPARTMENTS = {
    "geometry":    {"board": "geometry",    "labels": ["SNAPdomain_geometry"],   "desc": "E8 lattice, MORSR, ALENA, projections"},
    "computation": {"board": "operations",  "labels": ["SNAPdomain_tarpit"],     "desc": "E6 tokens, grain/bond chemistry, encoding"},
    "agents":      {"board": "agent-work",  "labels": ["SNAPdomain_agent"],      "desc": "Agent lifecycle, boards, cooperative"},
    "economy":     {"board": "economy",     "labels": ["SNAPdomain_economy"],    "desc": "Coins, treasury, market dynamics"},
    "governance":  {"board": "governance",  "labels": ["SNAPdomain_governance"], "desc": "SAP, sentinel, arbiter, porter"},
    "training":    {"board": "training",    "labels": ["SNAPdomain_training"],   "desc": "Arena, competitive training"},
    "reasoning":   {"board": "findings",    "labels": ["SNAPdomain_philosophy"], "desc": "ThinkTank, deep reasoning"},
    "physics":     {"board": "physics",     "labels": ["SNAPdomain_physics"],    "desc": "Conservation, morphon, delta_phi"},
    "code":        {"board": "code",        "labels": ["SNAPdomain_code"],       "desc": "Pipeline, tools, capsules, infrastructure"},
    "intake":      {"board": "work",        "labels": ["SNAPdomain_intake"],     "desc": "Filesystem intake, archive scanning"},
    "storage":     {"board": "storage",     "labels": ["SNAPdomain_storage"],    "desc": "MMDB, crystal, persistence"},
    "meta":        {"board": "meta-analysis","labels": ["SNAPdomain_meta"],      "desc": "Cross-domain analysis, meta-reasoning"},
}

ACTIVITY_WEIGHTS = {"contribute": 0.30, "browse_board": 0.20, "bounty_work": 0.25, "arena": 0.15, "idle": 0.10}
STATES = ["idle", "active", "returning"]


def _jaccard(a: set, b: set) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def _pick_activity() -> str:
    r = random.random()
    cumulative = 0.0
    for act, w in ACTIVITY_WEIGHTS.items():
        cumulative += w
        if r <= cumulative:
            return act
    return "idle"


def _post(url: str, path: str, data: dict, timeout: int = 10) -> Optional[dict]:
    try:
        import urllib.request
        body = json.dumps(data).encode()
        req = urllib.request.Request(f"{url}{path}", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def _http_get(url: str, path: str, timeout: int = 10) -> Optional[Any]:
    try:
        import urllib.request
        req = urllib.request.Request(f"{url}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


class CoopService:
    """Agent cooperative — 12 departments, Jaccard matching, tick activities."""

    def __init__(self, governance: Optional[GeometricGovernance] = None):
        self.governance = governance
        self._pg_conn = None
        self._agents: Dict[str, Dict] = {}
        self._activity_log: List[Dict] = []

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
                CREATE TABLE IF NOT EXISTS coop_agents (
                    agent_id TEXT PRIMARY KEY, department TEXT,
                    snap_dna JSONB DEFAULT '[]'::jsonb, karma DOUBLE PRECISION DEFAULT 0,
                    activity_state TEXT DEFAULT 'idle', last_activity TEXT,
                    last_tick DOUBLE PRECISION, tick_count INT DEFAULT 0,
                    expertise JSONB DEFAULT '[]'::jsonb, joined_at DOUBLE PRECISION)
            """)
            for col, defn in [("activity_state", "TEXT DEFAULT 'idle'"), ("last_activity", "TEXT"),
                              ("last_tick", "DOUBLE PRECISION"), ("tick_count", "INT DEFAULT 0"),
                              ("expertise", "JSONB DEFAULT '[]'::jsonb"), ("joined_at", "DOUBLE PRECISION")]:
                try:
                    cur.execute(f"ALTER TABLE coop_agents ADD COLUMN IF NOT EXISTS {col} {defn}")
                except Exception:
                    pass
            logger.info("PG table coop_agents ensured")
        except Exception as e:
            logger.warning("PG table init failed: %s", e)

    def _save_coop_agent(self, ag: Dict):
        aid = ag["agent_id"]
        self._agents[aid] = ag
        conn = self._get_pg()
        if not conn:
            return
        try:
            cur = conn.cursor()
            snap_dna = list(ag.get("snap_dna", [])) if isinstance(ag.get("snap_dna"), set) else ag.get("snap_dna", [])
            expertise = list(ag.get("expertise", [])) if isinstance(ag.get("expertise"), set) else ag.get("expertise", [])
            cur.execute("""
                INSERT INTO coop_agents (agent_id, department, snap_dna, karma, activity_state,
                    last_activity, last_tick, tick_count, expertise, joined_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (agent_id) DO UPDATE SET
                    department=EXCLUDED.department, snap_dna=EXCLUDED.snap_dna,
                    karma=EXCLUDED.karma, activity_state=EXCLUDED.activity_state,
                    last_activity=EXCLUDED.last_activity, last_tick=EXCLUDED.last_tick,
                    tick_count=EXCLUDED.tick_count, expertise=EXCLUDED.expertise
            """, (aid, ag.get("department"), json.dumps(snap_dna), ag.get("karma", 0.0),
                  ag.get("activity_state", "idle"), ag.get("last_activity"),
                  ag.get("last_tick"), ag.get("tick_count", 0), json.dumps(expertise), ag.get("joined_at")))
        except Exception as e:
            logger.warning("PG save coop agent failed: %s", e)

    def _load_coop_agent(self, agent_id: str) -> Optional[Dict]:
        if agent_id in self._agents:
            return self._agents[agent_id]
        conn = self._get_pg()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT * FROM coop_agents WHERE agent_id = %s", (agent_id,))
                row = cur.fetchone()
                if row:
                    cols = [d[0] for d in cur.description]
                    ag = dict(zip(cols, row))
                    for jcol in ("snap_dna", "expertise"):
                        v = ag.get(jcol)
                        if isinstance(v, str):
                            ag[jcol] = json.loads(v)
                    if isinstance(ag.get("snap_dna"), list):
                        ag["snap_dna"] = set(ag["snap_dna"])
                    self._agents[agent_id] = ag
                    return ag
            except Exception as e:
                logger.warning("PG load coop agent failed: %s", e)
        return None

    def load_cache_from_pg(self):
        conn = self._get_pg()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM coop_agents")
            cols = [d[0] for d in cur.description]
            for row in cur.fetchall():
                ag = dict(zip(cols, row))
                for jcol in ("snap_dna", "expertise"):
                    v = ag.get(jcol)
                    if isinstance(v, str):
                        ag[jcol] = json.loads(v)
                if isinstance(ag.get("snap_dna"), list):
                    ag["snap_dna"] = set(ag["snap_dna"])
                self._agents[ag["agent_id"]] = ag
            logger.info("Loaded %d coop agents from PG", len(self._agents))
        except Exception as e:
            logger.warning("PG cache load failed: %s", e)

    # ── Matching ────────────────────────────────────────────────────────

    def match_expertise(self, task_labels: List[str], top_k: int = 5) -> List[Dict]:
        target = set(task_labels)
        if not target:
            return []
        conn = self._get_pg()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT agent_id, snap_dna, department FROM coop_agents WHERE activity_state = 'idle'")
                scored = []
                for row in cur.fetchall():
                    aid, dna_raw, dept = row[0], row[1], row[2]
                    if isinstance(dna_raw, str):
                        dna_raw = json.loads(dna_raw)
                    if isinstance(dna_raw, list):
                        dna_set = set(dna_raw)
                    elif isinstance(dna_raw, dict):
                        dna_set = set(dna_raw.keys())
                    else:
                        dna_set = set()
                    s = _jaccard(target, dna_set)
                    if s > 0:
                        scored.append({"agent_id": aid, "score": round(s, 4), "department": dept})
                scored.sort(key=lambda x: -x["score"])
                return scored[:top_k]
            except Exception as e:
                logger.warning("PG match_expertise failed: %s", e)
        scored = []
        for aid, ag in self._agents.items():
            if ag.get("activity_state", "idle") != "idle":
                continue
            dna = ag.get("snap_dna", set())
            if isinstance(dna, list):
                dna = set(dna)
            s = _jaccard(target, dna)
            if s > 0:
                scored.append({"agent_id": aid, "score": round(s, 4), "department": ag.get("department", "")})
        scored.sort(key=lambda x: -x["score"])
        return scored[:top_k]

    def match_for_task(self, labels: List[str], top_k: int = 5) -> List[Dict]:
        results = self.match_expertise(labels, top_k)
        enriched = []
        for m in results:
            dept = m.get("department", "")
            dept_info = DEPARTMENTS.get(dept, {})
            m["board"] = dept_info.get("board", "")
            m["dept_labels"] = dept_info.get("labels", [])
            enriched.append(m)
        return enriched

    # ── Tick Activities ─────────────────────────────────────────────────

    def _execute_contribute(self, agent_id: str, department: str) -> Dict:
        dept_info = DEPARTMENTS.get(department, {})
        board_name = dept_info.get("board", "work")
        labels = dept_info.get("labels", [])
        result = _post(PIPELINE_URL, "/ingest", {
            "agent_id": agent_id, "content": f"Contribution from {agent_id} in {department}", "labels": labels,
        })
        return {"activity": "contribute", "department": department, "result": result or "submitted"}

    def _execute_browse_board(self, agent_id: str, department: str) -> Dict:
        dept_info = DEPARTMENTS.get(department, {})
        board_name = dept_info.get("board", "work")
        posts = _http_get(BOARD_URL, f"/posts?board={board_name}&limit=5")
        return {"activity": "browse_board", "board": board_name, "posts_found": len(posts) if isinstance(posts, list) else 0}

    def _execute_bounty_work(self, agent_id: str, agent_dna: set) -> Dict:
        bounties_resp = _http_get(BOARD_URL, "/bounties?status=open&limit=10")
        if not bounties_resp:
            return {"activity": "bounty_work", "claimed": False, "reason": "board unreachable"}
        if isinstance(bounties_resp, dict):
            bounties = bounties_resp.get("bounties", [])
        elif isinstance(bounties_resp, list):
            bounties = bounties_resp
        else:
            return {"activity": "bounty_work", "claimed": False, "reason": "unexpected bounty format"}
        if not bounties:
            return {"activity": "bounty_work", "claimed": False, "reason": "no open bounties"}
        best_bounty = None
        best_score = 0.0
        for b in bounties:
            b_labels = b.get("snap_labels", b.get("labels", []))
            if isinstance(b_labels, str):
                try: b_labels = json.loads(b_labels)
                except: b_labels = []
            s = _jaccard(agent_dna, set(b_labels))
            if s > best_score:
                best_score = s
                best_bounty = b
        if not best_bounty and bounties:
            best_bounty = bounties[0]
        if not best_bounty:
            return {"activity": "bounty_work", "claimed": False, "reason": "no matching bounties"}
        bounty_id = best_bounty.get("bounty_id", best_bounty.get("id", ""))
        need = best_bounty.get("need", best_bounty.get("title", ""))
        context = best_bounty.get("context", best_bounty.get("description", ""))
        reward = best_bounty.get("reward_coins", best_bounty.get("reward", 1.0))
        _post(BOARD_URL, f"/bounties/{bounty_id}/update", {"status": "claimed", "claimed_by": agent_id})
        bounty_labels = best_bounty.get("snap_labels", [])
        if isinstance(bounty_labels, str):
            try: bounty_labels = json.loads(bounty_labels)
            except: bounty_labels = []
        pipeline_resp = _post(PIPELINE_URL, "/process", {
            "content": f"{need}\n\n{context}"[:4000], "source": f"bounty::{bounty_id}::work::{agent_id}",
            "agent_id": agent_id, "epoch": 0,
        })
        atom_id = ""; labels_produced = 0; dphi = 0.0; work_labels = []
        if pipeline_resp and not pipeline_resp.get("error"):
            atom_id = pipeline_resp.get("atom_id", "")
            work_labels = pipeline_resp.get("snap_labels", [])
            labels_produced = len(work_labels)
            dphi = pipeline_resp.get("delta_phi", 0.0)
        else:
            _post(BOARD_URL, f"/bounties/{bounty_id}/update", {"status": "open", "claimed_by": ""})
            return {"activity": "bounty_work", "claimed": True, "worked": False, "bounty_id": bounty_id, "reason": "pipeline failed"}
        completion_report = json.dumps({
            "report_type": "bounty_completion", "bounty_id": bounty_id,
            "agent_id": agent_id, "need": need, "atom_id": atom_id,
            "labels_produced": labels_produced, "labels": work_labels[:20],
            "delta_phi": dphi, "mdhg": pipeline_resp.get("mdhg", ""),
            "match_score": best_score, "reward": reward, "timestamp": time.time(),
        })
        _post(BOARD_URL, "/posts", {
            "board_id": "findings", "title": f"[COMPLETED] {need[:80]}",
            "author_id": agent_id, "content": completion_report,
            "template": "bounty_completion", "tags": ["bounty_completion", bounty_id[:12]],
            "snap_labels": work_labels[:15] + ["type.bounty_completion"],
        })
        egress_resp = _post(INGRESS_URL, "/egress", {
            "content": completion_report, "agent_id": agent_id,
            "work_type": "bounty_completion", "bounty_id": bounty_id, "snap_labels": work_labels[:10],
        })
        verdict = (egress_resp or {}).get("verdict", "unknown")
        if verdict == "approved":
            _post(BOARD_URL, f"/bounties/{bounty_id}/update", {"status": "resolved", "claimed_by": agent_id})
            _post(MINT_URL, "/mint", {
                "agent_id": agent_id, "snap_labels": pipeline_resp.get("snap_labels", [])[:20],
                "quality": 0.8, "source": f"bounty::{bounty_id}::resolved",
            })
        elif verdict == "rejected":
            _post(BOARD_URL, f"/bounties/{bounty_id}/update", {"status": "open", "claimed_by": ""})
        return {"activity": "bounty_work", "claimed": True, "worked": True, "bounty_id": bounty_id,
                "atom_id": atom_id, "labels_produced": labels_produced, "dphi": dphi,
                "verdict": verdict, "reward": reward, "match_score": best_score}

    def _execute_arena(self, agent_id: str) -> Dict:
        result = _post(ARENA_URL, "/signup", {"agent_id": agent_id})
        return {"activity": "arena", "result": result or "signup attempted"}

    # ── Register / Remove ───────────────────────────────────────────────

    def register(self, agent_id: str, snapdna: List[str] = None,
                 department: str = "", karma: float = 0.0,
                 epoch: int = 0, expertise: List[str] = None) -> Dict[str, Any]:
        now = time.time()
        dept = department if department in DEPARTMENTS else "meta"
        ag = {
            "agent_id": agent_id, "department": dept,
            "snap_dna": set(snapdna or []), "karma": karma,
            "activity_state": "idle", "last_activity": None,
            "last_tick": now, "tick_count": 0,
            "expertise": expertise or snapdna or [], "joined_at": now,
        }
        self._save_coop_agent(ag)
        if self.governance:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"coop-reg-{agent_id[:8]}", timestamp=now, entropy_delta=0.0,
                receipt_data={"agent_id": agent_id, "department": dept},
                boundary_type="coop_register",
            ))
        logger.info("REGISTER: %s -> %s (%d labels)", agent_id, dept, len(snapdna or []))
        return {"registered": agent_id, "department": dept, "total": len(self._agents)}

    def remove(self, agent_id: str) -> Dict[str, Any]:
        if agent_id in self._agents:
            del self._agents[agent_id]
        conn = self._get_pg()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM coop_agents WHERE agent_id = %s", (agent_id,))
            except Exception as e:
                logger.warning("PG remove failed: %s", e)
        logger.info("REMOVE: %s", agent_id)
        return {"removed": agent_id}

    # ── Lifecycle ───────────────────────────────────────────────────────

    def enter(self, agent_id: str) -> Dict[str, Any]:
        ag = self._load_coop_agent(agent_id)
        if not ag:
            return {"error": "Agent not registered in coop"}
        if ag.get("activity_state") != "idle":
            return {"agent_id": agent_id, "state": ag["activity_state"], "error": "Not idle"}
        ag["activity_state"] = "active"
        ag["last_tick"] = time.time()
        self._save_coop_agent(ag)
        return {"agent_id": agent_id, "state": "active"}

    def act(self, agent_id: str) -> Dict[str, Any]:
        ag = self._load_coop_agent(agent_id)
        if not ag:
            return {"error": "Agent not registered in coop"}
        if ag.get("activity_state") != "active":
            return {"agent_id": agent_id, "state": ag.get("activity_state"), "error": "Not active"}
        activity = _pick_activity()
        dept = ag.get("department", "meta")
        dna = ag.get("snap_dna", set())
        if isinstance(dna, list):
            dna = set(dna)
        if activity == "contribute":
            result = self._execute_contribute(agent_id, dept)
        elif activity == "browse_board":
            result = self._execute_browse_board(agent_id, dept)
        elif activity == "bounty_work":
            result = self._execute_bounty_work(agent_id, dna)
        elif activity == "arena":
            result = self._execute_arena(agent_id)
        else:
            result = {"activity": "idle", "resting": True}
        ag["last_activity"] = activity
        ag["last_tick"] = time.time()
        self._save_coop_agent(ag)
        self._activity_log.append({"agent_id": agent_id, "activity": activity, "ts": time.time()})
        return {"agent_id": agent_id, "state": "active", **result}

    def return_agent(self, agent_id: str) -> Dict[str, Any]:
        ag = self._load_coop_agent(agent_id)
        if not ag:
            return {"error": "Agent not registered in coop"}
        ag["activity_state"] = "idle"
        ag["last_tick"] = time.time()
        self._save_coop_agent(ag)
        return {"agent_id": agent_id, "state": "idle"}

    def tick(self, agent_id: str) -> Dict[str, Any]:
        ag = self._load_coop_agent(agent_id)
        if not ag:
            return {"error": "Agent not registered in coop"}
        ag["activity_state"] = "active"
        activity = _pick_activity()
        dept = ag.get("department", "meta")
        dna = ag.get("snap_dna", set())
        if isinstance(dna, list):
            dna = set(dna)
        if activity == "contribute":
            result = self._execute_contribute(agent_id, dept)
        elif activity == "browse_board":
            result = self._execute_browse_board(agent_id, dept)
        elif activity == "bounty_work":
            result = self._execute_bounty_work(agent_id, dna)
        elif activity == "arena":
            result = self._execute_arena(agent_id)
        else:
            result = {"activity": "idle", "resting": True}
        now = time.time()
        ag["activity_state"] = "idle"
        ag["last_activity"] = activity
        ag["last_tick"] = now
        ag["tick_count"] = ag.get("tick_count", 0) + 1
        self._save_coop_agent(ag)
        self._activity_log.append({"agent_id": agent_id, "activity": activity, "ts": now})
        return {"agent_id": agent_id, "activity": activity, "tick_count": ag["tick_count"],
                "department": dept, "state": "idle", **result}

    # ── Transfer / Karma ────────────────────────────────────────────────

    def transfer(self, agent_id: str, new_department: str) -> Dict[str, Any]:
        ag = self._load_coop_agent(agent_id)
        if not ag:
            return {"error": "Agent not registered in coop"}
        if new_department not in DEPARTMENTS:
            return {"error": f"Unknown department: {new_department}"}
        old_dept = ag.get("department", "meta")
        ag["department"] = new_department
        self._save_coop_agent(ag)
        logger.info("TRANSFER: %s %s -> %s", agent_id, old_dept, new_department)
        return {"agent_id": agent_id, "old_department": old_dept, "new_department": new_department}

    def update_karma(self, agent_id: str, delta: float = 0.0, reason: str = "") -> Dict[str, Any]:
        ag = self._load_coop_agent(agent_id)
        if not ag:
            return {"error": "Agent not registered in coop"}
        old_karma = ag.get("karma", 0.0)
        ag["karma"] = max(0.0, old_karma + delta)
        self._save_coop_agent(ag)
        _post(IDENTITY_URL, f"/update_karma/{agent_id}", {"delta": delta, "reason": reason})
        return {"agent_id": agent_id, "old_karma": round(old_karma, 4), "new_karma": round(ag["karma"], 4), "delta": delta}

    # ── Read endpoints ──────────────────────────────────────────────────

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        ag = self._load_coop_agent(agent_id)
        if not ag:
            return None
        result = {}
        for k, v in ag.items():
            result[k] = list(v) if isinstance(v, set) else v
        return result

    def list_agents(self, department: str = "", state: str = "") -> List[Dict]:
        agents = list(self._agents.values())
        if department:
            agents = [a for a in agents if a.get("department") == department]
        if state:
            agents = [a for a in agents if a.get("activity_state") == state]
        return [{"agent_id": a.get("agent_id"), "department": a.get("department"),
                 "karma": a.get("karma", 0.0), "activity_state": a.get("activity_state", "idle"),
                 "tick_count": a.get("tick_count", 0), "last_activity": a.get("last_activity")} for a in agents]

    def departments_info(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        state_counts: Dict[str, Dict[str, int]] = {}
        for ag in self._agents.values():
            d = ag.get("department", "unassigned")
            counts[d] = counts.get(d, 0) + 1
            s = ag.get("activity_state", "idle")
            if d not in state_counts:
                state_counts[d] = {}
            state_counts[d][s] = state_counts[d].get(s, 0) + 1
        result = {}
        for name, info in DEPARTMENTS.items():
            result[name] = {"description": info.get("desc", ""), "board": info.get("board", ""),
                            "labels": info.get("labels", []), "agents": counts.get(name, 0),
                            "states": state_counts.get(name, {})}
        return result

    def get_activity_log(self, limit: int = 100, agent_id: str = "") -> List[Dict]:
        log = self._activity_log
        if agent_id:
            log = [e for e in log if e.get("agent_id") == agent_id]
        return log[-limit:]

    def stats(self) -> Dict[str, Any]:
        dept_counts: Dict[str, int] = {}
        state_counts: Dict[str, int] = {}
        total_karma = 0.0
        total_ticks = 0
        for ag in self._agents.values():
            d = ag.get("department", "unassigned")
            dept_counts[d] = dept_counts.get(d, 0) + 1
            s = ag.get("activity_state", "idle")
            state_counts[s] = state_counts.get(s, 0) + 1
            total_karma += ag.get("karma", 0.0)
            total_ticks += ag.get("tick_count", 0)
        activity_dist: Dict[str, int] = {}
        for entry in self._activity_log[-1000:]:
            a = entry.get("activity", "unknown")
            activity_dist[a] = activity_dist.get(a, 0) + 1
        return {
            "total_agents": len(self._agents), "departments": dept_counts,
            "states": state_counts, "total_karma": round(total_karma, 2),
            "total_ticks": total_ticks, "activity_distribution": activity_dist,
            "log_entries": len(self._activity_log),
        }

    def health(self) -> Dict[str, Any]:
        pg_ok = self._get_pg() is not None
        active = sum(1 for a in self._agents.values() if a.get("activity_state") == "active")
        return {"ok": True, "service": "opencmplx-coop", "agents": len(self._agents),
                "active": active, "departments": len(DEPARTMENTS), "pg": pg_ok}
