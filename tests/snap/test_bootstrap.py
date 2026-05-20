"""Bootstrap and matrix-backed checks."""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from cmplx.snap import SNAPEngine


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_bootstrap_snap_port_registers():
    from runtime.cmplx_bootstrap import register_all

    register_all()
    prov = MorphonController.get().get_provider("snap")
    assert prov is not None
    assert isinstance(prov, SNAPEngine)


def test_engine_label_appends_ledger():
    eng = SNAPEngine()
    eng.label({"k": 1}, key="d")
    assert eng.ledger.length == 1
