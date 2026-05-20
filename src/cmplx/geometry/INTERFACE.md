# geometry — Interface

The geometry layer provides the lattice projections morphons inhabit:

- **E8** — 8-dimensional dense lattice; every morphon has an E8 vector.
- **Leech** — 24-dimensional even unimodular lattice; embeds three E8 slices.
- **Niemeier** — the 24 even unimodular lattices in dimension 24; alternative
  24-D substrates for different operation symmetries.

This top-level `cmplx.geometry` package exposes a single provider
(`Geometry`) that implements the `geometry` port on `MorphonController`.
The individual sub-packages (`e8/`, `leech/`, `niemeier/`) hold the
math and can be used directly when full lattice operations are needed.

## What this package exposes

| Symbol | Purpose |
|---|---|
| `Geometry` | Provider class implementing `e8_coordinates` and `leech_point`. |
| `cmplx.geometry.e8.E8` | Direct E8 helper — root system, nearest-root, projection. |
| `cmplx.geometry.leech.Leech` | Direct Leech helper — Leech point encoding. |

## Algorithm — hash-based projection

For the geometry port, the projection is **content-addressed**: a
morphon's E8 coordinate and Leech point are deterministic functions of
its payload hash. This matches the `snapdna.py` historical pattern (the
production E8 embedding used by all the unified runtimes).

### E8 coordinates

```
sha256(payload) → 64 hex chars
take first 16 hex (8 bytes)
for each byte: map [0,255] → [-1, 1] via (byte - 128) / 128
normalize to unit sphere (divide by L2 norm)
round to 6 decimal places
return 8-tuple
```

The result is a point on the surface of the 7-sphere in 8-D (the unit
ball's surface). Not strictly an E8 lattice point — but a content-
addressed projection into E8 space. Snapping to the nearest actual
lattice point is an extended operation on `cmplx.geometry.e8.E8`.

### Leech point

```
sha256(payload) → 64 hex chars
take next 48 hex chars (24 bytes)
encode as base16 string with a `leech::` prefix
return string
```

Leech-space encoding is simpler — we use the hash bytes directly as a
24-byte address. Full Leech lattice math (nearest codeword via Golay
correction, etc.) is in `cmplx.geometry.leech` for callers that need it.

## Invariants

1. **Deterministic**: same payload → same coordinates, every time.
2. **Pure**: no morphon mutation.
3. **No external dependencies for the port**: stdlib only (`hashlib`).
4. **Extended operations may require numpy**: `cmplx.geometry.e8.E8`'s
   full root system and nearest-root operations use numpy internally;
   the port itself does not.

## What this package does NOT do

- Doesn't store coordinates (that's `cmplx.memory.mmdb`).
- Doesn't decide *which* Niemeier lattice a morphon belongs to (that's a
  separate operation; the morphon's coefficient table carries that decision).
- Doesn't compute chirp encodings (that's `cmplx.transport.chirp`, which
  consumes geometry).

## How morphon talks to this

Through the `geometry` port:

```python
from cmplx.morphon import MorphonController
from cmplx.geometry import Geometry

MorphonController.get().register("geometry", Geometry())

m = Morphon.forge(payload={"k": "v"})
m.project_to_e8()    # tuple of 8 floats
m.project_to_leech() # leech:: prefixed string
```
