"""
Persistent SQLite store for the token index.

Schema is small but indexed across every column a future inference
lookup might query. Writes are idempotent — re-running the builder
inserts or replaces but does not duplicate rows.

The store also handles the cross-port writes to the `memory` and
`receipt` providers when they are registered. SpeedLight writes go
through `warmstart.publish_entry` so the same entry advertises itself
under every key future lookups might use.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Optional

from ..bridge import (
    get_cache_provider,
    get_memory_provider,
    get_receipt_provider,
    has_provider,
)
from .substrate_epoch import _epoch_from_conn, notify_substrate_mutation
from .warmstart import IndexEntryPayload, publish_entry

logger = logging.getLogger(__name__)

DEFAULT_STREAM = "en"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS token_bonds (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    concat        TEXT    NOT NULL,
    quad_left     TEXT    NOT NULL,
    quad_right    TEXT    NOT NULL,
    bond_level    INTEGER NOT NULL,
    case_mode     TEXT    NOT NULL,
    language      TEXT    NOT NULL,
    stream        TEXT    NOT NULL DEFAULT 'en',
    morphon_id    TEXT    NOT NULL,
    parent_morphon_id TEXT,
    snap_key      TEXT    NOT NULL,
    digital_root  INTEGER NOT NULL,
    lane          TEXT    NOT NULL,
    e8_signature  TEXT    NOT NULL,
    cache_key     TEXT    NOT NULL,
    warmstart     TEXT    NOT NULL,
    created_at    REAL    NOT NULL,
    UNIQUE(concat, case_mode, language, stream)
);

CREATE INDEX IF NOT EXISTS idx_token_bonds_concat ON token_bonds(concat);
CREATE INDEX IF NOT EXISTS idx_token_bonds_left   ON token_bonds(quad_left);
CREATE INDEX IF NOT EXISTS idx_token_bonds_right  ON token_bonds(quad_right);
CREATE INDEX IF NOT EXISTS idx_token_bonds_snap   ON token_bonds(snap_key);
CREATE INDEX IF NOT EXISTS idx_token_bonds_dr     ON token_bonds(digital_root);
CREATE INDEX IF NOT EXISTS idx_token_bonds_lane   ON token_bonds(lane);
CREATE INDEX IF NOT EXISTS idx_token_bonds_level  ON token_bonds(bond_level);
CREATE INDEX IF NOT EXISTS idx_token_bonds_lang   ON token_bonds(language);
CREATE INDEX IF NOT EXISTS idx_token_bonds_case   ON token_bonds(case_mode);
CREATE INDEX IF NOT EXISTS idx_token_bonds_stream ON token_bonds(stream);

CREATE TABLE IF NOT EXISTS build_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at   REAL    NOT NULL,
    finished_at  REAL,
    levels       TEXT    NOT NULL,
    alphabet     TEXT    NOT NULL,
    languages    TEXT    NOT NULL,
    case_modes   TEXT    NOT NULL,
    total_seen   INTEGER NOT NULL DEFAULT 0,
    total_stored INTEGER NOT NULL DEFAULT 0,
    stats_json   TEXT
);
"""

UPSERT_SQL = """
INSERT INTO token_bonds (
    concat, quad_left, quad_right, bond_level, case_mode, language, stream,
    morphon_id, parent_morphon_id, snap_key, digital_root, lane,
    e8_signature, cache_key, warmstart, created_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(concat, case_mode, language, stream) DO UPDATE SET
    morphon_id        = excluded.morphon_id,
    parent_morphon_id = excluded.parent_morphon_id,
    snap_key          = excluded.snap_key,
    digital_root      = excluded.digital_root,
    lane              = excluded.lane,
    e8_signature      = excluded.e8_signature,
    cache_key         = excluded.cache_key,
    warmstart         = excluded.warmstart,
    created_at        = excluded.created_at;
"""

