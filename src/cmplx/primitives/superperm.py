"""
Combinatorial superpermutation primitives (n=4..8 schedule spine).

Superpermutation strings are **supervisor cursors** — never ribbon content.
Shipped records live under ``data/superpermutations/n{4..8}.json``.
"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from itertools import permutations
from pathlib import Path
from typing import Any, Iterable

SUPERPERM_N4 = "123412314231243121342132413214321"
N4_LENGTH = len(SUPERPERM_N4)
N4_PERM_COUNT = 24
N4_SYMBOLS = ("1", "2", "3", "4")

_SUPPORTED_N = frozenset({4, 5, 6, 7, 8})
SUPPORTED_N = _SUPPORTED_N
_SUPERPERM_DIR = Path(__file__).resolve().parents[3] / "data" / "superpermutations"


def _load_record(n: int) -> dict[str, Any]:
    if n not in _SUPPORTED_N:
        raise ValueError(f"unsupported superpermutation n={n} (supported: {sorted(_SUPPORTED_N)})")
    path = _SUPERPERM_DIR / f"n{n}.json"
    if not path.is_file():
        if n == 4:
            return {
                "n": 4,
                "status": "validated",
                "superpermutation": SUPERPERM_N4,
                "length": len(SUPERPERM_N4),
            }
        return {"n": n, "status": "missing", "superpermutation": None}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=8)
def load_superperm_record(n: int) -> dict[str, Any]:
    return dict(_load_record(n))


def superperm_n(n: int) -> str:
    """Return validated superpermutation string for n in 4..8."""
    rec = load_superperm_record(n)
    status = str(rec.get("status", "missing")).lower()
    sp = rec.get("superpermutation") or rec.get("superperm")
    if status in ("pending", "missing", "escrow") or not sp:
        raise ValueError(f"superpermutation n={n} not validated (status={status!r})")
    text = str(sp)
    if not coverage_check(text, n=n):
        raise ValueError(f"superpermutation n={n} fails coverage_check")
    return text


def superperm_length(n: int) -> int:
    return len(superperm_n(n))


def phase_at(index: int, *, n: int = 4) -> int:
    """Digit at supervisor cursor position (symbol in 1..n)."""
    s = superperm_n(n)
    ch = s[index % len(s)]
    return int(ch)


def coverage_check(s: str | None = None, *, n: int = 4) -> bool:
    """True when every permutation of 1..n appears as a length-n substring."""
    text = s if s is not None else superperm_n(n)
    if len(text) < n:
        return False
    symbols = [str(i) for i in range(1, n + 1)]
    needed = {"".join(p) for p in permutations(symbols)}
    found = {text[i : i + n] for i in range(len(text) - n + 1)}
    return needed <= found


def coverage_checksum(s: str | None = None, *, n: int = 4) -> str:
    """Stable short checksum of coverage set (for manifest verification)."""
    text = s if s is not None else superperm_n(n)
    symbols = [str(i) for i in range(1, n + 1)]
    perms = sorted("".join(p) for p in permutations(symbols))
    covered = sorted({text[i : i + n] for i in range(len(text) - n + 1)})
    payload = json.dumps({"perms": perms, "covered": covered}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def provenance_class(n: int) -> str:
    rec = load_superperm_record(n)
    return str(rec.get("provenance_class", "unknown"))


def status_for_n(n: int) -> str:
    return str(load_superperm_record(n).get("status", "missing"))


def load_n4_metadata() -> dict:
    return load_superperm_record(4)


def load_n5_metadata() -> dict:
    return load_superperm_record(5)


def n5_status() -> str:
    return status_for_n(5)


def n6_status() -> str:
    return status_for_n(6)


def n7_status() -> str:
    return status_for_n(7)


def n8_status() -> str:
    return status_for_n(8)


def n5_superpermutation_or_none() -> str | None:
    if status_for_n(5) != "validated":
        return None
    try:
        return superperm_n(5)
    except ValueError:
        return None


def n5_alternates() -> list[str]:
    """All eight validated minimals (palindrome + seven trees)."""
    rec = load_superperm_record(5)
    if status_for_n(5) != "validated":
        return []
    alts = rec.get("alternates")
    if alts:
        return [str(s) for s in alts]
    sp = rec.get("superpermutation")
    return [str(sp)] if sp else []


def n5_tree_alternates() -> list[str]:
    """Seven non-palindrome minimals only."""
    return [
        str(e.get("superpermutation"))
        for e in _n5_labeled_entries()
        if not e.get("is_palindrome")
    ]


def n5_palindrome_or_none() -> str | None:
    rec = load_superperm_record(5)
    if status_for_n(5) != "validated":
        return None
    pal = rec.get("palindrome") or rec.get("superpermutation")
    return str(pal) if pal else None


def _n5_labeled_entries() -> list[dict[str, Any]]:
    rec = load_superperm_record(5)
    labeled = rec.get("labeled_alternates")
    if labeled:
        return list(labeled)
    alts = n5_alternates()
    return [
        {
            "alternate_index": i,
            "superpermutation": s,
            "is_palindrome": s == s[::-1],
            "label": f"johnston:minimal:{i + 1}",
        }
        for i, s in enumerate(alts)
    ]


def n5_octad_layout() -> str:
    rec = load_superperm_record(5)
    return str(rec.get("octad_layout") or "1_palindrome_7_trees")


def octad_version() -> str:
    path = _SUPERPERM_DIR / "octad_n4.json"
    if path.is_file():
        rec = json.loads(path.read_text(encoding="utf-8"))
        return str(rec.get("octad_layout") or rec.get("octad_version") or "1_palindrome_7_trees")
    return "1_palindrome_7_trees"


def n4_permutation_set() -> set[str]:
    return {"".join(p) for p in permutations(N4_SYMBOLS)}


def digit_at(index: int, *, n: int = 4) -> int:
    return phase_at(index, n=n)


def iter_digits(length: int | None = None, *, n: int = 4) -> Iterable[int]:
    return walk_phases(length, n=n)


def is_palindrome_phase(index: int, *, n: int = 4) -> bool:
    s = superperm_n(n)
    prefix = s[: index + 1]
    return len(prefix) >= 2 and prefix == prefix[::-1]


def walk_phases(length: int | None = None, *, n: int = 4) -> Iterable[int]:
    s = superperm_n(n)
    limit = len(s) if length is None else int(length)
    for i in range(limit):
        yield int(s[i % len(s)])


def all_statuses() -> dict[str, str]:
    return {f"n{k}": status_for_n(k) for k in sorted(_SUPPORTED_N)}


__all__ = [
    "N4_LENGTH",
    "N4_PERM_COUNT",
    "N4_SYMBOLS",
    "SUPERPERM_N4",
    "SUPPORTED_N",
    "superperm_n",
    "superperm_length",
    "load_superperm_record",
    "phase_at",
    "digit_at",
    "coverage_check",
    "coverage_checksum",
    "provenance_class",
    "status_for_n",
    "walk_phases",
    "iter_digits",
    "is_palindrome_phase",
    "load_n4_metadata",
    "load_n5_metadata",
    "n5_status",
    "n6_status",
    "n7_status",
    "n8_status",
    "n5_superpermutation_or_none",
    "n5_alternates",
    "n5_tree_alternates",
    "n5_palindrome_or_none",
    "n5_octad_layout",
    "octad_version",
    "n4_permutation_set",
    "all_statuses",
]
