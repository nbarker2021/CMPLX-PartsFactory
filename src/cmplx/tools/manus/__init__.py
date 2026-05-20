"""Manus dev/review toolkit — 30 scientific instruments + rail adapters."""
from __future__ import annotations

import json
from pathlib import Path

from .registry import CMPLXToolRegistry

_MANIFEST = Path(__file__).with_name("manifest_v3.json")


def load_manifest_v3() -> dict:
    if _MANIFEST.is_file():
        return json.loads(_MANIFEST.read_text(encoding="utf-8"))
    return {}


__all__ = ["CMPLXToolRegistry", "load_manifest_v3"]