_MIGRATE_STREAM_SQL = """
CREATE TABLE IF NOT EXISTS token_bonds_v2 (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    concat        TEXT    NOT NULL,
    quad_left     TEXT    NOT NULL,
    quad_right    TEXT    NOT NULL,
    bond_level    INTEGER NOT NULL,
    case_mode     TEXT    NOT NULL,
    language      TEXT    NOT NULL,
    stream        TEXT    NOT NULL DEFAULT 'en',
    morphon_id    TEXT    NOT NULL,
    parent_morphon_id TEXT,
    snap_key      TEXT    NOT NULL,
    digital_root  INTEGER NOT NULL,
    lane          TEXT    NOT NULL,
    e8_signature  TEXT    NOT NULL,
    cache_key     TEXT    NOT NULL,
    warmstart     TEXT    NOT NULL,
    created_at    REAL    NOT NULL,
    UNIQUE(concat, case_mode, language, stream)
);
INSERT INTO token_bonds_v2 (
    id, concat, quad_left, quad_right, bond_level, case_mode, language, stream,
    morphon_id, parent_morphon_id, snap_key, digital_root, lane,
    e8_signature, cache_key, warmstart, created_at
)
SELECT
    id, concat, quad_left, quad_right, bond_level, case_mode, language, 'en',
    morphon_id, parent_morphon_id, snap_key, digital_root, lane,
    e8_signature, cache_key, warmstart, created_at
FROM token_bonds;
DROP TABLE token_bonds;
ALTER TABLE token_bonds_v2 RENAME TO token_bonds;
CREATE INDEX IF NOT EXISTS idx_token_bonds_concat ON token_bonds(concat);
CREATE INDEX IF NOT EXISTS idx_token_bonds_left   ON token_bonds(quad_left);
CREATE INDEX IF NOT EXISTS idx_token_bonds_right  ON token_bonds(quad_right);
CREATE INDEX IF NOT EXISTS idx_token_bonds_snap   ON token_bonds(snap_key);
CREATE INDEX IF NOT EXISTS idx_token_bonds_dr     ON token_bonds(digital_root);
CREATE INDEX IF NOT EXISTS idx_token_bonds_lane   ON token_bonds(lane);
CREATE INDEX IF NOT EXISTS idx_token_bonds_level  ON token_bonds(bond_level);
CREATE INDEX IF NOT EXISTS idx_token_bonds_lang   ON token_bonds(language);
CREATE INDEX IF NOT EXISTS idx_token_bonds_case   ON token_bonds(case_mode);
CREATE INDEX IF NOT EXISTS idx_token_bonds_stream ON token_bonds(stream);
"""


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {str(row[1]) for row in cur.fetchall()}


def _migrate_token_bonds_stream(conn: sqlite3.Connection) -> None:
    """Add ``stream`` column and widen UNIQUE constraint for legacy DBs."""
    try:
        columns = _table_columns(conn, "token_bonds")
    except sqlite3.OperationalError:
        return
    if not columns:
        return
    if "stream" in columns:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_token_bonds_stream ON token_bonds(stream)"
        )
        return
    conn.executescript(_MIGRATE_STREAM_SQL)


def _e8_signature(coords: tuple[float, ...] | list[float]) -> str:
    """Stable hash of E8 coordinates rounded to 6 decimal places."""
    rounded = tuple(round(float(c), 6) for c in coords)
    return hashlib.sha256(
        json.dumps(rounded, default=str).encode("utf-8")
    ).hexdigest()[:16]


# ────────────────────────────────────────────────────────────────────────────
# Store
# ────────────────────────────────────────────────────────────────────────────

