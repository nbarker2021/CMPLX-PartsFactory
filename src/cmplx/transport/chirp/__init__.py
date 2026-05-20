"""
cmplx.transport.chirp — DTMF audio carrier for morphons.

One implementation of the broader `cmplx.transport.carrier` framework.
See INTERFACE.md and BRIDGE.md alongside this package.
"""
from __future__ import annotations

from .chirp import (
    Chirp,
    ChirpFrame,
    DTMFCarrier,
    encode_frame,
    decode_frame,
)
from .carriers import DTMF_CARRIERS, carrier_for_channel

__all__ = [
    "Chirp",
    "ChirpFrame",
    "DTMFCarrier",
    "encode_frame",
    "decode_frame",
    "DTMF_CARRIERS",
    "carrier_for_channel",
]
