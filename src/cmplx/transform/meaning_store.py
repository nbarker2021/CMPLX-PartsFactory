"""
AddressMeaningStore — snap_key → semantic label mapping (Table 2).

Lives in the same SQLite file as ``token_bonds`` (single-DB crystal bundle).
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


ADDRESS_MEANING_SCHEMA = """
CREATE TABLE IF NOT EXISTS address_meaning (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snap_key        TEXT NOT NULL,
    lane            TEXT NOT NULL,
    digital_root    INTEGER NOT NULL,
    label           TEXT NOT NULL,
    label_source    TEXT NOT NULL,
    source_doc      TEXT,
    source_span     TEXT,
    ennead_id       TEXT,
    receipt_hash    TEXT,
    created_at      REAL NOT NULL,
    UNIQUE(snap_key, lane, digital_root, label, source_doc)
);
CREATE INDEX IF NOT EXISTS idx_meaning_snap ON address_meaning(snap_key);
CREATE INDEX IF NOT EXISTS idx_meaning_label ON address_meaning(label);
CREATE INDEX IF NOT EXISTS idx_meaning_doc ON address_meaning(source_doc);
"""

UPSERT_MEANING = """
INSERT INTO address_meaning (
    snap_key, lane, digital_root, label, label_source,
    source_doc, source_span, ennead_id, receipt_hash, created_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(snap_key, lane, digital_root, label, source_doc) DO UPDATE SET
    label_source = excluded.label_source,
    source_span  = excluded.source_span,
    receipt_hash = excluded.receipt_hash,
    created_at   = excluded.created_at;
"""


@dataclass
class MeaningRow:
    snap_key: str
    lane: str
    digital_root: int
    label: str
    label_source: str
    source_doc: Optional[str] = None
    source_span: Optional[str] = None
    ennead_id: Optional[str] = None
    receipt_hash: Optional[str] = None
    created_at: float = 0.0
    id: Optional[int] = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "snap_key": self.snap_key,
            "lane": self.lane,
            "digital_root": self.digital_root,
            "label": self.label,
            "label_source": self.label_source,
            "source_doc": self.source_doc,
            "source_span": self.source_span,
            "ennead_id": self.ennead_id,
            "receipt_hash": self.receipt_hash,
            "created_at": self.created_at,
        }


class AddressMeaningStore:
    """CRUD + query for ``address_meaning`` rows."""

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
        self._conn.executescript(ADDRESS_MEANING_SCHEMA)
        self._conn.commit()

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection, db_path: str = ":memory:") -> "AddressMeaningStore":
        return cls(db_path, conn=conn)

    def upsert(
        self,
        *,
        snap_key: str,
        lane: str,
        digital_root: int,
        label: str,
        label_source: str,
        source_doc: Optional[str] = None,
        source_span: Optional[str] = None,
        ennead_id: Optional[str] = None,
        receipt_hash: Optional[str] = None,
    ) -> None:
        self._conn.execute(
            UPSERT_MEANING,
            (
                snap_key,
                lane,
                int(digital_root),
                label,
                label_source,
                source_doc,
                source_span,
                ennead_id,
                receipt_hash,
                time.time(),
            ),
        )
        self._conn.commit()

    def by_snap_key(self, snap_key: str, limit: int = 100) -> list[MeaningRow]:
        cur = self._conn.execute(
            "SELECT * FROM address_meaning WHERE snap_key = ? LIMIT ?",
            (snap_key, int(limit)),
        )
        return self._rows(cur)

    def by_label(self, label: str, limit: int = 100) -> list[MeaningRow]:
        cur = self._conn.execute(
            "SELECT * FROM address_meaning WHERE label LIKE ? LIMIT ?",
            (f"%{label}%", int(limit)),
        )
        return self._rows(cur)

    def by_doc(self, source_doc: str, limit: int = 500) -> list[MeaningRow]:
        cur = self._conn.execute(
            "SELECT * FROM address_meaning WHERE source_doc = ? LIMIT ?",
            (source_doc, int(limit)),
        )
        return self._rows(cur)

    def all_rows(self, limit: int = 10000) -> list[MeaningRow]:
        cur = self._conn.execute(
            "SELECT * FROM address_meaning LIMIT ?",
            (int(limit),),
        )
        return self._rows(cur)

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM address_meaning")
        return int(cur.fetchone()[0])

    def stats(self) -> dict[str, Any]:
        cur = self._conn.execute(
            "SELECT label_source, COUNT(*) FROM address_meaning GROUP BY label_source"
        )
        by_source = {str(r[0]): int(r[1]) for r in cur.fetchall()}
        return {"total_rows": self.count(), "by_label_source": by_source}

    @staticmethod
    def _rows(cursor: sqlite3.Cursor) -> list[MeaningRow]:
        columns = [c[0] for c in cursor.description]
        out: list[MeaningRow] = []
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            out.append(
                MeaningRow(
                    id=d.get("id"),
                    snap_key=str(d["snap_key"]),
                    lane=str(d["lane"]),
                    digital_root=int(d["digital_root"]),
                    label=str(d["label"]),
                    label_source=str(d["label_source"]),
                    source_doc=d.get("source_doc"),
                    source_span=d.get("source_span"),
                    ennead_id=d.get("ennead_id"),
                    receipt_hash=d.get("receipt_hash"),
                    created_at=float(d.get("created_at") or 0),
                )
            )
        return out

    def close(self) -> None:
        if self._owns_conn:
            self._conn.close()

    def __enter__(self) -> "AddressMeaningStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


__all__ = ["ADDRESS_MEANING_SCHEMA", "MeaningRow", "AddressMeaningStore"]
