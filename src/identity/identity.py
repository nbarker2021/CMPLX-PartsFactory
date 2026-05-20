#!/usr/bin/env python3
"""
CMPLX-PartsFactory — Agent Identity

Unique identity tags per agent with capability fingerprinting, domain membership,
governance constraints, lineage tracking, and lifecycle status management.
SQLite-persisted with PostgreSQL sidecar sync via LocalCRT.
"""

import os
import json
import sqlite3
import uuid
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger("identity")

IDENTITY_DB_PATH = "/mnt/d/PartsFactory/CMPLX-PartsFactory/data/identity_registry.sqlite"

IDENTITY_SCHEMA = """
CREATE TABLE IF NOT EXISTS identities (
    agent_id TEXT PRIMARY KEY,
    identity_tag TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL,
    archetype TEXT NOT NULL,
    serial TEXT NOT NULL,
    capability_fingerprint TEXT,
    domain_membership TEXT,
    governance_constraints TEXT,
    lineage TEXT,
    status TEXT DEFAULT 'initialized',
    dna_sequence TEXT,
    brain_template TEXT,
    e8_coordinates TEXT,
    created_at REAL,
    updated_at REAL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS capability_index (
    cap_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    capability TEXT NOT NULL,
    proficiency REAL DEFAULT 0.5,
    verified INTEGER DEFAULT 0,
    FOREIGN KEY (agent_id) REFERENCES identities(agent_id)
);

CREATE TABLE IF NOT EXISTS domain_roster (
    roster_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    role TEXT,
    joined_at REAL,
    FOREIGN KEY (agent_id) REFERENCES identities(agent_id)
);

CREATE TABLE IF NOT EXISTS lineage_edges (
    edge_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    ancestor_id TEXT NOT NULL,
    relationship TEXT,
    contribution_weight REAL DEFAULT 0.0,
    recorded_at REAL,
    FOREIGN KEY (agent_id) REFERENCES identities(agent_id),
    FOREIGN KEY (ancestor_id) REFERENCES identities(agent_id)
);

CREATE TABLE IF NOT EXISTS status_log (
    log_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    status TEXT NOT NULL,
    transitioned_at REAL,
    reason TEXT,
    FOREIGN KEY (agent_id) REFERENCES identities(agent_id)
);

CREATE INDEX IF NOT EXISTS idx_identity_domain ON identities(domain);
CREATE INDEX IF NOT EXISTS idx_identity_archetype ON identities(archetype);
CREATE INDEX IF NOT EXISTS idx_identity_status ON identities(status);
CREATE INDEX IF NOT EXISTS idx_cap_agent ON capability_index(agent_id);
CREATE INDEX IF NOT EXISTS idx_roster_domain ON domain_roster(domain);
CREATE INDEX IF NOT EXISTS idx_lineage_agent ON lineage_edges(agent_id);
"""

VALID_STATUSES = {"initialized", "active", "idle", "retired", "suspended"}


