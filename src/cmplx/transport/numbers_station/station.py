"""
NumbersStationCarrier — stub.

Planned behavior:
  - encode(morphon) renders a spoken-style script:
      "{agent_name}, channel {channel}, group: {8 digits} {8 digits},
       signoff {morphon_id_short}."
    The 8 digits encode the E8 sign bits as a 0/1 sequence; the
    second 8 digits encode the leech first byte's bits.
  - decode(frame) parses the script back to the identity dict.

The carrier's `payload_bytes` is the UTF-8 script text. A separate
voice-synthesis layer turns this into audio. The pattern preserves
the "lossless for identity bits" property: digits in, digits out.

Current implementation: a working text-only round-trip, so future
voice work can plug in without re-deriving the layout.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from cmplx.geometry.leech import LEECH_PREFIX
from cmplx.transport.carrier import Carrier, CarrierFrame

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


DEFAULT_AGENT = "alena"


@dataclass(frozen=True)
class NumbersStationFrame(CarrierFrame):
    agent_name: str = DEFAULT_AGENT


def _bits_msb_first(byte_val: int, n_bits: int = 8) -> str:
    return "".join(str((byte_val >> (n_bits - 1 - i)) & 1) for i in range(n_bits))


def _bits_from_str(s: str) -> int:
    word = 0
    for i, ch in enumerate(s):
        if ch == "1":
            word |= 1 << (len(s) - 1 - i)
    return word


class NumbersStationCarrier(Carrier):
    name = "numbers_station"

    def __init__(self, agent_name: str = DEFAULT_AGENT) -> None:
        self.agent_name = agent_name

    def encode(self, morphon: "Morphon") -> NumbersStationFrame:
        if morphon.dr_channel is None:
            morphon.project_to_channel()
        if morphon.e8_coordinates is None:
            morphon.project_to_e8()
        if morphon.leech_point is None:
            morphon.project_to_leech()

        upper = 0
        for i, c in enumerate(morphon.e8_coordinates):
            if c >= 0:
                upper |= 1 << (7 - i)
        hex_part = morphon.leech_point[len(LEECH_PREFIX):]
        lower = int(hex_part[:2], 16)

        script = (
            f"{self.agent_name}, channel {morphon.dr_channel}, "
            f"group: {_bits_msb_first(upper)} {_bits_msb_first(lower)}, "
            f"signoff {morphon.id}."
        )
        return NumbersStationFrame(
            carrier_name=self.name,
            morphon_id=morphon.id,
            channel=morphon.dr_channel,
            payload_bytes=script.encode("utf-8"),
            agent_name=self.agent_name,
        )

    def decode(self, frame: CarrierFrame) -> dict[str, Any]:
        if frame.carrier_name != self.name:
            raise ValueError(
                f"NumbersStationCarrier cannot decode frame from carrier "
                f"{frame.carrier_name!r}"
            )
        text = frame.payload_bytes.decode("utf-8")
        # Format: "<agent>, channel <ch>, group: <8 bits> <8 bits>, signoff <id>."
        try:
            agent_part, ch_part, group_part, signoff_part = text.split(", ")
            channel = int(ch_part.removeprefix("channel ").strip())
            bits = group_part.removeprefix("group: ").strip()
            upper_str, lower_str = bits.split(" ")
            upper_word = _bits_from_str(upper_str)
            lower_word = _bits_from_str(lower_str)
            morphon_id = signoff_part.removeprefix("signoff ").rstrip(".")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"malformed numbers-station script: {text!r}") from e

        return {
            "morphon_id": morphon_id,
            "channel": channel,
            "upper_word": upper_word,
            "lower_word": lower_word,
            "e8_sign_bits": [(upper_word >> (7 - i)) & 1 for i in range(8)],
            "leech_first_byte": lower_word,
            "agent_name": agent_part.strip(),
        }
