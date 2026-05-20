"""
MDHG — Multi-Dimensional Hash Graph.

The addressing layer for morphons. Each morphon's payload hashes to one
of nine digital-root channels (1-9), organized into three triads of
three: Initiation/Forge/Apex (1-3), Movement/Action/Manifestation (4-6),
Archive/Forge/Reset (7-9).

See INTERFACE.md for the contract and BRIDGE.md for how this plugs into
the morphon controller.

This implementation is hand-built from the design spec. The historical
composed canonical (`_history_reference/composed_mdhg_v3.py`) contained
69 methods across 14 variants; the runnable contract is much smaller.
"""
from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


# ---------------------------------------------------------------------------
# Channel structure
# ---------------------------------------------------------------------------

class Channel(Enum):
    """The nine digital-root channels. Values 1-9."""
    INITIATION = 1
    FORGE = 2
    APEX = 3
    MOVEMENT = 4
    ACTION = 5
    MANIFESTATION = 6
    ARCHIVE = 7
    FORGE_CLOSE = 8
    RESET = 9


class Triad(Enum):
    """Each channel belongs to one of three triads."""
    LOW = "low"      # 1-2-3
    MID = "mid"      # 4-5-6
    HIGH = "high"    # 7-8-9


# Lookup tables — channel int → (Channel name, Triad)
_CHANNEL_BY_INT: dict[int, Channel] = {ch.value: ch for ch in Channel}
_TRIAD_BY_INT: dict[int, Triad] = {
    1: Triad.LOW, 2: Triad.LOW, 3: Triad.LOW,
    4: Triad.MID, 5: Triad.MID, 6: Triad.MID,
    7: Triad.HIGH, 8: Triad.HIGH, 9: Triad.HIGH,
}


# ---------------------------------------------------------------------------
# Digital-root helper
# ---------------------------------------------------------------------------

def digital_root(value: int) -> int:
    """Recursively sum digits of `value` until a single digit 1-9 remains.

    The conventional digital-root maps 0 → 0; we map 0 → 9 here because
    channels are 1-9 (not 0-8). This matches the system's convention of
    treating 9 as "complete cycle" rather than zero.
    """
    if value < 0:
        value = -value
    while value >= 10:
        value = sum(int(d) for d in str(value))
    return value if value > 0 else 9


def digital_root_hex(hex_string: str) -> int:
    """Digital-root of a hex string's content. Each hex char is its 0-15
    digit value; we sum those and reduce."""
    total = 0
    for c in hex_string.lower():
        if c.isdigit():
            total += int(c)
        elif "a" <= c <= "f":
            total += 10 + (ord(c) - ord("a"))
        # ignore non-hex chars
    return digital_root(total)


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

class MDHG:
    """Stateless addressing provider. Hashes a morphon's payload to a
    digital-root channel 1-9.

    Instantiate once at boot and register with `MorphonController` on
    the `addressing` port:

    >>> from cmplx.morphon import MorphonController
    >>> MorphonController.get().register("addressing", MDHG())
    """

    # ------------------------------------------------------------------
    # AddressingProvider protocol
    # ------------------------------------------------------------------

    def channel_for(self, morphon: "Morphon") -> int:
        """Return the digital-root channel (1-9) for this morphon."""
        sha_hex = self._sha256_of_payload(morphon.payload)
        return digital_root_hex(sha_hex)

    # ------------------------------------------------------------------
    # Extended surface
    # ------------------------------------------------------------------

    def hierarchical_address(self, morphon: "Morphon") -> tuple[str, int, str, str]:
        """Return the full address: (sha256_hex, channel, register, triad)."""
        sha_hex = self._sha256_of_payload(morphon.payload)
        channel = digital_root_hex(sha_hex)
        register = _CHANNEL_BY_INT[channel].name
        triad = _TRIAD_BY_INT[channel].value
        return sha_hex, channel, register, triad

    def channel_of(self, channel: int) -> Channel:
        """Convert a channel int to its Channel enum value."""
        if channel not in _CHANNEL_BY_INT:
            raise ValueError(f"channel out of range: {channel} (expected 1-9)")
        return _CHANNEL_BY_INT[channel]

    def triad_of(self, channel: int) -> Triad:
        """Return the triad (LOW/MID/HIGH) that a channel belongs to."""
        if channel not in _TRIAD_BY_INT:
            raise ValueError(f"channel out of range: {channel} (expected 1-9)")
        return _TRIAD_BY_INT[channel]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _sha256_of_payload(payload) -> str:
        """sha256 of a stable JSON serialization of the payload."""
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
