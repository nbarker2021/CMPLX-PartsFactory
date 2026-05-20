"""
TemplateFrame — treat the current token index as the first template
frame and measure its constraint power.

Given an existing token_index.sqlite, this module answers:

  - Slot coverage: for each (level, position, case_mode), which letters
    are present? Is the slot "solved" (all 25 non-base letters seen)?

  - Template admit-sets: given a partial window (e.g. fix the left
    half of an 8-char window), how many right-half completions does
    the substrate admit?

  - Forced-cell ratio: across a sample of partial windows, what
    fraction admit exactly 1 continuation (forced), ≤5 continuations
    (highly constrained), or ≥6 (free)?

  - Constraint compression: log2 of how many bits the substrate has
    eliminated from a uniform prior over the candidate space.

The substrate itself is the read-only input. Nothing in this module
writes to the DB. Output is purely measurement.
"""
from __future__ import annotations

import math
import random
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence


# ────────────────────────────────────────────────────────────────────────────
# Slot coverage
# ────────────────────────────────────────────────────────────────────────────

# Concentric ring positions: (level, (lo, hi))
RING_POSITIONS = {1: (0, 7), 2: (1, 6), 3: (2, 5)}


@dataclass
class SlotCoverage:
    """Per (level, position, case_mode) → set of distinct characters seen."""

    seen: dict[tuple[int, int, str], set[str]] = field(default_factory=dict)
    alphabet_size: int = 26

    def add(self, level: int, position: int, case_mode: str, char: str) -> None:
        key = (level, position, case_mode)
        self.seen.setdefault(key, set()).add(char.lower())

    def is_solved(self, level: int, position: int, case_mode: str) -> bool:
        """A slot is 'solved' if it has all alphabet_size-1 non-base letters."""
        return len(self.seen.get((level, position, case_mode), set())) >= self.alphabet_size - 1

    def coverage_pct(self, level: int, position: int, case_mode: str) -> float:
        seen = len(self.seen.get((level, position, case_mode), set()))
        return 100.0 * seen / max(self.alphabet_size - 1, 1)

    def slot_summary(self) -> list[dict]:
        out: list[dict] = []
        for (level, pos, cm), letters in sorted(self.seen.items()):
            out.append({
                "level": level,
                "position": pos,
                "case_mode": cm,
                "distinct_letters": len(letters),
                "coverage_pct": round(100.0 * len(letters) / max(self.alphabet_size - 1, 1), 1),
                "solved": len(letters) >= self.alphabet_size - 1,
            })
        return out

    def aggregate_by_position(self) -> dict[int, dict]:
        """Roll up across case modes and levels: per position, max
        coverage observed and whether *any* (level, case) slot is solved."""
        by_pos: dict[int, dict] = {}
        for (level, pos, cm), letters in self.seen.items():
            slot = by_pos.setdefault(pos, {"max_coverage": 0, "solved_in": []})
            n = len(letters)
            if n > slot["max_coverage"]:
                slot["max_coverage"] = n
            if n >= self.alphabet_size - 1:
                slot["solved_in"].append(f"L{level}/{cm}")
        for slot in by_pos.values():
            slot["max_coverage_pct"] = round(
                100.0 * slot["max_coverage"] / max(self.alphabet_size - 1, 1), 1
            )
        return by_pos


# ────────────────────────────────────────────────────────────────────────────
# Template frame
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class AdmitSet:
    """The set of substrate entries that match a partial-window template."""

    prefix: str
    matching_concats: list[str] = field(default_factory=list)
    distinct_completions: set[str] = field(default_factory=set)

    @property
    def size(self) -> int:
        return len(self.matching_concats)

    @property
    def completion_count(self) -> int:
        return len(self.distinct_completions)

    @property
    def is_forced(self) -> bool:
        return self.completion_count == 1

    @property
    def is_empty(self) -> bool:
        return self.size == 0


