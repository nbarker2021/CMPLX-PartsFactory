"""
PixelCarrier — RGB pixel-block carrier for morphons.

The encoding pattern is from the historical CQE-GVS system: the three
CRT rails (channels 3, 6, 9 in the MDHG taxonomy) are mapped to the
R, G, B planes of an 8x8 pixel block.

Layout of the 8x8 RGB block (row-major):
  - Row 0 (R-rail / channel 3): the morphon's DR channel encoded in
    binary across the 8 pixels (MSB→LSB). For channels 1-9, only the
    bottom 4 bits carry signal; the upper 4 are zero.
  - Rows 1-4 (G-rail / channel 6): the 8 E8 sign bits, two bits per
    row, written as solid 255/0 cells across each row pair.
  - Rows 5-7 (B-rail / channel 9): the 8 bits of the leech first byte,
    distributed across 3 rows × 8 columns (only first 8 cells used).

The layout is intentionally redundant — it gives us slack for visual
recognition and dithered transmission. The decoder only needs the
*first* relevant sample per field, so noise on later rows is fine.

This is lossless for the identity fields: channel, E8 sign bits, and
leech first byte. It is NOT a full-state restoration; the morphon's
payload still lives in MMDB and is fetched by `morphon_id`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from cmplx.geometry.leech import LEECH_PREFIX
from cmplx.transport.carrier import Carrier, CarrierFrame

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


BLOCK_SIZE = 8  # 8x8 RGB block — one cell per E8 dim, one block per rail


# ---------------------------------------------------------------------------
# PixelFrame — CarrierFrame extension with width/height metadata
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PixelFrame(CarrierFrame):
    """CarrierFrame for pixel-block transmission.

    Inherits `carrier_name`, `morphon_id`, `channel`, `payload_bytes`.
    Adds `width` and `height` so a receiver can deserialize the raw
    RGB bytes back into a 2D grid without external metadata.
    """
    width: int = BLOCK_SIZE
    height: int = BLOCK_SIZE


# ---------------------------------------------------------------------------
# Helpers — pure functions on bytes/ints
# ---------------------------------------------------------------------------

def _bits_msb_first(byte_val: int, n_bits: int = 8) -> list[int]:
    return [(byte_val >> (n_bits - 1 - i)) & 1 for i in range(n_bits)]


def _upper_word_from_e8(coords: tuple[float, ...]) -> int:
    word = 0
    for i, c in enumerate(coords):
        if c >= 0:
            word |= 1 << (7 - i)
    return word


def _lower_word_from_leech(leech_point: str) -> int:
    if not leech_point.startswith(LEECH_PREFIX):
        raise ValueError(f"leech_point lacks prefix {LEECH_PREFIX!r}")
    hex_part = leech_point[len(LEECH_PREFIX):]
    if len(hex_part) < 2:
        raise ValueError(f"leech_point hex too short: {leech_point}")
    return int(hex_part[:2], 16)


def _build_block(channel: int, upper_word: int, lower_word: int) -> bytes:
    """Render the 8x8x3 RGB block as raw bytes."""
    pixels = bytearray(BLOCK_SIZE * BLOCK_SIZE * 3)

    # Row 0 — R rail (channel)
    channel_bits = _bits_msb_first(channel, 8)
    for col, bit in enumerate(channel_bits):
        idx = (0 * BLOCK_SIZE + col) * 3
        pixels[idx + 0] = 255 if bit else 0  # R
        # G and B left at 0

    # Rows 1-4 — G rail (E8 sign bits: 8 bits across 4 rows, 2 per row)
    upper_bits = _bits_msb_first(upper_word, 8)
    for k, bit in enumerate(upper_bits):
        row = 1 + (k // 2)
        col_start = (k % 2) * 4
        for col_offset in range(4):
            col = col_start + col_offset
            idx = (row * BLOCK_SIZE + col) * 3
            pixels[idx + 1] = 255 if bit else 0  # G

    # Rows 5-7 — B rail (leech first byte: 8 bits across columns)
    lower_bits = _bits_msb_first(lower_word, 8)
    for row in (5, 6, 7):
        for col, bit in enumerate(lower_bits):
            idx = (row * BLOCK_SIZE + col) * 3
            pixels[idx + 2] = 255 if bit else 0  # B

    return bytes(pixels)


def _read_block(pixels: bytes) -> tuple[int, int, int]:
    """Inverse of `_build_block`. Returns (channel, upper_word, lower_word)."""
    if len(pixels) != BLOCK_SIZE * BLOCK_SIZE * 3:
        raise ValueError(
            f"expected {BLOCK_SIZE * BLOCK_SIZE * 3} pixel bytes, "
            f"got {len(pixels)}"
        )

    # Row 0, R channel — recover the channel
    channel = 0
    for col in range(8):
        idx = (0 * BLOCK_SIZE + col) * 3
        bit = 1 if pixels[idx + 0] >= 128 else 0
        channel |= bit << (7 - col)

    # Rows 1-4, G channel — recover the 8 E8 sign bits
    upper_word = 0
    for k in range(8):
        row = 1 + (k // 2)
        col_start = (k % 2) * 4
        idx = (row * BLOCK_SIZE + col_start) * 3
        bit = 1 if pixels[idx + 1] >= 128 else 0
        upper_word |= bit << (7 - k)

    # Row 5, B channel — recover the leech first byte
    lower_word = 0
    for col in range(8):
        idx = (5 * BLOCK_SIZE + col) * 3
        bit = 1 if pixels[idx + 2] >= 128 else 0
        lower_word |= bit << (7 - col)

    return channel, upper_word, lower_word


# ---------------------------------------------------------------------------
# The Carrier
# ---------------------------------------------------------------------------

class PixelCarrier(Carrier):
    """RGB pixel-block carrier.

    >>> from cmplx.morphon import MorphonController
    >>> from cmplx.transport.pixel import PixelCarrier
    >>> MorphonController.get().register("transport", PixelCarrier())
    """

    name = "pixel"

    def encode(self, morphon: "Morphon") -> PixelFrame:
        if morphon.dr_channel is None:
            morphon.project_to_channel()
        if morphon.e8_coordinates is None:
            morphon.project_to_e8()
        if morphon.leech_point is None:
            morphon.project_to_leech()

        channel = morphon.dr_channel
        upper = _upper_word_from_e8(morphon.e8_coordinates)
        lower = _lower_word_from_leech(morphon.leech_point)

        # Prepend a tiny JSON header so morphon_id survives in the payload
        # (the pixel bytes alone do not carry the id). Header is a single
        # length-prefixed blob; the remaining bytes are the raw RGB block.
        header = json.dumps({"morphon_id": morphon.id}).encode("utf-8")
        header_len = len(header).to_bytes(2, "big")
        block = _build_block(channel, upper, lower)
        payload = header_len + header + block

        return PixelFrame(
            carrier_name=self.name,
            morphon_id=morphon.id,
            channel=channel,
            payload_bytes=payload,
            width=BLOCK_SIZE,
            height=BLOCK_SIZE,
        )

    def decode(self, frame: CarrierFrame) -> dict[str, Any]:
        if frame.carrier_name != self.name:
            raise ValueError(
                f"PixelCarrier cannot decode frame from carrier "
                f"{frame.carrier_name!r}"
            )
        data = frame.payload_bytes
        header_len = int.from_bytes(data[:2], "big")
        header = json.loads(data[2:2 + header_len].decode("utf-8"))
        block = data[2 + header_len:]

        channel, upper_word, lower_word = _read_block(block)

        return {
            "morphon_id": header["morphon_id"],
            "channel": channel,
            "upper_word": upper_word,
            "lower_word": lower_word,
            "e8_sign_bits": _bits_msb_first(upper_word, 8),
            "leech_first_byte": lower_word,
        }
