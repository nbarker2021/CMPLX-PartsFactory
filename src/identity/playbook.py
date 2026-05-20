#!/usr/bin/env python3
"""
CMPLX-PartsFactory — Playbook Engine

Register, execute, and compose playbooks — named procedures with sequenced steps.
Playbooks are the operational unit of agent work. Templates provided for
crystal_store, mdhg_explore, and stratify_and_tag operations.
"""

import os
import json
import sqlite3
import uuid
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger("playbook")

PLAYBOOK_DB_PATH = "/mnt/d/PartsFactory/CMPLX-PartsFactory/data/playbook_engine.sqlite"

PLAYBOOK_SCHEMA = """
CREATE TABLE IF NOT EXISTS playbooks (
    playbook_id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    steps TEXT,
    tags TEXT,
    version INTEGER DEFAULT 1,
    created_at REAL,
    updated_at REAL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS playbook_runs (
    run_id TEXT PRIMARY KEY,
    playbook_id TEXT NOT NULL,
    agent_id TEXT,
    status TEXT DEFAULT 'pending',
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    started_at REAL,
    completed_at REAL,
    results TEXT,
    error TEXT,
    metadata TEXT,
    FOREIGN KEY (playbook_id) REFERENCES playbooks(playbook_id)
);

CREATE TABLE IF NOT EXISTS playbook_compositions (
    comp_id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    playbook_ids TEXT,
    sequence TEXT,
    description TEXT,
    created_at REAL
);

CREATE INDEX IF NOT EXISTS idx_pb_name ON playbooks(name);
CREATE INDEX IF NOT EXISTS idx_pb_runs_agent ON playbook_runs(agent_id);
CREATE INDEX IF NOT EXISTS idx_pb_runs_status ON playbook_runs(status);
"""


@dataclass
class PlaybookStep:
    name: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    on_success: str = "continue"
    on_failure: str = "abort"
    timeout_seconds: int = 60


