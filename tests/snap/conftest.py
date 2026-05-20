"""Shared fixtures for SNAP HTTP tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cmplx.snap._adapters import http_service


@pytest.fixture
def fresh_engine():
    return http_service.reset_engine()


@pytest.fixture
def client(fresh_engine):
    return TestClient(http_service.app)
