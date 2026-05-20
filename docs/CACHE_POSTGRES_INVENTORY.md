# Cache Postgres Deep Survey

**Date**: 2026-05-12  
**Database**: `unification_aggregator` on `postgres-cache` (port 55432)  
**Total Size**: 4,020 MB data + 23 GB WAL

---

## 1. Critical Finding: Ingest Queue STALLED

The cache postgres has an **active job queue** (`ingest.queue`) that is **deadlocked**:

| Status | Count | Notes |
|--------|-------|-------|
| `queued` | **476,112** | Waiting to be processed |
| `done` | 241,816 | Successfully completed |
| `running` | **1** | **Locked since May 6 (6 days ago!)** |
| `dead` | 1 | Failed after 3 attempts |

**The running job**:
- Action: `catalog_code`
- Locked by: `dbu-b36ad2e1`
- Locked at: `2026-05-06 23:54:44` (6 days ago)
- Likely cause: Worker crashed/interrupted, never released the lock

**Queued breakdown**:
- `catalog_code`: 338,205 jobs
- `catalog_doc`: 131,044 jobs
- `profile_data_text`: 6,298 jobs
- `archive_expand`: 561 jobs
- `discover_root`: 4 jobs

**This means the entire cataloging pipeline has been frozen for 6 days.**

---

## 2. Schema Inventory (8 Schemas, 53 Tables)

### `artifact` — Raw artifact registry
| Table | Rows | Size | Purpose |
|-------|------|------|---------|
| `source` | 1,093,022 | 2,443 MB | Every file discovered across spaces |
| `archive_lineage` | 1,003,625 | 377 MB | Archive-to-extracted-content relationships |
| `file_type_profile` | 1,093,022 | 171 MB | MIME type / file classification |
| `source_hash` | 4,206 | 1 MB | SHA-256 hashes (only 0.4% coverage!) |

All artifacts are from **`manny-unification-2`** (274 GB referenced).  
**No PartsFactory or OCbuild data has been ingested.**

### `catalog` — Processed content catalog
| Table | Rows | Size | Purpose |
|-------|------|------|---------|
| `doc_source` | 555,207 | 215 MB | Document content extraction |
| `code_source` | 438,324 | 182 MB | Code AST analysis |
| `code_report` | — | 3,032 kB | Generated code reports |
| `doc_report` | — | 4,032 kB | Generated doc reports |
| `db_report` | — | 3,288 kB | Database analysis reports |
| `sql_source` | — | 1,000 kB | SQL text sources |
| `db_source` | — | 768 kB | Database schema sources |

### `catalog.code_source` structure
Key columns:
- `source_id` (UUID) → links to `artifact.source`
- `language` (text) — detected language
- `system_of_origin` (text) — which system the file belongs to
- `line_count` (integer)
- `function_names`, `class_names`, `imports`, `entry_points`, `exports` (JSONB)
- `capabilities_summary` (text)
- `implement_status` (text) — `evidence` | `skip` | ???
- `confidence` (text)
- `profiled_at` (timestamp)

**implement_status distribution**:
- `evidence`: 438,315 (99.998%)
- `skip`: 9 (0.002%)
- **ZERO promoted to `implement` or `canonical`**

**By system_of_origin**:
- `cmplx-tmn1`: 219,898 files
- `datasets-review`: 86,135 files
- `cqe`: 65,590 files
- `aletheia`: 38,131 files
- `cmplx-build`: 12,859 files
- `unknown`: 10,756 files
- `external-session`: 2,544 files
- `cmplx-tmn2`: 2,411 files

### `ingest` — Pipeline job queue
| Table | Rows | Purpose |
|-------|------|---------|
| `queue` | 717,930 | Active job queue (see stalled status above) |
| `receipt` | — | 164 MB | Ingestion receipts |
| `checkpoint` | — | 80 kB | Pipeline checkpoints |
| `dead_letter` | — | 32 kB | Failed jobs archive |

