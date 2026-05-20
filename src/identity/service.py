#!/usr/bin/env python3
"""
CMPLX-PartsFactory — LocalCRT Sidecar & Integration Service

Bridges identity, playbook, instruction, and contract systems to:
  - LocalCRT sidecar channels (identity_report, playbook_sync)
  - PostgreSQL aggregation (identity and playbook tables)
  - Wallet service (identity-linked wallets)
  - Expertise pipeline (agent identity for expert creation)

Acts as the integration layer between all four identity subsystems
and the broader CMPLX ecosystem.
"""

import os
import json
import sqlite3
import uuid
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from .identity import AgentIdentity
from .playbook import PlaybookEngine
from .instructions import InstructionManager
from .contracts import ContractEngine

logger = logging.getLogger("identity.service")

SIDECAR_DB_PATH = "/mnt/d/PartsFactory/CMPLX-PartsFactory/data/localcrt_sidecar.sqlite"

SIDECAR_SCHEMA = """
CREATE TABLE IF NOT EXISTS identity_report_log (
    report_id TEXT PRIMARY KEY,
    agent_id TEXT,
    event_type TEXT,
    payload TEXT,
    channel TEXT,
    delivered INTEGER DEFAULT 0,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS playbook_sync_log (
    sync_id TEXT PRIMARY KEY,
    playbook_id TEXT,
    playbook_name TEXT,
    run_id TEXT,
    event_type TEXT,
    payload TEXT,
    channel TEXT,
    delivered INTEGER DEFAULT 0,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS postgres_pending (
    pending_id TEXT PRIMARY KEY,
    table_name TEXT NOT NULL,
    action TEXT NOT NULL,
    payload TEXT,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_at REAL,
    synced_at REAL
);

CREATE TABLE IF NOT EXISTS wallets (
    wallet_id TEXT PRIMARY KEY,
    agent_id TEXT UNIQUE NOT NULL,
    identity_tag TEXT,
    balance REAL DEFAULT 0.0,
    token_type TEXT DEFAULT 'CMPLX',
    created_at REAL,
    updated_at REAL,
    metadata TEXT,
    FOREIGN KEY (agent_id) REFERENCES identities(agent_id)
);

CREATE TABLE IF NOT EXISTS wallet_transactions (
    tx_id TEXT PRIMARY KEY,
    wallet_id TEXT NOT NULL,
    tx_type TEXT NOT NULL,
    amount REAL,
    balance_before REAL,
    balance_after REAL,
    reference TEXT,
    created_at REAL,
    FOREIGN KEY (wallet_id) REFERENCES wallets(wallet_id)
);

CREATE TABLE IF NOT EXISTS expert_pipeline_queue (
    queue_id TEXT PRIMARY KEY,
    agent_id TEXT,
    identity_tag TEXT,
    pipeline_action TEXT,
    payload TEXT,
    status TEXT DEFAULT 'queued',
    created_at REAL,
    processed_at REAL,
    result TEXT
);

CREATE INDEX IF NOT EXISTS idx_report_agent ON identity_report_log(agent_id);
CREATE INDEX IF NOT EXISTS idx_sync_playbook ON playbook_sync_log(playbook_id);
CREATE INDEX IF NOT EXISTS idx_pg_pending ON postgres_pending(status, priority);
CREATE INDEX IF NOT EXISTS idx_wallet_agent ON wallets(agent_id);
CREATE INDEX IF NOT EXISTS idx_tx_wallet ON wallet_transactions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_status ON expert_pipeline_queue(status);
"""


