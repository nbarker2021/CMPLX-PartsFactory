# mmdb — Interface

**MMDB** (Morphon Memory Database) is the system's persistence layer.
It stores morphons keyed by id and queryable by channel + geometry,
preserving the full serialized form including receipt chain.

Backed by SQLite for the first build (stdlib, zero external deps).
The schema can be swapped later (Postgres, custom store) without
changing the interface — the swap point is the provider class.

## What this package exposes

| Symbol | Purpose |
|---|---|
| `MMDB(path: str \| Path)` | Provider class. Instantiate with a DB file path. |
| `MMDB.store(morphon)` | Persist a morphon. Idempotent on id. |
| `MMDB.fetch(morphon_id)` | Return a Morphon, or None. |
| `MMDB.delete(morphon_id)` | Remove a morphon. Returns True if it existed. |
| `MMDB.count()` | Total number of morphons stored. |
| `MMDB.find_by_channel(channel)` | Iterator over morphons in a DR channel. |
| `MMDB.find_by_parent(parent_id)` | Iterator over morphons whose parent is `parent_id`. |
| `MMDB.close()` | Close the connection. |
| `MMDB` as context manager | `with MMDB(":memory:") as db: ...` |

## Schema

One table, two indexes. Designed for the operations above; richer
queries are easy to add but not yet in scope.

```sql
CREATE TABLE morphons (
    id              TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    state           TEXT NOT NULL,
    dr_channel      INTEGER,                 -- 1-9 or NULL
    parent          TEXT,                    -- id of parent morphon, or NULL
    payload_json    TEXT NOT NULL,           -- json.dumps(morphon.payload)
    serialized_json TEXT NOT NULL,           -- full Morphon.serialize() result
    updated_at      TEXT NOT NULL
);
CREATE INDEX idx_morphons_channel ON morphons(dr_channel);
CREATE INDEX idx_morphons_parent  ON morphons(parent);
```

The full morphon (including e8 coords, leech point, receipts) lives in
`serialized_json`. The columns `dr_channel` and `parent` are extracted
as separate columns for fast indexed lookup.

## Invariants

1. **Store is idempotent** on id: storing the same morphon twice
   overwrites the row (the latest version wins, with `updated_at`
   advanced).
2. **Fetch round-trips**: `fetch(m.id)` returns a Morphon equal to the
   one stored (modulo timestamp on `updated_at` which is set by store).
3. **No mutation**: `store` doesn't change the morphon it received.
4. **Connection is single-threaded**: this implementation uses one
   sqlite3.Connection. Multi-threaded use needs a connection-pool layer
   on top — out of scope here.

## What this package does NOT do

- Doesn't compute channels or coordinates — caller must have already
  called `morphon.project_to_channel()` etc. before storing.
- Doesn't run admission — caller goes through `cmplx.constraints`
  separately.
- Doesn't propagate to other stores — single backend.
- Doesn't compress / encrypt — `serialized_json` is raw JSON.

## How morphon talks to this

Through the `memory` port:

```python
from cmplx.morphon import MorphonController
from cmplx.memory.mmdb import MMDB

with MMDB("/path/to/morphons.db") as db:
    MorphonController.get().register("memory", db)
    # ...
```

Or via the controller's compound operation:

```python
controller.admit_and_store(morphon)  # uses memory port internally
```
