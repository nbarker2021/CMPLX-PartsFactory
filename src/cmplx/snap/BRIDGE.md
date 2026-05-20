# snap — Bridge

## Port provided

`snap` — `SNAPEngine` is the canonical provider. Consumers go through
the port to label items, evaluate lens states, or run a Gate369
selection.

## Ports consumed

- `receipt` — unified provenance when `SNAP_MINT_RECEIPT=1` (default on).
  `SNAPEngine` mints `POST` on label, `GATE` on Gate369 fail, `PROCESS` otherwise;
  `SNAPLedger` remains the in-process mirror chain. `mint_run_snapshot(workspace, …)`
  writes run JSONL via `ReceiptChain.write_run_receipt` for controller/CQE alignment.

## Ports consumed (optional)

- `crystal` — `CrystalRegistry.mount_ennead` mounts ennead facets as
  `E8Node`s with `snap_labels` from `SNAPEngine.label`; `crystallize`
  records the ledger op when containment warrants it.
- `memory` (planned) — to persist `SNAPTransaction` chains beyond
  process lifetime (MMDB row per transaction).

## Static imports

| Imports from | What | Why |
|---|---|---|
| (stdlib only) | hashlib, inspect, re | Rule matching + hash chaining. |

The SNAP engine intentionally has zero geometry imports — labels and
lenses are abstract over the underlying lattice. When SNAP needs to
emit `e8_coords`, it delegates through the `crystal` port.

## What other components import FROM snap

| Importer (current + planned) | What |
|---|---|
| `cmplx.crystal` (planned wiring) | `SNAPLabel` to attach to `E8Node.snap_labels`. |
| `cmplx.engine.cqe` (planned) | `SNAPLedger` for receipt chaining alongside its own `delta_phi ≤ 0` audit. |
| `cmplx.routing.agrm` (planned) | `LensBank` + `BaseLens.evaluate()` for chamber-decision gating. |
| `cmplx.transport.pixel` (planned) | `SNAPLabel.all_labels` to drive SNAP→shape rendering (the giraffe pipeline). |

## Cross-component semantics

SNAP closes the **decomposition** half of the pipeline that Crystal
closes the **mounting** half of:

```
content
   │
   ▼
SNAPLabeler.label(item) ──── 5 dimensions, rule-derived
   │
   ▼
LensBank.evaluate(state) ─── pass | refine (polarity-aware)
   │
   ▼ (if pass)
Gate369Engine.process(bodies, predicates)
   │                              │
   ├── triad: top-3 by lens score │
   ├── hexad: pairwise invariants │
   └── ennead: 9-body containment ├── crystallized=True if c>0.7
                                  ▼
                       Crystal.add_node(... snap_labels=label.all_labels ...)
                                  │
                                  ▼
                  receipt_chain extended (SNAPLedger + Crystal.receipt_chain)
```

This is the spine the user described: SNAP decomposes, Crystal binds,
MDHG addresses, ALENA projects, the carrier renders. Receipts make it
auditable end-to-end.