class LocalCRT:
    def __init__(self, identity: AgentIdentity = None,
                 playbook: PlaybookEngine = None,
                 instructions: InstructionManager = None,
                 contracts: ContractEngine = None,
                 db_path: str = None):
        self.identity = identity
        self.playbook = playbook
        self.instructions = instructions
        self.contracts = contracts
        self.db_path = db_path or SIDECAR_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._pg_sync_fn: Optional[Callable] = None
        self._channels: Dict[str, List[Callable]] = {
            "identity_report": [],
            "playbook_sync": [],
        }

    def connect(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SIDECAR_SCHEMA)
        self._conn.commit()

        if self.identity:
            self.identity.set_sidecar_sync(self._sidecar_dispatch)
        if self.playbook:
            self.playbook.set_sidecar_sync(self._sidecar_dispatch)

    def set_postgres_sync(self, sync_fn: Callable):
        self._pg_sync_fn = sync_fn

    def subscribe(self, channel: str, handler: Callable):
        if channel in self._channels:
            self._channels[channel].append(handler)

    def _sidecar_dispatch(self, channel: str, payload: Any):
        now = time.time()
        if channel == "identity_report":
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            self._conn.execute("""
                INSERT INTO identity_report_log (report_id, agent_id, event_type, payload, channel, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                payload.get("agent_id") if isinstance(payload, dict) else None,
                "identity_event",
                json.dumps(payload),
                channel,
                now,
            ))
        elif channel == "playbook_sync":
            sync_id = f"sync_{uuid.uuid4().hex[:12]}"
            self._conn.execute("""
                INSERT INTO playbook_sync_log (sync_id, playbook_id, playbook_name, run_id, event_type, payload, channel, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sync_id,
                payload.get("playbook_id") if isinstance(payload, dict) else None,
                payload.get("playbook_name") if isinstance(payload, dict) else None,
                payload.get("run_id") if isinstance(payload, dict) else None,
                "playbook_event",
                json.dumps(payload),
                channel,
                now,
            ))

        self._conn.commit()
        self._notify_subscribers(channel, payload)
        self._queue_postgres_sync(channel, payload)

    def _notify_subscribers(self, channel: str, payload: Any):
        for handler in self._channels.get(channel, []):
            try:
                handler(payload)
            except Exception as e:
                logger.error("Subscriber error on %s: %s", channel, e)

    def _queue_postgres_sync(self, channel: str, payload: Any):
        pg_id = f"pg_{uuid.uuid4().hex[:12]}"
        table = "identity_events" if channel == "identity_report" else "playbook_events"
        self._conn.execute("""
            INSERT INTO postgres_pending (pending_id, table_name, action, payload, priority, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pg_id, table, "upsert", json.dumps(payload), 50, "pending", time.time()))
        self._conn.commit()

    # --- Wallet Service ---

    def create_wallet(self, agent_id: str, identity_tag: str = None,
                      initial_balance: float = 0.0,
                      token_type: str = "CMPLX",
                      metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        wallet_id = f"wal_{uuid.uuid4().hex[:12]}"
        now = time.time()
        self._conn.execute("""
            INSERT OR REPLACE INTO wallets (wallet_id, agent_id, identity_tag, balance, token_type, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (wallet_id, agent_id, identity_tag, initial_balance, token_type,
              now, now, json.dumps(metadata or {})))
        self._conn.commit()
        logger.info("Created wallet %s for agent %s", wallet_id, agent_id)
        return self.get_wallet(wallet_id=wallet_id)

    def get_wallet(self, wallet_id: str = None, agent_id: str = None) -> Optional[Dict[str, Any]]:
        if wallet_id:
            cursor = self._conn.execute("SELECT * FROM wallets WHERE wallet_id = ?", (wallet_id,))
        elif agent_id:
            cursor = self._conn.execute("SELECT * FROM wallets WHERE agent_id = ?", (agent_id,))
        else:
            return None
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_wallet(row)

    def credit_wallet(self, agent_id: str, amount: float,
                      reference: str = "", tx_type: str = "credit") -> Dict[str, Any]:
        wallet = self.get_wallet(agent_id=agent_id)
        if not wallet:
            wallet = self.create_wallet(agent_id=agent_id)
        balance_before = wallet["balance"]
        balance_after = balance_before + amount
        self._conn.execute(
            "UPDATE wallets SET balance = ?, updated_at = ? WHERE agent_id = ?",
            (balance_after, time.time(), agent_id),
        )
        tx_id = f"tx_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO wallet_transactions (tx_id, wallet_id, tx_type, amount, balance_before, balance_after, reference, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx_id, wallet["wallet_id"], tx_type, amount, balance_before, balance_after, reference, time.time()))
        self._conn.commit()
        return {
            "wallet_id": wallet["wallet_id"],
            "agent_id": agent_id,
            "tx_id": tx_id,
            "amount": amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
        }

    def debit_wallet(self, agent_id: str, amount: float,
                     reference: str = "", tx_type: str = "debit") -> Dict[str, Any]:
        wallet = self.get_wallet(agent_id=agent_id)
        if not wallet:
            raise ValueError(f"No wallet for agent: {agent_id}")
        if wallet["balance"] < amount:
            raise ValueError(f"Insufficient balance: {wallet['balance']} < {amount}")
        return self.credit_wallet(agent_id, -amount, reference, tx_type)

    def get_transactions(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        wallet = self.get_wallet(agent_id=agent_id)
        if not wallet:
            return []
        cursor = self._conn.execute("""
            SELECT * FROM wallet_transactions WHERE wallet_id = ? ORDER BY created_at DESC LIMIT ?
        """, (wallet["wallet_id"], limit))
        return [dict(row) for row in cursor.fetchall()]

    # --- Expertise Pipeline Integration ---

    def queue_expert_creation(self, agent_id: str, identity_tag: str,
                              pipeline_action: str = "create_expert",
                              payload: Dict[str, Any] = None) -> str:
        queue_id = f"pipe_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO expert_pipeline_queue (queue_id, agent_id, identity_tag, pipeline_action, payload, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (queue_id, agent_id, identity_tag, pipeline_action,
              json.dumps(payload or {}), "queued", time.time()))
        self._conn.commit()
        logger.info("Queued expert creation for %s (%s)", identity_tag, pipeline_action)
        return queue_id

    def process_pipeline_queue(self, handler: Callable = None, limit: int = 5) -> List[Dict[str, Any]]:
        cursor = self._conn.execute("""
            SELECT * FROM expert_pipeline_queue
            WHERE status = 'queued'
            ORDER BY created_at ASC LIMIT ?
        """, (limit,))
        items = [dict(row) for row in cursor.fetchall()]
        results = []
        for item in items:
            try:
                if handler:
                    result = handler(item)
                else:
                    result = {"status": "acknowledged", "queue_id": item["queue_id"]}
                self._conn.execute(
                    "UPDATE expert_pipeline_queue SET status = ?, processed_at = ?, result = ? WHERE queue_id = ?",
                    ("processed", time.time(), json.dumps(result), item["queue_id"]),
                )
                results.append(result)
            except Exception as e:
                self._conn.execute(
                    "UPDATE expert_pipeline_queue SET status = ? WHERE queue_id = ?",
                    ("failed", item["queue_id"]),
                )
                logger.error("Pipeline queue item %s failed: %s", item["queue_id"], e)
        self._conn.commit()
        return results

    # --- PostgreSQL Sync ---

    def sync_to_postgres(self, batch_size: int = 50) -> Dict[str, Any]:
        if not self._pg_sync_fn:
            return {"error": "No PostgreSQL sync function configured"}
        cursor = self._conn.execute("""
            SELECT * FROM postgres_pending
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC LIMIT ?
        """, (batch_size,))
        items = [dict(row) for row in cursor.fetchall()]
        synced = 0
        failed = 0
        for item in items:
            try:
                self._pg_sync_fn(
                    table=item["table_name"],
                    action=item["action"],
                    payload=json.loads(item["payload"]),
                )
                self._conn.execute(
                    "UPDATE postgres_pending SET status = 'synced', synced_at = ? WHERE pending_id = ?",
                    (time.time(), item["pending_id"]),
                )
                synced += 1
            except Exception as e:
                logger.error("PG sync failed for %s: %s", item["pending_id"], e)
                failed += 1
        self._conn.commit()
        return {"synced": synced, "failed": failed, "total": len(items)}

    def get_pending_sync_count(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM postgres_pending WHERE status = 'pending'"
        ).fetchone()
        return row["cnt"]

    # --- Report Channel Access ---

    def get_identity_reports(self, agent_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        if agent_id:
            cursor = self._conn.execute("""
                SELECT * FROM identity_report_log WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?
            """, (agent_id, limit))
        else:
            cursor = self._conn.execute("""
                SELECT * FROM identity_report_log ORDER BY created_at DESC LIMIT ?
            """, (limit,))
        return [self._row_to_report(row) for row in cursor.fetchall()]

    def get_playbook_syncs(self, playbook_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        if playbook_id:
            cursor = self._conn.execute("""
                SELECT * FROM playbook_sync_log WHERE playbook_id = ? ORDER BY created_at DESC LIMIT ?
            """, (playbook_id, limit))
        else:
            cursor = self._conn.execute("""
                SELECT * FROM playbook_sync_log ORDER BY created_at DESC LIMIT ?
            """, (limit,))
        return [self._row_to_sync(row) for row in cursor.fetchall()]

    # --- Full System Status ---

    def get_system_status(self) -> Dict[str, Any]:
        cursor = self._conn.execute("SELECT COUNT(*) FROM identity_report_log")
        report_count = cursor.fetchone()[0]
        cursor = self._conn.execute("SELECT COUNT(*) FROM playbook_sync_log")
        sync_count = cursor.fetchone()[0]
        cursor = self._conn.execute("SELECT COUNT(*) FROM wallets")
        wallet_count = cursor.fetchone()[0]
        cursor = self._conn.execute("SELECT COUNT(*) FROM expert_pipeline_queue")
        pipeline_count = cursor.fetchone()[0]
        pending_pg = self.get_pending_sync_count()

        subsystems = {}
        if self.identity:
            subsystems["identity"] = self.identity.get_manifest()
        if self.playbook:
            subsystems["playbook"] = {"registered": len(self.playbook.list_playbooks())}

        return {
            "sidecar": {
                "identity_reports": report_count,
                "playbook_syncs": sync_count,
                "pending_postgres_syncs": pending_pg,
            },
            "wallets": wallet_count,
            "pipeline_queue": pipeline_count,
            "subsystems": subsystems,
            "db_path": self.db_path,
        }

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _row_to_wallet(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        if d.get("metadata") and isinstance(d["metadata"], str):
            try:
                d["metadata"] = json.loads(d["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass
        return d

    def _row_to_report(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        if d.get("payload") and isinstance(d["payload"], str):
            try:
                d["payload"] = json.loads(d["payload"])
            except (json.JSONDecodeError, TypeError):
                pass
        return d

    def _row_to_sync(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        if d.get("payload") and isinstance(d["payload"], str):
            try:
                d["payload"] = json.loads(d["payload"])
            except (json.JSONDecodeError, TypeError):
                pass
        return d
