"""
MMDB — Morphon Memory Database.

SQLite-backed persistence for Morphon. See INTERFACE.md and BRIDGE.md
for the contract. The implementation is intentionally minimal — the
schema captures what the bridge needs; richer query surfaces (by
geometry coordinate, by receipt operation, by time range) come in
later iterations.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Optional, Union

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


_SCHEMA = """
CREATE TABLE IF NOT EXISTS morphons (
    id              TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    state           TEXT NOT NULL,
    dr_channel      INTEGER,
    parent          TEXT,
    payload_json    TEXT NOT NULL,
    serialized_json TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_morphons_channel ON morphons(dr_channel);
CREATE INDEX IF NOT EXISTS idx_morphons_parent  ON morphons(parent);
"""


class MMDB:
    """SQLite-backed Morphon Memory Database.

    Single-connection, thread-safe via a lock. For in-memory use, pass
    `":memory:"` as the path. For file-backed, pass any filesystem path.

    Use as a context manager to ensure clean shutdown:

    >>> with MMDB(":memory:") as db:
    ...     db.store(morphon)
    """

    def __init__(self, path: Union[str, Path]) -> None:
        self._path = str(path)
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        self._open()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _open(self) -> None:
        if self._conn is not None:
            return
        self._conn = sqlite3.connect(
            self._path,
            check_same_thread=False,
            isolation_level=None,  # autocommit
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def __enter__(self) -> "MMDB":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # MemoryProvider protocol
    # ------------------------------------------------------------------

    def store(self, morphon: "Morphon") -> None:
        """Persist a morphon. Idempotent on id — re-storing overwrites
        the row with current state, payload, and serialization. Updates
        `updated_at` timestamp.
        """
        if self._conn is None:
            raise RuntimeError("MMDB connection is closed")
        now = datetime.now(timezone.utc).isoformat()
        data = morphon.serialize()
        payload_json = json.dumps(data["payload"], sort_keys=True, default=str)
        serialized_json = json.dumps(data, ensure_ascii=False, default=str)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO morphons
                    (id, created_at, state, dr_channel, parent,
                     payload_json, serialized_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    state=excluded.state,
                    dr_channel=excluded.dr_channel,
                    parent=excluded.parent,
                    payload_json=excluded.payload_json,
                    serialized_json=excluded.serialized_json,
                    updated_at=excluded.updated_at
                """,
                (
                    data["id"],
                    data["created_at"],
                    data["state"],
                    data.get("dr_channel"),
                    data.get("parent"),
                    payload_json,
                    serialized_json,
                    now,
                ),
            )

    def fetch(self, morphon_id: str) -> Optional["Morphon"]:
        """Return the Morphon with `morphon_id`, or None if not stored."""
        if self._conn is None:
            raise RuntimeError("MMDB connection is closed")
        with self._lock:
            row = self._conn.execute(
                "SELECT serialized_json FROM morphons WHERE id = ?",
                (morphon_id,),
            ).fetchone()
        if row is None:
            return None
        # Lazy import to avoid an import cycle if cmplx.morphon imports
        # MMDB at top level (which it doesn't currently, but defensive).
        from cmplx.morphon import Morphon
        return Morphon.deserialize(json.loads(row[0]))

    # ------------------------------------------------------------------
    # Extended surface
    # ------------------------------------------------------------------

    def delete(self, morphon_id: str) -> bool:
        """Remove the morphon. Return True if a row was deleted."""
        if self._conn is None:
            raise RuntimeError("MMDB connection is closed")
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM morphons WHERE id = ?", (morphon_id,)
            )
            return cur.rowcount > 0

    def count(self) -> int:
        if self._conn is None:
            raise RuntimeError("MMDB connection is closed")
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM morphons").fetchone()[0]

    def find_by_channel(self, channel: int) -> Iterator["Morphon"]:
        """Iterate all morphons whose DR channel matches `channel`."""
        if self._conn is None:
            raise RuntimeError("MMDB connection is closed")
        from cmplx.morphon import Morphon
        with self._lock:
            cur = self._conn.execute(
                "SELECT serialized_json FROM morphons WHERE dr_channel = ? "
                "ORDER BY created_at",
                (channel,),
            )
            for (serialized,) in cur:
                yield Morphon.deserialize(json.loads(serialized))

    def find_by_parent(self, parent_id: str) -> Iterator["Morphon"]:
        """Iterate all morphons whose parent is `parent_id`."""
        if self._conn is None:
            raise RuntimeError("MMDB connection is closed")
        from cmplx.morphon import Morphon
        with self._lock:
            cur = self._conn.execute(
                "SELECT serialized_json FROM morphons WHERE parent = ? "
                "ORDER BY created_at",
                (parent_id,),
            )
            for (serialized,) in cur:
                yield Morphon.deserialize(json.loads(serialized))

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def path(self) -> str:
        return self._path

    def __repr__(self) -> str:
        n = self.count() if self._conn is not None else "closed"
        return f"MMDB(path={self._path!r}, morphons={n})"
