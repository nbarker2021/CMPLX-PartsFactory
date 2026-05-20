#!/usr/bin/env python
"""Build TAG_INDEX.json from rag_manifest.jsonl."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_PKG = REPO / "export" / "morphonic-rebuild-handoff-2026-05-19"


def build_tag_index(pkg: Path) -> dict[str, list[str]]:
    manifest = pkg / "08_RAG_AND_GRAPH" / "rag_manifest.jsonl"
    if not manifest.is_file():
        return {}
    by_tag: dict[str, list[str]] = defaultdict(list)
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cid = row.get("chunk_id", "")
        for tag in row.get("tags", []):
            if cid and cid not in by_tag[tag]:
                by_tag[tag].append(cid)
    out = pkg / "08_RAG_AND_GRAPH" / "TAG_INDEX.json"
    out.write_text(json.dumps(dict(sorted(by_tag.items())), indent=2), encoding="utf-8")
    return dict(by_tag)


def main() -> int:
    pkg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PKG
    tags = build_tag_index(pkg)
    print(json.dumps({"tags": len(tags), "total_refs": sum(len(v) for v in tags.values())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