@dataclass
class Playbook:
    name: str
    description: str = ""
    steps: List[PlaybookStep] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PlaybookEngine:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or PLAYBOOK_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._handlers: Dict[str, Callable] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._sidecar_sync_fn: Optional[callable] = None

    def connect(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(PLAYBOOK_SCHEMA)
        self._conn.commit()
        self._register_default_templates()

    def set_sidecar_sync(self, sync_fn: callable):
        self._sidecar_sync_fn = sync_fn

    def register_handler(self, action: str, handler_fn: Callable):
        self._handlers[action] = handler_fn

    def _register_default_templates(self):
        if not self._conn.execute("SELECT COUNT(*) FROM playbooks").fetchone()[0]:
            self._install_crystal_store_playbook()
            self._install_mdhg_explore_playbook()
            self._install_stratify_and_tag_playbook()

    def _install_crystal_store_playbook(self):
        self.register_playbook(
            name="crystal_store",
            description="Store content into MMDB crystal database with snap labels",
            steps=[
                PlaybookStep("prepare", "validate_input", {"required_fields": ["content", "domain"]}),
                PlaybookStep("encode", "dna_encode", {"algorithm": "quadratic_invariant"}),
                PlaybookStep("store", "crystal_store", {"target": "mmdb", "snap_labels": ["{domain}"]}),
                PlaybookStep("verify", "verify_storage", {"check_receipt": True}),
                PlaybookStep("log", "log_result", {"channel": "identity_report"}),
            ],
            tags=["storage", "crystal", "mmdb"],
            metadata={"category": "storage", "critical": True},
        )

    def _install_mdhg_explore_playbook(self):
        self.register_playbook(
            name="mdhg_explore",
            description="Explore MDHG manifold for geometric patterns and crossings",
            steps=[
                PlaybookStep("probe", "mdhg_probe", {"depth": 3, "mode": "explore"}),
                PlaybookStep("analyze", "analyze_manifold", {"extract": ["geodesics", "boundaries"]}),
                PlaybookStep("report", "generate_report", {"format": "geometric_summary"}),
                PlaybookStep("log", "log_result", {"channel": "identity_report"}),
            ],
            tags=["explore", "mdhg", "manifold"],
            metadata={"category": "discovery", "domain": "mdhg"},
        )

    def _install_stratify_and_tag_playbook(self):
        self.register_playbook(
            name="stratify_and_tag",
            description="Stratify a concept and apply domain tags via SNAP service",
            steps=[
                PlaybookStep("stratify", "snap_stratify", {"concept": "{concept}", "depth": 3}),
                PlaybookStep("classify", "classify_strata", {"taxonomy": "domain"}),
                PlaybookStep("tag", "apply_tags", {"target": "{target}", "source": "stratification"}),
                PlaybookStep("log", "log_result", {"channel": "playbook_sync"}),
            ],
            tags=["classify", "tag", "stratify", "snap"],
            metadata={"category": "classification", "domain": "snap"},
        )

    def register_playbook(self, name: str, description: str = "",
                          steps: List[PlaybookStep] = None,
                          tags: List[str] = None,
                          metadata: Dict[str, Any] = None) -> str:
        steps = steps or []
        tags = tags or []
        metadata = metadata or {}
        existing = self._conn.execute(
            "SELECT playbook_id, version FROM playbooks WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            playbook_id = existing["playbook_id"]
            version = existing["version"] + 1
            self._conn.execute("""
                UPDATE playbooks SET description = ?, steps = ?, tags = ?,
                    version = ?, updated_at = ?, metadata = ?
                WHERE playbook_id = ?
            """, (
                description,
                json.dumps([asdict(s) for s in steps]),
                json.dumps(tags),
                version,
                time.time(),
                json.dumps(metadata),
                playbook_id,
            ))
        else:
            playbook_id = f"pb_{uuid.uuid4().hex[:12]}"
            version = 1
            self._conn.execute("""
                INSERT INTO playbooks (playbook_id, name, description, steps, tags, version, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                playbook_id, name, description,
                json.dumps([asdict(s) for s in steps]),
                json.dumps(tags), version,
                time.time(), time.time(), json.dumps(metadata),
            ))
        self._conn.commit()
        logger.info("Registered playbook: %s (v%d)", name, version)
        if self._sidecar_sync_fn:
            self._sidecar_sync_fn("playbook_sync", {
                "playbook_id": playbook_id, "name": name, "version": version,
            })
        return playbook_id

    def get_playbook(self, name: str = None, playbook_id: str = None) -> Optional[Dict[str, Any]]:
        if playbook_id and playbook_id in self._cache:
            return self._cache[playbook_id]
        if name:
            cursor = self._conn.execute(
                "SELECT * FROM playbooks WHERE name = ?", (name,)
            )
        elif playbook_id:
            cursor = self._conn.execute(
                "SELECT * FROM playbooks WHERE playbook_id = ?", (playbook_id,)
            )
        else:
            return None
        row = cursor.fetchone()
        if not row:
            return None
        pb = dict(row)
        pb["steps"] = json.loads(pb["steps"]) if isinstance(pb["steps"], str) else pb["steps"]
        pb["tags"] = json.loads(pb["tags"]) if isinstance(pb["tags"], str) else pb["tags"]
        pb["metadata"] = json.loads(pb["metadata"]) if isinstance(pb.get("metadata"), str) else pb.get("metadata")
        self._cache[pb["playbook_id"]] = pb
        return pb

    def list_playbooks(self, tag: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        if tag:
            cursor = self._conn.execute(
                "SELECT * FROM playbooks WHERE tags LIKE ? ORDER BY name LIMIT ?",
                (f'%"{tag}"%', limit),
            )
        else:
            cursor = self._conn.execute(
                "SELECT * FROM playbooks ORDER BY name LIMIT ?", (limit,)
            )
        return [dict(row) for row in cursor.fetchall()]

    def execute(self, playbook_name: str, agent_id: str = None,
                variables: Dict[str, Any] = None,
                step_filter: List[str] = None) -> Dict[str, Any]:
        pb = self.get_playbook(name=playbook_name)
        if not pb:
            raise ValueError(f"Playbook not found: {playbook_name}")
        steps_data = pb["steps"]
        vars_map = variables or {}
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        now = time.time()

        resolved_steps = []
        for s in steps_data:
            resolved_params = {}
            for k, v in s.get("params", {}).items():
                if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                    resolved_params[k] = vars_map.get(v[1:-1], v)
                else:
                    resolved_params[k] = v
            resolved_steps.append({**s, "params": resolved_params})

        if step_filter:
            resolved_steps = [s for s in resolved_steps if s["name"] in step_filter]

        total = len(resolved_steps)
        self._conn.execute("""
            INSERT INTO playbook_runs (run_id, playbook_id, agent_id, status,
                current_step, total_steps, started_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, pb["playbook_id"], agent_id, "running", 0, total, now,
              json.dumps({"playbook_name": playbook_name, "variables": vars_map})))
        self._conn.commit()

        results = []
        step_idx = 0
        error = None

        for step_idx, step in enumerate(resolved_steps):
            step_result = self._execute_step(step, agent_id, run_id, step_idx, total)
            results.append(step_result)
            self._conn.execute(
                "UPDATE playbook_runs SET current_step = ? WHERE run_id = ?",
                (step_idx + 1, run_id),
            )
            self._conn.commit()

            if not step_result["success"]:
                if step.get("on_failure", "abort") == "abort":
                    error = step_result.get("error", f"Step '{step['name']}' failed")
                    break
                elif step.get("on_failure") == "skip":
                    continue

        completed_at = time.time()
        final_status = "completed" if not error else "failed"
        self._conn.execute("""
            UPDATE playbook_runs SET status = ?, completed_at = ?, results = ?, error = ?
            WHERE run_id = ?
        """, (final_status, completed_at, json.dumps(results), error, run_id))
        self._conn.commit()

        outcome = {
            "run_id": run_id,
            "playbook_name": playbook_name,
            "status": final_status,
            "steps_completed": step_idx + 1 if error else total,
            "total_steps": total,
            "results": results,
            "error": error,
            "started_at": now,
            "completed_at": completed_at,
        }

        if self._sidecar_sync_fn:
            self._sidecar_sync_fn("playbook_sync", outcome)

        return outcome

    def _execute_step(self, step: Dict[str, Any], agent_id: str,
                      run_id: str, step_idx: int, total: int) -> Dict[str, Any]:
        action = step.get("action", "")
        params = step.get("params", {})
        logger.info("  [%d/%d] %s (%s)", step_idx + 1, total, step["name"], action)

        if action in self._handlers:
            try:
                result = self._handlers[action](**params)
                return {
                    "step_name": step["name"],
                    "action": action,
                    "success": True,
                    "result": result,
                    "step_index": step_idx,
                }
            except Exception as e:
                logger.error("Step '%s' failed: %s", step["name"], e)
                return {
                    "step_name": step["name"],
                    "action": action,
                    "success": False,
                    "error": str(e),
                    "step_index": step_idx,
                }
        else:
            logger.warning("No handler registered for action: %s", action)
            return {
                "step_name": step["name"],
                "action": action,
                "success": False,
                "error": f"No handler for action: {action}",
                "step_index": step_idx,
            }

    def compose(self, name: str, playbook_names: List[str],
                description: str = "",
                merge_steps: bool = True) -> Dict[str, Any]:
        composed_steps = []
        for pb_name in playbook_names:
            pb = self.get_playbook(name=pb_name)
            if not pb:
                raise ValueError(f"Playbook not found for composition: {pb_name}")
            steps = pb["steps"]
            for s in steps:
                s_copy = dict(s)
                s_copy["_source_playbook"] = pb_name
                composed_steps.append(s_copy)

        composed_pb = Playbook(
            name=name,
            description=description or f"Composed from: {', '.join(playbook_names)}",
            steps=[PlaybookStep(**s) for s in composed_steps],
            tags=["composed"],
            metadata={"source_playbooks": playbook_names},
        )

        pb_id = self.register_playbook(
            name=composed_pb.name,
            description=composed_pb.description,
            steps=composed_pb.steps,
            tags=composed_pb.tags,
            metadata=composed_pb.metadata,
        )

        comp_id = f"comp_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO playbook_compositions (comp_id, name, playbook_ids, sequence, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (comp_id, name, json.dumps(playbook_names),
              json.dumps([s["name"] for s in composed_steps]),
              description, time.time()))
        self._conn.commit()

        return {"composition_id": comp_id, "playbook_id": pb_id, "name": name, "steps": len(composed_steps)}

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        cursor = self._conn.execute("SELECT * FROM playbook_runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        for field in ["results", "metadata"]:
            if d.get(field) and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    def list_runs(self, playbook_name: str = None, agent_id: str = None,
                  status: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        if playbook_name:
            pb = self.get_playbook(name=playbook_name)
            if pb:
                conditions.append("playbook_id = ?")
                params.append(pb["playbook_id"])
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if status:
            conditions.append("status = ?")
            params.append(status)
        sql = "SELECT * FROM playbook_runs"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        cursor = self._conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
