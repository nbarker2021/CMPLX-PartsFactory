"""
Language filter for the token index.

A `LanguageFilter` decides whether an 8-character quad-pair window is
a *plausible* fragment in a target language. The default English
implementation uses a small frequency table of common English bigrams
plus a forbidden-bigram set (combinations that essentially never
occur). This is intentionally coarse — it filters out obvious noise
without claiming to be a real language model.

The filter is pluggable: callers can register additional filters by
instantiating `LanguageFilter` with their own bigram tables, or by
subclassing for richer rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .bonds import QuadBond


# ────────────────────────────────────────────────────────────────────────────
# English defaults
# ────────────────────────────────────────────────────────────────────────────

# Top English bigrams by frequency (Norvig 2013 letter-pair statistics,
# truncated). Order is not meaningful — we use this as a set.
ENGLISH_COMMON_BIGRAMS: frozenset[str] = frozenset({
    "th", "he", "in", "er", "an", "re", "on", "at", "en", "nd",
    "ti", "es", "or", "te", "of", "ed", "is", "it", "al", "ar",
    "st", "to", "nt", "ng", "se", "ha", "as", "ou", "io", "le",
    "ve", "co", "me", "de", "hi", "ri", "ro", "ic", "ne", "ea",
    "ra", "ce", "li", "ch", "ll", "be", "ma", "si", "om", "ur",
})

# Bigrams that almost never occur in real English text. If any appears
# in the 8-char window, the bond is rejected.
ENGLISH_FORBIDDEN_BIGRAMS: frozenset[str] = frozenset({
    "qq", "jj", "vv", "zz", "xx", "ww", "kk",
    "jq", "qj", "qz", "zq", "qx", "xq", "qy", "yq",
    "vj", "jv", "vq", "qv", "vx", "xv", "vz", "zv",
    "wj", "jw", "wq", "qw", "wx", "xw", "wz", "zw",
    "kq", "qk", "kx", "xk",
    "fk", "kf", "gj", "jg", "hj", "jh", "pq", "qp",
})


# ────────────────────────────────────────────────────────────────────────────
# Filter
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LanguageFilter:
    """Pluggable language-plausibility filter for quad bonds.

    The default rule for `accept(bond)`:
      1. The lowercased 8-char concat contains at least `min_common`
         common bigrams.
      2. The lowercased 8-char concat contains no forbidden bigrams.

    Both tables are case-insensitive and can be overridden per
    language. Set `min_common=0` and pass empty tables for the
    permissive "any" filter (accepts everything).
    """

    name: str
    common_bigrams: frozenset[str] = field(default_factory=frozenset)
    forbidden_bigrams: frozenset[str] = field(default_factory=frozenset)
    min_common: int = 1

    def accept(self, bond: QuadBond) -> bool:
        concat = bond.concat.lower()
        bigrams = [concat[i : i + 2] for i in range(len(concat) - 1)]

        for bg in bigrams:
            if bg in self.forbidden_bigrams:
                return False

        if self.min_common <= 0:
            return True
        hits = sum(1 for bg in bigrams if bg in self.common_bigrams)
        return hits >= self.min_common

    def filter(self, bonds: Iterable[QuadBond]) -> Iterable[QuadBond]:
        return (b for b in bonds if self.accept(b))


# ────────────────────────────────────────────────────────────────────────────
# Factory functions
# ────────────────────────────────────────────────────────────────────────────

def english_filter(*, min_common: int = 1) -> LanguageFilter:
    """The default English filter."""
    return LanguageFilter(
        name="english",
        common_bigrams=ENGLISH_COMMON_BIGRAMS,
        forbidden_bigrams=ENGLISH_FORBIDDEN_BIGRAMS,
        min_common=min_common,
    )


def any_filter() -> LanguageFilter:
    """Permissive filter that accepts every bond."""
    return LanguageFilter(
        name="any",
        common_bigrams=frozenset(),
        forbidden_bigrams=frozenset(),
        min_common=0,
    )


REGISTRY: dict[str, LanguageFilter] = {
    "any": any_filter(),
    "english": english_filter(),
}


def get_filter(name: str) -> LanguageFilter:
    """Look up a filter by name. Falls back to `any` if missing so the
    builder never crashes on an unknown language tag."""
    return REGISTRY.get(name, REGISTRY["any"])


__all__ = [
    "ENGLISH_COMMON_BIGRAMS",
    "ENGLISH_FORBIDDEN_BIGRAMS",
    "LanguageFilter",
    "english_filter",
    "any_filter",
    "get_filter",
    "REGISTRY",
]
