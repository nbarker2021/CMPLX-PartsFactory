#!/usr/bin/env python3
"""
CMPLX-PartsFactory — Personal Node

A lightweight companion node that tracks operator preferences, session history,
and E8 coordinate state. Serves as the local brain for the PartsFactory agent.
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


def _runtime_path(*parts: str) -> str:
    root = os.environ.get("CMPLX_RUNTIME_DIR")
    if root:
        return str(Path(root).joinpath(*parts))
    if os.name == "nt":
        return str(Path("D:/PartsFactory/runtime/CMPLX-PartsFactory").joinpath(*parts))
    return str(
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
        .joinpath("cmplx-partsfactory", *parts)
    )


DEFAULT_NODE_PATH = _runtime_path("personal_node", "node_state.sqlite")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS preferences (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    channel_id TEXT,
    started_at TEXT,
    last_activity TEXT,
    context_summary TEXT,
    e8_coords TEXT
);

CREATE TABLE IF NOT EXISTS work_windows (
    window_id TEXT PRIMARY KEY,
    started_at TEXT,
    completed_at TEXT,
    checkpoint_count INTEGER,
    artifacts_created TEXT,
    notes TEXT
);
"""


class PersonalNode:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_NODE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = None

    def connect(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def set_preference(self, key: str, value: Any):
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO preferences (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, json.dumps(value), datetime.now().isoformat()))
        self._conn.commit()

    def get_preference(self, key: str) -> Optional[Any]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def start_session(self, session_id: str, channel_id: str = None, e8_coords: List[float] = None):
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (session_id, channel_id, started_at, last_activity, e8_coords)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            channel_id,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            json.dumps(e8_coords) if e8_coords else None,
        ))
        self._conn.commit()

    def touch_session(self, session_id: str, context_summary: str = None):
        cursor = self._conn.cursor()
        cursor.execute("""
            UPDATE sessions SET last_activity = ? WHERE session_id = ?
        """, (datetime.now().isoformat(), session_id))
        if context_summary:
            cursor.execute("""
                UPDATE sessions SET context_summary = ? WHERE session_id = ?
            """, (context_summary, session_id))
        self._conn.commit()

    def start_work_window(self, window_id: str) -> str:
        cursor = self._conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO work_windows (window_id, started_at, checkpoint_count, artifacts_created)
            VALUES (?, ?, 0, ?)
        """, (window_id, now, json.dumps([])))
        self._conn.commit()
        return window_id

    def checkpoint(self, window_id: str, artifact: str = None):
        cursor = self._conn.cursor()
        cursor.execute("""
            UPDATE work_windows SET checkpoint_count = checkpoint_count + 1 WHERE window_id = ?
        """, (window_id,))
        if artifact:
            cursor.execute("SELECT artifacts_created FROM work_windows WHERE window_id = ?", (window_id,))
            row = cursor.fetchone()
            artifacts = json.loads(row[0]) if row and row[0] else []
            artifacts.append(artifact)
            cursor.execute("""
                UPDATE work_windows SET artifacts_created = ? WHERE window_id = ?
            """, (json.dumps(artifacts), window_id))
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


if __name__ == "__main__":
    node = PersonalNode()
    node.connect()
    print(f"Personal node initialized at {node.db_path}")
    node.set_preference("default_model", "kimi-k2.6")
    print(f"Preference: default_model = {node.get_preference('default_model')}")
    node.close()
