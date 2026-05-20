"""
DTMF carrier frequencies for the 9 chirp channels.

The 9 channels map to the standard DTMF 3×3 grid (keypad 1-9), which
lets chirp transport ride over telephony-grade infrastructure for free.
The frequency pairs are exact DTMF rows × columns.

`DTMF_CARRIERS` is keyed by `Channel` enum value (int 1-9) and returns
`(low_hz, high_hz)`.

Imports `Channel` and `Triad` from `cmplx.addressing.mdhg` — these are
shared structural types, not runtime ports. The cross-import is by
design (see `BRIDGE.md`).
"""
from __future__ import annotations

from cmplx.addressing.mdhg import Channel, Triad


# DTMF row frequencies (low) — keyed by triad of the channel.
_ROW_HZ = {
    Triad.LOW: 697,
    Triad.MID: 770,
    Triad.HIGH: 852,
}

# DTMF column frequencies (high) — keyed by channel position within its triad.
# Channels 1, 4, 7 are column 1 (1209 Hz); 2, 5, 8 are column 2 (1336 Hz);
# 3, 6, 9 are column 3 (1477 Hz).
_COL_HZ = {
    1: 1209, 4: 1209, 7: 1209,
    2: 1336, 5: 1336, 8: 1336,
    3: 1477, 6: 1477, 9: 1477,
}


def _triad_for_channel(channel_int: int) -> Triad:
    if channel_int <= 3:
        return Triad.LOW
    if channel_int <= 6:
        return Triad.MID
    return Triad.HIGH


def carrier_for_channel(channel_int: int) -> tuple[int, int]:
    """Return (low_hz, high_hz) for an int channel 1-9."""
    if channel_int not in _COL_HZ:
        raise ValueError(f"channel out of range: {channel_int} (expected 1-9)")
    low = _ROW_HZ[_triad_for_channel(channel_int)]
    high = _COL_HZ[channel_int]
    return low, high


# Materialized map for callers that want the table directly.
DTMF_CARRIERS: dict[int, tuple[int, int]] = {
    ch: carrier_for_channel(ch) for ch in range(1, 10)
}
