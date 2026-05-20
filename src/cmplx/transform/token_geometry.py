"""
token_geometry table — optional E6/E8 coords keyed by concat + stream.
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

TOKEN_GEOMETRY_SCHEMA = """
CREATE TABLE IF NOT EXISTS token_geometry (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    concat          TEXT NOT NULL,
    stream          TEXT NOT NULL DEFAULT 'en',
    translation_key TEXT,
    snap_key        TEXT NOT NULL,
    e6_coords       TEXT NOT NULL,
    e8_coords       TEXT NOT NULL,
    created_at      REAL NOT NULL,
    UNIQUE(concat, stream)
);
CREATE INDEX IF NOT EXISTS idx_geom_snap ON token_geometry(snap_key);
CREATE INDEX IF NOT EXISTS idx_geom_translation ON token_geometry(translation_key);
"""

UPSERT_GEOMETRY = """
INSERT INTO token_geometry (
    concat, stream, translation_key, snap_key, e6_coords, e8_coords, created_at
)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(concat, stream) DO UPDATE SET
    translation_key = excluded.translation_key,
    snap_key        = excluded.snap_key,
    e6_coords       = excluded.e6_coords,
    e8_coords       = excluded.e8_coords,
    created_at      = excluded.created_at;
"""


@dataclass
class GeometryRow:
    concat: str
    stream: str
    snap_key: str
    e6_coords: tuple[float, ...]
    e8_coords: tuple[float, ...]
    translation_key: Optional[str] = None


class TokenGeometryStore:
    def __init__(self, db_path: str | Path, *, conn: sqlite3.Connection | None = None) -> None:
        self.db_path = str(db_path)
        self._owns = conn is None
        if conn is not None:
            self._conn = conn
        else:
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.executescript(TOKEN_GEOMETRY_SCHEMA)
        self._conn.commit()

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection, db_path: str = ":memory:") -> "TokenGeometryStore":
        return cls(db_path, conn=conn)

    def upsert(self, row: GeometryRow) -> None:
        import json

        self._conn.execute(
            UPSERT_GEOMETRY,
            (
                row.concat,
                row.stream,
                row.translation_key,
                row.snap_key,
                json.dumps(list(row.e6_coords)),
                json.dumps(list(row.e8_coords)),
                time.time(),
            ),
        )
        self._conn.commit()

    def by_concat(self, concat: str, stream: str = "en") -> Optional[GeometryRow]:
        import json

        cur = self._conn.execute(
            "SELECT * FROM token_geometry WHERE concat = ? AND stream = ?",
            (concat, stream),
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        d = dict(zip(cols, row))
        return GeometryRow(
            concat=str(d["concat"]),
            stream=str(d["stream"]),
            snap_key=str(d["snap_key"]),
            e6_coords=tuple(json.loads(d["e6_coords"])),
            e8_coords=tuple(json.loads(d["e8_coords"])),
            translation_key=d.get("translation_key"),
        )

    def close(self) -> None:
        if self._owns:
            self._conn.close()


__all__ = ["GeometryRow", "TokenGeometryStore", "TOKEN_GEOMETRY_SCHEMA"]
