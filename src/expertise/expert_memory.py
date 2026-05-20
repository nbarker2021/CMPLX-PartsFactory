"""ExpertMemory — SQLite-backed persistent memory per expert.

Each expert gets its own memory store for history, decisions, and learned patterns.
Builds on the patterns from PersonalNode.
"""

from __future__ import annotations
import os
import json
import sqlite3
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger("expertise.memory")

DEFAULT_MEMORY_DIR = "/mnt/d/PartsFactory/CMPLX-PartsFactory/data/expert_memories"

MEMORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_entries (
    entry_id TEXT PRIMARY KEY,
    expert_id TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    content TEXT,
    embedding BLOB,
    relevance_score REAL DEFAULT 0.0,
    created_at REAL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS experience_log (
    log_id TEXT PRIMARY KEY,
    expert_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    input_summary TEXT,
    output_summary TEXT,
    success INTEGER,
    performance_ms REAL,
    created_at REAL,
    context TEXT
);

CREATE TABLE IF NOT EXISTS learned_patterns (
    pattern_id TEXT PRIMARY KEY,
    expert_id TEXT NOT NULL,
    pattern_type TEXT,
    pattern_data TEXT,
    confidence REAL DEFAULT 0.0,
    hit_count INTEGER DEFAULT 0,
    last_used REAL,
    created_at REAL
);

CREATE INDEX IF NOT EXISTS idx_memory_expert ON memory_entries(expert_id);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(entry_type);
CREATE INDEX IF NOT EXISTS idx_experience_expert ON experience_log(expert_id);
CREATE INDEX IF NOT EXISTS idx_patterns_expert ON learned_patterns(expert_id);
"""


class ExpertMemory:
    """SQLite-backed persistent memory for a single expert."""

    def __init__(self, expert_id: str, memory_dir: str = None):
        self.expert_id = expert_id
        self.memory_dir = memory_dir or DEFAULT_MEMORY_DIR
        os.makedirs(self.memory_dir, exist_ok=True)
        self.db_path = os.path.join(self.memory_dir, f"{expert_id}.sqlite")
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(MEMORY_SCHEMA)
        self._conn.commit()

    def store_entry(self, entry_type: str, content: Any,
                    relevance_score: float = 0.0,
                    metadata: Dict[str, Any] = None) -> str:
        import uuid
        entry_id = f"mem_{uuid.uuid4().hex[:12]}"
        content_json = json.dumps(content) if not isinstance(content, str) else content
        embedding = self._compute_embedding(str(content))
        meta_json = json.dumps(metadata or {})
        self._conn.execute("""
            INSERT INTO memory_entries (entry_id, expert_id, entry_type, content,
                                         embedding, relevance_score, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, self.expert_id, entry_type, content_json,
              embedding.tobytes() if embedding is not None else None,
              relevance_score, time.time(), meta_json))
        self._conn.commit()
        return entry_id

    def recall(self, query: str, entry_type: str = None,
               top_k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self._compute_embedding(query)
        cursor = self._conn.execute(
            "SELECT * FROM memory_entries WHERE expert_id = ?",
            (self.expert_id,)
        )
        scored = []
        for row in cursor.fetchall():
            if entry_type and row["entry_type"] != entry_type:
                continue
            stored_blob = row["embedding"]
            if stored_blob:
                stored = np.frombuffer(stored_blob, dtype=np.float64)
                sim = float(np.dot(query_embedding, stored) /
                            (np.linalg.norm(query_embedding) * np.linalg.norm(stored) + 1e-10))
                scored.append((sim, dict(row)))
        scored.sort(key=lambda x: x[0], reverse=True)
        result = []
        for sim, row in scored[:top_k]:
            row["similarity"] = sim
            if row["metadata"]:
                row["metadata"] = json.loads(row["metadata"])
            result.append(row)
        return result

    def log_experience(self, operation: str, input_summary: str,
                       output_summary: str, success: bool,
                       performance_ms: float = 0.0,
                       context: Dict[str, Any] = None) -> str:
        import uuid
        log_id = f"exp_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO experience_log (log_id, expert_id, operation, input_summary,
                                         output_summary, success, performance_ms,
                                         created_at, context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_id, self.expert_id, operation, input_summary,
              output_summary, int(success), performance_ms,
              time.time(), json.dumps(context or {})))
        self._conn.commit()
        return log_id

    def learn_pattern(self, pattern_type: str, pattern_data: Any,
                      confidence: float = 0.1) -> str:
        import uuid
        pattern_id = f"pat_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO learned_patterns (pattern_id, expert_id, pattern_type,
                                           pattern_data, confidence, hit_count,
                                           last_used, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
        """, (pattern_id, self.expert_id, pattern_type,
              json.dumps(pattern_data), confidence,
              time.time(), time.time()))
        self._conn.commit()
        return pattern_id

    def retrieve_similar_contexts(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return self.recall(query, entry_type="context", top_k=top_k)

    def get_performance_stats(self) -> Dict[str, Any]:
        cursor = self._conn.execute(
            "SELECT COUNT(*) as total, SUM(success) as successes, "
            "AVG(performance_ms) as avg_ms FROM experience_log WHERE expert_id = ?",
            (self.expert_id,)
        )
        row = cursor.fetchone()
        total = row["total"] or 0
        successes = row["successes"] or 0
        return {
            "total_operations": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": successes / total if total > 0 else 0.0,
            "avg_latency_ms": row["avg_ms"] or 0.0,
            "memory_entries": self._conn.execute(
                "SELECT COUNT(*) FROM memory_entries WHERE expert_id = ?",
                (self.expert_id,)
            ).fetchone()[0],
            "learned_patterns": self._conn.execute(
                "SELECT COUNT(*) FROM learned_patterns WHERE expert_id = ?",
                (self.expert_id,)
            ).fetchone()[0],
        }

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _compute_embedding(self, text: str) -> np.ndarray:
        words = text.lower().split()
        embedding = np.zeros(64, dtype=np.float64)
        for i, word in enumerate(words[:64]):
            embedding[i % 64] += hash(word) % 10000 / 10000.0
        norm = np.linalg.norm(embedding)
        return embedding / (norm + 1e-10)