class AgentIdentity:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or IDENTITY_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._serial_counters: Dict[str, int] = {}
        self._sidecar_sync_fn: Optional[callable] = None

    def connect(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(IDENTITY_SCHEMA)
        self._conn.commit()
        self._load_serial_counters()

    def set_sidecar_sync(self, sync_fn: callable):
        self._sidecar_sync_fn = sync_fn

    def _load_serial_counters(self):
        cursor = self._conn.execute(
            "SELECT domain, archetype, COUNT(*) as cnt FROM identities GROUP BY domain, archetype"
        )
        for row in cursor.fetchall():
            key = f"{row['domain']}-{row['archetype']}"
            self._serial_counters[key] = row["cnt"]

    def _next_serial(self, domain: str, archetype: str) -> str:
        key = f"{domain}-{archetype}"
        self._serial_counters[key] = self._serial_counters.get(key, 0) + 1
        return f"{self._serial_counters[key]:04d}"

    def register(self, domain: str, archetype: str,
                 capability_fingerprint: List[str] = None,
                 domain_membership: List[str] = None,
                 governance_constraints: Dict[str, Any] = None,
                 lineage: List[Dict[str, Any]] = None,
                 dna_sequence: str = None,
                 brain_template: Dict[str, Any] = None,
                 e8_coordinates: List[float] = None,
                 metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        serial = self._next_serial(domain, archetype)
        identity_tag = f"{domain}-{archetype}-{serial}"
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        now = time.time()

        identity = {
            "agent_id": agent_id,
            "identity_tag": identity_tag,
            "domain": domain,
            "archetype": archetype,
            "serial": serial,
            "capability_fingerprint": capability_fingerprint or [],
            "domain_membership": domain_membership or [domain],
            "governance_constraints": governance_constraints or {},
            "lineage": lineage or [],
            "status": "initialized",
            "dna_sequence": dna_sequence or "",
            "brain_template": brain_template or {},
            "e8_coordinates": e8_coordinates or [0.0] * 8,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
        }

        self._conn.execute("""
            INSERT INTO identities (
                agent_id, identity_tag, domain, archetype, serial,
                capability_fingerprint, domain_membership, governance_constraints,
                lineage, status, dna_sequence, brain_template, e8_coordinates,
                created_at, updated_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_id, identity_tag, domain, archetype, serial,
            json.dumps(identity["capability_fingerprint"]),
            json.dumps(identity["domain_membership"]),
            json.dumps(identity["governance_constraints"]),
            json.dumps(identity["lineage"]),
            identity["status"],
            identity["dna_sequence"],
            json.dumps(identity["brain_template"]),
            json.dumps(identity["e8_coordinates"]),
            now, now, json.dumps(identity["metadata"]),
        ))

        for cap in (capability_fingerprint or []):
            cap_id = f"cap_{uuid.uuid4().hex[:12]}"
            self._conn.execute("""
                INSERT INTO capability_index (cap_id, agent_id, capability, proficiency, verified)
                VALUES (?, ?, ?, ?, ?)
            """, (cap_id, agent_id, cap, 0.5, 0))

        for dom in (domain_membership or [domain]):
            roster_id = f"rost_{uuid.uuid4().hex[:12]}"
            self._conn.execute("""
                INSERT INTO domain_roster (roster_id, domain, agent_id, role, joined_at)
                VALUES (?, ?, ?, ?, ?)
            """, (roster_id, dom, agent_id, "member", now))

        for entry in (lineage or []):
            edge_id = f"edge_{uuid.uuid4().hex[:12]}"
            self._conn.execute("""
                INSERT INTO lineage_edges (edge_id, agent_id, ancestor_id, relationship, contribution_weight, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (edge_id, agent_id, entry.get("ancestor_id", ""),
                  entry.get("relationship", "derived_from"),
                  entry.get("contribution_weight", 0.5), now))

        log_id = f"log_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO status_log (log_id, agent_id, status, transitioned_at, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (log_id, agent_id, "initialized", now, "Agent registered"))

        self._conn.commit()
        self._cache[agent_id] = identity
        logger.info("Registered identity: %s (%s)", identity_tag, agent_id)

        if self._sidecar_sync_fn:
            self._sidecar_sync_fn("identity_report", identity)

        return identity

    def get(self, agent_id: str = None, identity_tag: str = None) -> Optional[Dict[str, Any]]:
        if agent_id and agent_id in self._cache:
            return self._cache[agent_id]
        if identity_tag:
            tag_to_id = self.resolve_tag(identity_tag)
            if tag_to_id:
                agent_id = tag_to_id
        if not agent_id:
            return None
        cursor = self._conn.execute("SELECT * FROM identities WHERE agent_id = ?", (agent_id,))
        row = cursor.fetchone()
        if not row:
            return None
        identity = self._row_to_dict(row)
        self._cache[agent_id] = identity
        return identity

    def resolve_tag(self, identity_tag: str) -> Optional[str]:
        cursor = self._conn.execute(
            "SELECT agent_id FROM identities WHERE identity_tag = ?", (identity_tag,)
        )
        row = cursor.fetchone()
        return row["agent_id"] if row else None

    def set_status(self, agent_id: str, status: str, reason: str = ""):
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Valid: {VALID_STATUSES}")
        now = time.time()
        self._conn.execute(
            "UPDATE identities SET status = ?, updated_at = ? WHERE agent_id = ?",
            (status, now, agent_id),
        )
        log_id = f"log_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO status_log (log_id, agent_id, status, transitioned_at, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (log_id, agent_id, status, now, reason))
        self._conn.commit()
        if agent_id in self._cache:
            self._cache[agent_id]["status"] = status
        logger.info("Identity %s status -> %s", agent_id, status)
        if self._sidecar_sync_fn:
            self._sidecar_sync_fn("identity_report", {
                "agent_id": agent_id, "status": status, "reason": reason,
            })

    def add_capability(self, agent_id: str, capability: str, proficiency: float = 0.5):
        cap_id = f"cap_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO capability_index (cap_id, agent_id, capability, proficiency, verified)
            VALUES (?, ?, ?, ?, ?)
        """, (cap_id, agent_id, capability, proficiency, 0))
        self._conn.execute(
            "UPDATE identities SET updated_at = ? WHERE agent_id = ?",
            (time.time(), agent_id),
        )
        self._conn.commit()
        if agent_id in self._cache:
            self._cache[agent_id].setdefault("capability_fingerprint", []).append(capability)
        if self._sidecar_sync_fn:
            self._sidecar_sync_fn("identity_report", {
                "agent_id": agent_id, "capability_added": capability,
            })

    def add_lineage_entry(self, agent_id: str, ancestor_id: str,
                          relationship: str = "derived_from",
                          contribution_weight: float = 0.5):
        edge_id = f"edge_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO lineage_edges (edge_id, agent_id, ancestor_id, relationship, contribution_weight, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (edge_id, agent_id, ancestor_id, relationship, contribution_weight, time.time()))
        self._conn.commit()

    def get_lineage(self, agent_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM lineage_edges WHERE agent_id = ? ORDER BY recorded_at", (agent_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_capabilities(self, agent_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM capability_index WHERE agent_id = ?", (agent_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_domain_memberships(self, agent_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM domain_roster WHERE agent_id = ?", (agent_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_status_history(self, agent_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM status_log WHERE agent_id = ? ORDER BY transitioned_at DESC", (agent_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def search(self, domain: str = None, archetype: str = None,
               status: str = None, capability: str = None,
               query: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        if domain:
            conditions.append("domain = ?")
            params.append(domain)
        if archetype:
            conditions.append("archetype = ?")
            params.append(archetype)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if capability:
            conditions.append("agent_id IN (SELECT agent_id FROM capability_index WHERE capability = ?)")
            params.append(capability)
        if query:
            conditions.append("(identity_tag LIKE ? OR domain LIKE ? OR archetype LIKE ?)")
            params.extend([f"%{query}%"] * 3)
        sql = "SELECT * FROM identities"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        cursor = self._conn.execute(sql, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def list_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        return self.search(domain=domain)

    def list_by_archetype(self, archetype: str) -> List[Dict[str, Any]]:
        return self.search(archetype=archetype)

    def get_manifest(self) -> Dict[str, Any]:
        cursor = self._conn.execute("SELECT COUNT(*) FROM identities")
        total = cursor.fetchone()[0]
        cursor = self._conn.execute("SELECT COUNT(*) FROM identities WHERE status = 'active'")
        active = cursor.fetchone()[0]
        cursor = self._conn.execute("SELECT domain, COUNT(*) as cnt FROM identities GROUP BY domain")
        domains = {row["domain"]: row["cnt"] for row in cursor.fetchall()}
        cursor = self._conn.execute("SELECT archetype, COUNT(*) as cnt FROM identities GROUP BY archetype")
        archetypes = {row["archetype"]: row["cnt"] for row in cursor.fetchall()}
        return {
            "total_agents": total,
            "active_agents": active,
            "domains": domains,
            "archetypes": archetypes,
            "db_path": self.db_path,
        }

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        for field in ["capability_fingerprint", "domain_membership",
                       "governance_constraints", "lineage", "brain_template",
                       "e8_coordinates", "metadata"]:
            if d.get(field) and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
