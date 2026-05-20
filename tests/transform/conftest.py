"""Shared fixtures for cmplx.transform tests."""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from cmplx.transform.bridge import reset_bootstrap_state


@pytest.fixture(autouse=True)
def _reset_controller_and_bootstrap():
    MorphonController.reset_for_tests()
    reset_bootstrap_state()
    yield
    MorphonController.reset_for_tests()
    reset_bootstrap_state()
