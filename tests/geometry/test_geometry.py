"""
Smoke tests for cmplx.geometry — the E8 + Leech provider.
"""
from __future__ import annotations

import math

import pytest

from cmplx.geometry import Geometry, E8, Leech
from cmplx.geometry.e8 import (
    e8_coordinates_for,
    e8_coordinates_from_payload,
    nearest_root,
    e8_roots,
)
from cmplx.geometry.leech import leech_point_for, LEECH_PREFIX
from cmplx.morphon import Morphon, MorphonController


# ---------------------------------------------------------------------------
# E8 standalone
# ---------------------------------------------------------------------------

def test_e8_coordinates_returns_8_tuple():
    coords = e8_coordinates_from_payload({"k": "v"})
    assert isinstance(coords, tuple)
    assert len(coords) == 8


def test_e8_coordinates_are_floats_in_range():
    coords = e8_coordinates_from_payload({"k": "v"})
    for c in coords:
        assert isinstance(c, float)
        assert -1.001 <= c <= 1.001


def test_e8_coordinates_are_on_unit_sphere():
    coords = e8_coordinates_from_payload({"k": "v"})
    norm_sq = sum(c * c for c in coords)
    # Within a small rounding tolerance of 1.0 (we round to 6 decimal places).
    assert abs(norm_sq - 1.0) < 1e-4


def test_e8_coordinates_deterministic():
    a = e8_coordinates_from_payload({"hello": "world"})
    b = e8_coordinates_from_payload({"hello": "world"})
    assert a == b


def test_e8_coordinates_diverge_on_different_payloads():
    a = e8_coordinates_from_payload({"k": "v"})
    b = e8_coordinates_from_payload({"k": "u"})
    assert a != b


def test_e8_roots_count_is_240():
    roots = e8_roots()
    assert len(roots) == 240
    # All roots have squared length 2
    for r in roots:
        assert abs(sum(x * x for x in r) - 2.0) < 1e-9


def test_nearest_root_returns_a_root():
    coords = e8_coordinates_from_payload({"k": "v"})
    r = nearest_root(coords)
    assert r in e8_roots()


# ---------------------------------------------------------------------------
# Leech standalone
# ---------------------------------------------------------------------------

def test_leech_point_starts_with_prefix():
    p = leech_point_for(Morphon.forge(payload={"k": "v"}))
    assert p.startswith(LEECH_PREFIX)


def test_leech_point_length_is_24_bytes_hex_plus_prefix():
    p = leech_point_for(Morphon.forge(payload={"k": "v"}))
    # 7 chars prefix + 48 hex = 55
    assert len(p) == len(LEECH_PREFIX) + 48


def test_leech_point_deterministic_per_payload():
    m1 = Morphon.forge(payload={"same": "data"})
    m2 = Morphon.forge(payload={"same": "data"})
    assert leech_point_for(m1) == leech_point_for(m2)


# ---------------------------------------------------------------------------
# Bridge integration
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_geometry_plugs_in_as_provider():
    MorphonController.get().register("geometry", Geometry())
    m = Morphon.forge(payload={"hello": "world"})
    coords = m.project_to_e8()
    point = m.project_to_leech()
    assert len(coords) == 8
    assert point.startswith(LEECH_PREFIX)
    # Cached on morphon
    assert m.e8_coordinates == coords
    assert m.leech_point == point


def test_e8_namespace_class():
    assert E8.DIMENSION == 8
    assert E8.KISSING_NUMBER == 240
    coords = E8.coordinates_from_payload({"a": 1})
    assert len(coords) == 8


def test_leech_namespace_class():
    assert Leech.DIMENSION == 24
    assert Leech.PREFIX == "leech::"
    p = Leech.point_from_payload({"a": 1})
    assert p.startswith("leech::")
