#!/usr/bin/env python
"""Chunk curated morphonic docs into RAG-ready markdown with manifest."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "export" / "morphonic-rebuild-handoff-2026-05-19"

# ~500–1500 token target: split on ## headers, merge small sections
MAX_CHARS = 4500
MIN_CHARS = 250

CURATED_SOURCES: list[tuple[str, list[str], str]] = [
    (
        "doctrine",
        [
            "docs/MORPHONIC_UNIFIED_DOCTRINE.md",
            "docs/MORPHONIC_SUBSTRATE_CRYSTAL_PLAN.md",
            "docs/MORPHONIC_OPERATIONAL_V1_CHECKPOINT.md",
            "docs/MORPHONIC_PRODUCTION_RUNBOOK.md",
            "docs/MORPHONIC_TEST_REVIEW_2026-05-19.md",
            "docs/HP_NHYPER_TOWER_INTEGRATION.md",
            "docs/NHYPER_TOWER_ESCROW.md",
        ],
        "done",
    ),
    (
        "transform_api",
        [
            "src/cmplx/transform/BRIDGE.md",
            "src/cmplx/transform/INTERFACE.md",
        ],
        "done",
    ),
    (
        "checkpoints",
        [
            "../identity_review/checkpoints/2026-05-19-001-morphonic-mvp.md",
            "../identity_review/checkpoints/2026-05-19-002-morphonic-unified-e2e.md",
            "../identity_review/checkpoints/2026-05-19-006-morphonic-production-hardening.md",
            "../identity_review/checkpoints/2026-05-19-008-morphonic-operational-v1.md",
        ],
        "done",
    ),
]


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:80] or "chunk"


def _split_sections(text: str) -> list[tuple[str, str]]:
    parts = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    sections: list[tuple[str, str]] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        title = lines[0].lstrip("#").strip() if lines else "section"
        sections.append((title, part))
    if not sections:
        return [("body", text)]
    return sections


def _merge_sections(sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
    merged: list[tuple[str, str]] = []
    buf_title = ""
    buf_body = ""
    for title, body in sections:
        if len(buf_body) + len(body) < MIN_CHARS:
            buf_title = buf_title or title
            buf_body = (buf_body + "\n\n" + body).strip()
            continue
        if buf_body:
            merged.append((buf_title or title, buf_body))
            buf_body = ""
            buf_title = ""
        if len(body) <= MAX_CHARS:
            merged.append((title, body))
        else:
            # hard split long sections
            for i in range(0, len(body), MAX_CHARS):
                merged.append((f"{title} ({i // MAX_CHARS + 1})", body[i : i + MAX_CHARS]))
    if buf_body:
        merged.append((buf_title or "section", buf_body))
    return merged


def _chunk_id(source: str, title: str, idx: int) -> str:
    raw = f"{source}:{title}:{idx}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def export_chunks(out_root: Path) -> dict[str, int]:
    rag_dir = out_root / "08_RAG_AND_GRAPH" / "rag_chunks"
    rag_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_root / "08_RAG_AND_GRAPH" / "rag_manifest.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict] = []
    chunk_idx = 0

    with manifest_path.open("w", encoding="utf-8") as mf:
        for tag_group, paths, default_status in CURATED_SOURCES:
            for rel in paths:
                src = (REPO / rel).resolve()
                if not src.is_file():
                    alt = (REPO.parent / "identity_review" / Path(rel).name)
                    if "checkpoints" in rel and alt.is_file():
                        src = alt
                    else:
                        continue
                text = src.read_text(encoding="utf-8", errors="replace")
                rel_posix = src.relative_to(REPO.parent).as_posix() if REPO.parent in src.parents else rel
                for sec_i, (title, body) in enumerate(_merge_sections(_split_sections(text))):
                    cid = _chunk_id(rel_posix, title, sec_i)
                    fname = f"{chunk_idx:04d}_{_slug(title)}_{cid}.md"
                    chunk_path = rag_dir / fname
                    status = default_status
                    if "todo" in body.lower() or "pending" in body.lower() or "blocked" in body.lower():
                        status = "partial"
                    front = (
                        f"---\n"
                        f"id: {cid}\n"
                        f"title: {title}\n"
                        f"tags: [{tag_group}, morphonic]\n"
                        f"source: {rel_posix}\n"
                        f"phase: operational_v1\n"
                        f"status: {status}\n"
                        f"---\n\n"
                    )
                    chunk_path.write_text(front + body + "\n", encoding="utf-8")
                    row = {
                        "chunk_id": cid,
                        "file": f"rag_chunks/{fname}",
                        "title": title,
                        "tags": [tag_group, "morphonic"],
                        "source_path": rel_posix,
                        "status": status,
                    }
                    mf.write(json.dumps(row) + "\n")
                    manifest_rows.append(row)
                    chunk_idx += 1

    def _emit_handoff_md(extra: Path, tag_group: str) -> None:
        nonlocal chunk_idx
        if "rag_chunks" in extra.parts or extra.name in (
            "README_START_HERE.md",
            "HANDOFF_COVER.md",
        ):
            return
        rel = extra.relative_to(out_root).as_posix()
        text = extra.read_text(encoding="utf-8", errors="replace")
        if len(text) < 80:
            return
        for sec_i, (title, body) in enumerate(_merge_sections(_split_sections(text))):
            if len(body) < 80:
                continue
            cid = _chunk_id(rel, title, sec_i)
            fname = f"{chunk_idx:04d}_{_slug(title)}_{cid}.md"
            tags = [tag_group, "morphonic", "handoff"]
            if "13_MODULE_DEEP_DIVES" in rel:
                tags.append("module-dive")
            if "11_SOURCE_CORPUS" in rel:
                tags.append("source-corpus")
            if "12_TEST_SPEC" in rel:
                tags.append("test-spec")
            front = (
                f"---\n"
                f"id: {cid}\n"
                f"title: {title}\n"
                f"tags: [{', '.join(tags)}]\n"
                f"source: {rel}\n"
                f"phase: handoff\n"
                f"status: done\n"
                f"---\n\n"
            )
            (rag_dir / fname).write_text(front + body + "\n", encoding="utf-8")
            row = {
                "chunk_id": cid,
                "file": f"rag_chunks/{fname}",
                "title": title,
                "tags": tags,
                "source_path": rel,
                "status": "done",
            }
            with manifest_path.open("a", encoding="utf-8") as mf:
                mf.write(json.dumps(row) + "\n")
            manifest_rows.append(row)
            chunk_idx += 1

    seen_sources: set[str] = {r["source_path"] for r in manifest_rows}
    priority_roots = [
        (out_root / "11_SOURCE_CORPUS", "source-corpus"),
        (out_root / "13_MODULE_DEEP_DIVES", "module-dive"),
        (out_root / "02_ARCHITECTURE", "architecture"),
        (out_root / "12_TEST_SPEC", "test-spec"),
        (out_root / "00_REBUILD_PLAYBOOK", "playbook"),
    ]
    for root, tag_group in priority_roots:
        if not root.is_dir():
            continue
        for extra in sorted(root.glob("**/*.md")):
            rel = extra.relative_to(out_root).as_posix()
            if rel in seen_sources:
                continue
            _emit_handoff_md(extra, tag_group)
            seen_sources.add(rel)

    for extra in sorted(out_root.glob("**/*.md")):
        rel = extra.relative_to(out_root).as_posix()
        if rel in seen_sources or "rag_chunks" in extra.parts:
            continue
        _emit_handoff_md(extra, "handoff")
        seen_sources.add(rel)

    code_root = out_root / "11_SOURCE_CORPUS" / "code"
    if code_root.is_dir():
        for py in sorted(code_root.rglob("*.py")):
            rel = py.relative_to(out_root).as_posix()
            text = py.read_text(encoding="utf-8", errors="replace")
            head = "\n".join(text.splitlines()[:120])
            if len(head) < 100:
                continue
            for i in range(0, len(head), MAX_CHARS):
                part = head[i : i + MAX_CHARS]
                title = f"{py.stem} (source excerpt {i // MAX_CHARS + 1})"
                cid = _chunk_id(rel, title, i)
                fname = f"{chunk_idx:04d}_{_slug(title)}_{cid}.md"
                tags = ["source-corpus", "morphonic", "code"]
                front = (
                    f"---\n"
                    f"id: {cid}\n"
                    f"title: {title}\n"
                    f"tags: [{', '.join(tags)}]\n"
                    f"source: {rel}\n"
                    f"phase: handoff\n"
                    f"status: done\n"
                    f"---\n\n"
                )
                (rag_dir / fname).write_text(front + "```python\n" + part + "\n```\n", encoding="utf-8")
                row = {
                    "chunk_id": cid,
                    "file": f"rag_chunks/{fname}",
                    "title": title,
                    "tags": tags,
                    "source_path": rel,
                    "status": "done",
                }
                with manifest_path.open("a", encoding="utf-8") as mf:
                    mf.write(json.dumps(row) + "\n")
                manifest_rows.append(row)
                chunk_idx += 1

    return {"chunks": chunk_idx, "manifest_rows": len(manifest_rows)}


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    stats = export_chunks(out)
    print(json.dumps({"out": str(out), **stats}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
