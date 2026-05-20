# MMDB Read-Only Import Recipe

Generated: 2026-05-13

## Status

Read-only recipe. No Postgres writes are approved or implemented.

## Source

- Quarantine path: `/kernel/quarantine/sqlite/artifact-parts-factory-mmdb-corpus-zip-mmdb-corpus-03-historical-builds-historical-builds/mmdb.sqlite`
- SHA-256: `35a780a60d5c9b84abca95e36efe2e030eb97761db95cae63dee3f7e68d45bb5`
- Size: 7,098,368 bytes

## Contract

Target record types:

- `memory_atom`
- `memory_edge`
- `receipt`

Every future imported record must preserve:

- source archive/member receipt
- quarantine path
- source database SHA-256
- table name
- primary key values
- deterministic row hash

## Table Mapping

| Source Table | Target Record | Candidate Rows | Mapping |
| --- | --- | ---: | --- |
| `lattice_nodes` | `memory_atom` | 552 | `node_id` identity, `payload_json` content, `content_hash` source hash, E8 geometry metadata |
| `lattice_edges` | `memory_edge` | 34,995 | `node_id`, `neighbor_id`, `relation`, `cost` recall graph |
| `receipts` | `receipt` | 2 | `receipt_id` identity, `receipt_json` content, run/controller/status/timestamp provenance |

## Dry-Run Result

- Candidate records: 35,549
- Evaluated rows: 1,554
- Sample transformed records: 6
- Postgres writes: 0

JSON validation in evaluated rows:

- `lattice_nodes.coord_json`: 552 valid arrays
- `lattice_nodes.payload_json`: 552 valid objects
- `receipts.receipt_json`: 2 valid objects
- `lattice_edges`: no JSON columns

## Identity

Use this deterministic identity rule:

`row_hash = sha256(contract_version + db_sha + table + primary_key + canonical_row_json)`

The row hash is the replay/dedupe key. A later write-capable importer should
skip, merge, or version records with an already-seen row hash.

## Approval Gates

Before any Postgres write:

- Compare this contract against live memory API surfaces.
- Decide target schema or adapter shape.
- Produce backup/export receipt.
- Require explicit approval for write-capable importer creation and execution.

## Compatibility Plan

The compatibility planner compared this recipe against discovered memory tools,
routes, and runtime health.

Endpoint:

- `POST /api/unified/memory/mmdb-import-compatibility`

Result:

- Recommended strategy: `repo_kernel_staging_adapter_first`
- `memory_atom`: strong static surface coverage through `insert_atom` plus
  several candidate runtime routes such as MMDB store/bridge/ingest surfaces.
- `receipt`: strong static surface coverage through `insert_receipt` and
  `log_speedlight_receipt`, plus receipt mint/record route candidates.
- `memory_edge`: partial coverage only; edges should remain in neutral graph
  staging until DAG, bond, or MDHG semantics are selected.
- Runtime health: current memory targets are not healthy.
- Write status: blocked until explicit approval.

Staging tables proposed by the planner:

- `memory_import_atoms`
- `memory_import_edges`
- `memory_import_receipts`

This preserves the import recipe as actionable future work without calling live
write surfaces prematurely.
