"""LineageDB — SQLite store for artifact provenance and canonical decisions."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .scanner import ArtifactRecord


SCHEMA = """
CREATE TABLE IF NOT EXISTS artifact (
    artifact_id   TEXT PRIMARY KEY,
    rel_path      TEXT NOT NULL,
    abs_path      TEXT NOT NULL,
    basename      TEXT NOT NULL,
    size_bytes    INTEGER,
    lines         INTEGER,
    content_hash  TEXT NOT NULL,
    ast_hash      TEXT NOT NULL,
    top_level     TEXT,
    repo_tag      TEXT,
    scan_batch    TEXT
);

CREATE TABLE IF NOT EXISTS cluster (
    cluster_id    TEXT PRIMARY KEY,
    tool_name     TEXT UNIQUE NOT NULL,   -- human-readable canonical name
    ast_hash      TEXT NOT NULL,           -- what ties the cluster together
    status        TEXT DEFAULT 'open',     -- open | reviewing | canonical | rejected
    notes         TEXT,
    created_at    TEXT
);

CREATE TABLE IF NOT EXISTS cluster_member (
    cluster_id    TEXT REFERENCES cluster(cluster_id),
    artifact_id   TEXT REFERENCES artifact(artifact_id),
    rank          INTEGER,                 -- user-assigned preference (1 = best)
    reason        TEXT,                    -- why kept or rejected
    PRIMARY KEY (cluster_id, artifact_id)
);

CREATE TABLE IF NOT EXISTS canonical_file (
    tool_name     TEXT PRIMARY KEY,
    cluster_id    TEXT REFERENCES cluster(cluster_id),
    rel_path      TEXT NOT NULL,           -- where the single file lives
    content_hash  TEXT NOT NULL,
    lines         INTEGER,
    created_at    TEXT,
    derived_from  TEXT                     -- JSON list of artifact_ids
);

CREATE INDEX IF NOT EXISTS idx_artifact_ast ON artifact(ast_hash);
CREATE INDEX IF NOT EXISTS idx_artifact_repo ON artifact(repo_tag);
CREATE INDEX IF NOT EXISTS idx_artifact_basename ON artifact(basename);
"""


class LineageDB:
    def __init__(self, db_path: str = "data/canonicalization.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def insert_artifact(self, rec: ArtifactRecord) -> None:
        d = asdict(rec)
        cols = ", ".join(d.keys())
        placeholders = ", ".join(["?"] * len(d))
        self.conn.execute(
            f"INSERT OR REPLACE INTO artifact ({cols}) VALUES ({placeholders})",
            tuple(d.values()),
        )

    def commit(self) -> None:
        self.conn.commit()

    def get_clusters_by_basename(self, basename: str) -> list[dict[str, Any]]:
        """Return groups of artifacts sharing the same basename, keyed by ast_hash."""
        cur = self.conn.execute(
            "SELECT * FROM artifact WHERE basename = ? ORDER BY ast_hash, repo_tag",
            (basename,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        clusters: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            clusters.setdefault(r["ast_hash"], []).append(r)
        return [
            {"ast_hash": h, "artifacts": arts, "count": len(arts)}
            for h, arts in clusters.items()
        ]

    def create_cluster(self, cluster_id: str, tool_name: str, ast_hash: str, notes: str = "") -> None:
        import datetime as dt
        self.conn.execute(
            "INSERT OR REPLACE INTO cluster (cluster_id, tool_name, ast_hash, status, notes, created_at) VALUES (?, ?, ?, 'open', ?, ?)",
            (cluster_id, tool_name, ast_hash, notes, dt.datetime.utcnow().isoformat()),
        )

    def add_cluster_member(self, cluster_id: str, artifact_id: str, rank: int | None = None, reason: str = "") -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO cluster_member (cluster_id, artifact_id, rank, reason) VALUES (?, ?, ?, ?)",
            (cluster_id, artifact_id, rank, reason),
        )

    def record_canonical(self, tool_name: str, cluster_id: str, rel_path: str, content_hash: str, lines: int, derived_from: list[str]) -> None:
        import datetime as dt
        self.conn.execute(
            "INSERT OR REPLACE INTO canonical_file (tool_name, cluster_id, rel_path, content_hash, lines, created_at, derived_from) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tool_name, cluster_id, rel_path, content_hash, lines, dt.datetime.utcnow().isoformat(), json.dumps(derived_from)),
        )
        self.conn.execute(
            "UPDATE cluster SET status = 'canonical' WHERE cluster_id = ?",
            (cluster_id,),
        )

    def get_canonical(self, tool_name: str) -> dict[str, Any] | None:
        cur = self.conn.execute(
            "SELECT * FROM canonical_file WHERE tool_name = ?", (tool_name,)
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def cluster_report(self, tool_name: str) -> dict[str, Any]:
        """Full report for a tool: all variants, canonical decision, lineage."""
        cur = self.conn.execute(
            "SELECT * FROM cluster WHERE tool_name = ?", (tool_name,)
        )
        cluster = dict(cur.fetchone()) if cur else None
        if not cluster:
            return {"error": "no cluster found"}

        cur = self.conn.execute(
            "SELECT a.*, cm.rank, cm.reason FROM artifact a JOIN cluster_member cm ON a.artifact_id = cm.artifact_id WHERE cm.cluster_id = ? ORDER BY cm.rank, a.lines DESC",
            (cluster["cluster_id"],)
        )
        members = [dict(r) for r in cur.fetchall()]

        canonical = self.get_canonical(tool_name)

        return {
            "tool_name": tool_name,
            "cluster": cluster,
            "variants": members,
            "canonical": canonical,
            "total_variants": len(members),
            "total_lines_if_kept_all": sum(m["lines"] for m in members),
        }

    def close(self) -> None:
        self.conn.close()
