"""Bootstrap: symbolic port registers TarPit provider."""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from cmplx.symbolic.tarpit import TarPitSymbolicProvider


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_bootstrap_symbolic_port_registers():
    from runtime.cmplx_bootstrap import register_all

    register_all()
    prov = MorphonController.get().get_provider("symbolic")
    assert prov is not None
    assert isinstance(prov, TarPitSymbolicProvider)