class TemplateFrame:
    """Read-only template-frame view over a token_index.sqlite."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        if not Path(self.db_path).exists():
            raise FileNotFoundError(self.db_path)
        self._conn = sqlite3.connect(self.db_path)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "TemplateFrame":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ── Slot coverage ───────────────────────────────────────────────────

    def slot_coverage(self) -> SlotCoverage:
        cov = SlotCoverage()
        cur = self._conn.execute(
            "SELECT concat, bond_level, case_mode FROM token_bonds"
        )
        for concat, level, case_mode in cur:
            for ring_level, (lo, hi) in RING_POSITIONS.items():
                if ring_level <= int(level):
                    cov.add(int(level), lo, case_mode, concat[lo])
                    cov.add(int(level), hi, case_mode, concat[hi])
        return cov

    # ── Template admit-set ──────────────────────────────────────────────

    def admit_set_by_left(
        self,
        quad_left: str,
        *,
        case_mode: str = "lower",
        language: Optional[str] = None,
    ) -> AdmitSet:
        """Given a 4-char left quad, return every right quad the
        substrate has paired it with."""
        sql = (
            "SELECT concat, quad_right FROM token_bonds "
            "WHERE quad_left = ? AND case_mode = ?"
        )
        params: list = [quad_left, case_mode]
        if language is not None:
            sql += " AND language = ?"
            params.append(language)
        cur = self._conn.execute(sql, params)
        result = AdmitSet(prefix=quad_left)
        for concat, qr in cur:
            result.matching_concats.append(concat)
            result.distinct_completions.add(qr)
        return result

    def admit_set_by_outer_ring(
        self,
        outer_char: str,
        *,
        case_mode: str = "lower",
        language: Optional[str] = None,
    ) -> AdmitSet:
        """Fix only the outer ring (positions 0, 7) and report all
        inner-ring completions the substrate admits."""
        sql = (
            "SELECT concat, substr(concat, 2, 6) AS inner FROM token_bonds "
            "WHERE substr(concat, 1, 1) = ? AND substr(concat, 8, 1) = ? "
            "AND case_mode = ?"
        )
        params: list = [outer_char, outer_char, case_mode]
        if language is not None:
            sql += " AND language = ?"
            params.append(language)
        cur = self._conn.execute(sql, params)
        result = AdmitSet(prefix=f"{outer_char}......{outer_char}")
        for concat, inner in cur:
            result.matching_concats.append(concat)
            result.distinct_completions.add(inner)
        return result

    def admit_set_by_partial(
        self,
        pattern: str,
        *,
        case_mode: str = "lower",
        language: Optional[str] = None,
    ) -> AdmitSet:
        """`pattern` is an 8-char string with '?' as wildcard. Returns
        every concat matching the fixed positions."""
        if len(pattern) != 8:
            raise ValueError("pattern must be 8 chars (use '?' for wildcards)")
        clauses: list[str] = ["case_mode = ?"]
        params: list = [case_mode]
        for i, ch in enumerate(pattern):
            if ch != "?":
                clauses.append(f"substr(concat, {i + 1}, 1) = ?")
                params.append(ch)
        if language is not None:
            clauses.append("language = ?")
            params.append(language)
        sql = "SELECT concat FROM token_bonds WHERE " + " AND ".join(clauses)
        cur = self._conn.execute(sql, params)
        result = AdmitSet(prefix=pattern)
        for (concat,) in cur:
            result.matching_concats.append(concat)
            # The "completion" is the wildcard chars only.
            completion = "".join(
                concat[i] for i in range(8) if pattern[i] == "?"
            )
            if completion:
                result.distinct_completions.add(completion)
            else:
                result.distinct_completions.add(concat)
        return result

    # ── Forced-cell ratio sweep ─────────────────────────────────────────

    def forced_cell_sweep(
        self,
        *,
        n_samples: int = 200,
        case_mode: str = "lower",
        language: Optional[str] = None,
        seed: int = 0,
    ) -> "ForcedCellReport":
        """Sample `n_samples` distinct quad-left prefixes from the
        substrate. For each, count distinct admitted quad-rights.
        Returns a histogram of admit-set sizes — the canonical
        forced/constrained/free statistic."""
        rng = random.Random(seed)
        cur = self._conn.execute(
            "SELECT DISTINCT quad_left FROM token_bonds WHERE case_mode = ?"
            + (" AND language = ?" if language is not None else ""),
            (case_mode, language) if language is not None else (case_mode,),
        )
        all_lefts = [row[0] for row in cur]
        if not all_lefts:
            return ForcedCellReport(total=0)
        if len(all_lefts) > n_samples:
            sample = rng.sample(all_lefts, n_samples)
        else:
            sample = all_lefts

        report = ForcedCellReport(total=len(sample))
        for qleft in sample:
            adm = self.admit_set_by_left(qleft, case_mode=case_mode, language=language)
            n = adm.completion_count
            report.sizes.append(n)
            if n == 1:
                report.forced += 1
            elif n <= 5:
                report.highly_constrained += 1
            elif n <= 25:
                report.constrained += 1
            else:
                report.free += 1
        return report

    # ── Constraint compression ──────────────────────────────────────────

    def compression_bits(
        self,
        *,
        case_mode: str = "lower",
        language: Optional[str] = None,
    ) -> dict:
        """Average log2 reduction from a uniform-26 prior at each free
        slot. With our enumeration, each entry has 1 free position per
        ring (outer ring is one degree of freedom because positions
        0 and 7 are tied; same for 1,6 and 2,5)."""
        sweep = self.forced_cell_sweep(
            n_samples=500, case_mode=case_mode, language=language
        )
        if sweep.total == 0:
            return {"total": 0, "bits_saved_per_slot": 0.0}
        # The free slot for a level-2 quad-left → quad-right inference
        # has 26^3 = 17576 theoretical right halves. The substrate
        # admits `size` of them.
        max_universe = 26 ** 3
        bits_saved = []
        for size in sweep.sizes:
            if size == 0:
                continue
            bits_saved.append(math.log2(max_universe / max(size, 1)))
        return {
            "samples": sweep.total,
            "avg_admit_size": round(sum(sweep.sizes) / max(len(sweep.sizes), 1), 2),
            "median_admit_size": int(sorted(sweep.sizes)[len(sweep.sizes) // 2]) if sweep.sizes else 0,
            "max_universe": max_universe,
            "avg_bits_saved": round(sum(bits_saved) / max(len(bits_saved), 1), 2),
            "max_possible_bits": round(math.log2(max_universe), 2),
            "forced_count": sweep.forced,
            "highly_constrained_count": sweep.highly_constrained,
            "constrained_count": sweep.constrained,
            "free_count": sweep.free,
        }


# ────────────────────────────────────────────────────────────────────────────
# Reports
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class ForcedCellReport:
    total: int = 0
    forced: int = 0  # admit_count == 1
    highly_constrained: int = 0  # 2 ≤ count ≤ 5
    constrained: int = 0  # 6 ≤ count ≤ 25
    free: int = 0  # count > 25
    sizes: list[int] = field(default_factory=list)

    def as_dict(self) -> dict:
        total = max(self.total, 1)
        return {
            "total_samples": self.total,
            "forced": self.forced,
            "highly_constrained": self.highly_constrained,
            "constrained": self.constrained,
            "free": self.free,
            "forced_pct": round(100.0 * self.forced / total, 2),
            "highly_constrained_pct": round(100.0 * self.highly_constrained / total, 2),
            "constrained_pct": round(100.0 * self.constrained / total, 2),
            "free_pct": round(100.0 * self.free / total, 2),
            "median_admit_size": int(sorted(self.sizes)[len(self.sizes) // 2]) if self.sizes else 0,
            "max_admit_size": max(self.sizes) if self.sizes else 0,
        }


def template_report(db_path: str | Path) -> dict:
    """Top-level entry point: runs the full template-frame analysis
    against an existing token_index.sqlite and returns a structured
    report dict."""
    with TemplateFrame(db_path) as frame:
        cov = frame.slot_coverage()
        per_position = cov.aggregate_by_position()
        compression = {
            cm: frame.compression_bits(case_mode=cm, language="any")
            for cm in ("lower", "upper")
        }
        forced_sweep_lower = frame.forced_cell_sweep(case_mode="lower", language="any").as_dict()
        forced_sweep_english = frame.forced_cell_sweep(case_mode="lower", language="english").as_dict()
    return {
        "db_path": str(db_path),
        "slot_coverage_by_position": per_position,
        "slot_summary": cov.slot_summary(),
        "compression_bits": compression,
        "forced_cell_sweep_lower_any": forced_sweep_lower,
        "forced_cell_sweep_lower_english": forced_sweep_english,
    }


__all__ = [
    "RING_POSITIONS",
    "SlotCoverage",
    "AdmitSet",
    "TemplateFrame",
    "ForcedCellReport",
    "template_report",
]
