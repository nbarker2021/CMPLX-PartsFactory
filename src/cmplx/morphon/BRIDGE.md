# morphon — Bridge / Controller Contract

This document defines how other components in the unified system
talk to and through the `cmplx.morphon` package. The bridge is
the wiring layer — the manifolds-in-manifolds connective tissue
between components.

Concretely the bridge is exposed by `controller.py` in this
package. Other components depend on the controller's interface,
not on the morphon's internals.

## Why a bridge

If components imported each other directly, the system would
become a tangle of cross-dependencies. With a bridge:

- `cmplx.morphon` declares operations the world can request.
- `cmplx.addressing.mdhg` registers itself as the addressing
  bridge; calls to `morphon.project_to_channel()` route through
  it.
- `cmplx.memory.mmdb` registers itself as the persistence bridge.
- New components can be added without rewriting morphon — they
  just register with the controller.

This matches the historical pattern (the morphonic_pipeline,
lambda_controllers, regression_controller wiring observed in
the REPORT/ documents). We surface that pattern as a first-class
contract instead of leaving it implicit.

## The controller's responsibilities

`MorphonController` is the single entry point for *operating* on
morphons across component boundaries. It:

1. Holds registrations from other components.
2. Routes operations to the right registered handler.
3. Records every operation as a receipt on the morphon's chain.
4. Enforces invariants from `INTERFACE.md` at the boundary.

## Operations the controller mediates

| Operation | Bridge port name | Provider component |
|---|---|---|
| Hash → DR channel | `addressing` | `cmplx.addressing.mdhg` |
| Encode E8 / Leech | `geometry` | `cmplx.geometry.{e8,leech,niemeier}` |
| Encode as chirp | `transport` | `cmplx.transport.chirp` |
| Persist / fetch | `memory` | `cmplx.memory.mmdb` |
| Admit against laws | `constraints` | `cmplx.constraints.aletheia` |
| Evolve payload | `engine` | `cmplx.engine.cqe` |
| Symbolic derive | `symbolic` | `cmplx.symbolic.tarpit` |
| Route through graph | `routing` | `cmplx.routing.agrm` |

For each port:

- Provider component implements a small protocol (see "Provider
  protocols" below).
- Provider calls `MorphonController.register(port, handler)` once
  at boot.
- Operations on a morphon dispatch to the registered handler.

## Provider protocols

Each port has a minimal protocol. Provider components implement
the protocol; the controller adapts it.

### `addressing` port

```python
class AddressingProvider(Protocol):
    def channel_for(self, morphon: Morphon) -> int:
        """Return DR channel 1-9 for this morphon's payload."""
```

### `geometry` port

```python
class GeometryProvider(Protocol):
    def e8_coordinates(self, morphon: Morphon) -> tuple[float, ...]:
        """Return the morphon's 8-D E8 projection."""
    def leech_point(self, morphon: Morphon) -> str:
        """Return the morphon's encoded Leech-lattice point."""
```

### `memory` port

```python
class MemoryProvider(Protocol):
    def store(self, morphon: Morphon) -> None: ...
    def fetch(self, morphon_id: str) -> Morphon | None: ...
```

### `constraints` port

```python
class ConstraintsProvider(Protocol):
    def admit(self, morphon: Morphon) -> tuple[bool, str]:
        """Return (admitted, reason)."""
```

### `engine` port

```python
class EngineProvider(Protocol):
    def evolve(self, morphon: Morphon, op: str, **kw) -> Morphon:
        """Apply a CQE operation, return a new morphon."""
```

(Others omitted for brevity; same shape.)

## How a request flows through

A request to "store this morphon and admit it":

1. User code constructs a morphon via `Morphon.forge(...)`.
2. User code calls `MorphonController.admit_and_store(morphon)`.
3. Controller dispatches:
   a. `constraints.admit(morphon)` — if rejected, raise.
   b. `addressing.channel_for(morphon)` — cache channel on morphon.
   c. `geometry.e8_coordinates(morphon)` — cache E8 coords.
   d. `memory.store(morphon)` — persist.
4. Controller appends a receipt: `("admit_and_store", time, providers_used)`.
5. Return the (now-extended) morphon to the caller.

The user code never imports `mdhg`, `aletheia`, `mmdb` directly.
It interacts with `cmplx.morphon` only.

## Bootstrap

A small registry is initialized at import time:

```python
# in cmplx/morphon/controller.py

from typing import Protocol

class MorphonController:
    _instance: "MorphonController | None" = None

    def __init__(self):
        self._providers: dict[str, object] = {}

    @classmethod
    def get(cls) -> "MorphonController":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, port: str, provider: object) -> None:
        if port in self._providers:
            raise RuntimeError(f"port {port} already registered")
        self._providers[port] = provider

    def has(self, port: str) -> bool:
        return port in self._providers

    def get_provider(self, port: str):
        if port not in self._providers:
            raise LookupError(f"no provider for port {port!r}")
        return self._providers[port]
```

## What happens when a port has no provider

The component-under-test can still construct and inspect a
morphon (state transitions, payload, id, etc.) but operations
that require a port fail loudly:

```python
m = Morphon.forge(payload={"text": "hello"})
m.state  # works
m.project_to_channel()  # raises LookupError if addressing not registered
```

This is the design tension we want: morphon stays usable
standalone for testing, but production paths through it require
the full bridge configuration.

## Bridge testing

Smoke tests in `tests/` exercise:

- A morphon can be forged and inspected without any bridges.
- A morphon's state machine transitions correctly.
- When a fake `addressing` provider is registered,
  `morphon.project_to_channel()` returns its result.
- When the controller is asked to use an unregistered port, it
  raises `LookupError` cleanly.

The pattern these tests establish is the model for every other
component's bridge tests.

## Receipt spine (slot-01)

`MorphonController.register` mints **ASSIGN** on the `receipt` port when
enabled. `get_provider` misses mint **GATE** before raising `LookupError`.
`Morphon.forge` / `transition_to` mint **BIRTH** / **CROSSING** via
`_receipt_bridge.py` (`MORPHON_MINT_RECEIPT=1` default). Local
`cmplx.morphon.Receipt` tuples remain on the morphon; spine receipts are
separate — see `identity_review/TODO_MORPHON_SLOT10_11.md`.

## Status

This is the first component built under the new "parts-plugged-
into-a-designed-system" approach. The patterns above are the
baseline; they will be replicated for every other family
(`addressing`, `memory`, `geometry`, `transport`, `constraints`,
`engine`, etc.).
