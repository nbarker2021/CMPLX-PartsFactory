"""cmplx.transport — carrier framework for transmitting morphons.

A morphon's identity is carrier-agnostic; the same morphon can be
encoded as DTMF audio, pixels, video frames, voice readouts, or
geometric glyphs. The `Carrier` ABC defines the contract; concrete
carriers live in subpackages (`chirp` for DTMF, `pixel` for E8→RGB,
etc.).
"""
from __future__ import annotations

from .carrier import Carrier, CarrierFrame, CarrierRegistry
from .provider import TransportProviderFacade

__all__ = ["Carrier", "CarrierFrame", "CarrierRegistry", "TransportProviderFacade"]
