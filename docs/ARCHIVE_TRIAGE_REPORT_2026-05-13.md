# Archive Triage Report

Generated: 2026-05-13

## New Repo-Kernel Capabilities

- `POST /api/sources/archive-compare`
- `POST /api/sources/archive-duplicate-candidates`
- `POST /api/sources/{source_id}/archive-member`
- `POST /api/sources/{source_id}/archive-corpus-summary`
- `POST /api/sources/cleanup-evidence`
- `POST /api/sources/{source_id}/file-hash-slice`
- `POST /api/sources/{source_id}/archive-hash-slice`
- `POST /api/sources/{source_id}/archive-sqlite-quarantine-probe`
- `POST /api/sources/hash-slice-batch`
- `POST /api/sources/file-breakdown-plan`
- `GET /api/self/cleanup-ledger`

MCP equivalents:

- `repo_kernel_archive_compare`
- `repo_kernel_archive_duplicate_candidates`
- `repo_kernel_archive_member_read`
- `repo_kernel_archive_corpus_summary`
- `repo_kernel_cleanup_evidence`
- `repo_kernel_file_hash_slice`
- `repo_kernel_archive_hash_slice`
- `repo_kernel_archive_sqlite_quarantine_probe`
- `repo_kernel_hash_slice_batch`
- `repo_kernel_file_breakdown_plan`
- `repo_kernel_cleanup_ledger`

Most operations are read-only. The SQLite quarantine probe is the one approved
extraction path: it copies exactly one selected SQLite-like zip member into the
repo-kernel quarantine area, then opens that copy in read-only SQLite mode. No
source archive is modified, and no delete or archival action is approved by
these reports.

## Duplicate Candidates

Same-name/same-size archive scan across `parts_factory`, `manny_unification_2`,
and `oc_build` found three toolkit pairs:

| Archive | Copies | Classification |
| --- | ---: | --- |
| `CMPLX_Tool_Suite.zip` | 2 | content-equivalent zip members |
| `CMPLX_Tool_Suite_V2.zip` | 2 | content-equivalent zip members |
| `CMPLX_Tool_Suite_V3.zip` | 2 | content-equivalent zip members |

The outer zip SHA-256 hashes differ, but the internal member path/size/CRC
signatures match. Treat these as duplicate-content candidates pending a cleanup
approval process.

## Corpus Manifest Summaries

| Archive | Files | Size | Skipped | Duplicate Collapses In Manifest | Distribution |
| --- | ---: | --- | ---: | ---: | --- |
| `agenthub-corpus.zip` | 14 | 0.2 MB | 0 | 113 | active implementation, agent ecosystem, historical builds, dataset uniques |
| `mmdb-corpus.zip` | 351 | 197.6 MB | 2 | 10,207 | 1 active implementation, 350 historical builds |
| `tmn-corpus.zip` | 2,057 | 185.0 MB | 10 | 7,239 | agent ecosystem, historical builds, dataset uniques |

## MMDB Notes

`mmdb-corpus.zip` contains many SQLite/database members and a strong duplicate
collapse signal. Top duplicate rows include repeated SQLite WAL/SHM files,
MMDB test ingestion files, adapters, service scripts, and historical runtime
snapshots. This corpus should feed the memory runtime and cleanup evidence
ledger before any extraction-heavy work.

## Cleanup Evidence

The first non-destructive cleanup evidence pass reports:

- 3 duplicate candidate groups
- 3 compared groups
- 6,606,569 bytes of potential reclaim if approved
- Retain candidate: Manny evidence substrate copy
- Archive candidates: PartsFactory duplicate toolkit zips

This is not a deletion instruction. It is an approval-gated cleanup ledger
entry showing where duplicate-content archives can be reviewed first.

## File Hash Slice Pass

The first exact file-hash batch compared top-level PartsFactory zip files
against Manny's `assorted toolkits` zip files.

- 118 archive files hashed
- 74 unique hashes
- 44 exact duplicate groups
- 1,598,206,009 bytes of potential reclaim if approved
- 44 exact duplicate candidates persisted to the cleanup ledger

The initial PartsFactory-only top-level zip slice had no internal exact
duplicates. The cross-root batch found the real duplication: copied
dimensional-forms split archives under both PartsFactory and Manny evidence.

## MMDB Import Plan

The MMDB corpus import plan is exposed through:

- `POST /api/unified/memory/corpus-import-plan`
- MCP tool `repo_kernel_memory_corpus_import_plan`

Current plan-only results:

- 60 database members listed in `mmdb-corpus.zip`
- 42 database members hashed under the 5 MB safety gate
- 18 database members skipped by the size gate
- 0 duplicate database hashes in the bounded hashed slice
- 1 memory import-plan candidate persisted to the cleanup ledger

The next implemented step is the approval-gated SQLite quarantine probe: copy a
selected MMDB database member to `/kernel/quarantine`, inspect schema/table
counts read-only, and then decide whether it maps cleanly to the unified memory
contract. Postgres writes remain approval-gated.

First approved probe result:

- Member: `mmdb_controller.sqlite`
- Size: 20,480 bytes
- SHA-256: `d62a5fdd6b341b2f8b21c7db5239f471b551206d7f78880b1d2de87eb17b8ea4`
- Quarantine copy: `/kernel/quarantine/sqlite/artifact-parts-factory-mmdb-corpus-zip-mmdb-corpus-03-historical-builds-historical-builds/mmdb_controller.sqlite`
- Schema objects: 2 tables
- `lattice_nodes`: 1 row
- `receipts`: 0 rows
- Postgres writes: none

## Oversized File Fallback

The file breakdown planner is available for members that are too large or fail
normal parsing. It chooses a strategy by type, such as SQLite table windows,
archive member batches, JSON/CSV record windows, text line windows, or binary
byte ranges. It is plan-only and does not split files until a future approved
quarantine materialization step is added.

First dry run used a 7,098,368 byte MMDB SQLite member skipped by the initial
5 MB import-planning gate. The planner selected `sqlite_table_windows`, with a
normal-first path of quarantine copy, read-only schema probe, and then
table-level row windows if needed.

That same richer MMDB member was then approved for quarantine probing:

- Member: `_run_out_patch2/ws_main/mmdb/mmdb.sqlite`
- Size: 7,098,368 bytes
- SHA-256: `35a780a60d5c9b84abca95e36efe2e030eb97761db95cae63dee3f7e68d45bb5`
- Schema objects: 3 tables
- `lattice_nodes`: 552 rows
- `lattice_edges`: 34,995 rows
- `receipts`: 2 rows

The bounded row preview shows this database is useful for agentic memory
mapping: receipt rows include run IDs, step IDs, controller names, timestamps,
status, and receipt JSON; lattice nodes include E8 coordinates, content hashes,
payload JSON, and node kinds such as `receipt` and `token_item`; lattice edges
encode graph relationships such as `knn`.

The read-only MMDB import dry-run now maps this database to candidate unified
memory records:

- 35,549 candidate records
- 1,554 rows evaluated under safety caps
- 6 sample transformed records returned
- `lattice_nodes` -> `memory_atom`
- `lattice_edges` -> `memory_edge`
- `receipts` -> `receipt`
- Postgres writes: 0

Recipe artifact: `docs/MMDB_READONLY_IMPORT_RECIPE_2026-05-13.md`.
