"""
SurfaceMode — notation and math surface morphisms.

Unicode equivalence and operator normalization for sidecar streams
(math, notation). YAML-driven via ``data/rule_libs/notation/``.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


class SurfaceMode(str, Enum):
    UNICODE_EQUIV = "unicode_equiv"
    OPERATOR = "operator"
    LATEX_COMMAND = "latex_command"
    PLAIN = "plain"


_DEFAULT_NOTATION_ROOT = Path(__file__).resolve().parents[4] / "data" / "rule_libs" / "notation"


def load_notation_lib(path: str | Path | None = None) -> dict[str, Any]:
    """Load merged notation YAML (starter + user extensions)."""
    root = Path(path) if path else _DEFAULT_NOTATION_ROOT
    merged: dict[str, Any] = {
        "version": "1",
        "unicode_equiv": {},
        "operators": {},
        "latex_commands": {},
    }
    if not root.is_dir():
        return merged
    for yaml_file in sorted(root.rglob("*.yaml")):
        if yaml is None:
            break
        with yaml_file.open(encoding="utf-8") as fh:
            doc = yaml.safe_load(fh) or {}
        for key in ("unicode_equiv", "operators", "latex_commands"):
            section = doc.get(key) or {}
            if isinstance(section, dict):
                merged[key].update(section)
    return merged


def _build_reverse_equiv(unicode_equiv: dict[str, Any]) -> dict[str, str]:
    """Map every alias character to its canonical key."""
    rev: dict[str, str] = {}
    for canonical, aliases in unicode_equiv.items():
        rev[canonical] = canonical
        if isinstance(aliases, str):
            rev[aliases] = canonical
        elif isinstance(aliases, Iterable):
            for alias in aliases:
                rev[str(alias)] = canonical
    return rev


def normalize_surface(
    text: str,
    *,
    mode: SurfaceMode = SurfaceMode.UNICODE_EQUIV,
    lib: Optional[dict[str, Any]] = None,
) -> str:
    """Apply surface normalization for notation/math streams."""
    if mode is SurfaceMode.PLAIN:
        return text
    lib = lib or load_notation_lib()
    if mode is SurfaceMode.UNICODE_EQUIV:
        rev = _build_reverse_equiv(lib.get("unicode_equiv") or {})
        return "".join(rev.get(ch, ch) for ch in text)
    if mode is SurfaceMode.OPERATOR:
        ops = lib.get("operators") or {}
        out = text
        for src, dst in sorted(ops.items(), key=lambda kv: -len(kv[0])):
            out = out.replace(src, dst)
        return out
    if mode is SurfaceMode.LATEX_COMMAND:
        cmds = lib.get("latex_commands") or {}
        out = text
        for src, dst in sorted(cmds.items(), key=lambda kv: -len(kv[0])):
            out = out.replace(src, dst)
        return out
    raise ValueError(f"unknown SurfaceMode: {mode!r}")


def surfaces_equivalent(
    a: str,
    b: str,
    *,
    mode: SurfaceMode = SurfaceMode.UNICODE_EQUIV,
    lib: Optional[dict[str, Any]] = None,
) -> bool:
    return normalize_surface(a, mode=mode, lib=lib) == normalize_surface(b, mode=mode, lib=lib)


__all__ = [
    "SurfaceMode",
    "load_notation_lib",
    "normalize_surface",
    "surfaces_equivalent",
]
