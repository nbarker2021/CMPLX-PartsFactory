from __future__ import annotations

from cmplx.symbolic.tarpit.mdhg_bridge import bind_tape_cell, route_tape_cell
from cmplx.symbolic.tarpit.mdhg_tape import TarpitMDHGTape


def test_route_tape_cell_has_full_address():
    r = route_tape_cell({"glyph": "α", "tags": ["tarpit"]})
    assert r["mdhg_address"]
    assert r["planet_id"]


def test_bind_tape_cell_writes_routing():
    tape = TarpitMDHGTape()
    out = bind_tape_cell(tape, {"glyph": "β"}, position=("planet_0", 3))
    assert out["routing"]["mdhg_address"]
    cell = tape.read_cell(("planet_0", 3))
    assert cell.get("mdhg_address")
