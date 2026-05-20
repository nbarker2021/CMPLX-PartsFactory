# MMDB Memory Agentic Profile

Generated: 2026-05-13

## Purpose

This note records what the first richer MMDB quarantine probe teaches future
agents about the memory substrate. It is evidence for mapping, not an import
approval.

## Source

- Source root: `parts_factory`
- Archive: `mmdb-corpus.zip`
- Member: `mmdb-corpus/03-historical-builds/historical builds/Family Builds-legacy/CMPLX 2/cmplx_unified/runtime/_run_out_patch2/ws_main/mmdb/mmdb.sqlite`
- Quarantine path: `/kernel/quarantine/sqlite/artifact-parts-factory-mmdb-corpus-zip-mmdb-corpus-03-historical-builds-historical-builds/mmdb.sqlite`
- Size: 7,098,368 bytes
- SHA-256: `35a780a60d5c9b84abca95e36efe2e030eb97761db95cae63dee3f7e68d45bb5`

## Tables

| Table | Rows | Agentic Role | Notes |
| --- | ---: | --- | --- |
| `lattice_nodes` | 552 | agent memory / geometry | Nodes carry `node_id`, `kind`, `lattice_type`, `coord_json`, `content_hash`, and `payload_json`. |
| `lattice_edges` | 34,995 | geometry graph | Edges connect `node_id` to `neighbor_id` with relations such as `knn`. |
| `receipts` | 2 | receipt provenance | Receipts carry `run_id`, `step_id`, `controller`, `timestamp_utc`, `status`, and `receipt_json`. |

## Import-Mapping Hints

- `receipts.receipt_id` is a strong deterministic identity for receipt atoms.
- `receipts.receipt_json` should become structured provenance/content after
  JSON validation.
- `lattice_nodes.node_id` is a strong deterministic identity for memory nodes.
- `lattice_nodes.payload_json` is the likely content payload; `content_hash` is
  provenance or source identity, not the primary content field.
- `lattice_nodes.coord_json`, `lattice_type`, `dim`, `shell`, and `mass` should
  map to geometry metadata.
- `lattice_edges` should not be flattened into text first; it is a relationship
  table useful for recall traversal.

## Agent Use

Future agents should use this profile to build memory import adapters that
preserve source archive, archive member, quarantine path, table name, row
identity, and row hash in every generated atom/receipt. Postgres writes remain
approval-gated.

## Read-Only Dry Run

The first dry-run import recipe evaluated this quarantined database with no
Postgres writes.

- Candidate records: 35,549
- Evaluated rows: 1,554
- Sample transformed records: 6
- `lattice_nodes`: 552 evaluated of 552; `coord_json` and `payload_json` were
  valid JSON in all evaluated rows.
- `receipts`: 2 evaluated of 2; `receipt_json` was valid JSON in all evaluated
  rows.
- `lattice_edges`: 1,000 evaluated of 34,995 under the row cap; no required
  field errors in the evaluated slice.

Dry-run target records:

- `lattice_nodes` -> `memory_atom`
- `lattice_edges` -> `memory_edge`
- `receipts` -> `receipt`

Identity rule:

`row_hash = sha256(contract_version + db_sha + table + primary_key + canonical_row_json)`

This gives agents a replay-safe and dedupe-aware path for later approved imports.
