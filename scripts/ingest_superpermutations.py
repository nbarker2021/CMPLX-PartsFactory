#!/usr/bin/env python3
"""Fetch and validate published superpermutations n=4..8 into data/superpermutations/."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "data" / "superpermutations"
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

SOURCES = {
    5: {
        "url": "http://www.njohnston.ca/superperm5.txt",
        "provenance_class": "minimal",
        "multi_line": True,
    },
    6: {
        "url": "http://www.njohnston.ca/superperm6_1wasted.txt",
        "provenance_class": "record",
        "multi_line": False,
    },
    7: {
        "url": "https://gregegan.net/SCIENCE/Superpermutations/7_5908.txt",
        "provenance_class": "record",
        "multi_line": False,
    },
    8: {
        "url": "https://gregegan.net/SCIENCE/Superpermutations/8_46205.txt",
        "provenance_class": "record",
        "multi_line": False,
    },
}


def _extract_superperm_string(raw: str, n: int) -> str:
    """Pull the longest digit-only line (or joined digits) from source text."""
    candidates: list[str] = []
    allowed = set("0123456789")
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("http") or line.startswith("See "):
            continue
        digits = "".join(ch for ch in line if ch in allowed)
        if len(digits) >= __import__("math").factorial(n):
            candidates.append(digits)
    if candidates:
        return max(candidates, key=len)
    joined = "".join(ch for ch in raw if ch in allowed)
    if joined:
        return joined
    raise ValueError(f"n={n}: no digit string found in source")


def _fetch_text(url: str, timeout: float = 120.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "CMPLX-PartsFactory/ingest"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _parse_n5_minimals(raw: str) -> tuple[list[str], dict[str, str]]:
    """Extract eight length-153 digit lines + journal lines from Johnston file."""
    journal: dict[str, str] = {}
    strings: list[str] = []
    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith("#"):
            if "minimal" in text.lower():
                journal["heading"] = text.lstrip("# ").strip()
            elif "found by" in text.lower():
                journal["discoverer_note"] = text.lstrip("# ").strip()
            continue
        if not text.isdigit():
            continue
        if len(text) != 153:
            continue
        strings.append(text)
    if len(strings) != 8:
        raise ValueError(f"n=5: expected 8 minimal strings of length 153, got {len(strings)}")
    return strings, journal


def _parse_lines(raw: str, *, multi_line: bool, n: int) -> list[str]:
    if n == 5 and multi_line:
        strings, _journal = _parse_n5_minimals(raw)
        return strings
    if not multi_line:
        return [_extract_superperm_string(raw, n)]
    lines: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("http") or line.startswith("See "):
            continue
        lines.append(line)
    return lines


def _validate_alphabet(text: str, n: int) -> None:
    allowed = set(str(i) for i in range(1, n + 1))
    bad = set(text) - allowed
    if bad:
        raise ValueError(f"n={n}: invalid characters {sorted(bad)}")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ingest_n(
    n: int,
    *,
    from_file: Path | None = None,
    dry_run: bool = False,
) -> dict:
    from cmplx.primitives.superperm import coverage_check, coverage_checksum

    meta = SOURCES[n]
    raw = from_file.read_text(encoding="utf-8") if from_file else _fetch_text(meta["url"])
    if n == 5:
        lines, journal = _parse_n5_minimals(raw)
        return _ingest_n5_octad(
            lines, journal=journal, source_url=meta["url"], dry_run=dry_run
        )

    lines = _parse_lines(raw, multi_line=bool(meta.get("multi_line")), n=n)
    if not lines:
        raise ValueError(f"n={n}: no string extracted")

    canonical = lines[0]
    _validate_alphabet(canonical, n)
    if not coverage_check(canonical, n=n):
        raise ValueError(f"n={n}: coverage_check failed for canonical string")

    record: dict = {
        "n": n,
        "status": "validated",
        "superpermutation": canonical,
        "length": len(canonical),
        "permutation_count": __import__("math").factorial(n),
        "provenance_class": meta["provenance_class"],
        "source_url": meta["url"],
        "sha256": _sha256(canonical),
        "coverage_checksum": coverage_checksum(canonical, n=n),
    }

    if not dry_run:
        path = OUT_DIR / f"n{n}.json"
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def _ingest_n5_octad(
    lines: list[str],
    *,
    journal: dict[str, str],
    source_url: str,
    dry_run: bool,
) -> dict:
    from cmplx.primitives.superperm import coverage_check, coverage_checksum

    labeled: list[dict] = []
    palindrome_index: int | None = None
    for idx, text in enumerate(lines):
        _validate_alphabet(text, 5)
        if not coverage_check(text, n=5):
            raise ValueError(f"n=5: coverage_check failed at index {idx}")
        is_pal = text == text[::-1]
        if is_pal:
            if palindrome_index is not None:
                raise ValueError("n=5: multiple palindrome minimals in source")
            palindrome_index = idx
        labeled.append(
            {
                "alternate_index": idx,
                "superpermutation": text,
                "length": len(text),
                "is_palindrome": is_pal,
                "role": "palindrome" if is_pal else "tree",
                "label": f"johnston:minimal:{idx + 1}",
                "journal_ref": f"{source_url}#minimal-{idx + 1}",
                "sha256": _sha256(text),
                "coverage_checksum": coverage_checksum(text, n=5),
            }
        )
    if palindrome_index is None:
        raise ValueError("n=5: no palindrome minimal found in source")

    # Octad order: palindrome at phase 0, then seven tree alternates in source order.
    tree_entries = [e for e in labeled if not e["is_palindrome"]]
    if len(tree_entries) != 7:
        raise ValueError(f"n=5: expected 7 non-palindrome minimals, got {len(tree_entries)}")
    pal_entry = labeled[palindrome_index]
    octad_slots: list[dict] = [
        {
            "phase": 0,
            "slot_id": "pal_n5_minimal",
            "role": "palindrome",
            "alternate_index": pal_entry["alternate_index"],
            "label": pal_entry["label"],
            "journal_ref": pal_entry["journal_ref"],
            "is_palindrome": True,
            "sha256": pal_entry["sha256"],
            "coverage_checksum": pal_entry["coverage_checksum"],
        }
    ]
    for tree_phase, entry in enumerate(tree_entries, start=1):
        octad_slots.append(
            {
                "phase": tree_phase,
                "slot_id": f"tree_n5_{tree_phase}",
                "role": "tree",
                "alternate_index": entry["alternate_index"],
                "label": entry["label"],
                "journal_ref": entry["journal_ref"],
                "is_palindrome": False,
                "sha256": entry["sha256"],
                "coverage_checksum": entry["coverage_checksum"],
            }
        )

    palindrome_sp = pal_entry["superpermutation"]
    record: dict = {
        "n": 5,
        "status": "validated",
        "superpermutation": palindrome_sp,
        "palindrome": palindrome_sp,
        "palindrome_index": palindrome_index,
        "length": 153,
        "permutation_count": 120,
        "provenance_class": "minimal",
        "source_url": source_url,
        "sha256": pal_entry["sha256"],
        "coverage_checksum": pal_entry["coverage_checksum"],
        "alternates": [e["superpermutation"] for e in labeled],
        "labeled_alternates": labeled,
        "alternate_count": 8,
        "tree_alternate_count": 7,
        "octad_layout": "1_palindrome_7_trees",
        "journal": journal,
    }
    octad_n5 = {
        "n": 5,
        "octad_layout": "1_palindrome_7_trees",
        "source_url": source_url,
        "journal": journal,
        "palindrome_id": "pal_n5_minimal",
        "tree_ids": [f"tree_n5_{i}" for i in range(1, 8)],
        "slots": octad_slots,
        "digit_to_letter": {"1": "a", "2": "b", "3": "c", "4": "d", "5": "e"},
    }

    if not dry_run:
        (OUT_DIR / "n5.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        (OUT_DIR / "octad_n5.json").write_text(json.dumps(octad_n5, indent=2) + "\n", encoding="utf-8")
        from cmplx.primitives.superperm import load_superperm_record
        from cmplx.primitives.n5_octad import load_n5_octad_schedule

        load_superperm_record.cache_clear()
        load_n5_octad_schedule.cache_clear()

    return {"n5": record, "octad_n5": octad_n5}


def ingest_n4(*, dry_run: bool = False) -> dict:
    """Refresh n4.json checksum fields from bundled constant."""
    from cmplx.primitives.superperm import SUPERPERM_N4, coverage_checksum

    record = {
        "n": 4,
        "status": "validated",
        "superpermutation": SUPERPERM_N4,
        "superperm": SUPERPERM_N4,
        "length": len(SUPERPERM_N4),
        "permutation_count": 24,
        "palindrome": True,
        "provenance_class": "minimal",
        "source_url": "bundled:primitives/superperm.py",
        "sha256": _sha256(SUPERPERM_N4),
        "coverage_checksum": coverage_checksum(SUPERPERM_N4, n=4),
    }
    if not dry_run:
        (OUT_DIR / "n4.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest published superpermutations.")
    parser.add_argument("--n", type=int, action="append", help="Single n (4-8). Repeatable.")
    parser.add_argument("--all", action="store_true", help="Ingest n=4..8")
    parser.add_argument("--from-file", type=Path, default=None, help="Local file (single --n only)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    targets = list(range(4, 9)) if args.all else (args.n or [5])
    if args.from_file and len(targets) != 1:
        parser.error("--from-file requires exactly one --n")

    results: list[dict] = []
    for n in targets:
        if n == 4:
            results.append(ingest_n4(dry_run=args.dry_run))
        elif n in SOURCES:
            results.append(
                ingest_n(n, from_file=args.from_file, dry_run=args.dry_run)
            )
        else:
            raise SystemExit(f"unsupported n={n}")

    print(json.dumps({"ok": True, "ingested": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
