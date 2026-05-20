# speedlight — Interface

The **unified idempotent computation cache**. SpeedLight enforces
`f(f(x)) = f(x)` — once a result is cached at a task's address, the
computation is never repeated. Every result lives at an MDHG-shaped
address (`planet.city.building.floor.room.atom`) so neighbor queries
become prefix queries and proximity queries become E8 geometry.

Promoted from `SpeedLight` / `MMDBSpeedLight` / `SpeedLightDistributed`
canonicals, `tmn1_speedlight_service.py` (GlobalIndex), the
`mdhg_speedlight.py` 6-layer address scheme, and the TMN2 service
contracts.

## Surface

### Receipts (the provenance unit)

- `ComputationReceipt` — `receipt_id, task_id, task_hash, result_hash,
  result, cost_seconds, cached_at, fn_name, e8_coords, leech_coords,
  metadata`. The atomic record of "this computation was run".
- `ReceiptStore` — append + lookup + iterate; pluggable backend (the
  default is in-process; `MMDBReceiptStore` planned for persistence).

### Address (the cache-key shape)

- `compute_mdhg_address(content, content_hash, snap_labels, e8_coords,
  atom_id) -> dict` — produces the 6-layer
  `planet.city.building.floor.room.atom` address. Planets are named
  (mercury, venus, ..., pluto); city is entry-type-derived (forge,
  library, vault, nexus); building is E8 sign pattern; floor is
  SNAP-label hash (the **label neighborhood**); room is content hash;
  atom is unique id.
- Neighbor helpers: `address_prefix(address, level)` strips the
  hierarchy at any level, so prefix matches give planet-/building-/
  floor-/room-level neighborhoods.
- **10 named aspects** for an address — the canonical cache keys per
  atom: `gate_w4, gate_w80, kaprekar, sacred, phi, e8_nearest,
  weyl_chamber, bonds, labels, metadata`. Stored as
  `{address}:{aspect}`.

### Core cache

- `SpeedLight(max_cache_size=10_000_000)` — base cache.
  - `compute(task_id, compute_fn, *args, **kwargs) -> (result, cost,
    receipt)` — idempotent execute-or-cache.
  - `get(key) -> value | None`, `put(key, value, metadata=None) -> None` —
    raw key/value API.
  - `get_aspect(address, aspect) -> value | None`,
    `put_aspect(address, aspect, value) -> None` — MDHG-address-keyed.
  - `compute_and_cache(address, aspect, compute_fn) -> value` — full
    idempotent pattern: check → compute if miss → store → return.
  - `share_cache(other)` — merge another SpeedLight's receipts.
  - `clear()`, `stats() -> dict`, `report() -> str`.
- `SpeedLightDistributed` — `threading.RLock` wrapper for multi-agent
  use.

### Tiers

- `TwoTierCache` — T1 (in-memory LRU `OrderedDict`, capped) + T2
  (durable backend; the default is in-process dict but adapter for
  MMDB is exposed). T1 miss → check T2 → promote on hit.
- Connects to `cmplx.addressing.mdhg.MDHGMultiScale` for fast/med/slow
  worldline caching: SpeedLight's T1 == multiscale.fast, T2 == med,
  archive == slow.

### Geometric index

- `GlobalIndex` — in-process E8 proximity index.
  - `admit(atom_id, e8_coords, labels, content_hash)` — record entry.
  - `query(e8_coords, k=10, label_filter=None) -> [(atom_id, distance,
    labels)]` — top-k L2 neighbors with optional label mask.
  - `stats()`.

### Equivalence learning

- `EquivalenceLearner(threshold=0.95)` — merges receipts whose results
  are cosine-similar above threshold (the "learn_equivalence"
  endpoint from TMN2's engine).
  - `register(receipt)` — admit a receipt to the prototype pool.
  - `find_equivalent(result_vec) -> Optional[receipt_id]` —
    prototype lookup.
  - `prototypes() -> list[dict]` — current learned classes.

### Worldline cache

- `WorldlineCache(speedlight, multiscale)` — bridges SpeedLight with
  `MDHGMultiScale` for time-axis caching. The same task at successive
  time-ticks lands in `fast`; promoted to `med` at keyframes; archived
  to `slow`.

### Provider

- `SpeedLightProvider` — bundles `SpeedLight` + `GlobalIndex` +
  `EquivalenceLearner` + (optional) `WorldlineCache`. Registers on
  the `cache` port of `MorphonController`.

### Statistics / reporting

- `stats()` returns `{hits, misses, hit_rate_percent, cached_tasks,
  bytes_stored, total_time_saved_seconds, efficiency_multiplier}`.
- `report()` returns a human-readable summary including the
  100k-agent speedup projection from the original.

## What's NOT in this layer

- The HTTP service skin (FastAPI endpoints `/compute`, `/put`,
  `/get`, `/receipts`, `/lineage`, `/stats`, `/ledger`, `/prototypes`).
  Lives in a future `services/speedlight_service.py`.
- The `cqe_speedlight_miner_mvp` — receipt-mining for pattern
  extraction. Planned as `cmplx.speedlight.miner`.
- The full GeoTokenizer (base100 codec + LayerBridge) from the TMN2
  engine. Separate `cmplx.tokenization` work.
- MMDB-backed persistence — uses `cmplx.memory.mmdb` through the
  `memory` port when registered. Currently in-process only.
