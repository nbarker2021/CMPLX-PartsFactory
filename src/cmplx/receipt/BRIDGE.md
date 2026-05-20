# receipt — Bridge

## Port provided

`receipt` — `ReceiptProvider` is the canonical provider. Any
component that needs provenance for an operation mints a receipt
through this port.

## Ports consumed (optional)

- `memory` (MMDB) — durable persistence. Without it the chain is
  in-process only.
- `conservation` (NSL) — for `delta_phi` enrichment. The provider
  accepts an `NSLSectors` arg on mint; if NSL is registered it can
  also auto-record the receipt into the NSL ledger as a side effect.
- `addressing` (MDHG) — for atom-id resolution when an atom is named
  by content rather than id.

## Static imports

| Imports from | What | Why |
|---|---|---|
| (stdlib only) | hashlib, json, uuid, time | Hash chain + JSON serialization. |

The receipt package is intentionally stdlib-only so it can be
imported by every system without risking dependency cycles.

## What other components import FROM receipt

| Importer (current + planned) | What |
|---|---|
| `cmplx.snap.SNAPLedger` (planned refactor) | Delegates `append()` to `ReceiptChain.mint(receipt_type="PROCESS", ...)`. |
| `cmplx.crystal.types.Crystal` (planned refactor) | `extend_receipt(tag)` becomes `ReceiptChain.mint(receipt_type="MINT", atom_id=crystal_id, ...)`. |
| `cmplx.nsl.NSLLedger` (planned refactor) | NSL conservation receipts wrap a Receipt with `receipt_type="GATE"`. |
| `cmplx.symbolic.tarpit.WallEmitter` (planned wiring) | OutputWall → `MINT` receipt; ErrorWall → `CROSSING` receipt; bond → `BOND` receipt. |
| `cmplx.morsr.Handshake` (planned wiring) | Each pulse handshake → `PROCESS` receipt with `delta_phi` set from NSL sectors. |
| `cmplx.engine.cqe` (next) | The whole executor mints receipts at every step. |

## External JSONL bridges (2026-05-18)

`receipts_bridge.py` — escrow merge from CQE unified runtime / geometry_lattice
staging. Normalizes **GeoLight** and **TokLight** JSONL ledgers and merges them
into one sorted timeline (`load_geolight`, `load_toklight`, `merge_timelines`).
This is analytics over file-backed ledgers, not a second in-process `ReceiptChain`.

## Cross-component semantics

The receipt chain is the **provenance spine**. Every meaningful state
change in the system writes a receipt; the chain provides:

1. **Audit trail** — `verify_chain()` proves the history hasn't been
   tampered with (Merkle property).
2. **Replay** — `walk_chain(head)` reconstructs the operation sequence
   from any tip.
3. **Coordination** — `chain_for_atom(atom_id)` shows every operation
   that touched an atom.
4. **DAG topology** — `DagEdgeStore` links receipts into dependency
   graphs (e.g., "BOND(A→B)" creates an edge SNAP-label-overlap-weighted
   between A and B).

```
component operation
   │
   ▼
ReceiptProvider.mint(
    receipt_type=..., agent_id=..., atom_id=..., operation=...,
    delta_phi=..., snap_labels=..., epoch=...,
)
   │
   ├─ Receipt(receipt_hash = sha256(prev:op:atom:ts))
   ├─ ReceiptChain.append(receipt) — head moves forward
   ├─ multi-index updated (by_agent, by_atom, by_type)
   ├─ optional: NSL.ledger.append(receipt as NSLReceipt)
   └─ optional: DagEdgeStore.add(...)
   │
   ▼
caller proceeds — provenance is now durable in the chain
```

The Merkle property: any later `verify_chain()` call walks every
receipt and recomputes `sha256(prev:op:atom:ts)` against `receipt_hash`.
If a single byte was edited, the chain breaks.
