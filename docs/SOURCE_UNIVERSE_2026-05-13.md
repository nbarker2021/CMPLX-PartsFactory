# Source Universe

Generated: 2026-05-13

Repo-kernel now treats the workspace as a source universe, not a single repo
scope. The clean GitHub clones remain the active module substrate, while the
larger local folders are mounted as bounded evidence roots.

## Mounted Roots

| Source | Role | Access | Container Path |
| --- | --- | --- | --- |
| `repo_kernel_repos` | active module substrate | rw | `/kernel/repos` |
| `parts_factory` | creative yard | ro | `/sources/PartsFactory` |
| `manny_unification_2` | evidence substrate | ro | `/sources/MannyUnification2` |
| `oc_build` | design doctrine | ro | `/sources/OCbuild` |

## API

- `GET /api/sources`
- `POST /api/sources/{source_id}/inventory`
- `POST /api/sources/{source_id}/markers`
- `POST /api/sources/{source_id}/archive-manifest`
- `POST /api/sources/{source_id}/archive-member`
- `POST /api/sources/{source_id}/archive-corpus-summary`
- `POST /api/sources/{source_id}/file-hash-slice`
- `POST /api/sources/{source_id}/archive-hash-slice`
- `POST /api/sources/{source_id}/archive-sqlite-quarantine-probe`
- `POST /api/sources/hash-slice-batch`
- `POST /api/sources/file-breakdown-plan`
- `POST /api/sources/quarantine/sqlite-preview`
- `POST /api/sources/quarantine/mmdb-import-dry-run`
- `POST /api/sources/archive-triage`
- `POST /api/sources/archive-compare`
- `POST /api/sources/archive-duplicate-candidates`
- `POST /api/sources/cleanup-evidence`
- `GET /api/self/cleanup-ledger`
- `POST /api/self/cleanup-ledger`

MCP tools:

- `repo_kernel_sources`
- `repo_kernel_source_inventory`
- `repo_kernel_source_markers`
- `repo_kernel_archive_manifest`
- `repo_kernel_archive_member_read`
- `repo_kernel_archive_corpus_summary`
- `repo_kernel_file_hash_slice`
- `repo_kernel_archive_hash_slice`
- `repo_kernel_archive_sqlite_quarantine_probe`
- `repo_kernel_hash_slice_batch`
- `repo_kernel_file_breakdown_plan`
- `repo_kernel_quarantine_sqlite_preview`
- `repo_kernel_mmdb_import_dry_run`
- `repo_kernel_archive_triage`
- `repo_kernel_archive_compare`
- `repo_kernel_archive_duplicate_candidates`
- `repo_kernel_cleanup_evidence`
- `repo_kernel_cleanup_ledger`

## Policy

Inventories are bounded and resumable. They identify git repos, compose files,
archives, SQLite-like databases, and manifests without extracting archives,
starting services, or writing databases. Zip manifests can be inspected without
extracting their contents.

Archive triage ranks discovered archives by likely domain and practical
inspection cost. It is a prioritization queue, not a deletion or extraction
decision.

Archive comparison distinguishes outer archive identity from internal member
equivalence. Two zip files can have different outer SHA-256 hashes while still
containing the same member paths, sizes, and CRCs. Such pairs are recorded as
content-equivalent candidates, not deletion approvals.

Archive member reads are bounded in-memory reads of a single member, meant for
small text manifests and reports. They do not extract archives to disk.

Corpus summary parsing reads `MANIFEST.md` inside a zip and extracts structured
fields such as total files, source workspace, precedence buckets, skipped files,
and duplicate-collapse counts.

Cleanup evidence combines duplicate archive candidates and corpus summaries into
retain/archive recommendations. It is explicitly non-destructive and approval
gated.

Hash slices provide exact SHA-256 duplicate evidence across bounded directory
or zip-member slices. Batch hash slices can compare multiple roots in one call.

SQLite quarantine probes are the first approved extraction path. They copy one
selected SQLite-like zip member into `/kernel/quarantine`, leave the source
archive untouched, and open the quarantined copy with SQLite read-only mode to
report tables, columns, and optional row counts.

File breakdown plans are fallback-only. They describe how to split an oversized
or parse-hostile file into manageable evidence chunks if normal manifest, hash,
or schema probing fails. The planner does not materialize chunks.

SQLite previews read only quarantined copies and return bounded row samples with
cell caps, hashes, schema hints, and agentic memory-role classifications. They
are meant to help future agents understand what a database actually contains
before any import or live write is considered.

MMDB import dry-runs transform quarantined SQLite rows into candidate memory
atoms, receipt records, and graph edges. They validate JSON fields, assign
deterministic row hashes, estimate import size, and return sample transformed
records without writing Postgres.

The memory workflow compatibility planner lives under the unified memory API,
not the source API. It compares dry-run records to discovered tools, routes, and
runtime health so future agents know whether to stage, route, or wait for
approval.
