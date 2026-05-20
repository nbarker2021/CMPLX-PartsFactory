"""
cmplx.transport.numbers_station — NumbersStationCarrier stub.

A `Carrier` that will encode a morphon as a spoken-digit readout in
the numbers-station style: the channel + 8 E8 sign bits + leech first
byte rendered as a sequence of digits, plus an agent signoff naming
the morphon by id.

Voice synthesis itself is delegated; this carrier produces the
**script** (the text to be spoken). Audio rendering is downstream.
"""
from __future__ import annotations

from .station import NumbersStationCarrier, NumbersStationFrame

__all__ = ["NumbersStationCarrier", "NumbersStationFrame"]
