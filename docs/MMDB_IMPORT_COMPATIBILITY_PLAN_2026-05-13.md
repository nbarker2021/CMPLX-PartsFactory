# MMDB Import Compatibility Plan

Generated: 2026-05-13

## Status

Plan-only. No live runtime calls and no Postgres writes.

## Source Recipe

- Recipe: `docs/MMDB_READONLY_IMPORT_RECIPE_2026-05-13.md`
- Quarantine path: `/kernel/quarantine/sqlite/artifact-parts-factory-mmdb-corpus-zip-mmdb-corpus-03-historical-builds-historical-builds/mmdb.sqlite`
- Source SHA-256: `35a780a60d5c9b84abca95e36efe2e030eb97761db95cae63dee3f7e68d45bb5`

## Compatibility Result

Recommended strategy: `repo_kernel_staging_adapter_first`

| Target | Rows | Coverage | Notes |
| --- | ---: | --- | --- |
| `memory_atom` | 552 | strong | Candidate `insert_atom` MCP surface exists; runtime routes also include MMDB store/bridge/ingest surfaces. |
| `receipt` | 2 | strong | Candidate `insert_receipt` and `log_speedlight_receipt` MCP surfaces exist; receipt mint/record routes also exist. |
| `memory_edge` | 34,995 | partial | Edges represent recall graph relationships and need neutral staging before mapping to DAG, bond, or MDHG semantics. |

## Runtime Health

Current memory runtime targets are not healthy:

- `tmn2-mmdb`
- `tmn2-mmdb-pg-bridge`
- `tmn2-mmdb-discovery`
- `tmn2-receipt`

Do not call write routes until selected services are approved, started, and
health-checked.

## Staging Contract

Proposed neutral staging tables:

- `memory_import_atoms`
- `memory_import_edges`
- `memory_import_receipts`

Each staged record should carry:

- `row_hash`
- transformed target fields
- source database SHA-256
- quarantine path
- source table
- primary key values
- status

## Next Implementation Item

Implement a repo-kernel staging adapter that materializes the dry-run records
into a local repo-kernel SQLite staging database only after approval for local
staging writes. This is still separate from Postgres/runtime writes.
