"""
Case-shift variants for quad bonds.

Each base bond expands into multiple case forms. The eight defaults
together cover the "seam token cases" — the patterns that arise when
real text crosses a quad boundary:

    LOWER         the canonical lowercase form (`baaa|aaab`)
    UPPER         the canonical uppercase form (`BAAA|AAAB`)
    LEAD_LEFT     left quad starts capital (`Baaa|aaab`) — start-of-word
    LEAD_RIGHT    right quad starts capital (`baaa|Aaab`) — *seam token*,
                  e.g. a new word begins inside the window
    LEAD_BOTH     both quads start capital (`Baaa|Aaab`) — two adjacent words
    CAMEL_INNER   capital at the very seam (`baaA|Aaab`) — *seam token*,
                  e.g. CamelCase word boundary
    ALTERNATING   `BaAa|AaAb` — stress / acronym-y pattern
    PALINDROME    mirror-symmetric case (`BaaB|BaaB` style)

The set is intentionally finite and pluggable; callers can pass their
own list of `CaseMode` values when building the index.
"""
from __future__ import annotations

from dataclasses import replace
from enum import Enum
from typing import Iterable

from .bonds import QUAD_LEN, QuadBond


class CaseMode(str, Enum):
    LOWER = "lower"
    UPPER = "upper"
    LEAD_LEFT = "lead_left"
    LEAD_RIGHT = "lead_right"
    LEAD_BOTH = "lead_both"
    CAMEL_INNER = "camel_inner"
    ALTERNATING = "alternating"
    PALINDROME = "palindrome"


DEFAULT_CASE_MODES: tuple[CaseMode, ...] = tuple(CaseMode)

# Case modes that specifically mark the inter-quad seam — these are
# the patterns most likely to span a real-word boundary inside the
# 8-char window. Builders can opt to keep only these to focus the
# index on cross-word transitions.
SEAM_CASE_MODES: tuple[CaseMode, ...] = (
    CaseMode.LEAD_RIGHT,
    CaseMode.LEAD_BOTH,
    CaseMode.CAMEL_INNER,
)


# ────────────────────────────────────────────────────────────────────────────
# Case pattern application
# ────────────────────────────────────────────────────────────────────────────

def _apply_pattern(concat: str, upper_positions: Iterable[int]) -> str:
    """Return `concat` with characters at `upper_positions` uppercased
    and all other characters lowercased."""
    upper_set = set(upper_positions)
    return "".join(
        ch.upper() if i in upper_set else ch.lower()
        for i, ch in enumerate(concat)
    )


def apply_case(bond: QuadBond, mode: CaseMode) -> QuadBond:
    """Return a new bond whose 8-char window has the given case pattern."""
    concat = bond.concat

    if mode is CaseMode.LOWER:
        new_concat = concat.lower()
    elif mode is CaseMode.UPPER:
        new_concat = concat.upper()
    elif mode is CaseMode.LEAD_LEFT:
        new_concat = _apply_pattern(concat, [0])
    elif mode is CaseMode.LEAD_RIGHT:
        new_concat = _apply_pattern(concat, [QUAD_LEN])
    elif mode is CaseMode.LEAD_BOTH:
        new_concat = _apply_pattern(concat, [0, QUAD_LEN])
    elif mode is CaseMode.CAMEL_INNER:
        # Capital on each side of the seam.
        new_concat = _apply_pattern(concat, [QUAD_LEN - 1, QUAD_LEN])
    elif mode is CaseMode.ALTERNATING:
        new_concat = _apply_pattern(
            concat, [i for i in range(len(concat)) if i % 2 == 0]
        )
    elif mode is CaseMode.PALINDROME:
        # Mirror-symmetric case pattern about the center.
        n = len(concat)
        new_concat = _apply_pattern(
            concat,
            [0, n - 1, QUAD_LEN - 1, QUAD_LEN],
        )
    else:
        raise ValueError(f"unknown CaseMode: {mode!r}")

    return replace(
        bond,
        quad_left=new_concat[:QUAD_LEN],
        quad_right=new_concat[QUAD_LEN:],
    )


def case_variants(
    bond: QuadBond,
    modes: Iterable[CaseMode] = DEFAULT_CASE_MODES,
) -> list[tuple[CaseMode, QuadBond]]:
    """Return `(mode, bond_with_that_case)` for each requested mode.
    Duplicates (where two modes produce the same string) are kept —
    they reflect distinct semantic positions in the index even when
    the concatenation collides (e.g. for an all-base bond)."""
    return [(mode, apply_case(bond, mode)) for mode in modes]


__all__ = [
    "CaseMode",
    "DEFAULT_CASE_MODES",
    "SEAM_CASE_MODES",
    "apply_case",
    "case_variants",
]
