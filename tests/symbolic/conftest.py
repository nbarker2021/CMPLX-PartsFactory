"""Shared fixtures for TarPit HTTP tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cmplx.symbolic.tarpit._adapters import http_service


@pytest.fixture
def fresh_provider():
    return http_service.reset_provider()


@pytest.fixture
def client(fresh_provider):
    return TestClient(http_service.app)
