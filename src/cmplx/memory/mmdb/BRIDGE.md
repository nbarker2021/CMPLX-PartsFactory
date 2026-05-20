# mmdb — Bridge

## Port provided

`memory` on `MorphonController`. Implements:

```python
class MemoryProvider(Protocol):
    def store(self, morphon: Morphon) -> None: ...
    def fetch(self, morphon_id: str) -> Morphon | None: ...
```

## Provider class

`MMDB` from `cmplx.memory.mmdb`. Constructed with a path (or
`":memory:"` for an in-memory store). Can also be used as a context
manager.

## Ports consumed

None. SQLite-backed; stdlib only.

## How to wire up

```python
from cmplx.morphon import MorphonController
from cmplx.memory.mmdb import MMDB

db = MMDB("/tmp/morphons.db")
MorphonController.get().register("memory", db)

# At shutdown
db.close()
```

## Test fixtures

Tests use `MMDB(":memory:")` for isolation. They verify:

- Store → fetch round-trip preserves all morphon fields.
- Store is idempotent on id.
- Fetch returns None for unknown ids.
- Indexed queries (by channel, by parent) return the right rows.
- The compound `admit_and_store` flow on the controller works when MMDB
  is the registered memory provider.
