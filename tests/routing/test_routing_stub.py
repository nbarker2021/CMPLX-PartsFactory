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


def test_solve_returns_not_implemented():
    routing = AGRMRoutingProvider()
    out = routing.solve([(0.0, 0.0), (1.0, 1.0)])
    assert out["status"] == "not_implemented"
