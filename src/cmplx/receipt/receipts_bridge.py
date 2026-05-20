"""
Bridge GeoLight and TokLight JSONL ledgers into one sorted timeline.

Merged from escrow witness:
``CMPLX-history/staging/by-family/unclassified/geometry_lattice/receipts_bridge.py``
(canonical of 8 variants). Complements in-process ``ReceiptChain`` — this module
reads external JSONL audit files, not the Merkle store.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load JSONL records; skip blank or invalid lines."""
    p = Path(path)
    if not p.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def load_geolight(ledger_path: str | Path) -> list[dict[str, Any]]:
    """Normalize GeoLight ledger rows for timeline merge."""
    out: list[dict[str, Any]] = []
    for r in read_jsonl(ledger_path):
        out.append(
            {
                "ts": r.get("ts"),
                "scope": r.get("scope", "geom"),
                "channel": r.get("channel", 3),
                "cost": r.get("cost", 0.0),
                "input_hash": r.get("input_hash"),
                "result_hash": r.get("result_hash"),
                "receipt": r.get("entry"),
                "prev": r.get("prev"),
                "lane": "GeoLight",
            }
        )
    return out


def load_toklight(ledger_path: str | Path) -> list[dict[str, Any]]:
    """Normalize TokLight ledger rows for timeline merge."""
    out: list[dict[str, Any]] = []
    for r in read_jsonl(ledger_path):
        out.append(
            {
                "ts": r.get("ts"),
                "scope": r.get("scope", "tokenizer"),
                "op": r.get("op"),
                "cost": r.get("cost", 0.0),
                "input_hash": r.get("input_hash"),
                "result_hash": r.get("result_hash"),
                "receipt": r.get("entry"),
                "prev": r.get("prev"),
                "lane": "TokLight",
            }
        )
    return out


def merge_timelines(*timelines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Concatenate and sort timeline rows by timestamp then lane."""
    merged: list[dict[str, Any]] = []
    for tl in timelines:
        merged.extend(tl)
    merged.sort(key=lambda r: (r.get("ts", 0), r.get("lane", "")))
    return merged
