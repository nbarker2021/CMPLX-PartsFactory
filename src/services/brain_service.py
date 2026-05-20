"""Compatibility entrypoint for the CMPLX cognition brain HTTP service."""
from __future__ import annotations

from cmplx.cognition.brain.service import (
    BrainBridgeStubs,
    BrainHTTPService,
    BridgeStub,
    create_app,
)

app = create_app()

__all__ = [
    "BrainBridgeStubs",
    "BrainHTTPService",
    "BridgeStub",
    "app",
    "create_app",
]
