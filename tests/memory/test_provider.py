"""
F-3 facade tests — MMDBMemoryProvider against MemoryProvider Protocol.

Verifies:
  1. Protocol compliance + registration on `memory` port.
  2. store/fetch core methods round-trip.
  3. store_edge / neighbors edge traversal.
  4. by_e8_coordinates filters by Euclidean distance.
  5. ETP delegation + fallback parity.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import (
    Morphon,
    MorphonController,
    MemoryProvider,
)
from cmplx.memory.mmdb import MMDBMemoryProvider
from cmplx.symbolic.tarpit import TarPitSymbolicProvider


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


@pytest.fixture
def provider():
    p = MMDBMemoryProvider(":memory:")
    yield p
    p.close()


# ---------------------------------------------------------------------------
# 1. Protocol compliance
# ---------------------------------------------------------------------------

def test_provider_satisfies_memory_protocol(provider):
    assert isinstance(provider, MemoryProvider)


def test_provider_registers_on_memory_port(provider):
    MorphonController.get().register("memory", provider)
    assert MorphonController.get().has("memory")


# ---------------------------------------------------------------------------
# 2. store / fetch round-trip
# ---------------------------------------------------------------------------

def test_store_then_fetch_returns_equivalent_morphon(provider):
    m = Morphon.forge(payload={"k": "v"})
    provider.store(m)
    m2 = provider.fetch(m.id)
    assert m2 is not None
    assert m2.id == m.id
    assert m2.payload == m.payload


def test_fetch_unknown_returns_none(provider):
    assert provider.fetch("not_an_id") is None


# ---------------------------------------------------------------------------
# 3. Edge traversal
# ---------------------------------------------------------------------------

def test_store_edge_and_neighbors_default_relation(provider):
    a = Morphon.forge(payload={"x": 1})
    b = Morphon.forge(payload={"x": 2})
    provider.store(a)
    provider.store(b)
    provider.store_edge(a.id, b.id, relation="follows")

    assert provider.neighbors(a.id) == [b.id]


def test_store_edge_filtered_by_relation(provider):
    a = Morphon.forge(payload={"x": 1})
    b = Morphon.forge(payload={"x": 2})
    c = Morphon.forge(payload={"x": 3})
    provider.store(a)
    provider.store(b)
    provider.store(c)
    provider.store_edge(a.id, b.id, relation="follows")
    provider.store_edge(a.id, c.id, relation="references")

    assert provider.neighbors(a.id, relation="follows") == [b.id]
    assert provider.neighbors(a.id, relation="references") == [c.id]
    assert set(provider.neighbors(a.id)) == {b.id, c.id}


def test_edge_weight_orders_neighbors_descending(provider):
    a = Morphon.forge(payload={"x": 1})
    b = Morphon.forge(payload={"x": 2})
    c = Morphon.forge(payload={"x": 3})
    provider.store(a)
    provider.store(b)
    provider.store(c)
    provider.store_edge(a.id, b.id, relation="follows", weight=0.5)
    provider.store_edge(a.id, c.id, relation="follows", weight=0.9)

    # c (higher weight) ranks before b
    assert provider.neighbors(a.id, relation="follows") == [c.id, b.id]


def test_neighbors_of_unknown_is_empty(provider):
    assert provider.neighbors("not_an_id") == []


def test_store_edge_replace_updates_weight(provider):
    a = Morphon.forge(payload={"x": 1})
    b = Morphon.forge(payload={"x": 2})
    provider.store(a)
    provider.store(b)
    provider.store_edge(a.id, b.id, relation="follows", weight=0.3)
    provider.store_edge(a.id, b.id, relation="follows", weight=0.9)
    # Both with same relation — second call replaces. Still one entry.
    assert provider.neighbors(a.id) == [b.id]


# ---------------------------------------------------------------------------
# 4. by_e8_coordinates
# ---------------------------------------------------------------------------

def test_by_e8_coordinates_exact_match(provider):
    m = Morphon.forge(payload={"k": "v"})
    m.e8_coordinates = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
    provider.store(m)

    matches = provider.by_e8_coordinates(
        (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8), radius=0.0
    )
    assert len(matches) == 1
    assert matches[0].id == m.id


def test_by_e8_coordinates_radius_filter(provider):
    near = Morphon.forge(payload={"label": "near"})
    near.e8_coordinates = (0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    far = Morphon.forge(payload={"label": "far"})
    far.e8_coordinates = (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    provider.store(near)
    provider.store(far)

    # Search around origin with radius 0.5 — only `near` matches.
    matches = provider.by_e8_coordinates(
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), radius=0.5
    )
    assert len(matches) == 1
    assert matches[0].id == near.id


def test_by_e8_coordinates_skips_morphons_without_coords(provider):
    m = Morphon.forge(payload={"k": "v"})  # no e8_coordinates
    provider.store(m)

    matches = provider.by_e8_coordinates(
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), radius=1.0
    )
    assert matches == []


# ---------------------------------------------------------------------------
# 5. ETP delegation + fallback parity
# ---------------------------------------------------------------------------

def test_encode_to_etp_fallback_when_symbolic_unregistered(provider):
    m = Morphon.forge(payload={"k": "v"})
    program = provider.encode_to_etp(m)
    assert isinstance(program, str)
    assert all(c in "}<>+01" for c in program)


def test_encode_to_etp_delegates_when_symbolic_registered(provider):
    symbolic = TarPitSymbolicProvider()
    MorphonController.get().register("symbolic", symbolic)
    m = Morphon.forge(payload={"k": "v"})
    via_provider = provider.encode_to_etp(m)
    via_symbolic = symbolic.encode_to_etp(m)
    assert via_provider == via_symbolic


def test_encode_to_etp_fallback_parity_with_symbolic(provider):
    """Fallback encoder produces the same output as TarPitSymbolicProvider."""
    symbolic = TarPitSymbolicProvider(program_length=32)
    m = Morphon.forge(payload={"k": "v"})

    fallback = provider.encode_to_etp(m)  # no symbolic registered
    assert fallback == symbolic.encode_to_etp(m)


def test_decode_from_etp_empty_returns_marker(provider):
    m = provider.decode_from_etp([])
    assert m.payload == {"etp_decode": "empty_ledger"}


def test_decode_from_etp_captures_final_row(provider):
    symbolic = TarPitSymbolicProvider(default_max_steps=50)
    result = symbolic.run_program("}0}1>")
    decoded = provider.decode_from_etp(result["ledger"])
    assert decoded.payload["etp_decode"] is True


# ---------------------------------------------------------------------------
# 6. Health + lifecycle
# ---------------------------------------------------------------------------

def test_health_reports_count_after_inserts(provider):
    m1 = Morphon.forge(payload={"k": "v1"})
    m2 = Morphon.forge(payload={"k": "v2"})
    provider.store(m1)
    provider.store(m2)
    assert provider.health["morphon_count"] == 2


def test_extensions_initialized_after_first_edge_call(provider):
    a = Morphon.forge(payload={"x": 1})
    b = Morphon.forge(payload={"x": 2})
    provider.store(a)
    provider.store(b)
    assert provider.health["extensions_initialized"] is False
    provider.store_edge(a.id, b.id, relation="follows")
    assert provider.health["extensions_initialized"] is True
