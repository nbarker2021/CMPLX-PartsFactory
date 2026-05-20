"""
VideoCarrier — stub.

Planned behavior:
  - encode(morphon) renders N pixel blocks across time, rotating the
    E8 coordinates through 4 toroidal modes (poloidal/toroidal/
    meridional/helical → EM/Weak/Strong/Gravity dispatch from GVS).
  - decode(frame) recovers the static identity bits plus the rotation
    mode that was active at frame[0].

For now: NotImplementedError on encode/decode. The class exists so
upstream code can register a placeholder and the DAG can show the
intent.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from cmplx.transport.carrier import Carrier, CarrierFrame

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


@dataclass(frozen=True)
class VideoFrame(CarrierFrame):
    """CarrierFrame for video transmission.

    `frame_count` and `fps` describe the time axis. `payload_bytes`
    will be the concatenated RGB-block sequence.
    """
    frame_count: int = 0
    fps: int = 24


class VideoCarrier(Carrier):
    name = "video"

    def encode(self, morphon: "Morphon") -> VideoFrame:
        raise NotImplementedError(
            "VideoCarrier is a stub. The implementation requires "
            "cmplx.geometry.toroidal (planned, from GVS)."
        )

    def decode(self, frame: CarrierFrame) -> dict[str, Any]:
        raise NotImplementedError(
            "VideoCarrier.decode is a stub. See encode() for context."
        )
