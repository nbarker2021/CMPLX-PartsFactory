"""
Carrier — the abstract base for any signaling medium that encodes a
morphon as a transmittable artifact.

The architectural insight from CQE-GVS: a morphon's identity is
carrier-agnostic. The same morphon can be encoded as:
  - DTMF audio tones (the original chirp form)
  - Pixel blocks via CRT-rail E8 → RGB
  - Video frames via toroidal flow + GVS rendering
  - Voice readout (numbers-station style — digits + agent signoff)
  - Geometric glyphs via ALENA's 3-6-9 projection snap

Every carrier is **lossless** by construction: the morphon's identity
(its E8 coordinates, channel, leech point) round-trips through the
carrier without information loss. This is the property the GVS
extract_e8_from_frame() function proves; the same property holds for
audio decoding, voice decoding, etc.

The carrier abstraction lets the same morphon flow through multiple
mediums simultaneously — a state broadcast can be audible to humans
(DTMF), visible (pixel), and machine-readable (numbers station) all
at the same time.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


@dataclass(frozen=True)
class CarrierFrame:
    """The encoded form of a morphon through ONE carrier.

    Subclasses (DTMFFrame, PixelFrame, etc.) extend with carrier-
    specific fields. The base contract is:

      - `carrier_name`: which carrier produced this frame
      - `morphon_id`: identity so a receiver can correlate
      - `channel`: the morphon's DR channel (1-9)
      - `payload_bytes`: the carrier-rendered form (audio bytes,
        pixel array bytes, voice script bytes, etc.)
    """
    carrier_name: str
    morphon_id: str
    channel: int
    payload_bytes: bytes


class Carrier(ABC):
    """A signaling medium. Encodes a morphon to a CarrierFrame, and
    decodes a CarrierFrame back to a partial morphon (identity +
    cached projections; payload itself lives in MMDB).

    Carriers register themselves on the `transport` port of
    `MorphonController` (multiple carriers can coexist; see
    CarrierRegistry).
    """

    #: Stable name. Used to identify the carrier in CarrierFrame.
    name: str = "unnamed_carrier"

    @abstractmethod
    def encode(self, morphon: "Morphon") -> CarrierFrame:
        """Produce a CarrierFrame for this morphon."""

    @abstractmethod
    def decode(self, frame: CarrierFrame) -> dict[str, Any]:
        """Inverse of `encode` — extract identifying fields and any
        cached projections from a CarrierFrame.

        Returns a dict at minimum containing `morphon_id` and
        `channel`. Carrier-specific extras (recovered E8 coords,
        leech point bytes, etc.) go in additional keys.
        """

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"


class CarrierRegistry:
    """Holds multiple registered carriers. Used as the provider on the
    `transport` port when a deployment wants more than one carrier
    available simultaneously.

    >>> reg = CarrierRegistry()
    >>> reg.register(DTMFCarrier())
    >>> reg.register(PixelCarrier())
    >>> MorphonController.get().register("transport", reg)

    The morphon controller's `encode(morphon)` is then ambiguous
    (which carrier?) — callers go through the registry explicitly:

    >>> reg = MorphonController.get().get_provider("transport")
    >>> audio_frame = reg.get("dtmf").encode(morphon)
    >>> pixel_frame = reg.get("pixel").encode(morphon)
    """

    def __init__(self) -> None:
        self._carriers: dict[str, Carrier] = {}

    def register(self, carrier: Carrier) -> None:
        if not isinstance(carrier, Carrier):
            raise TypeError(f"expected Carrier, got {type(carrier).__name__}")
        if carrier.name in self._carriers:
            raise RuntimeError(f"carrier {carrier.name!r} already registered")
        self._carriers[carrier.name] = carrier

    def get(self, name: str) -> Carrier:
        if name not in self._carriers:
            raise LookupError(
                f"no carrier {name!r} registered "
                f"(available: {sorted(self._carriers)})"
            )
        return self._carriers[name]

    def has(self, name: str) -> bool:
        return name in self._carriers

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._carriers))

    # --- TransportProvider protocol satisfaction ----------------------
    # If only one carrier is registered, `encode` works directly. If
    # multiple, this raises and the caller must dispatch explicitly.

    def encode(self, morphon: "Morphon") -> CarrierFrame:
        """Encode using the only registered carrier, or raise if
        ambiguous. For multi-carrier dispatch use `get(name).encode()`.
        """
        if not self._carriers:
            raise LookupError("no carriers registered")
        if len(self._carriers) > 1:
            raise RuntimeError(
                f"multiple carriers registered ({sorted(self._carriers)}); "
                f"dispatch explicitly via .get(name).encode(morphon)"
            )
        (carrier,) = self._carriers.values()
        return carrier.encode(morphon)

    def __repr__(self) -> str:
        return f"<CarrierRegistry carriers={sorted(self._carriers)}>"
