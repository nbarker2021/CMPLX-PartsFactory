"""Read claims registry without promoting honesty labels."""
from __future__ import annotations

import json
from pathlib import Path

PROVEN_LABELS = frozenset({"PROVEN", "TRANSPORTED", "BOUNDED_EXEC", "EXPRESSIBLE"})


def default_registry_path() -> Path:
    import os

    root = Path(os.environ.get("PROOF_LAB_ROOT", Path.cwd()))
    return root / "packages" / "lattice-forge" / "claims" / "registry.jsonl"


def load_claims(path: Path | None = None) -> list[dict]:
    reg = path or default_registry_path()
    rows: list[dict] = []
    for line in reg.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def filter_nonproven(claims: list[dict]) -> list[dict]:
    return [c for c in claims if c.get("honesty_label") not in PROVEN_LABELS]
