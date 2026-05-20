"""ClusterEngine — group artifact variants and prepare them for review."""

from __future__ import annotations

import hashlib
from typing import Any

from .database import LineageDB


class ClusterEngine:
    """Manages the lifecycle of a canonicalization cluster."""

    def __init__(self, db: LineageDB):
        self.db = db

    def auto_cluster_basename(self, basename: str) -> list[dict[str, Any]]:
        """Group all artifacts with this basename by AST hash. Returns cluster summaries."""
        return self.db.get_clusters_by_basename(basename)

    def register_cluster(self, tool_name: str, ast_hash: str, artifact_ids: list[str], notes: str = "") -> str:
        """Create a cluster and link all variant artifacts."""
        cluster_id = hashlib.sha256((tool_name + ast_hash).encode()).hexdigest()[:16]
        self.db.create_cluster(cluster_id, tool_name, ast_hash, notes)
        for aid in artifact_ids:
            self.db.add_cluster_member(cluster_id, aid)
        self.db.commit()
        return cluster_id

    def rank_variants(self, cluster_id: str, ranked_ids: list[tuple[str, int, str]]) -> None:
        """Assign user preference ranks to variants."""
        for artifact_id, rank, reason in ranked_ids:
            self.db.add_cluster_member(cluster_id, artifact_id, rank, reason)
        self.db.commit()
