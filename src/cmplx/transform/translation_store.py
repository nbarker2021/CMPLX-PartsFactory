"""
TranslationLinkStore — cross-stream translation links for multistream lib.

Lives in the same SQLite file as ``token_bonds`` (single-DB crystal bundle).
Rows tie a ``translation_key`` (document/chunk identity) to per-stream token
rows via ``concat`` and ``snap_key``.
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

DEFAULT_STREAM = "en"
VALID_STREAMS = frozenset({"en", "native", "math", "notation"})

TRANSLATION_LINKS_SCHEMA = """
CREATE TABLE IF NOT EXISTS translation_links (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    translation_key TEXT NOT NULL,
    stream          TEXT NOT NULL DEFAULT 'en',
    concat          TEXT NOT NULL,
    snap_key        TEXT NOT NULL,
    lane            TEXT,
    digital_root    INTEGER,
    source_doc      TEXT,
    source_span     TEXT,
    created_at      REAL NOT NULL,
    UNIQUE(translation_key, stream, concat)
);
CREATE INDEX IF NOT EXISTS idx_translation_key ON translation_links(translation_key);
CREATE INDEX IF NOT EXISTS idx_translation_stream ON translation_links(stream);
CREATE INDEX IF NOT EXISTS idx_translation_snap ON translation_links(snap_key);
CREATE INDEX IF NOT EXISTS idx_translation_concat ON translation_links(concat);
"""

UPSERT_TRANSLATION_LINK = """
INSERT INTO translation_links (
    translation_key, stream, concat, snap_key, lane, digital_root,
    source_doc, source_span, created_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(translation_key, stream, concat) DO UPDATE SET
    snap_key     = excluded.snap_key,
    lane         = excluded.lane,
    digital_root = excluded.digital_root,
    source_doc   = excluded.source_doc,
    source_span  = excluded.source_span,
    created_at   = excluded.created_at;
"""


@dataclass
class TranslationLinkRow:
    translation_key: str
    stream: str
    concat: str
    snap_key: str
    lane: Optional[str] = None
    digital_root: Optional[int] = None
    source_doc: Optional[str] = None
    source_span: Optional[str] = None
    created_at: float = 0.0
    id: Optional[int] = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "translation_key": self.translation_key,
            "stream": self.stream,
            "concat": self.concat,
            "snap_key": self.snap_key,
            "lane": self.lane,
            "digital_root": self.digital_root,
            "source_doc": self.source_doc,
            "source_span": self.source_span,
            "created_at": self.created_at,
        }


class TranslationLinkStore:
    """CRUD + query for ``translation_links`` rows."""

    def __init__(self, db_path: str | Path, *, conn: sqlite3.Connection | None = None) -> None:
        self.db_path = str(db_path)
        self._owns_conn = conn is None
        if conn is not None:
            self._conn = conn
        else:
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=60.0)
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(TRANSLATION_LINKS_SCHEMA)
        self._conn.commit()

    @classmethod
    def from_connection(
        cls, conn: sqlite3.Connection, db_path: str = ":memory:"
    ) -> "TranslationLinkStore":
        return cls(db_path, conn=conn)

    def upsert(
        self,
        *,
        translation_key: str,
        stream: str = DEFAULT_STREAM,
        concat: str,
        snap_key: str,
        lane: Optional[str] = None,
        digital_root: Optional[int] = None,
        source_doc: Optional[str] = None,
        source_span: Optional[str] = None,
    ) -> None:
        self._conn.execute(
            UPSERT_TRANSLATION_LINK,
            (
                translation_key,
                stream,
                concat,
                snap_key,
                lane,
                int(digital_root) if digital_root is not None else None,
                source_doc,
                source_span,
                time.time(),
            ),
        )
        self._conn.commit()

    def by_translation_key(
        self, translation_key: str, *, stream: Optional[str] = None, limit: int = 500
    ) -> list[TranslationLinkRow]:
        if stream is None:
            cur = self._conn.execute(
                "SELECT * FROM translation_links WHERE translation_key = ? LIMIT ?",
                (translation_key, int(limit)),
            )
        else:
            cur = self._conn.execute(
                "SELECT * FROM translation_links WHERE translation_key = ? AND stream = ? LIMIT ?",
                (translation_key, stream, int(limit)),
            )
        return self._rows(cur)

    def by_stream(self, stream: str, limit: int = 10000) -> list[TranslationLinkRow]:
        cur = self._conn.execute(
            "SELECT * FROM translation_links WHERE stream = ? LIMIT ?",
            (stream, int(limit)),
        )
        return self._rows(cur)

    def by_snap_key(self, snap_key: str, limit: int = 100) -> list[TranslationLinkRow]:
        cur = self._conn.execute(
            "SELECT * FROM translation_links WHERE snap_key = ? LIMIT ?",
            (snap_key, int(limit)),
        )
        return self._rows(cur)

    def all_rows(self, limit: int = 10000) -> list[TranslationLinkRow]:
        cur = self._conn.execute(
            "SELECT * FROM translation_links LIMIT ?",
            (int(limit),),
        )
        return self._rows(cur)

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM translation_links")
        return int(cur.fetchone()[0])

    def stats(self) -> dict[str, Any]:
        cur = self._conn.execute(
            "SELECT stream, COUNT(*) FROM translation_links GROUP BY stream"
        )
        by_stream = {str(r[0]): int(r[1]) for r in cur.fetchall()}
        return {"total_rows": self.count(), "by_stream": by_stream}

    def distinct_translation_keys(self, limit: int = 10000) -> list[str]:
        cur = self._conn.execute(
            "SELECT DISTINCT translation_key FROM translation_links ORDER BY translation_key LIMIT ?",
            (int(limit),),
        )
        return [str(row[0]) for row in cur.fetchall()]

    @staticmethod
    def _rows(cursor: sqlite3.Cursor) -> list[TranslationLinkRow]:
        columns = [c[0] for c in cursor.description]
        out: list[TranslationLinkRow] = []
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            dr = d.get("digital_root")
            out.append(
                TranslationLinkRow(
                    id=d.get("id"),
                    translation_key=str(d["translation_key"]),
                    stream=str(d["stream"]),
                    concat=str(d["concat"]),
                    snap_key=str(d["snap_key"]),
                    lane=d.get("lane"),
                    digital_root=int(dr) if dr is not None else None,
                    source_doc=d.get("source_doc"),
                    source_span=d.get("source_span"),
                    created_at=float(d.get("created_at") or 0),
                )
            )
        return out

    def close(self) -> None:
        if self._owns_conn:
            self._conn.close()

    def __enter__(self) -> "TranslationLinkStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


__all__ = [
    "DEFAULT_STREAM",
    "VALID_STREAMS",
    "TRANSLATION_LINKS_SCHEMA",
    "TranslationLinkRow",
    "TranslationLinkStore",
]
