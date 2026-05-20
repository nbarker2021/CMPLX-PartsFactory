# pixel — Interface

A `Carrier` that encodes a morphon as an RGB pixel block via the
CRT-rail (3/6/9) projection pattern from the historical CQE-GVS
system. The encoding is **lossless** with respect to the morphon's
identity (channel, E8 sign bits, leech first byte) — running
`decode(encode(m))` recovers the same fields that `DTMFCarrier.decode`
would yield.

## Surface

### `class PixelFrame(CarrierFrame)`
Adds `width: int`, `height: int`. The `payload_bytes` are the raw
8-bit-per-channel RGB pixels in row-major order (length =
`width * height * 3`).

### `class PixelCarrier(Carrier)`
- `name = "pixel"`
- `encode(morphon) -> PixelFrame`: produces an 8×8 RGB block where:
  - Red rail (channel = 3): channel bits packed across the top row.
  - Green rail (channel = 6): E8 sign bits across the middle rows.
  - Blue rail (channel = 9): leech first byte across the bottom rows.
- `decode(frame) -> dict`: extracts `morphon_id`, `channel`,
  `e8_sign_bits`, `leech_first_byte`.

The 8×8 size is fixed (one row per E8 dimension; one block per rail).
The block is reproducible — same morphon always renders to the same
pixel buffer.

## What's NOT in this layer

- Image file I/O (PNG/JPEG): handled by callers via Pillow or stdlib.
- Multi-block tiling for larger morphon collections: a separate
  `PixelTile` composer (planned).
- Sub-pixel anti-aliasing / dithering — every pixel is a flat 8-bit
  rail value.
