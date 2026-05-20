"""
n=5 octad schedule — one palindrome minimal + seven tree minimals (Johnston/Chaffin).

Each octad phase 0–7 walks its own length-153 superpermutation string at the
same step index (supervisor cursor), not a single palindrome-only spine.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_SUPERPERM_DIR = Path(__file__).resolve().parents[3] / "data" / "superpermutations"
_N5_JSON = _SUPERPERM_DIR / "n5.json"
_OCTAD_N5_JSON = _SUPERPERM_DIR / "octad_n5.json"


@dataclass(frozen=True)
class N5OctadSlot:
    phase: int
    slot_id: str
    role: str
    alternate_index: int
    label: str
    journal_ref: str
    superpermutation: str
    is_palindrome: bool
    sha256: str = ""
    coverage_checksum: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "slot_id": self.slot_id,
            "role": self.role,
            "alternate_index": self.alternate_index,
            "label": self.label,
            "journal_ref": self.journal_ref,
            "is_palindrome": self.is_palindrome,
            "length": len(self.superpermutation),
            "sha256": self.sha256,
            "coverage_checksum": self.coverage_checksum,
        }


@dataclass(frozen=True)
class N5OctadSchedule:
    """Eightfold n=5 supervisor schedule (palindrome + 7 trees)."""

    slots: tuple[N5OctadSlot, ...]
    digit_to_letter: dict[str, str]
    journal: dict[str, str]
    source_url: str = ""
    walk_length: int = 153

    def __post_init__(self) -> None:
        if len(self.slots) != 8:
            raise ValueError(f"n5 octad requires 8 slots, got {len(self.slots)}")

    def slot_at_phase(self, phase: int) -> N5OctadSlot:
        return self.slots[int(phase) % 8]

    def superperm_at_phase(self, phase: int) -> str:
        return self.slot_at_phase(phase).superpermutation

    def digit_at_step(self, step_index: int) -> tuple[int, str, N5OctadSlot]:
        """Return (phase, digit_char, slot) for supervisor step index."""
        phase = int(step_index) % 8
        slot = self.slot_at_phase(phase)
        pos = int(step_index)
        if pos >= self.walk_length:
            pos = pos % self.walk_length
        return phase, slot.superpermutation[pos], slot

    def tree_slots(self) -> tuple[N5OctadSlot, ...]:
        return tuple(s for s in self.slots if s.role == "tree")

    def palindrome_slot(self) -> N5OctadSlot:
        for slot in self.slots:
            if slot.is_palindrome:
                return slot
        raise ValueError("n5 octad: no palindrome slot")

    def as_dict(self) -> dict[str, Any]:
        return {
            "n": 5,
            "walk_length": self.walk_length,
            "source_url": self.source_url,
            "journal": self.journal,
            "slots": [s.as_dict() for s in self.slots],
        }


def _build_schedule_from_n5(rec: dict[str, Any], octad: dict[str, Any]) -> N5OctadSchedule:
    labeled = list(rec.get("labeled_alternates") or [])
    by_index = {int(e["alternate_index"]): e for e in labeled}
    slots: list[N5OctadSlot] = []
    for slot_rec in octad.get("slots") or []:
        idx = int(slot_rec["alternate_index"])
        entry = by_index.get(idx)
        if entry is None:
            raise ValueError(f"n5 octad: missing labeled alternate {idx}")
        sp = str(entry.get("superpermutation") or "")
        slots.append(
            N5OctadSlot(
                phase=int(slot_rec["phase"]),
                slot_id=str(slot_rec["slot_id"]),
                role=str(slot_rec["role"]),
                alternate_index=idx,
                label=str(slot_rec.get("label") or entry.get("label", "")),
                journal_ref=str(slot_rec.get("journal_ref") or entry.get("journal_ref", "")),
                superpermutation=sp,
                is_palindrome=bool(slot_rec.get("is_palindrome")),
                sha256=str(slot_rec.get("sha256") or entry.get("sha256", "")),
                coverage_checksum=str(
                    slot_rec.get("coverage_checksum") or entry.get("coverage_checksum", "")
                ),
            )
        )
    slots.sort(key=lambda s: s.phase)
    return N5OctadSchedule(
        slots=tuple(slots),
        digit_to_letter={str(k): str(v) for k, v in (octad.get("digit_to_letter") or {}).items()},
        journal=dict(octad.get("journal") or rec.get("journal") or {}),
        source_url=str(octad.get("source_url") or rec.get("source_url") or ""),
        walk_length=int(rec.get("length") or 153),
    )


@lru_cache(maxsize=1)
def load_n5_octad_schedule() -> N5OctadSchedule:
    if not _N5_JSON.is_file():
        raise ValueError("n5.json missing")
    rec = json.loads(_N5_JSON.read_text(encoding="utf-8"))
    if str(rec.get("status")) != "validated":
        raise ValueError(f"n5 not validated (status={rec.get('status')!r})")
    if _OCTAD_N5_JSON.is_file():
        octad = json.loads(_OCTAD_N5_JSON.read_text(encoding="utf-8"))
    else:
        octad = _synthetic_octad_from_record(rec)
    return _build_schedule_from_n5(rec, octad)


def _synthetic_octad_from_record(rec: dict[str, Any]) -> dict[str, Any]:
    labeled = list(rec.get("labeled_alternates") or [])
    if not labeled and rec.get("alternates"):
        labeled = [
            {
                "alternate_index": i,
                "superpermutation": s,
                "is_palindrome": str(s) == str(s)[::-1],
                "label": f"johnston:minimal:{i + 1}",
                "journal_ref": f"{rec.get('source_url', '')}#minimal-{i + 1}",
            }
            for i, s in enumerate(rec["alternates"])
        ]
    pal = next(e for e in labeled if e.get("is_palindrome"))
    trees = [e for e in labeled if not e.get("is_palindrome")]
    slots = [
        {
            "phase": 0,
            "slot_id": "pal_n5_minimal",
            "role": "palindrome",
            "alternate_index": pal["alternate_index"],
            "label": pal.get("label"),
            "journal_ref": pal.get("journal_ref"),
            "is_palindrome": True,
        }
    ]
    for phase, entry in enumerate(trees, start=1):
        slots.append(
            {
                "phase": phase,
                "slot_id": f"tree_n5_{phase}",
                "role": "tree",
                "alternate_index": entry["alternate_index"],
                "label": entry.get("label"),
                "journal_ref": entry.get("journal_ref"),
                "is_palindrome": False,
            }
        )
    return {
        "n": 5,
        "octad_layout": "1_palindrome_7_trees",
        "slots": slots,
        "digit_to_letter": {"1": "a", "2": "b", "3": "c", "4": "d", "5": "e"},
    }


def n5_labeled_alternates() -> list[dict[str, Any]]:
    rec = json.loads(_N5_JSON.read_text(encoding="utf-8")) if _N5_JSON.is_file() else {}
    return list(rec.get("labeled_alternates") or [])


__all__ = [
    "N5OctadSlot",
    "N5OctadSchedule",
    "load_n5_octad_schedule",
    "n5_labeled_alternates",
]
