"""ExpertRegistry — Searchable registry of all created experts.

Tracks capabilities, success rates, performance metrics, and lineage
for every expert. SQLite-backed with in-memory cache.
"""

from __future__ import annotations
import os
import json
import sqlite3
import time
import uuid
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("expertise.registry")

DEFAULT_REGISTRY_PATH = "/mnt/d/PartsFactory/CMPLX-PartsFactory/data/expert_registry.sqlite"

REGISTRY_SCHEMA = """
CREATE TABLE IF NOT EXISTS experts (
    expert_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    archetype TEXT,
    dna_sequence TEXT,
    purpose TEXT,
    capabilities TEXT,
    governance_boundaries TEXT,
    brain_template TEXT,
    instruction_set TEXT,
    agent_definition TEXT,
    created_at REAL,
    updated_at REAL,
    status TEXT DEFAULT 'active',
    performance_score REAL DEFAULT 0.0,
    success_rate REAL DEFAULT 0.0,
    total_operations INTEGER DEFAULT 0,
    successful_operations INTEGER DEFAULT 0,
    avg_latency_ms REAL DEFAULT 0.0,
    composition_count INTEGER DEFAULT 0,
    tags TEXT,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS expert_lineage (
    lineage_id TEXT PRIMARY KEY,
    expert_id TEXT NOT NULL,
    ancestor_id TEXT NOT NULL,
    relationship TEXT,
    contribution_weight REAL DEFAULT 0.0,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS expert_compositions (
    comp_id TEXT PRIMARY KEY,
    expert_id TEXT NOT NULL,
    composed_with TEXT,
    result_expert_id TEXT,
    convergence_score REAL,
    rounds INTEGER,
    created_at REAL
);

CREATE INDEX IF NOT EXISTS idx_experts_domain ON experts(domain);
CREATE INDEX IF NOT EXISTS idx_experts_archetype ON experts(archetype);
CREATE INDEX IF NOT EXISTS idx_experts_status ON experts(status);
CREATE INDEX IF NOT EXISTS idx_lineage_expert ON expert_lineage(expert_id);
CREATE INDEX IF NOT EXISTS idx_compositions_expert ON expert_compositions(expert_id);
"""


