"""MDHG-backed tape (glyphic_tarpit preview promotion)."""
from __future__ import annotations

from cmplx.symbolic.tarpit.mdhg_tape import MDHGTapeBackend, TarpitMDHGTape


def test_backend_put_get_memory():
    backend = MDHGTapeBackend(":memory:")
    backend.put("planet_0", 0, {"glyph": "α", "value": 1})
    row = backend.get("planet_0", 0)
    assert row is not None
    assert row["payload"]["glyph"] == "α"


def test_tape_write_read():
    tape = TarpitMDHGTape()
    tape.write_cell({"glyph": "β", "tags": ["test"]}, position=("planet_0", 2))
    cell = tape.read_cell(("planet_0", 2))
    assert cell["glyph"] == "β"


def test_tape_move_pointer():
    tape = TarpitMDHGTape()
    tape.pointer = ("planet_0", 5)
    tape.move_pointer(3)
    assert tape.pointer == ("planet_0", 8)
    tape.move_pointer(-10)
    assert tape.pointer[0] == "planet_-1"
