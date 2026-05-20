"""
morph_signatures table — persist morphism probes keyed by concat pair.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

MORPH_SIGNATURE_SCHEMA = """
CREATE TABLE IF NOT EXISTS morph_signatures (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    concat_base     TEXT NOT NULL,
    concat_variant  TEXT NOT NULL,
    generator       TEXT NOT NULL DEFAULT 'probe',
    delta_snap      INTEGER NOT NULL DEFAULT 0,
    delta_lane      INTEGER NOT NULL DEFAULT 0,
    delta_dr        INTEGER NOT NULL DEFAULT 0,
    verdict         TEXT NOT NULL DEFAULT '',
    payload_json    TEXT NOT NULL DEFAULT '{}',
    created_at      REAL NOT NULL,
    UNIQUE(concat_base, concat_variant, generator)
);
CREATE INDEX IF NOT EXISTS idx_morph_sig_base ON morph_signatures(concat_base);
"""

UPSERT_MORPH_SIG = """
INSERT INTO morph_signatures (
    concat_base, concat_variant, generator, delta_snap, delta_lane, delta_dr,
    verdict, payload_json, created_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(concat_base, concat_variant, generator) DO UPDATE SET
    delta_snap     = excluded.delta_snap,
    delta_lane     = excluded.delta_lane,
    delta_dr       = excluded.delta_dr,
    verdict        = excluded.verdict,
    payload_json   = excluded.payload_json,
    created_at     = excluded.created_at;
"""


@dataclass
class StoredMorphSignature:
    concat_base: str
    concat_variant: str
    generator: str
    delta_snap: int
    delta_lane: int
    delta_dr: int
    verdict: str
    payload: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "concat_base": self.concat_base,
            "concat_variant": self.concat_variant,
            "generator": self.generator,
            "delta_snap": self.delta_snap,
            "delta_lane": self.delta_lane,
            "delta_dr": self.delta_dr,
            "verdict": self.verdict,
            "payload": self.payload,
        }


class MorphSignatureStore:
    def __init__(self, db_path: str | Path, *, conn: sqlite3.Connection | None = None) -> None:
        self.db_path = str(db_path)
        self._owns = conn is None
        if conn is not None:
            self._conn = conn
        else:
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.executescript(MORPH_SIGNATURE_SCHEMA)
        self._conn.commit()

    @classmethod
    def from_connection(
        cls, conn: sqlite3.Connection, db_path: str = ":memory:"
    ) -> "MorphSignatureStore":
        return cls(db_path, conn=conn)

    def upsert(self, sig: StoredMorphSignature) -> None:
        self._conn.execute(
            UPSERT_MORPH_SIG,
            (
                sig.concat_base,
                sig.concat_variant,
                sig.generator,
                int(sig.delta_snap),
                int(sig.delta_lane),
                int(sig.delta_dr),
                sig.verdict,
                json.dumps(sig.payload, default=str),
                time.time(),
            ),
        )
        self._conn.commit()

    def export_jsonl(self, path: str | Path) -> int:
        """Append all rows to a JSONL file (for crystal bundle sidecars)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cur = self._conn.execute("SELECT * FROM morph_signatures ORDER BY id")
        cols = [c[0] for c in cur.description]
        count = 0
        with path.open("a", encoding="utf-8") as fh:
            for row in cur.fetchall():
                d = dict(zip(cols, row))
                if "payload_json" in d:
                    d["payload"] = json.loads(d.pop("payload_json") or "{}")
                fh.write(json.dumps(d, default=str) + "\n")
                count += 1
        return count

    def close(self) -> None:
        if self._owns:
            self._conn.close()


__all__ = [
    "MORPH_SIGNATURE_SCHEMA",
    "StoredMorphSignature",
    "MorphSignatureStore",
]
