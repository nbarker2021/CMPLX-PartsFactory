# chirp — Bridge

## Port provided

`transport` on `MorphonController`. Implements:

```python
class TransportProvider(Protocol):
    def encode(self, morphon: Morphon) -> ChirpFrame: ...
```

(The protocol declares `bytes` as the return type; we return a
`ChirpFrame` dataclass which is structurally what bytes would render.
A future audio-rendering wrapper can be added without changing the
port contract.)

## Provider class

`Chirp` from `cmplx.transport.chirp`. Stateless.

## Ports consumed

| Port | Provider | Why |
|---|---|---|
| `addressing` | `cmplx.addressing.mdhg` | To compute the morphon's DR channel if not cached. |
| `geometry` | `cmplx.geometry` | To compute E8 coordinates and Leech point if not cached. |

Both are *soft* consumes — if the morphon already has the cached
projections (`dr_channel`, `e8_coordinates`, `leech_point`), chirp
uses those directly. The ports are only invoked when projections are
missing. This is the same lazy pattern morphon's own projection
methods use; chirp benefits without coupling tightly.

## Static imports (not runtime ports)

`Chirp` imports `Channel` and `Triad` enums and `DTMF_CARRIERS`
constants from `cmplx.addressing.mdhg`. These are *types and
constants*, not operations — Python-level imports, not port-level
bridges. The first instance of the cross-component static import
pattern surfaced in the DAG's earlier analysis.

## How to wire up

```python
from cmplx.morphon import MorphonController
from cmplx.addressing.mdhg import MDHG
from cmplx.geometry import Geometry
from cmplx.transport.chirp import Chirp

mc = MorphonController.get()
mc.register("addressing", MDHG())
mc.register("geometry", Geometry())
mc.register("transport", Chirp())
```

## Test fixtures

Tests verify:

- Encoding a morphon produces a frame with channel ∈ 1-9.
- Carrier frequencies match the DTMF grid for the channel.
- Upper word is 8 bits, derived from the morphon's E8 coord signs.
- Lower word is 8 bits, derived from the leech encoding.
- Decoding round-trips (identity preserved).
- A morphon with pre-cached projections doesn't re-invoke the
  addressing / geometry providers.
- A morphon without pre-cached projections triggers the providers.
- Two morphons with identical payload produce identical chirp frames.