class ExpertRegistry:
    """Searchable registry of all created experts."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_REGISTRY_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._cache: Dict[str, Dict[str, Any]] = {}

    def connect(self) -> None:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(REGISTRY_SCHEMA)
        self._conn.commit()

    def register_expert(self, expert_data: Dict[str, Any]) -> str:
        expert_id = expert_data.get("expert_id", f"exp_{uuid.uuid4().hex[:12]}")
        now = time.time()
        self._conn.execute("""
            INSERT OR REPLACE INTO experts (
                expert_id, name, domain, archetype, dna_sequence, purpose,
                capabilities, governance_boundaries, brain_template,
                instruction_set, agent_definition, created_at, updated_at,
                status, performance_score, success_rate, total_operations,
                successful_operations, avg_latency_ms, composition_count,
                tags, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            expert_id,
            expert_data.get("name", ""),
            expert_data.get("domain", ""),
            expert_data.get("archetype", ""),
            expert_data.get("dna_sequence", ""),
            expert_data.get("purpose", ""),
            json.dumps(expert_data.get("capabilities", [])),
            json.dumps(expert_data.get("governance_boundaries", {})),
            json.dumps(expert_data.get("brain_template", {})),
            json.dumps(expert_data.get("instruction_set", {})),
            json.dumps(expert_data.get("agent_definition", {})),
            expert_data.get("created_at", now),
            now,
            expert_data.get("status", "active"),
            expert_data.get("performance_score", 0.0),
            expert_data.get("success_rate", 0.0),
            expert_data.get("total_operations", 0),
            expert_data.get("successful_operations", 0),
            expert_data.get("avg_latency_ms", 0.0),
            expert_data.get("composition_count", 0),
            json.dumps(expert_data.get("tags", [])),
            json.dumps(expert_data.get("metadata", {})),
        ))
        self._conn.commit()
        self._cache[expert_id] = expert_data
        logger.info("Registered expert: %s (%s)", expert_id, expert_data.get("name"))
        return expert_id

    def get_expert(self, expert_id: str) -> Optional[Dict[str, Any]]:
        if expert_id in self._cache:
            return self._cache[expert_id]
        cursor = self._conn.execute(
            "SELECT * FROM experts WHERE expert_id = ?", (expert_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        expert = self._row_to_dict(row)
        self._cache[expert_id] = expert
        return expert

    def search_experts(self, domain: str = None, capability: str = None,
                       archetype: str = None, query: str = None,
                       min_success_rate: float = 0.0,
                       limit: int = 50) -> List[Dict[str, Any]]:
        conditions = ["status = 'active'"]
        params = []
        if domain:
            conditions.append("domain = ?")
            params.append(domain)
        if archetype:
            conditions.append("archetype = ?")
            params.append(archetype)
        if capability:
            conditions.append("capabilities LIKE ?")
            params.append(f'%"{capability}"%')
        if query:
            conditions.append("(name LIKE ? OR purpose LIKE ? OR tags LIKE ?)")
            params.extend([f"%{query}%"] * 3)
        if min_success_rate > 0:
            conditions.append("success_rate >= ?")
            params.append(min_success_rate)
        sql = f"SELECT * FROM experts WHERE {' AND '.join(conditions)} ORDER BY performance_score DESC LIMIT ?"
        params.append(limit)
        cursor = self._conn.execute(sql, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def update_performance(self, expert_id: str, success: bool,
                           latency_ms: float = 0.0) -> None:
        expert = self.get_expert(expert_id)
        if not expert:
            return
        total = expert.get("total_operations", 0) + 1
        successes = expert.get("successful_operations", 0) + (1 if success else 0)
        success_rate = successes / total if total > 0 else 0.0
        old_avg = expert.get("avg_latency_ms", 0.0)
        old_count = total - 1
        avg_latency = (old_avg * old_count + latency_ms) / total if old_count > 0 else latency_ms
        performance_score = success_rate * (1.0 - (avg_latency / (avg_latency + 1000.0)))
        self._conn.execute("""
            UPDATE experts SET total_operations = ?, successful_operations = ?,
                               success_rate = ?, avg_latency_ms = ?,
                               performance_score = ?, updated_at = ?
            WHERE expert_id = ?
        """, (total, successes, success_rate, avg_latency,
              performance_score, time.time(), expert_id))
        self._conn.commit()
        if expert_id in self._cache:
            self._cache[expert_id].update(
                total_operations=total, successful_operations=successes,
                success_rate=success_rate, avg_latency_ms=avg_latency,
                performance_score=performance_score
            )

    def record_lineage(self, expert_id: str, ancestor_id: str,
                       relationship: str = "derived_from",
                       contribution_weight: float = 0.5) -> str:
        lid = f"lin_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO expert_lineage (lineage_id, expert_id, ancestor_id,
                                         relationship, contribution_weight, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (lid, expert_id, ancestor_id, relationship, contribution_weight, time.time()))
        self._conn.commit()
        return lid

    def record_composition(self, expert_id: str, composed_with: str,
                           result_expert_id: str = None,
                           convergence_score: float = 0.0,
                           rounds: int = 0) -> str:
        cid = f"comp_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO expert_compositions (comp_id, expert_id, composed_with,
                                              result_expert_id, convergence_score,
                                              rounds, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cid, expert_id, composed_with, result_expert_id,
              convergence_score, rounds, time.time()))
        self._conn.commit()
        self._conn.execute(
            "UPDATE experts SET composition_count = composition_count + 1 WHERE expert_id = ?",
            (expert_id,)
        )
        self._conn.commit()
        return cid

    def get_lineage(self, expert_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM expert_lineage WHERE expert_id = ? ORDER BY created_at",
            (expert_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_composition_history(self, expert_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM expert_compositions WHERE expert_id = ? ORDER BY created_at DESC",
            (expert_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def list_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM experts ORDER BY performance_score DESC LIMIT ?",
            (limit,)
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_manifest(self) -> Dict[str, Any]:
        cursor = self._conn.execute("SELECT COUNT(*) as cnt FROM experts")
        total = cursor.fetchone()["cnt"]
        cursor = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM experts WHERE status = 'active'"
        )
        active = cursor.fetchone()["cnt"]
        cursor = self._conn.execute(
            "SELECT domain, COUNT(*) as cnt FROM experts GROUP BY domain ORDER BY cnt DESC"
        )
        domains = {row["domain"]: row["cnt"] for row in cursor.fetchall()}
        return {
            "total_experts": total,
            "active_experts": active,
            "domains": domains,
            "db_path": self.db_path,
        }

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        for field in ["capabilities", "governance_boundaries", "brain_template",
                       "instruction_set", "agent_definition", "tags", "metadata"]:
            if d.get(field) and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
