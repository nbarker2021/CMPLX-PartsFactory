"""
Quad-token bond enumeration.

A *quad bond* is an 8-character window split as `qqqq|qqqq` (two 4-char
quads with a seam between them). Bonds form concentric matching rings:

    Level 1 — outer ring: positions (0, 7) carry the same character.
              Starting from the trivial all-base state, a single
              character mutation gives `caaa|aaac` for character `c`.

    Level 2 — outer + first inner ring: positions (1, 6) match too.
              `cdaa|aadc` for characters (c, d).

    Level 3 — adds second inner ring: positions (2, 5).
              `cdef|fedc` for characters (c, d, e, f… wait, only 3 mutating).
              Concretely: `cdea|aedc` for (c, d, e), positions 3 and 4
              remain at the base character.

Each level is an *involution* in the sense that flipping the 8-char
ring around its midpoint leaves it invariant — every mutation has its
mirror partner.

The base alphabet is configurable; default is the 26 ASCII lowercase
letters. Case shifts live in `case.py`.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Sequence


# ────────────────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────────────────

DEFAULT_ALPHABET: tuple[str, ...] = tuple("abcdefghijklmnopqrstuvwxyz")
DEFAULT_BASE_CHAR: str = "a"
QUAD_LEN: int = 4

# Position pairs introduced at each involution level. Position numbering
# is over the concatenated 8-char string (left quad = 0..3, seam between
# 3 and 4, right quad = 4..7).
RING_POSITIONS: tuple[tuple[int, int], ...] = (
    (0, 7),  # outer ring
    (1, 6),  # first inner ring
    (2, 5),  # second inner ring
    # (3, 4) would close the palindrome — reserved for future expansion.
)


# ────────────────────────────────────────────────────────────────────────────
# Bond type
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class QuadBond:
    """One quad-pair bond at a given involution level."""

    quad_left: str
    quad_right: str
    level: int
    ring_chars: tuple[str, ...] = field(default_factory=tuple)
    base_char: str = DEFAULT_BASE_CHAR

    def __post_init__(self) -> None:
        if len(self.quad_left) != QUAD_LEN:
            raise ValueError(f"quad_left must be {QUAD_LEN} chars: {self.quad_left!r}")
        if len(self.quad_right) != QUAD_LEN:
            raise ValueError(f"quad_right must be {QUAD_LEN} chars: {self.quad_right!r}")

    @property
    def concat(self) -> str:
        """The 8-char concatenation (no seam character)."""
        return self.quad_left + self.quad_right

    @property
    def seam(self) -> str:
        """The 9-char display form with explicit seam `|`."""
        return f"{self.quad_left}|{self.quad_right}"

    def is_palindrome(self) -> bool:
        """True if the 8-char concat reads the same forwards and backwards
        (i.e. every ring has matching characters at its position pair)."""
        s = self.concat
        return s == s[::-1]


# ────────────────────────────────────────────────────────────────────────────
# Enumeration
# ────────────────────────────────────────────────────────────────────────────

def enumerate_bonds(
    level: int,
    *,
    alphabet: Sequence[str] = DEFAULT_ALPHABET,
    base_char: str = DEFAULT_BASE_CHAR,
    include_base: bool = False,
) -> Iterator[QuadBond]:
    """Yield every quad bond at the requested involution level.

    Args:
        level: 1, 2, or 3 (number of concentric rings carrying a
            non-base character at the matching position pair).
        alphabet: characters allowed in the ring positions.
        base_char: the character that fills non-ring positions.
        include_base: if False (default), the all-base bond
            `aaaa|aaaa` is skipped at every level. Set True to emit it
            once at the start.

    A level-`k` bond fills the outer `k` rings with chosen characters
    and leaves the remaining `(4 - k)` interior positions at base.
    """
    if level < 1 or level > len(RING_POSITIONS):
        raise ValueError(
            f"level must be in 1..{len(RING_POSITIONS)} (got {level})"
        )
    if len(base_char) != 1:
        raise ValueError(f"base_char must be one character: {base_char!r}")

    rings = RING_POSITIONS[:level]
    base_string = base_char * (QUAD_LEN * 2)

    seen_base = False
    for ring_choice in itertools.product(alphabet, repeat=level):
        chars = list(base_string)
        for (lo, hi), c in zip(rings, ring_choice):
            chars[lo] = c
            chars[hi] = c
        concat = "".join(chars)
        if concat == base_string:
            if include_base and not seen_base:
                seen_base = True
            else:
                continue
        yield QuadBond(
            quad_left=concat[:QUAD_LEN],
            quad_right=concat[QUAD_LEN:],
            level=level,
            ring_chars=tuple(ring_choice),
            base_char=base_char,
        )


def enumerate_levels(
    levels: Iterable[int],
    *,
    alphabet: Sequence[str] = DEFAULT_ALPHABET,
    base_char: str = DEFAULT_BASE_CHAR,
) -> Iterator[QuadBond]:
    """Yield bonds at every level in `levels`, in order. Each level
    contributes its own combinatorial expansion; duplicates between
    levels (e.g. a level-2 bond where the inner-ring character equals
    base) are not deduplicated — each level is its own structural
    layer in the index."""
    for lvl in levels:
        yield from enumerate_bonds(lvl, alphabet=alphabet, base_char=base_char)


def count_bonds(level: int, *, alphabet_size: int = len(DEFAULT_ALPHABET)) -> int:
    """Combinatorial size at a level: |alphabet|^level, minus the
    all-base entry which is filtered out by default."""
    return alphabet_size**level - 1


__all__ = [
    "DEFAULT_ALPHABET",
    "DEFAULT_BASE_CHAR",
    "QUAD_LEN",
    "RING_POSITIONS",
    "QuadBond",
    "enumerate_bonds",
    "enumerate_levels",
    "count_bonds",
]
