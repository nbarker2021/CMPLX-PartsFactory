#!/usr/bin/env python3
"""
CMPLX-PartsFactory — Instruction Manager

Active instruction sets per agent with governance rules, domain-specific
operating procedures, priority-based ordering, and full lifecycle management
(draft → active → superseded → archived). Integrates with AGENTS.md directive system.
"""

import os
import json
import sqlite3
import uuid
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger("instructions")

INSTRUCTIONS_DB_PATH = "/mnt/d/PartsFactory/CMPLX-PartsFactory/data/instruction_store.sqlite"

INSTRUCTIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS instruction_sets (
    set_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    instructions TEXT,
    lifecycle_status TEXT DEFAULT 'draft',
    priority INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    source TEXT,
    created_at REAL,
    activated_at REAL,
    superseded_at REAL,
    archived_at REAL,
    hash TEXT,
    metadata TEXT,
    FOREIGN KEY (agent_id) REFERENCES identities(agent_id)
);

CREATE TABLE IF NOT EXISTS governance_rules (
    rule_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    rule_key TEXT NOT NULL,
    rule_value TEXT,
    rule_type TEXT,
    priority INTEGER DEFAULT 0,
    enabled INTEGER DEFAULT 1,
    created_at REAL,
    metadata TEXT,
    FOREIGN KEY (agent_id) REFERENCES identities(agent_id)
);

