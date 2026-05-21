"""W1: crystal port registers via register_all and composes with snap."""
from __future__ import annotations

import pytest

from cmplx.crystal import CrystalRegistry
from cmplx.morphon import MorphonController
from cmplx.transform.bridge import reset_bootstrap_state
from runtime.cmplx_bootstrap import register_all


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    reset_bootstrap_state()
    yield
    MorphonController.reset_for_tests()
    reset_bootstrap_state()


def test_register_all_wires_crystal_port():
    status = register_all()
    ctrl = MorphonController.get()
    assert ctrl.has("crystal")
    assert status["crystal"] == "registered (in-process)"
    assert isinstance(ctrl.get_provider("crystal"), CrystalRegistry)


def test_crystal_create_after_bootstrap():
    register_all()
    reg = MorphonController.get().get_provider("crystal")
    c = reg.create(name="w1-smoke")
    assert c.name == "w1-smoke"
    assert reg.get(c.crystal_id) is c
