"""Hash-lanes port tests (slot-16)."""
from __future__ import annotations

import pytest

from cmplx.addressing.mdhg import MDHGAddressingProvider
from cmplx.hash_lanes import HashLanesProvider
from cmplx.morphon import Morphon, MorphonController
from cmplx.routing.provider import AGRMRoutingProvider


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_lane_for_uses_addressing():
    ctrl = MorphonController.get()
    ctrl.register("addressing", MDHGAddressingProvider())
    ctrl.register("routing", AGRMRoutingProvider())
    lanes = HashLanesProvider()
    m = Morphon.forge(payload={"item": "lane-test"})
    lane = lanes.lane_for(m)
    assert 1 <= lane["dr_channel"] <= 9
    assert len(lane["lane_id"]) == 32
    assert lane["hash_hex"]


def test_tour_plan_wires_routing_and_lanes():
    ctrl = MorphonController.get()
    ctrl.register("addressing", MDHGAddressingProvider())
    ctrl.register("routing", AGRMRoutingProvider())
    lanes = HashLanesProvider()
    cities = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    plan = lanes.tour_plan(cities)
    assert plan["status"] == "ok"
    assert plan["hop_count"] >= 2
    assert plan["routing"]["status"] == "ok"
    for hop in plan["hops"]:
        assert "lane_id" in hop
        assert "dr_channel" in hop
