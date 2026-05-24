from __future__ import annotations

from lattice_forge.algebra.o1_registry import (
    E8_WEYL_ORDER,
    WEYL_ORDER,
    chart_route_is_o1,
    root_count_ade,
    weyl_order,
)
from lattice_forge.substrate_map import WEYL_ROUTING_TABLE


def test_e8_weyl_order():
    assert E8_WEYL_ORDER == 696_729_600
    assert weyl_order("E8") == E8_WEYL_ORDER


def test_root_count_ade_e8():
    assert root_count_ade("E", 8) == 240


def test_chart_route_table_size():
    assert chart_route_is_o1()
    assert len(WEYL_ROUTING_TABLE) == 8
    assert all(len(row) == 8 for row in WEYL_ROUTING_TABLE)


def test_weyl_order_registry_keys():
    assert WEYL_ORDER["D4"] == 192
    assert WEYL_ORDER["G2"] == 12
