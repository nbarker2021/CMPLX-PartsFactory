# mdhg — Bridge

## Port provided

This package registers as the provider for the **`addressing`** port
on `MorphonController`.

## Provider class

`MDHG` from `cmplx.addressing.mdhg`. Implements the
`AddressingProvider` protocol declared in `cmplx.morphon.controller`:

```python
class AddressingProvider(Protocol):
    def channel_for(self, morphon: Morphon) -> int: ...
```

Plus the extended surface specific to MDHG:

```python
def hierarchical_address(self, morphon: Morphon) -> tuple[str, int, str, str]: ...
```

## Ports consumed

None. MDHG is stdlib-only — `hashlib`, `json`, `enum`. It sits as deep
in the DAG as morphon itself.

## How to wire up

In application bootstrap (or test fixture):

```python
from cmplx.morphon import MorphonController
from cmplx.addressing.mdhg import MDHG

MorphonController.get().register("addressing", MDHG())
```

After registration, any morphon's `project_to_channel()` returns the
deterministic 1-9 digital-root channel.

## Test fixtures

Tests register `MDHG()` as the addressing provider. They verify:

- Same payload → same channel across calls.
- Different payloads → distribution across channels (no concentration).
- Hierarchical address fields are correct.
- The morphon caches the channel after first lookup.
