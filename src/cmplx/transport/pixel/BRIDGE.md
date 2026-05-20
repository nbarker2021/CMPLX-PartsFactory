# pixel — Bridge

## Port provided

`PixelCarrier` registers on the `transport` port of
`MorphonController` — either directly (if it's the only carrier) or
inside a `CarrierRegistry` alongside `DTMFCarrier`.

## Ports consumed

**None** at runtime. All inputs come through the `Morphon` passed to
`encode`.

## Static imports

| Imports from | What | Why |
|---|---|---|
| `cmplx.transport.carrier` | `Carrier`, `CarrierFrame` | The base contract every carrier satisfies. |
| `cmplx.geometry.leech` | `LEECH_PREFIX` | To extract the first byte of the leech point hex (mirror of DTMF lower_word). |

The carrier is **lossless for identity fields**: encode → decode
round-trips channel (1-9), the 8 E8 sign bits, and the leech first
byte exactly. Full payload restoration is not the carrier's job —
that's MMDB by morphon_id.
