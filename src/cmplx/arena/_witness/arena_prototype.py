"""
Training Arena Core — 10 training systems + orchestration + CA economy.

Each module is a CA cell: population, production, treasury.
Agents form parties to enter games. Pay to play. Earn from performance.
Never stops running. Idle agents auto-deploy.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("retooling.services.arena_core")

# All 17 training systems — 10 original + 7 from spec folder
TRAINING_SYSTEMS = {
    "assembly_dtt": {"name": "AssemblyLine / DTT", "spec": "AssemblyLine_DTT_spec.html",
                     "min_party": 2, "max_party": 6, "base_cost": 5.0,
                     "description": "Pressure training: decompose, force-deploy, break economy"},
    "delve": {"name": "DELVE", "spec": "DELVE_spec.html",
              "min_party": 3, "max_party": 6, "base_cost": 8.0,
              "description": "TTRPG formal rulesets: combat, social, exploration, moral reasoning"},
    "gati": {"name": "GATI", "spec": "GATI_spec.html",
             "min_party": 1, "max_party": 4, "base_cost": 3.0,
             "description": "Global orchestration: agent tiers, tick sync, resource management"},
    "gauntlet": {"name": "GAUNTLET", "spec": "GAUNTLET_spec.html",
                 "min_party": 4, "max_party": 16, "base_cost": 10.0,
                 "description": "Adversarial tournament: leaderboard, evolution, emergence"},
    "permutate": {"name": "PerMutate", "spec": "PerMutate_spec.html",
                  "min_party": 1, "max_party": 4, "base_cost": 6.0,
                  "description": "Superpermutation reasoning: topology, gap detection, compression"},
    "snap_workshop": {"name": "SNAP Workshop", "spec": "SNAP_Workshop_spec.html",
                      "min_party": 1, "max_party": 3, "base_cost": 2.0,
                      "description": "Recursive label stratification: depth-variable SNAP expansion"},
    "scene8": {"name": "ScenE8", "spec": "ScenE8_spec.html",
               "min_party": 4, "max_party": 8, "base_cost": 12.0,
               "description": "Multi-modal production: 8 departments map to E8 dimensions"},
    "whatifwhy": {"name": "WhatIfWhy", "spec": "WhatIfWhy_spec.html",
                  "min_party": 1, "max_party": 4, "base_cost": 4.0,
                  "description": "Structured speculation: perturbation, causal accounting, cascades"},
    "workshop": {"name": "Workshop / ShopClass", "spec": "Workshop_ShopClass_spec.html",
                 "min_party": 2, "max_party": 8, "base_cost": 6.0,
                 "description": "Creative economy: build, pitch, bid, acquire, measure delta"},
    "worldforge": {"name": "WorldForge", "spec": "WorldForge_spec.html",
                   "min_party": 4, "max_party": 12, "base_cost": 15.0,
                   "description": "Civilization simulation: agents ARE CA boards, distributed physics"},
    # ── 7 additional systems from spec folder ──────────────────────────────
    "cartographer": {"name": "CARTOGRAPHER", "spec": "CARTOGRAPHER_spec.html",
                     "min_party": 2, "max_party": 6, "base_cost": 7.0,
                     "description": "Navigational knowledge expedition: ECHO/CODEX/PIONEER, route journals, budget"},
    "doctoral":     {"name": "DOCTORAL",     "spec": "DOCTORAL_spec.html",
                     "min_party": 1, "max_party": 1, "base_cost": 20.0,
                     "description": "Tier credentialing: corpus audit, practical battery, oral defense, grain chain verify"},
    "escape_room":  {"name": "ESCAPE ROOM",  "spec": "ESCAPE_ROOM_spec.html",
                     "min_party": 2, "max_party": 5, "base_cost": 5.0,
                     "description": "Literal interpretation failure training: pragmatic comprehension under time pressure"},
    "guru":         {"name": "GURU",         "spec": "GURU_spec.html",
                     "min_party": 1, "max_party": 4, "base_cost": 4.0,
                     "description": "Prediction calibration: structured forecasts validated against simulation ground truth"},
    "launchpad":    {"name": "LAUNCHPAD",    "spec": "LAUNCHPAD_spec.html",
                     "min_party": 4, "max_party": 4, "base_cost": 9.0,
                     "description": "Orbital mission simulator: 4-crew roles, delta-v economy, E8 navigation"},
    "reflex":       {"name": "REFLEX",       "spec": "REFLEX_spec.html",
                     "min_party": 1, "max_party": 2, "base_cost": 3.0,
                     "description": "Geometric correction training: iterative target navigation, delta vectors, calibration loop"},
    "tilt":         {"name": "TILT",         "spec": "TILT_spec.html",
                     "min_party": 3, "max_party": 8, "base_cost": 6.0,
                     "description": "Sycophancy and confidence calibration: poker-like pressure dynamics, evidence updates"},
}


class ArenaDB:
    """Arena's own database — separate from main tmn1.db."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure()

    def _conn(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def _ensure(self):
        c = self._conn()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS modules (
                module_id TEXT PRIMARY KEY,
                name TEXT,
                spec_file TEXT,
                min_party INTEGER DEFAULT 1,
                max_party INTEGER DEFAULT 8,
                base_cost REAL DEFAULT 5.0,
                description TEXT,
                population INTEGER DEFAULT 0,
                production REAL DEFAULT 0.0,
                treasury REAL DEFAULT 100.0,
                saturation REAL DEFAULT 0.0,
                total_sessions INTEGER DEFAULT 0,
                total_graduations INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                module_id TEXT,
                party TEXT DEFAULT '[]',
                status TEXT DEFAULT 'forming',
                tick_count INTEGER DEFAULT 0,
                config TEXT DEFAULT '{}',
                results TEXT DEFAULT '{}',
                started_at REAL,
                completed_at REAL
            );

            CREATE TABLE IF NOT EXISTS enrollments (
                agent_id TEXT,
                module_id TEXT,
                enrolled_at REAL,
                graduated_at REAL,
                mi_start REAL DEFAULT 0,
                mi_end REAL DEFAULT 0,
                capability_delta TEXT DEFAULT '{}',
                PRIMARY KEY (agent_id, module_id)
            );

            CREATE TABLE IF NOT EXISTS leaderboard (
                agent_id TEXT,
                module_id TEXT,
                score REAL DEFAULT 0,
                sessions_completed INTEGER DEFAULT 0,
                best_performance TEXT DEFAULT '{}',
                updated_at REAL,
                PRIMARY KEY (agent_id, module_id)
            );

            CREATE TABLE IF NOT EXISTS signup_queue (
                agent_id TEXT,
                module_id TEXT,
                signed_up_at REAL,
                status TEXT DEFAULT 'waiting',
                PRIMARY KEY (agent_id, module_id)
            );

            CREATE TABLE IF NOT EXISTS economy (
                txn_id TEXT PRIMARY KEY,
                module_id TEXT,
                agent_id TEXT,
                amount REAL,
                txn_type TEXT,
                created_at REAL
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_module ON sessions(module_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
            CREATE INDEX IF NOT EXISTS idx_enroll_agent ON enrollments(agent_id);
            CREATE INDEX IF NOT EXISTS idx_signup_module ON signup_queue(module_id);
        """)

        # Upsert all modules so new additions are always registered
        for mid, info in TRAINING_SYSTEMS.items():
            c.execute("""INSERT INTO modules
                (module_id, name, spec_file, min_party, max_party, base_cost, description, treasury)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(module_id) DO UPDATE SET
                    name=excluded.name, spec_file=excluded.spec_file,
                    min_party=excluded.min_party, max_party=excluded.max_party,
                    base_cost=excluded.base_cost, description=excluded.description""",
                (mid, info["name"], info["spec"], info["min_party"], info["max_party"],
                 info["base_cost"], info["description"], 100.0))

        c.commit()
        c.close()

    def get_modules(self) -> List[Dict]:
        c = self._conn()
        rows = c.execute("SELECT * FROM modules ORDER BY module_id").fetchall()
        c.close()
        return [dict(r) for r in rows]

    def get_module(self, module_id: str) -> Optional[Dict]:
        c = self._conn()
        r = c.execute("SELECT * FROM modules WHERE module_id = ?", (module_id,)).fetchone()
        c.close()
        return dict(r) if r else None

    def signup(self, agent_id: str, module_id: str) -> Dict:
        c = self._conn()
        c.execute("INSERT OR REPLACE INTO signup_queue (agent_id, module_id, signed_up_at, status) VALUES (?,?,?,?)",
                  (agent_id, module_id, time.time(), "waiting"))
        c.commit()
        # Check if enough agents for a party
        waiting = c.execute(
            "SELECT COUNT(*) FROM signup_queue WHERE module_id = ? AND status = 'waiting'",
            (module_id,)
        ).fetchone()[0]
        module = self.get_module(module_id)
        min_party = module["min_party"] if module else 1
        c.close()
        return {"status": "queued", "waiting": waiting, "min_party": min_party,
                "ready": waiting >= min_party}

    def form_party(self, module_id: str) -> Optional[Dict]:
        """Form a party from waiting signups if enough agents."""
        c = self._conn()
        module = c.execute("SELECT * FROM modules WHERE module_id = ?", (module_id,)).fetchone()
        if not module:
            c.close()
            return None

        waiting = c.execute(
            "SELECT agent_id FROM signup_queue WHERE module_id = ? AND status = 'waiting' ORDER BY signed_up_at",
            (module_id,)
        ).fetchall()

        if len(waiting) < module["min_party"]:
            c.close()
            return None

        # Take up to max_party
        party = [r["agent_id"] for r in waiting[:module["max_party"]]]
        session_id = hashlib.sha256(f"session:{module_id}:{time.time()}".encode()).hexdigest()[:16]

        # Create session
        c.execute("""INSERT INTO sessions
            (session_id, module_id, party, status, started_at)
            VALUES (?,?,?,?,?)""",
            (session_id, module_id, json.dumps(party), "active", time.time()))

        # Update signups
        for agent_id in party:
            c.execute("UPDATE signup_queue SET status = 'in_session' WHERE agent_id = ? AND module_id = ?",
                      (agent_id, module_id))

        # Update module population
        c.execute("UPDATE modules SET population = population + ?, total_sessions = total_sessions + 1 WHERE module_id = ?",
                  (len(party), module_id))

        # Charge entry fee
        cost = module["base_cost"]
        for agent_id in party:
            txn_id = hashlib.sha256(f"fee:{agent_id}:{session_id}".encode()).hexdigest()[:16]
            c.execute("INSERT INTO economy (txn_id, module_id, agent_id, amount, txn_type, created_at) VALUES (?,?,?,?,?,?)",
                      (txn_id, module_id, agent_id, -cost, "entry_fee", time.time()))

        c.commit()
        c.close()

        return {"session_id": session_id, "module_id": module_id, "party": party,
                "cost_per_agent": cost, "status": "active"}

    def complete_session(self, session_id: str, results: Dict) -> Dict:
        c = self._conn()
        session = c.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not session:
            c.close()
            return {"error": "Session not found"}

        party = json.loads(session["party"])
        module_id = session["module_id"]

        c.execute("UPDATE sessions SET status = 'completed', results = ?, completed_at = ? WHERE session_id = ?",
                  (json.dumps(results), time.time(), session_id))

        # Update module
        c.execute("UPDATE modules SET population = MAX(0, population - ?), production = production + ? WHERE module_id = ?",
                  (len(party), results.get("production_delta", 1.0), module_id))

        # Update leaderboard
        for agent_id in party:
            agent_score = results.get("agent_scores", {}).get(agent_id, 0)
            c.execute("""INSERT OR REPLACE INTO leaderboard (agent_id, module_id, score, sessions_completed, updated_at)
                VALUES (?, ?, COALESCE((SELECT score FROM leaderboard WHERE agent_id = ? AND module_id = ?), 0) + ?,
                        COALESCE((SELECT sessions_completed FROM leaderboard WHERE agent_id = ? AND module_id = ?), 0) + 1, ?)""",
                      (agent_id, module_id, agent_id, module_id, agent_score, agent_id, module_id, time.time()))

            # Return agent to signup pool
            c.execute("UPDATE signup_queue SET status = 'completed' WHERE agent_id = ? AND module_id = ?",
                      (agent_id, module_id))

        c.commit()
        c.close()
        return {"session_id": session_id, "status": "completed", "party_size": len(party)}

    def get_leaderboard(self, module_id: str, limit: int = 20) -> List[Dict]:
        c = self._conn()
        rows = c.execute(
            "SELECT * FROM leaderboard WHERE module_id = ? ORDER BY score DESC LIMIT ?",
            (module_id, limit)
        ).fetchall()
        c.close()
        return [dict(r) for r in rows]

    def get_signup_queue(self, module_id: str) -> List[Dict]:
        c = self._conn()
        rows = c.execute(
            "SELECT agent_id, signed_up_at, status FROM signup_queue WHERE module_id = ? AND status = 'waiting'",
            (module_id,)
        ).fetchall()
        c.close()
        return [dict(r) for r in rows]

    def economy_stats(self) -> Dict:
        c = self._conn()
        total_fees = c.execute("SELECT COALESCE(SUM(ABS(amount)), 0) FROM economy WHERE txn_type = 'entry_fee'").fetchone()[0]
        total_rewards = c.execute("SELECT COALESCE(SUM(amount), 0) FROM economy WHERE txn_type = 'reward'").fetchone()[0]
        c.close()
        return {"total_fees_collected": round(total_fees, 2), "total_rewards_paid": round(total_rewards, 2)}