### `capsules` — Service registry
| Table | Rows | Purpose |
|-------|------|---------|
| `registry` | 10 | Registered microservices |
| `jobs` | — | Capsule job tracking |

**Registered capsules**:
- `artifact-registry` (catalog)
- `code-graph` (code-intel)
- `sql-federation` (data-intel)
- `data-intel`
- `doc-intel`
- `pocket-memory` (memory)
- `agent-hub` (orchestration)
- `speedlight` (receipt-lineage)
- `tarpit` (atomization)
- `unique-systems` (evidence)

### `memory` — Agent memory layer
| Table | Purpose |
|-------|---------|
| `recall_index` | Keyed recall lookups |
| `session_note` | Session-level notes |
| `pocket_sync` | Pocket memory sync |
| `agent_observation` | Agent observation log |

### `provenance` — Evidence tracking
| Table | Purpose |
|-------|---------|
| `claim` | Formal claims about artifacts |
| `evidence_link` | Links between claims and sources |
| `confidence_label` | Confidence scoring |

### `dbmeta` — Database metadata
| Table | Size | Purpose |
|-------|------|---------|
| `row_batch_manifest` | 156 MB | Batch ingestion manifests |
| `column_snapshot` | 16 MB | Column-level snapshots |
| `table_snapshot` | 11 MB | Table-level snapshots |
| `sample_row` | 16 MB | Sample rows |
| `database_artifact` | 2,056 kB | Database artifact registry |

### `public` — Legacy / shared tables
Same tables as primary postgres plus some extras:
- `ai_memory_actions`, `ai_memory_decisions`, `ai_memory_graph`, `ai_memory_knowledge`, `ai_memory_sessions`
- `data_flow_context`, `data_flow_packets`, `data_flow_steps`
- `mdhg_nodes`, `mdhg_sessions`
- `mmdb_crystals`
- `paper_analyses`
- `pipeline_final`, `pipeline_results`
- `speedlight_cache`, `speedlight_receipts`
- `connectivity_test`

---

## 3. Architectural Implications

### What this database IS
- The **actual data catalog** for the entire CMPLX system
- Already contains **1M+ artifacts** and **438K code files** with AST analysis
- Has a **sophisticated job queue** for async processing
- Has **provenance tracking** for evidence-based reasoning
- Has **capsule registry** for service discovery

### What this database is NOT
- It does NOT contain PartsFactory data (only Manny)
- It does NOT have SHA-256 hashes for 99.6% of artifacts
- It does NOT have any `implement` or `canonical` promotions
- It is NOT being actively processed (queue stalled)

### Canonicalization Strategy Options

**Option A: Use `unification_hub` (primary postgres)**
- Pros: Clean schema, dedicated to canonicalization, we control it
- Cons: Duplicates work already done in cache, no linkage to existing catalog

**Option B: Use `unification_aggregator` (cache postgres)**
- Pros: Links to existing 438K code records, provenance tracking exists, capsule registry
- Cons: Queue is stalled, schema is complex, may need normalization

**Option C: Dual-write to both**
- Pros: Canonicalization lineage in hub, detailed metadata in cache
- Cons: Complexity, synchronization overhead

**Option D: Fix cache first, then canonicalize**
- Unlock the stalled queue
- Let it finish processing Manny data
- Then ingest PartsFactory data
- Use the resulting catalog for canonicalization

---

## 4. Immediate Actions Available

1. **Unlock the stalled ingest queue** — `UPDATE ingest.queue SET status = 'queued', locked_by = NULL, locked_at = NULL WHERE status = 'running'`
2. **Ingest PartsFactory data** — Populate `artifact.source` with the 55K PartsFactory files
3. **Hash the artifacts** — Compute SHA-256 for all records (currently 0.4% coverage)
4. **Promote existing evidence** — Update `catalog.code_source.implement_status` from `evidence` to `canonical`
5. **Cross-reference** — Link our SQLite canonicalization data to cache postgres records

---

*Survey completed. Awaiting directive on which path to take.*