class TokenIndexStore:
    """SQLite-backed token index with parallel writes to morphon ports."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        _migrate_token_bonds_stream(self._conn)
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()
        self._run_id: Optional[int] = None

    # ── Build run lifecycle ────────────────────────────────────────────

    def start_run(
        self,
        *,
        levels: Iterable[int],
        alphabet: Iterable[str],
        languages: Iterable[str],
        case_modes: Iterable[str],
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO build_runs (started_at, levels, alphabet, languages, case_modes) VALUES (?, ?, ?, ?, ?)",
            (
                time.time(),
                json.dumps(list(levels)),
                json.dumps(list(alphabet)),
                json.dumps(list(languages)),
                json.dumps(list(case_modes)),
            ),
        )
        self._conn.commit()
        self._run_id = cur.lastrowid
        return int(self._run_id)

    def finish_run(self, *, total_seen: int, total_stored: int, stats: dict) -> None:
        if self._run_id is None:
            return
        self._conn.execute(
            """
            UPDATE build_runs
            SET finished_at = ?, total_seen = ?, total_stored = ?, stats_json = ?
            WHERE id = ?
            """,
            (
                time.time(),
                int(total_seen),
                int(total_stored),
                json.dumps(stats, default=str),
                int(self._run_id),
            ),
        )
        self._conn.commit()

    # ── Entry writes ────────────────────────────────────────────────────

    def upsert(
        self,
        payload: IndexEntryPayload,
        *,
        bond_level: int,
        case_mode: str,
        language: str,
        stream: str = DEFAULT_STREAM,
    ) -> None:
        self._conn.execute(
            UPSERT_SQL,
            (
                payload.concat,
                payload.concat[:4],
                payload.concat[4:],
                int(bond_level),
                case_mode,
                language,
                stream,
                payload.morphon_id,
                payload.parent_morphon_id,
                payload.snap_key,
                int(payload.digital_root),
                payload.lane,
                _e8_signature(payload.e8_coords),
                payload.cache_key,
                payload.warmstart_outcome,
                time.time(),
            ),
        )
        # Commit per-row so a crash mid-build still leaves a usable
        # index. The cost is small at ~100k rows and is dominated by
        # the forge work anyway.
        self._conn.commit()
        notify_substrate_mutation(self._conn)

    def substrate_epoch(self) -> str:
        """Cache-bust generation for whole-forward SpeedLight keys."""
        return _epoch_from_conn(self._conn)

    # ── Multi-port writes ───────────────────────────────────────────────

    def publish(
        self,
        payload: IndexEntryPayload,
        case_mode_value: str,
        morphon: Any,
    ) -> None:
        """Mirror the entry into every registered morphonic memory layer."""
        # 1. SpeedLight cache (already used for warm-start probing).
        try:
            cache = get_cache_provider() if has_provider("cache") else None
        except Exception:
            cache = None
        if cache is not None:
            from .case import CaseMode

            try:
                cm = CaseMode(case_mode_value)
            except ValueError:
                cm = CaseMode.LOWER
            publish_entry(cache, payload, cm)

        # 2. MMDB memory.
        if has_provider("memory"):
            try:
                get_memory_provider().store(morphon)
            except Exception as exc:
                logger.debug("memory.store failed for %s: %s", payload.concat, exc)

    def mint_summary_receipt(
        self,
        *,
        total_stored: int,
        levels: Iterable[int],
        languages: Iterable[str],
        stats: dict,
    ) -> Optional[Any]:
        """Mint a single PROCESS receipt summarizing the whole build."""
        if not has_provider("receipt"):
            return None
        try:
            return get_receipt_provider().mint(
                receipt_type="PROCESS",
                atom_id="token_index",
                operation="token_index.build",
                payload={
                    "total_stored": int(total_stored),
                    "levels": list(levels),
                    "languages": list(languages),
                    "warmstart_stats": stats,
                },
            )
        except Exception as exc:
            logger.debug("receipt mint failed: %s", exc)
            return None

    # ── Queries (helpers for downstream inference) ──────────────────────

    def by_concat(
        self,
        concat: str,
        language: str | None = None,
        stream: str | None = None,
    ) -> list[dict]:
        clauses = ["concat = ?"]
        params: list[Any] = [concat]
        if language is not None:
            clauses.append("language = ?")
            params.append(language)
        if stream is not None:
            clauses.append("stream = ?")
            params.append(stream)
        sql = f"SELECT * FROM token_bonds WHERE {' AND '.join(clauses)}"
        cur = self._conn.execute(sql, params)
        return [dict(r) for r in self._rows(cur)]

    def by_left(self, quad_left: str, limit: int = 50) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM token_bonds WHERE quad_left = ? LIMIT ?",
            (quad_left, int(limit)),
        )
        return [dict(r) for r in self._rows(cur)]

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM token_bonds")
        return int(cur.fetchone()[0])

    def stats(self) -> dict:
        out: dict[str, Any] = {"total_rows": self.count()}
        cur = self._conn.execute(
            "SELECT bond_level, COUNT(*) FROM token_bonds GROUP BY bond_level"
        )
        out["by_level"] = {int(r[0]): int(r[1]) for r in cur.fetchall()}
        cur = self._conn.execute(
            "SELECT language, COUNT(*) FROM token_bonds GROUP BY language"
        )
        out["by_language"] = {str(r[0]): int(r[1]) for r in cur.fetchall()}
        cur = self._conn.execute(
            "SELECT case_mode, COUNT(*) FROM token_bonds GROUP BY case_mode"
        )
        out["by_case"] = {str(r[0]): int(r[1]) for r in cur.fetchall()}
        cur = self._conn.execute(
            "SELECT warmstart, COUNT(*) FROM token_bonds GROUP BY warmstart"
        )
        out["by_warmstart"] = {str(r[0]): int(r[1]) for r in cur.fetchall()}
        cur = self._conn.execute(
            "SELECT stream, COUNT(*) FROM token_bonds GROUP BY stream"
        )
        out["by_stream"] = {str(r[0]): int(r[1]) for r in cur.fetchall()}
        return out

    # ── Plumbing ────────────────────────────────────────────────────────

    @staticmethod
    def _rows(cursor: sqlite3.Cursor):
        columns = [c[0] for c in cursor.description]
        for row in cursor.fetchall():
            yield dict(zip(columns, row))

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "TokenIndexStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


__all__ = ["DEFAULT_STREAM", "TokenIndexStore", "SCHEMA_SQL"]
