"""
Chirp — DTMF audio carrier for morphons.

This module now implements ONE carrier (DTMF audio) within the
broader `cmplx.transport` carrier framework introduced in
`cmplx/transport/carrier.py`. The original `Chirp` class is retained
for backward compatibility; new code should use `DTMFCarrier`.

See:
  - `cmplx/transport/carrier.py` for the Carrier ABC + Registry.
  - `cmplx/transport/pixel/` for the pixel/image carrier (GVS pattern).
  - `cmplx/transport/chirp/INTERFACE.md` and `BRIDGE.md` for this
    carrier's contract.

The original DTMF tone-pair + 8-bit upper + 8-bit lower structure is
preserved exactly. What changed is that DTMF is now framed as one
implementation of the universal carrier pattern, not the only one.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from cmplx.geometry.leech import LEECH_PREFIX
from cmplx.transport.carrier import Carrier, CarrierFrame
from .carriers import DTMF_CARRIERS, carrier_for_channel

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


# ---------------------------------------------------------------------------
# ChirpFrame — structured form of an encoded chirp
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChirpFrame:
    """The encoded representation of a morphon as a chirp.

    Carries:
        - channel: 1-9 DR channel
        - low_hz, high_hz: DTMF carrier frequency pair
        - upper_word: 8 bits derived from E8 coords (signs)
        - lower_word: 8 bits derived from Leech-point hex
        - morphon_id: identity so a receiver can correlate back
    """
    channel: int
    low_hz: int
    high_hz: int
    upper_word: int      # 0..255
    lower_word: int      # 0..255
    morphon_id: str

    def __post_init__(self) -> None:
        if not 1 <= self.channel <= 9:
            raise ValueError(f"channel out of range: {self.channel}")
        if not 0 <= self.upper_word <= 255:
            raise ValueError(f"upper_word out of range: {self.upper_word}")
        if not 0 <= self.lower_word <= 255:
            raise ValueError(f"lower_word out of range: {self.lower_word}")

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "low_hz": self.low_hz,
            "high_hz": self.high_hz,
            "upper_word": self.upper_word,
            "lower_word": self.lower_word,
            "morphon_id": self.morphon_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ChirpFrame":
        return cls(**d)


# ---------------------------------------------------------------------------
# Encoding / decoding
# ---------------------------------------------------------------------------

def _upper_word_from_e8(coords: tuple[float, ...]) -> int:
    """8 bits, MSB first: bit_i = 1 if coords[i] >= 0 else 0."""
    if len(coords) != 8:
        raise ValueError(f"E8 coords must have length 8, got {len(coords)}")
    word = 0
    for i, c in enumerate(coords):
        if c >= 0:
            word |= 1 << (7 - i)
    return word


def _lower_word_from_superperm(morphon_id: str, *, index: int = 0) -> int:
    """8 bits from SUPERPERM_N4 phase at cursor (optional chirp lower word)."""
    from cmplx.primitives.superperm import phase_at

    phase = phase_at(index) % 16
    return (hash(morphon_id) & 0xF0) | phase


def _lower_word_from_leech(leech_point: str) -> int:
    """8 bits: int of the first 2 hex chars after the LEECH_PREFIX."""
    if not leech_point.startswith(LEECH_PREFIX):
        raise ValueError(f"leech_point lacks prefix {LEECH_PREFIX!r}")
    hex_part = leech_point[len(LEECH_PREFIX):]
    if len(hex_part) < 2:
        raise ValueError(f"leech_point hex too short: {leech_point}")
    return int(hex_part[:2], 16)


def encode_frame(morphon: "Morphon", *, lower_word_mode: str = "leech") -> ChirpFrame:
    """Pure morphon → ChirpFrame conversion.

    Requires the morphon's projections to be available. If `dr_channel`,
    `e8_coordinates`, or `leech_point` are missing, calls the morphon's
    project_* methods (which themselves go through the bridge — so
    the relevant providers must be registered).
    """
    if morphon.dr_channel is None:
        morphon.project_to_channel()
    if morphon.e8_coordinates is None:
        morphon.project_to_e8()
    if morphon.leech_point is None:
        morphon.project_to_leech()

    channel = morphon.dr_channel
    low_hz, high_hz = carrier_for_channel(channel)
    upper = _upper_word_from_e8(morphon.e8_coordinates)
    if lower_word_mode == "superperm":
        lower = _lower_word_from_superperm(morphon.id)
    else:
        lower = _lower_word_from_leech(morphon.leech_point)

    return ChirpFrame(
        channel=channel,
        low_hz=low_hz,
        high_hz=high_hz,
        upper_word=upper,
        lower_word=lower,
        morphon_id=morphon.id,
    )


def decode_frame(frame: ChirpFrame) -> dict:
    """Inverse: extract the identifying fields from a frame.

    Returns a dict with the morphon_id, channel, and the 4-bit prefixes
    of upper/lower words (the high nybble of each). Full restoration of
    a morphon requires the receiver to fetch from MMDB by id — chirp
    transmits identity + a few salient bits, not the whole payload.
    """
    return {
        "morphon_id": frame.morphon_id,
        "channel": frame.channel,
        "upper_word": frame.upper_word,
        "lower_word": frame.lower_word,
        "e8_sign_bits": [(frame.upper_word >> (7 - i)) & 1 for i in range(8)],
        "leech_first_byte": frame.lower_word,
        "low_hz": frame.low_hz,
        "high_hz": frame.high_hz,
    }


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

class Chirp:
    """Stateless chirp transport provider. Register on the `transport` port.

    >>> from cmplx.morphon import MorphonController
    >>> from cmplx.transport.chirp import Chirp
    >>> MorphonController.get().register("transport", Chirp())
    """

    def encode(self, morphon: "Morphon") -> ChirpFrame:
        return encode_frame(morphon)

    def decode(self, frame: ChirpFrame) -> dict:
        return decode_frame(frame)


# ---------------------------------------------------------------------------
# DTMFCarrier — the Carrier-framework form of chirp
# ---------------------------------------------------------------------------

class DTMFCarrier(Carrier):
    """DTMF audio carrier. Wraps `encode_frame` / `decode_frame` under
    the universal `Carrier` protocol so chirp can sit alongside pixel,
    video, and voice carriers on the `transport` port.

    The payload bytes are a JSON serialization of the `ChirpFrame` —
    enough to reconstruct the DTMF tone-pair, both 8-bit words, and the
    morphon_id at the receiver. Rendering to actual audio samples is a
    separate concern (see `cmplx.transport.chirp.audio`, planned).
    """

    name = "dtmf"

    def encode(self, morphon: "Morphon") -> CarrierFrame:
        frame = encode_frame(morphon)
        payload = json.dumps(frame.to_dict()).encode("utf-8")
        return CarrierFrame(
            carrier_name=self.name,
            morphon_id=frame.morphon_id,
            channel=frame.channel,
            payload_bytes=payload,
        )

    def decode(self, frame: CarrierFrame) -> dict[str, Any]:
        if frame.carrier_name != self.name:
            raise ValueError(
                f"DTMFCarrier cannot decode frame from carrier "
                f"{frame.carrier_name!r}"
            )
        data = json.loads(frame.payload_bytes.decode("utf-8"))
        chirp_frame = ChirpFrame.from_dict(data)
        return decode_frame(chirp_frame)
