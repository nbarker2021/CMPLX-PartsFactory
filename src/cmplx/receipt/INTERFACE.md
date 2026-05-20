# receipt — Interface

**The receipt chain — operation provenance for the whole system.**

Every operation across every component produces a `Receipt`. Receipts
chain via `prev_hash` (Merkle-style) — the chain IS the blockchain.
Multiple components currently implement this primitive separately
(SNAPLedger, Crystal.receipt_chain, NSLLedger, TarPit Handshake);
this package is the canonical home those all eventually delegate to.

Promoted from `CMPLX-TMN-main/src/receipt/receipt.py` — the
PG-backed FastAPI service. The in-process variant here is the
dependency-free default; the durable variant uses the `memory` port
when registered.

## Surface

### Receipt types (10 canonical)

`ReceiptType` enum — the operation classes that produce receipts:

- `MINT` — a new artifact created (crystal, atom, etc.)
- `POST` — content posted to a board / ledger
- `BOND` — two grains bonded (TarPit Dust formation)
- `PROCESS` — general computation step
- `ASSIGN` — capability / role assignment
- `VOTE` — governance decision
- `BIRTH` — agent / entity instantiated
- `DEATH` — agent / entity terminated
- `GATE` — NSL gate decision (accept / reject / amortize)
- `CROSSING` — boundary traversal (wall emission, layer transition)

Custom types are allowed (string-typed `receipt_type`); the enum is
the canonical set.

### `Receipt` dataclass

Fields:
- `receipt_id: str` (12-hex auto-id)
- `receipt_hash: str` — `SHA256(prev_hash:operation:atom_id:timestamp)`
- `prev_hash: str` — points back to the prior receipt
- `receipt_type: str` — one of `ReceiptType` or custom
- `agent_id: str` — who minted it
- `operator: str` — same as `agent_id` by default; can differ when one agent operates on behalf of another
- `atom_id: str` — what the operation was about (Crystal node id, etc.)
- `operation: str` — free-text op name
- `delta_phi: float` — NSL ΔΦ for this operation
- `snap_labels: list[str]` — labels the operation carried
- `epoch: int` — system epoch
- `chain_index: int` — sequential position
- `source_tag: str` — `"{agent}@epoch{epoch}::receipt::{id}"`
- `payload: dict` — arbitrary metadata
- `created_at: float`

`to_dict()`, `from_dict()`, `compute_hash()` helpers.

### `ReceiptChain`

The Merkle-chained store. In-process, with multiple indexes for fast
lookup.

API:
- `mint(receipt_type, agent_id, atom_id, operation, ..., parent_hash="") -> Receipt`
  — appends a new receipt; chains onto `parent_hash` (or `head` if empty)
- `verify(receipt_hash="", max_depth=100) -> dict` — walk back to
  genesis, validate every prev_hash link
- `verify_chain() -> dict` — full-chain consistency (every receipt's
  prev_hash equals previous receipt's hash)
- `walk_chain(start_hash, max_depth=100) -> list[Receipt]` — backward
  walk from a hash
- `by_id(id)`, `by_hash(h)`, `by_agent(id)`, `by_type(t)`,
  `by_atom(id)` — multi-index lookup
- `chain_for_atom(atom_id) -> list[Receipt]` — full chain belonging
  to one atom (chronological)
- `recent(limit=20, offset=0) -> list[Receipt]`
- `head -> str`, `length -> int`, `stats() -> dict`

### `DagEdge` + `DagEdgeStore`

Optional: receipts can be linked into a DAG via edges keyed on
`(source_id, target_id, edge_type)` with a weight + optional SNAP
overlap.

- `DagEdge(source_id, target_id, edge_type, weight, snap_overlap)`
- `DagEdgeStore.add(edge)` — upserts; latest weight wins
- `DagEdgeStore.outgoing(atom_id)`, `incoming(atom_id)`,
  `edges_of(atom_id)` — node-centric lookup

### `ReceiptProvider`

The port provider. Registers on the `receipt` port. Bundles
`ReceiptChain` + `DagEdgeStore`; exposes one-call helpers for the
common patterns.

## Constants

- `GENESIS_HASH = "0" * 64` — the all-zero head used before any
  receipt has been minted

## What's NOT in this layer

- The HTTP service skin (`/mint`, `/verify`, `/chain/{atom_id}`,
  `/dag_edge`, `/recent`, etc.) — lives in
  `services/receipt_service.py`, planned.
- Durable persistence — uses `memory` port (MMDB) when registered;
  in-process dict is the default.
- Cross-system refactoring (SNAPLedger / Crystal.receipt_chain /
  NSLLedger → all delegate to ReceiptChain) — separate follow-up;
  this package establishes the primitive without rewiring callers.
