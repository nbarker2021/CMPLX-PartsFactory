"""AgentMemory — SQLite-backed persistence for session history and knowledge base.

Thread-safe: each thread gets its own connection via thread-local storage.
"""

from __future__ import annotations
import json
import os
import sqlite3
import threading
import time
import uuid
import logging
from typing import Any

import numpy as np

logger = logging.getLogger("runtime.memory")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    agent_id TEXT,
    started_at REAL,
    last_activity REAL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS session_messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT,
    role TEXT,
    content TEXT,
    timestamp REAL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    doc_id TEXT PRIMARY KEY,
    content TEXT,
    embedding BLOB,
    metadata TEXT,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS agent_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS task_history (
    task_id TEXT PRIMARY KEY,
    task_type TEXT,
    input_data TEXT,
    output_data TEXT,
    status TEXT,
    started_at REAL,
    completed_at REAL,
    error TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_index (
    keyword TEXT,
    doc_id TEXT,
    PRIMARY KEY (keyword, doc_id),
    FOREIGN KEY (doc_id) REFERENCES knowledge_documents(doc_id)
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON session_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON session_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON task_history(task_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_keyword ON knowledge_index(keyword);
"""


class AgentMemory:
    """SQLite-backed persistent memory for the agent runtime.

    Thread-safe: uses a connection per thread (via thread-local storage).
    Manages session history, message logs, knowledge documents,
    key-value state, and task execution history.
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.environ.get(
            "AGENT_MEMORY_DB",
            "/mnt/d/PartsFactory/CMPLX-PartsFactory/data/agent_memory.sqlite",
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._local = threading.local()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.executescript(SCHEMA_SQL)
            conn.commit()
            self._local.conn = conn
        return self._local.conn

    def connect(self) -> None:
        self._get_conn()
        logger.info("AgentMemory initialized at %s", self.db_path)

    # ── Sessions ──────────────────────────────────────────────

    def create_session(self, session_id: str | None = None,
                       agent_id: str = "default",
                       metadata: dict | None = None) -> str:
        conn = self._get_conn()
        sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
        now = time.time()
        conn.execute(
            "INSERT OR REPLACE INTO sessions (session_id, agent_id, started_at, last_activity, metadata) VALUES (?, ?, ?, ?, ?)",
            (sid, agent_id, now, now, json.dumps(metadata or {})),
        )
        conn.commit()
        return sid

    def get_session(self, session_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def list_sessions(self, agent_id: str | None = None,
                      limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        if agent_id:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE agent_id = ? ORDER BY last_activity DESC LIMIT ?",
                (agent_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY last_activity DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def touch_session(self, session_id: str) -> None:
        conn = self._get_conn()
        conn.execute(
            "UPDATE sessions SET last_activity = ? WHERE session_id = ?",
            (time.time(), session_id),
        )
        conn.commit()

    # ── Messages ──────────────────────────────────────────────

    def add_message(self, session_id: str, role: str, content: str,
                    metadata: dict | None = None) -> str:
        conn = self._get_conn()
        mid = f"msg_{uuid.uuid4().hex[:12]}"
        conn.execute(
            "INSERT INTO session_messages (message_id, session_id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (mid, session_id, role, content, time.time(), json.dumps(metadata or {})),
        )
        conn.commit()
        self.touch_session(session_id)
        return mid

    def get_messages(self, session_id: str,
                     limit: int = 100) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM session_messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Knowledge Documents ───────────────────────────────────

    def add_document(self, content: str,
                     metadata: dict | None = None) -> str:
        conn = self._get_conn()
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        embedding = self._generate_embedding(content)
        conn.execute(
            "INSERT INTO knowledge_documents (doc_id, content, embedding, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (doc_id, content, embedding.tobytes(), json.dumps(metadata or {}), time.time()),
        )
        keywords = set(content.lower().split())
        for kw in keywords:
            conn.execute(
                "INSERT OR IGNORE INTO knowledge_index (keyword, doc_id) VALUES (?, ?)",
                (kw, doc_id),
            )
        conn.commit()
        return doc_id

    def query_knowledge(self, query_text: str, top_k: int = 5) -> list[dict]:
        conn = self._get_conn()
        query_emb = self._generate_embedding(query_text)
        rows = conn.execute(
            "SELECT doc_id, content, embedding, metadata FROM knowledge_documents"
        ).fetchall()
        scored: list[tuple[float, dict]] = []
        for row in rows:
            doc = dict(row)
            stored_emb = np.frombuffer(doc["embedding"], dtype=np.float64)
            sim = float(np.dot(query_emb, stored_emb))
            scored.append((sim, {
                "doc_id": doc["doc_id"],
                "content": doc["content"],
                "metadata": json.loads(doc["metadata"]) if doc["metadata"] else {},
                "similarity": sim,
            }))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:top_k]]

    def remove_document(self, doc_id: str) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM knowledge_documents WHERE doc_id = ?", (doc_id,))
        conn.execute("DELETE FROM knowledge_index WHERE doc_id = ?", (doc_id,))
        conn.commit()

    def _generate_embedding(self, text: str) -> np.ndarray:
        words = text.lower().split()
        emb = np.zeros(100, dtype=np.float64)
        for i, word in enumerate(words[:100]):
            emb[i % 100] += hash(word) % 1000 / 1000.0
        norm = np.linalg.norm(emb)
        return emb / (norm + 1e-10)

    # ── Agent State ───────────────────────────────────────────

    def set_state(self, key: str, value: Any) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO agent_state (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), time.time()),
        )
        conn.commit()

    def get_state(self, key: str) -> Any | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT value FROM agent_state WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def get_all_state(self) -> dict:
        conn = self._get_conn()
        rows = conn.execute("SELECT key, value FROM agent_state").fetchall()
        return {r["key"]: json.loads(r["value"]) for r in rows}

    # ── Task History ──────────────────────────────────────────

    def store_task(self, task_type: str, input_data: Any,
                   output_data: Any = None, status: str = "pending",
                   error: str | None = None) -> str:
        conn = self._get_conn()
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        now = time.time()
        conn.execute(
            "INSERT INTO task_history (task_id, task_type, input_data, output_data, status, started_at, completed_at, error) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (task_id, task_type, json.dumps(input_data),
             json.dumps(output_data) if output_data is not None else None,
             status, now, now if status in ("done", "failed") else None, error),
        )
        conn.commit()
        return task_id

    def update_task(self, task_id: str, output_data: Any = None,
                    status: str = "done", error: str | None = None) -> None:
        conn = self._get_conn()
        conn.execute(
            "UPDATE task_history SET output_data=?, status=?, completed_at=?, error=? WHERE task_id=?",
            (json.dumps(output_data) if output_data is not None else None,
             status, time.time(), error, task_id),
        )
        conn.commit()

    def get_task(self, task_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM task_history WHERE task_id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        for json_field in ("input_data", "output_data"):
            if result.get(json_field) and isinstance(result[json_field], str):
                try:
                    result[json_field] = json.loads(result[json_field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return result

    def list_tasks(self, task_type: str | None = None,
                   status: str | None = None,
                   limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        clauses = []
        params: list[Any] = []
        if task_type:
            clauses.append("task_type = ?")
            params.append(task_type)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM task_history {where} ORDER BY started_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            for json_field in ("input_data", "output_data"):
                if d.get(json_field) and isinstance(d[json_field], str):
                    try:
                        d[json_field] = json.loads(d[json_field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            results.append(d)
        return results

    # ── Lifecycle ─────────────────────────────────────────────

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    def stats(self) -> dict:
        conn = self._get_conn()
        counts = {}
        for table in ("sessions", "session_messages", "knowledge_documents",
                      "agent_state", "task_history"):
            row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM {table}"
            ).fetchone()
            counts[table] = row["cnt"] if row else 0
        return {"db_path": self.db_path, **counts}
