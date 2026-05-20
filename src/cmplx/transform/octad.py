"""
OctadSheet — n=4→n=5 eightfold scheduling (1 palindrome + 7 trees).

Data-driven from ``data/superpermutations/octad_n4.json`` until corpus
supplies real tree ids.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_DEFAULT_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "superpermutations" / "octad_n4.json"
)


@dataclass(frozen=True)
class OctadSheet:
    """One palindromic superset slot plus seven sequence-tree slots."""

    n: int
    palindrome_id: str
    tree_ids: tuple[str, ...]
    digit_to_letter: dict[str, str]

    def __post_init__(self) -> None:
        if len(self.tree_ids) != 7:
            raise ValueError(f"octad requires exactly 7 tree ids, got {len(self.tree_ids)}")

    @classmethod
    def for_active_n(cls, active_n: int, path: str | Path | None = None) -> "OctadSheet":
        """Load octad sheet for supervisor n (n=5 uses ``octad_n5.json``)."""
        if int(active_n) == 5:
            n5_path = (
                Path(path)
                if path
                else Path(__file__).resolve().parents[3] / "data" / "superpermutations" / "octad_n5.json"
            )
            if n5_path.is_file():
                return cls.from_json(n5_path)
        return cls.from_json(path)

    @classmethod
    def from_json(cls, path: str | Path | None = None) -> "OctadSheet":
        p = Path(path) if path else _DEFAULT_PATH
        with p.open(encoding="utf-8") as fh:
            data = json.load(fh)
        digit_map = data.get("digit_to_letter") or {
            "1": "a",
            "2": "b",
            "3": "c",
            "4": "d",
        }
        return cls(
            n=int(data.get("n", 4)),
            palindrome_id=str(data["palindrome_id"]),
            tree_ids=tuple(str(t) for t in data["tree_ids"]),
            digit_to_letter={str(k): str(v) for k, v in digit_map.items()},
        )

    def slot_id(self, phase: int) -> str:
        """Map octad phase 0–7 to palindrome or tree id."""
        phase = phase % 8
        if phase == 0:
            return self.palindrome_id
        return self.tree_ids[phase - 1]

    def letter_for_digit(self, digit: str) -> str:
        return self.digit_to_letter.get(digit, "a")

    def partial_pattern(self, digit: str, *, phase: int) -> Optional[str]:
        """Build an 8-char partial window for template admit queries.

        Palindrome phases fix outer ring (positions 0 and 7) with the
        digit-mapped letter; tree phases fix position 0 only (stub).
        """
        letter = self.letter_for_digit(digit)
        if phase % 8 == 0:
            return f"{letter}??????{letter}"
        return f"{letter}???????"


def octad_phase_at(index: int, *, width: int = 8) -> int:
    """Octad sheet phase 0–7 (0 = palindrome slot, 1–7 = tree slots)."""
    return index % width


__all__ = ["OctadSheet", "octad_phase_at"]
