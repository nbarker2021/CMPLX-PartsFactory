"""Agent Sidecar — per-agent persistent SQLite database with LocalCRT tick integration.

Each agent gets its own SQLite file at data/agents/{agent_id}/agent_local.db
with tables for brain, wallet, identity, playbooks, instructions, and experiences.
The sidecar runs a LocalCRT daemon for periodic operations.
"""
from __future__ import annotations
import json
import os
import sqlite3
import time
import threading
import logging
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

from daemon.local_crt import LocalCRT

logger = logging.getLogger("sidecar")

AGENT_DATA_ROOT = os.environ.get("AGENT_DATA_ROOT", "/workspace/PartsFactory/CMPLX-PartsFactory/data/agents")


class AgentSidecar:
    """Per-agent persistent SQLite with data access API."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.root = Path(AGENT_DATA_ROOT) / agent_id
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = str(self.root / "agent_local.db")
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS brain_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_key TEXT UNIQUE,
                state_value TEXT,
                updated_at REAL
            );
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT UNIQUE,
                content TEXT,
                metadata TEXT,
                created_at REAL
            );
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type TEXT,
                content TEXT,
                embedding TEXT,
                created_at REAL
            );
            CREATE TABLE IF NOT EXISTS wallet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_balance REAL DEFAULT 0.0,
                transaction_count INTEGER DEFAULT 0,
                updated_at REAL
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_type TEXT,
                amount REAL,
                balance_after REAL,
                note TEXT,
                created_at REAL
            );
            CREATE TABLE IF NOT EXISTS identity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identity_tag TEXT UNIQUE,
                archetype TEXT,
                domain TEXT,
                capabilities TEXT,
                status TEXT DEFAULT 'initialized',
                updated_at REAL
            );
            CREATE TABLE IF NOT EXISTS playbooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playbook_id TEXT UNIQUE,
                name TEXT,
                steps TEXT,
                created_at REAL
            );
            CREATE TABLE IF NOT EXISTS instructions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instruction_id TEXT UNIQUE,
                priority INTEGER DEFAULT 0,
                content TEXT,
                status TEXT DEFAULT 'active',
                created_at REAL
            );
        """)
        conn.commit()

    def save_brain_state(self, key: str, value: Any):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO brain_states (state_key, state_value, updated_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), time.time()),
            )
            conn.commit()

    def get_brain_state(self, key: str) -> Optional[Any]:
        cur = self._connect().execute("SELECT state_value FROM brain_states WHERE state_key = ?", (key,))
        row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def add_knowledge(self, doc_id: str, content: str, metadata: dict = None):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO knowledge (doc_id, content, metadata, created_at) VALUES (?, ?, ?, ?)",
                (doc_id, content, json.dumps(metadata or {}), time.time()),
            )
            conn.commit()

    def add_experience(self, entry_type: str, content: str, embedding: list = None):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT INTO experiences (entry_type, content, embedding, created_at) VALUES (?, ?, ?, ?)",
                (entry_type, content, json.dumps(embedding or []), time.time()),
            )
            conn.commit()

    def update_wallet(self, amount: float, tx_type: str = "adjustment", note: str = ""):
        with self._lock:
            conn = self._connect()
            cur = conn.execute("SELECT token_balance FROM wallet ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            balance = (row[0] if row else 0.0) + amount
            conn.execute("INSERT INTO wallet (token_balance, transaction_count, updated_at) VALUES (?, ?, ?)",
                         (balance, 1, time.time()))
            conn.execute("INSERT INTO transactions (tx_type, amount, balance_after, note, created_at) VALUES (?, ?, ?, ?, ?)",
                         (tx_type, amount, balance, note, time.time()))
            conn.commit()
            return balance

    def get_wallet(self) -> dict:
        cur = self._connect().execute("SELECT token_balance, transaction_count, updated_at FROM wallet ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        return {"balance": row[0], "tx_count": row[1], "updated": row[2]} if row else {"balance": 0.0, "tx_count": 0}

    def set_identity(self, tag: str, archetype: str, domain: str, capabilities: list):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO identity (identity_tag, archetype, domain, capabilities, status, updated_at) VALUES (?, ?, ?, ?, 'active', ?)",
                (tag, archetype, domain, json.dumps(capabilities), time.time()),
            )
            conn.commit()

    def get_identity(self) -> Optional[dict]:
        cur = self._connect().execute("SELECT * FROM identity ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)

    def add_playbook(self, playbook_id: str, name: str, steps: list):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO playbooks (playbook_id, name, steps, created_at) VALUES (?, ?, ?, ?)",
                (playbook_id, name, json.dumps(steps), time.time()),
            )
            conn.commit()

    def add_instruction(self, instruction_id: str, content: str, priority: int = 0):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO instructions (instruction_id, priority, content, status, created_at) VALUES (?, ?, ?, 'active', ?)",
                (instruction_id, priority, content, time.time()),
            )
            conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


def register_agent_daemon(agent_id: str, sidecar: AgentSidecar,
                           global_url: str = "http://localhost:8878/ingest") -> LocalCRT:
    """Create a LocalCRT daemon for this agent's periodic operations."""
    crt = LocalCRT(service_name=f"sidecar-{agent_id}", tick_interval=10.0)

    def _brain_save():
        sidecar.save_brain_state("tick_autosave", {"timestamp": time.time(), "status": "ok"})

    def _wallet_check():
        w = sidecar.get_wallet()
        logger.info("Agent %s wallet: balance=%.2f", agent_id, w["balance"])

    def _identity_report():
        ident = sidecar.get_identity()
        if ident:
            import urllib.request
            body = json.dumps({"agent_id": agent_id, "identity": dict(ident)}).encode()
            try:
                urllib.request.urlopen(global_url, data=body, timeout=5)
            except Exception:
                pass

    def _flush_outbound(items):
        if items:
            body = json.dumps({"agent_id": agent_id, "items": items}).encode()
            try:
                import urllib.request
                urllib.request.urlopen(global_url, data=body, timeout=10)
            except Exception:
                pass

    crt.register("brain_save", 3, _brain_save, "Persist brain state snapshot")
    crt.register("wallet_check", 5, _wallet_check, "Verify wallet integrity")
    crt.register("identity_report", 7, _identity_report, "Report identity to global")
    crt.register_buffer("agent_outbound", _flush_outbound, flush_period=2)

    return crt
