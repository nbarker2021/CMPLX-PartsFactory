"""
Warm-start lookup for the token index builder.

Every bond entry probes the SpeedLight cache for a related prior entry
before forging anything new. The probe is hierarchical — the
*tightest* relationship that hits classifies the entry:

    EXACT      — same 8-char concat already cached. Defined, no work.
    CASE_BASE  — the LOWER-case form is cached. Vague: inherit canonical
                 info, only the case metadata is new.
    PREDECESSOR— the level-(N-1) bond (same outer rings, one fewer
                 inner-ring character) is cached. Vague: forge with
                 parent=predecessor, inherit e8 vicinity.
    NEIGHBOR   — geometric neighbor (same digital_root + lane) found.
                 Vague: warm start canonical info from neighbor.
    COLD       — no related entry. Full forge + canonicalize.

Each cached entry advertises itself under multiple keys so future
entries can find it through any of these relationships.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .bonds import QUAD_LEN, QuadBond, RING_POSITIONS
from .case import CaseMode

try:
    from cmplx.primitives.core import NLAECNFChain
except ImportError:  # pragma: no cover
    NLAECNFChain = None  # type: ignore


def geometry_snap_key(concat: str) -> str:
    """SNAP key on lowercased concat — geometry invariant for case morphs."""
    if NLAECNFChain is None:
        return concat.lower()
    return str(NLAECNFChain.full_chain(concat.lower())["snap_key"])


# ────────────────────────────────────────────────────────────────────────────
# Outcome classification
# ────────────────────────────────────────────────────────────────────────────

class WarmStartOutcome(str, Enum):
    EXACT = "exact"            # defined
    CASE_BASE = "case_base"    # vague
    PREDECESSOR = "predecessor"  # vague
    NEIGHBOR = "neighbor"      # vague
    COLD = "cold"              # cold

    @property
    def is_defined(self) -> bool:
        return self is WarmStartOutcome.EXACT

    @property
    def is_vague(self) -> bool:
        return self in (
            WarmStartOutcome.CASE_BASE,
            WarmStartOutcome.PREDECESSOR,
            WarmStartOutcome.NEIGHBOR,
        )

    @property
    def is_cold(self) -> bool:
        return self is WarmStartOutcome.COLD


# ────────────────────────────────────────────────────────────────────────────
# Cache payloads
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class IndexEntryPayload:
    """The minimum information cached per index entry.

    Stored under three SpeedLight keys per entry:
      - `token_index::concat::{8char}`
      - `token_index::case_base::{8char_lower}`   (only for LOWER entries)
      - `token_index::predecessor::{8char}`        (for any entry; allows
        higher levels to find it as their predecessor)

    Plus a per-`(digital_root, lane)` neighbor bucket.
    """

    concat: str
    morphon_id: str
    snap_key: str
    e8_coords: tuple[float, ...]
    digital_root: int
    lane: str
    cache_key: str
    level: int
    case_mode: str
    language: str
    parent_morphon_id: Optional[str] = None
    warmstart_outcome: str = WarmStartOutcome.COLD.value


# ────────────────────────────────────────────────────────────────────────────
# Key construction
# ────────────────────────────────────────────────────────────────────────────

NAMESPACE = "token_index"


def key_exact(concat: str) -> str:
    return f"{NAMESPACE}::concat::{concat}"


def key_case_base(concat_lower: str) -> str:
    return f"{NAMESPACE}::case_base::{concat_lower}"


def key_predecessor(concat: str) -> str:
    return f"{NAMESPACE}::predecessor::{concat}"


def key_neighbor(digital_root: int, lane: str) -> str:
    return f"{NAMESPACE}::neighbor::dr{digital_root}::{lane}"


def case_base_eligible(base_payload: IndexEntryPayload, bond: QuadBond) -> bool:
    """CASE_BASE promotion requires surface-only change (Δsnap=0 geometry)."""
    if base_payload.concat.lower() != bond.concat.lower():
        return False
    if base_payload.concat == bond.concat:
        return True
    return geometry_snap_key(base_payload.concat) == geometry_snap_key(bond.concat)


def predecessor_concat(bond: QuadBond) -> Optional[str]:
    """The 8-char concat of the level-(N-1) bond — drop the innermost
    ring character (reset positions back to base). For level-1 bonds
    there is no predecessor."""
    if bond.level <= 1:
        return None
    chars = list(bond.concat)
    lo, hi = RING_POSITIONS[bond.level - 1]
    chars[lo] = bond.base_char
    chars[hi] = bond.base_char
    return "".join(chars)


# ────────────────────────────────────────────────────────────────────────────
# Lookup
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class WarmStartHit:
    """The result of one probe sequence for a bond/case/language entry."""

    outcome: WarmStartOutcome
    payload: Optional[IndexEntryPayload] = None
    hit_key: str = ""
    notes: dict = field(default_factory=dict)


@dataclass
class WarmStartStats:
    """Tally of warm-start outcomes across a build run."""

    exact: int = 0
    case_base: int = 0
    predecessor: int = 0
    neighbor: int = 0
    cold: int = 0

    def record(self, outcome: WarmStartOutcome) -> None:
        if outcome is WarmStartOutcome.EXACT:
            self.exact += 1
        elif outcome is WarmStartOutcome.CASE_BASE:
            self.case_base += 1
        elif outcome is WarmStartOutcome.PREDECESSOR:
            self.predecessor += 1
        elif outcome is WarmStartOutcome.NEIGHBOR:
            self.neighbor += 1
        else:
            self.cold += 1

    @property
    def total(self) -> int:
        return self.exact + self.case_base + self.predecessor + self.neighbor + self.cold

    @property
    def defined(self) -> int:
        return self.exact

    @property
    def vague(self) -> int:
        return self.case_base + self.predecessor + self.neighbor

    def as_dict(self) -> dict:
        total = max(self.total, 1)
        return {
            "total": self.total,
            "exact": self.exact,
            "case_base": self.case_base,
            "predecessor": self.predecessor,
            "neighbor": self.neighbor,
            "cold": self.cold,
            "defined_pct": 100.0 * self.defined / total,
            "vague_pct": 100.0 * self.vague / total,
            "cold_pct": 100.0 * self.cold / total,
        }


class WarmStartLookup:
    """Probes the SpeedLight cache for prior knowledge about an entry."""

    def __init__(self, cache_provider: Optional[Any]) -> None:
        self.cache = cache_provider

    # ── Probe ───────────────────────────────────────────────────────────

    def probe(self, bond: QuadBond, case_mode: CaseMode) -> WarmStartHit:
        if self.cache is None:
            return WarmStartHit(WarmStartOutcome.COLD)

        # 1. Exact concat hit.
        k = key_exact(bond.concat)
        payload = self._get_payload(k)
        if payload is not None:
            return WarmStartHit(WarmStartOutcome.EXACT, payload, k)

        # 2. Case-base hit (LOWER form of the same concat).
        if case_mode is not CaseMode.LOWER:
            k = key_case_base(bond.concat.lower())
            payload = self._get_payload(k)
            if payload is not None and case_base_eligible(payload, bond):
                return WarmStartHit(WarmStartOutcome.CASE_BASE, payload, k)

        # 3. Predecessor hit (level-1 lower).
        pred = predecessor_concat(bond)
        if pred is not None:
            k = key_predecessor(pred)
            payload = self._get_payload(k)
            if payload is not None:
                return WarmStartHit(WarmStartOutcome.PREDECESSOR, payload, k)

        # 4. Neighbor hit deferred: requires the entry's own
        # canonicalization to know its DR/lane, which is exactly what
        # we are trying to avoid. The builder may call
        # `probe_neighbor(...)` *after* canonicalization to retrofit a
        # neighbor classification.
        return WarmStartHit(WarmStartOutcome.COLD)

    def probe_neighbor(self, digital_root: int, lane: str) -> WarmStartHit:
        if self.cache is None:
            return WarmStartHit(WarmStartOutcome.COLD)
        bucket = self._get_payload(key_neighbor(digital_root, lane))
        if isinstance(bucket, list) and bucket:
            return WarmStartHit(
                WarmStartOutcome.NEIGHBOR,
                payload=bucket[0],
                hit_key=key_neighbor(digital_root, lane),
                notes={"bucket_size": len(bucket)},
            )
        return WarmStartHit(WarmStartOutcome.COLD)

    # ── Internals ───────────────────────────────────────────────────────

    def _get_payload(self, key: str) -> Optional[Any]:
        try:
            return self.cache.get(key)
        except Exception:
            return None


# ────────────────────────────────────────────────────────────────────────────
# Publish helpers
# ────────────────────────────────────────────────────────────────────────────

def publish_entry(
    cache_provider: Optional[Any],
    payload: IndexEntryPayload,
    case_mode: CaseMode,
) -> None:
    """Advertise an entry under every relationship key future entries
    might use to find it."""
    if cache_provider is None:
        return

    try:
        cache_provider.put(key_exact(payload.concat), payload)
        cache_provider.put(key_predecessor(payload.concat), payload)
        if case_mode is CaseMode.LOWER:
            cache_provider.put(key_case_base(payload.concat.lower()), payload)

        # Maintain a small neighbor bucket per (DR, lane). Cap size so a
        # single bucket cannot bloat memory; the first entry in the
        # bucket is enough for warm-starting.
        bucket_key = key_neighbor(payload.digital_root, payload.lane)
        bucket = cache_provider.get(bucket_key) or []
        if not isinstance(bucket, list):
            bucket = []
        if len(bucket) < 8:
            bucket.append(payload)
            cache_provider.put(bucket_key, bucket)
    except Exception:
        # Cache writes are best-effort; the SQLite store is authoritative.
        return


__all__ = [
    "case_base_eligible",
    "geometry_snap_key",
    "WarmStartOutcome",
    "WarmStartHit",
    "WarmStartStats",
    "WarmStartLookup",
    "IndexEntryPayload",
    "publish_entry",
    "predecessor_concat",
    "key_exact",
    "key_case_base",
    "key_predecessor",
    "key_neighbor",
    "NAMESPACE",
]