CREATE TABLE IF NOT EXISTS domain_procedures (
    proc_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    agent_id TEXT,
    procedure_text TEXT,
    procedure_type TEXT,
    priority INTEGER DEFAULT 0,
    created_at REAL,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_instr_agent ON instruction_sets(agent_id);
CREATE INDEX IF NOT EXISTS idx_instr_status ON instruction_sets(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_gov_agent ON governance_rules(agent_id);
CREATE INDEX IF NOT EXISTS idx_proc_domain ON domain_procedures(domain);
"""


class InstructionLifecycle(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


INSTRUCTION_TEMPLATES = {
    "governance_base": {
        "rules": [
            {"key": "audit_all_operations", "value": "true", "type": "compliance"},
            {"key": "record_boundary_events", "value": "true", "type": "compliance"},
            {"key": "max_entropy_delta", "value": "0.8", "type": "constraint"},
            {"key": "require_provenance", "value": "true", "type": "quality"},
            {"key": "log_to_identity_report", "value": "true", "type": "reporting"},
        ],
        "directives": [
            "Operate within defined governance boundaries at all times",
            "Log all operations with timestamps and receipts",
            "Never bypass geometric invariant checks",
            "Report governance violations immediately",
        ],
    },
    "domain_storage": {
        "rules": [
            {"key": "validate_input_before_store", "value": "true", "type": "safety"},
            {"key": "require_receipt_on_store", "value": "true", "type": "compliance"},
            {"key": "snap_label_all_crystals", "value": "true", "type": "quality"},
        ],
        "directives": [
            "Always validate input before storing to crystals",
            "Generate and verify receipts for every store operation",
            "Apply domain snap labels to all stored content",
        ],
    },
    "domain_analysis": {
        "rules": [
            {"key": "stratify_before_classify", "value": "true", "type": "procedure"},
            {"key": "verify_classification", "value": "true", "type": "quality"},
        ],
        "directives": [
            "Stratify concepts before applying classification tags",
            "Verify classification results against known taxonomies",
        ],
    },
    "agents_md_integration": {
        "rules": [
            {"key": "respect_work_window_discipline", "value": "true", "type": "protocol"},
            {"key": "review_memory_before_work", "value": "true", "type": "protocol"},
            {"key": "never_trust_prior_without_verification", "value": "true", "type": "epistemic"},
            {"key": "source_form_is_not_destiny", "value": "true", "type": "doctrine"},
            {"key": "geometry_is_primary", "value": "true", "type": "doctrine"},
        ],
        "directives": [
            "Follow 12.5% checkpoint protocol for all work windows",
            "Review memory before starting any work session",
            "Do not trust training prior without local verification",
            "Re-express artifacts freely — original form is not destiny",
            "Design in terms of geometry, not semantics",
        ],
    },
}


class InstructionManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or INSTRUCTIONS_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._cache: Dict[str, Dict[str, Any]] = {}

    def connect(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(INSTRUCTIONS_SCHEMA)
        self._conn.commit()

    def create_set(self, agent_id: str, name: str,
                   instructions: List[str],
                   description: str = "",
                   priority: int = 0,
                   source: str = "manual",
                   metadata: Dict[str, Any] = None) -> str:
        set_id = f"iset_{uuid.uuid4().hex[:12]}"
        now = time.time()
        instr_hash = hashlib.sha256(
            json.dumps(instructions, sort_keys=True).encode()
        ).hexdigest()[:16]

        self._conn.execute("""
            INSERT INTO instruction_sets (
                set_id, agent_id, name, description, instructions,
                lifecycle_status, priority, version, source,
                created_at, hash, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            set_id, agent_id, name, description,
            json.dumps(instructions),
            InstructionLifecycle.DRAFT.value,
            priority, 1, source,
            now, instr_hash,
            json.dumps(metadata or {}),
        ))
        self._conn.commit()
        logger.info("Created instruction set %s for agent %s", set_id, agent_id)
        return set_id

    def activate(self, set_id: str):
        now = time.time()
        self._conn.execute(
            "UPDATE instruction_sets SET lifecycle_status = ?, activated_at = ? WHERE set_id = ?",
            (InstructionLifecycle.ACTIVE.value, now, set_id),
        )
        self._conn.commit()

    def supersede(self, set_id: str):
        now = time.time()
        self._conn.execute(
            "UPDATE instruction_sets SET lifecycle_status = ?, superseded_at = ? WHERE set_id = ?",
            (InstructionLifecycle.SUPERSEDED.value, now, set_id),
        )
        self._conn.commit()

    def archive(self, set_id: str):
        now = time.time()
        self._conn.execute(
            "UPDATE instruction_sets SET lifecycle_status = ?, archived_at = ? WHERE set_id = ?",
            (InstructionLifecycle.ARCHIVED.value, now, set_id),
        )
        self._conn.commit()

    def get_active_set(self, agent_id: str) -> Optional[Dict[str, Any]]:
        cursor = self._conn.execute("""
            SELECT * FROM instruction_sets
            WHERE agent_id = ? AND lifecycle_status = 'active'
            ORDER BY priority DESC, created_at DESC LIMIT 1
        """, (agent_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_set(row)

    def get_set(self, set_id: str) -> Optional[Dict[str, Any]]:
        if set_id in self._cache:
            return self._cache[set_id]
        cursor = self._conn.execute(
            "SELECT * FROM instruction_sets WHERE set_id = ?", (set_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        s = self._row_to_set(row)
        self._cache[set_id] = s
        return s

    def list_sets(self, agent_id: str = None, lifecycle_status: str = None,
                  limit: int = 50) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if lifecycle_status:
            conditions.append("lifecycle_status = ?")
            params.append(lifecycle_status)
        sql = "SELECT * FROM instruction_sets"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY priority DESC, created_at DESC LIMIT ?"
        params.append(limit)
        cursor = self._conn.execute(sql, params)
        return [self._row_to_set(row) for row in cursor.fetchall()]

    def add_governance_rule(self, agent_id: str, rule_key: str,
                            rule_value: str, rule_type: str = "compliance",
                            priority: int = 0,
                            metadata: Dict[str, Any] = None) -> str:
        rule_id = f"rule_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO governance_rules (rule_id, agent_id, rule_key, rule_value,
                rule_type, priority, enabled, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rule_id, agent_id, rule_key, rule_value, rule_type,
              priority, 1, time.time(), json.dumps(metadata or {})))
        self._conn.commit()
        return rule_id

    def get_governance_rules(self, agent_id: str, enabled_only: bool = True) -> List[Dict[str, Any]]:
        if enabled_only:
            cursor = self._conn.execute("""
                SELECT * FROM governance_rules
                WHERE agent_id = ? AND enabled = 1
                ORDER BY priority DESC, created_at
            """, (agent_id,))
        else:
            cursor = self._conn.execute("""
                SELECT * FROM governance_rules WHERE agent_id = ?
                ORDER BY priority DESC, created_at
            """, (agent_id,))
        return [dict(row) for row in cursor.fetchall()]

    def add_domain_procedure(self, domain: str, procedure_text: str,
                             procedure_type: str = "operating",
                             agent_id: str = None,
                             priority: int = 0,
                             metadata: Dict[str, Any] = None) -> str:
        proc_id = f"proc_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO domain_procedures (proc_id, domain, agent_id, procedure_text,
                procedure_type, priority, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (proc_id, domain, agent_id, procedure_text, procedure_type,
              priority, time.time(), json.dumps(metadata or {})))
        self._conn.commit()
        return proc_id

    def get_domain_procedures(self, domain: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute("""
            SELECT * FROM domain_procedures WHERE domain = ?
            ORDER BY priority DESC, created_at
        """, (domain,))
        return [dict(row) for row in cursor.fetchall()]

    def apply_template(self, agent_id: str, template_name: str) -> str:
        if template_name not in INSTRUCTION_TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")
        template = INSTRUCTION_TEMPLATES[template_name]
        set_id = self.create_set(
            agent_id=agent_id,
            name=f"{template_name}_{int(time.time())}",
            instructions=template.get("directives", []),
            description=f"Template: {template_name}",
            priority=50,
            source="template",
        )
        for rule in template.get("rules", []):
            self.add_governance_rule(
                agent_id=agent_id,
                rule_key=rule["key"],
                rule_value=rule["value"],
                rule_type=rule.get("type", "compliance"),
                metadata={"template": template_name},
            )
        self.activate(set_id)
        return set_id

    def apply_all_base_templates(self, agent_id: str) -> List[str]:
        set_ids = []
        for template_name in INSTRUCTION_TEMPLATES:
            sid = self.apply_template(agent_id, template_name)
            set_ids.append(sid)
        return set_ids

    def get_full_directive(self, agent_id: str) -> Dict[str, Any]:
        active_set = self.get_active_set(agent_id)
        rules = self.get_governance_rules(agent_id)
        return {
            "agent_id": agent_id,
            "instructions": active_set["instructions"] if active_set else [],
            "governance_rules": rules,
            "instruction_set_id": active_set["set_id"] if active_set else None,
        }

    def search_procedures(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        cursor = self._conn.execute("""
            SELECT * FROM domain_procedures
            WHERE procedure_text LIKE ? OR domain LIKE ?
            ORDER BY priority DESC LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _row_to_set(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        for field in ["instructions", "metadata"]:
            if d.get(field) and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
