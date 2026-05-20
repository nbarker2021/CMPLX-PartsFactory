"""Tests for cmplx.transform.token_index.warmstart."""
from __future__ import annotations

from cmplx.transform.token_index.bonds import QuadBond
from cmplx.transform.token_index.case import CaseMode
from cmplx.transform.token_index.warmstart import (
    IndexEntryPayload,
    WarmStartLookup,
    WarmStartOutcome,
    WarmStartStats,
    key_case_base,
    key_exact,
    key_predecessor,
    predecessor_concat,
    publish_entry,
)


class FakeCache:
    """In-memory stand-in for the SpeedLight cache port."""

    def __init__(self) -> None:
        self.store: dict[str, object] = {}

    def get(self, k):  # noqa: ANN001
        return self.store.get(k)

    def put(self, k, v):  # noqa: ANN001
        self.store[k] = v


def _payload(concat: str, **overrides):
    base = {
        "concat": concat,
        "morphon_id": f"m-{concat}",
        "snap_key": "snap-" + concat,
        "e8_coords": (0.0,) * 8,
        "digital_root": 5,
        "lane": "transformative",
        "cache_key": key_exact(concat),
        "level": 1,
        "case_mode": "lower",
        "language": "any",
    }
    base.update(overrides)
    return IndexEntryPayload(**base)


def test_predecessor_concat_for_levels():
    b1 = QuadBond(quad_left="baaa", quad_right="aaab", level=1)
    assert predecessor_concat(b1) is None  # nothing before level 1
    b2 = QuadBond(quad_left="bcaa", quad_right="aacb", level=2)
    # Level 2 predecessor drops the level-2 ring (positions 1, 6) back
    # to base ("a"), keeping only the level-1 ring (positions 0, 7).
    assert predecessor_concat(b2) == "baaaaaab"


def test_warmstart_exact_hit():
    cache = FakeCache()
    publish_entry(cache, _payload("baaaaaab"), CaseMode.LOWER)
    lookup = WarmStartLookup(cache)
    bond = QuadBond(quad_left="baaa", quad_right="aaab", level=1)
    hit = lookup.probe(bond, CaseMode.LOWER)
    assert hit.outcome is WarmStartOutcome.EXACT
    assert hit.payload.concat == "baaaaaab"


def test_warmstart_case_base_hit():
    cache = FakeCache()
    publish_entry(cache, _payload("baaaaaab"), CaseMode.LOWER)
    lookup = WarmStartLookup(cache)
    upper = QuadBond(quad_left="BAAA", quad_right="AAAB", level=1)
    hit = lookup.probe(upper, CaseMode.UPPER)
    assert hit.outcome is WarmStartOutcome.CASE_BASE


def test_warmstart_predecessor_hit():
    cache = FakeCache()
    publish_entry(cache, _payload("baaaaaab"), CaseMode.LOWER)
    lookup = WarmStartLookup(cache)
    # Level-2 bond with same outer ring (b) and a new inner ring (c).
    bond_l2 = QuadBond(quad_left="bcaa", quad_right="aacb", level=2)
    hit = lookup.probe(bond_l2, CaseMode.LOWER)
    assert hit.outcome is WarmStartOutcome.PREDECESSOR
    assert hit.payload.concat == "baaaaaab"


def test_warmstart_cold_when_nothing_published():
    lookup = WarmStartLookup(FakeCache())
    bond = QuadBond(quad_left="baaa", quad_right="aaab", level=1)
    hit = lookup.probe(bond, CaseMode.LOWER)
    assert hit.outcome is WarmStartOutcome.COLD


def test_warmstart_no_cache_is_cold():
    lookup = WarmStartLookup(None)
    bond = QuadBond(quad_left="baaa", quad_right="aaab", level=1)
    assert lookup.probe(bond, CaseMode.LOWER).outcome is WarmStartOutcome.COLD


def test_stats_classifications():
    s = WarmStartStats()
    s.record(WarmStartOutcome.EXACT)
    s.record(WarmStartOutcome.CASE_BASE)
    s.record(WarmStartOutcome.PREDECESSOR)
    s.record(WarmStartOutcome.NEIGHBOR)
    s.record(WarmStartOutcome.COLD)
    assert s.defined == 1
    assert s.vague == 3
    assert s.cold == 1
    assert s.total == 5
