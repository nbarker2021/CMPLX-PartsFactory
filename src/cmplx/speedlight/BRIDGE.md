# speedlight — Bridge

## Port provided

`cache` — `SpeedLightProvider` is the canonical provider. Consumers
go through this port for any idempotent computation:
```
result = mc.get_provider("cache").compute_and_cache(address, "kaprekar", compute_fn)
```

## Ports consumed (optional)

- `memory` (MMDB) — for durable receipt persistence. SpeedLight's T2
  tier delegates here when registered; otherwise T2 is an in-process
  dict.
- `addressing` (MDHG) — for `MDHGMultiScale` integration with
  `WorldlineCache`. Without it, the cache is single-tier.
- `crystal` — when a SpeedLight result corresponds to a Crystal node,
  the `mdhg_address` field can be set from `E8Node.mdhg_address`.
- `snap` — to derive the `floor` (label neighborhood) portion of
  `compute_mdhg_address` from `SNAPLabel.all_labels`.

## Static imports

| Imports from | What | Why |
|---|---|---|
| `cmplx.geometry.alena` | `COUPLING`, `PHI` | Shared constants for E8 normalization. |
| `cmplx.crystal.fabric` | `assign_address` | Reuse the existing 6-layer address builder; SpeedLight's `compute_mdhg_address` is the SpeedLight-flavored variant. |

## What other components import FROM speedlight

| Importer (current + planned) | What |
|---|---|
| `cmplx.engine.cqe` (planned) | `SpeedLight.compute_and_cache` to memoize compound-op steps + receipts. |
| `cmplx.routing.agrm` (planned) | `GlobalIndex.query` for nearest-neighbor route candidates. |
| `cmplx.worlds.forge` (planned) | `WorldlineCache` for time-axis world state caching. |
| `cmplx.symbolic.tarpit` (planned wiring) | `SpeedLight.put_aspect(address, "bonds", ...)` so grain-bond outcomes ride the cache. |

## Cross-component semantics

SpeedLight is the **idempotency spine**. Every expensive computation
in the unified system goes through it:

```
caller
   │  task_id, fn, *args
   ▼
SpeedLight.compute(task_id, fn, *args)
   ├── cache hit? → return (cached_result, 0.0, receipt)
   │
   ▼ (miss)
fn(*args) → result
   │
   ▼
ComputationReceipt(task_id, result, cost, e8_coords, ...)
   │
   ├── receipt_cache[task_id] = receipt          ── T1 (memory)
   ├── ReceiptStore.append(receipt)              ── audit trail
   ├── GlobalIndex.admit(atom_id, e8_coords, ...)── proximity index
   └── EquivalenceLearner.register(receipt)      ── prototype merge
   │
   ▼
return (result, cost, receipt)
```

The 10 named aspects (`gate_w4, gate_w80, kaprekar, sacred, phi,
e8_nearest, weyl_chamber, bonds, labels, metadata`) are the
canonical compute-keys per atom. A Crystal's `E8Node` accrues these
aspects over its lifetime; any downstream consumer can ask for one
and get a hit if anyone has already computed it.

`f(f(x)) = f(x)` — once registered, never recomputed. That's the
deal SpeedLight makes with the rest of the system.
