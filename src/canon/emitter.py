"""CanonicalEmitter — write the single file and record lineage."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .database import LineageDB


class CanonicalEmitter:
    """Emits one canonical file per tool and records the decision."""

    def __init__(self, db: LineageDB, output_root: str = "src/canon/tools"):
        self.db = db
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)

    def emit(self, tool_name: str, cluster_id: str, content: str, derived_from: list[str]) -> str:
        """Write canonical file, record in DB, return relative path."""
        safe_name = tool_name.replace(" ", "_").replace("-", "_").lower()
        if safe_name.endswith(".py"):
            safe_name = safe_name[:-3]
        rel_path = f"src/canon/tools/{safe_name}.py"
        out_path = self.output_root / f"{safe_name}.py"
        out_path.write_text(content, encoding="utf-8")

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        lines = content.count("\n") + 1

        self.db.record_canonical(tool_name, cluster_id, rel_path, content_hash, lines, derived_from)
        self.db.commit()
        return rel_path
