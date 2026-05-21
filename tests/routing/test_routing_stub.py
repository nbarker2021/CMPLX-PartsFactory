"""AGRM routing stub — channel via MDHG addressing."""
from __future__ import annotations

import pytest

from cmplx.addressing.mdhg import MDHGAddressingProvider
from cmplx.morphon import Morphon, MorphonController
from cmplx.routing.provider import AGRMRoutingProvider


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_routing_stub_uses_addressing_channel():
    ctrl = MorphonController.get()
    ctrl.register("addressing", MDHGAddressingProvider())
    routing = AGRMRoutingProvider()
    ctrl.register("routing", routing)
    m = Morphon.forge(payload={"route": 1})
    assert routing.route_channel(m) == ctrl.get_provider("addressing").channel_for(m)


def test_solve_nearest_neighbor_tour():
    routing = AGRMRoutingProvider()
    cities = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    out = routing.solve(cities)
    assert out["status"] == "ok"
    assert out["mode"] == "nearest_neighbor"
    assert len(out["tour"]) == len(cities) + 1
    assert out["tour"][0] == out["tour"][-1]
    assert out["cost"] > 0


def test_solve_staging_status_in_result():
    routing = AGRMRoutingProvider()
    out = routing.solve([(0.0, 0.0), (2.0, 0.0)])
    assert "staging" in out
    assert "loaded" in out["staging"]
