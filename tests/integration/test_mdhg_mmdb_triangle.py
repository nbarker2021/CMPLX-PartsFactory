"""Triangle spine: MDHG addressing + MMDB memory via MorphonController."""
from __future__ import annotations

import pytest

from cmplx.addressing.mdhg import MDHGAddressingProvider
from cmplx.memory.mmdb import MMDBMemoryProvider
from cmplx.morphon import Morphon, MorphonController


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_mdhg_mmdb_channel_round_trip_via_controller():
    ctrl = MorphonController.get()
    ctrl.register("addressing", MDHGAddressingProvider())
    mem = MMDBMemoryProvider(":memory:")
    ctrl.register("memory", mem)
    try:
        m = Morphon.forge(payload={"triangle": "spine"})
        stored = ctrl.store(m)
        assert stored.dr_channel is not None
        assert 1 <= stored.dr_channel <= 9

        loaded = ctrl.fetch_required(m.id)
        assert loaded.dr_channel == stored.dr_channel

        by_ch = list(mem._db.find_by_channel(stored.dr_channel))
        assert any(x.id == m.id for x in by_ch)
    finally:
        mem.close()


def test_hierarchical_address_on_provider():
    prov = MDHGAddressingProvider()
    m = Morphon.forge(payload={"k": "v"})
    hx, ch, reg, triad = prov.hierarchical_address(m)
    assert len(hx) == 64
    assert 1 <= ch <= 9
    assert isinstance(reg, str)
    assert isinstance(triad, str)
