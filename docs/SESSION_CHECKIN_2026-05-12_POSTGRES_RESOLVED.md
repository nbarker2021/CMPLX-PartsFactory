# Session Check-in: Postgres Connectivity Resolved + Canonicalization Migration

**Date**: 2026-05-12  
**Phase**: Knowledge gate passed (0-12.5%) → Infrastructure accounting complete  
**Status**: Postgres lineage storage operational. First canonical cluster migrated.

---

## 1. Critical Infrastructure Discovery: Port 5432 Conflict

**Root cause of all Postgres connectivity failures identified.**

There are **TWO** PostgreSQL 16 instances competing for port 5432 on Windows:

| Service | Process | Binding | What Windows Python connects to |
|---------|---------|---------|--------------------------------|
| Docker `postgres` container | `com.docker.backend.exe` (PID 32428) | `0.0.0.0:5432`, `[::]:5432` | NO — intercepted by wslrelay |
| WSL2 Ubuntu native PostgreSQL | `wslrelay.exe` (PID 25536) | `127.0.0.1:5432` | YES — this is what `127.0.0.1` resolves to |

**Consequence**: Every Python/psycopg2 connection from Windows to `localhost:5432` or `127.0.0.1:5432` hits the **WSL2 native postgres**, not the Docker container. The WSL2 postgres has different credentials (unknown password), causing "password authentication failed" errors.

**Working connection paths**:
- `docker exec postgres psql ...` — connects inside container via unix socket (trust auth)
- `docker run --network=backend ...` — connects from sibling container on Docker network
- `opencode-session` container — has Python 3.11.2 + psycopg2 2.9.12, can reach `postgres:5432`
- **Not available**: Direct Windows Python to `127.0.0.1:5432` (goes to wrong postgres)

**Recommendation**: Always use containerized Python for Postgres operations, or configure WSL2 to not forward 5432.

---

## 2. PostgreSQL Schema Created

Created in `unification_hub` (Docker postgres, port 5432):

```sql
-- Cluster registry: one row per basename/tool
CREATE TABLE canonical_clusters (
    id SERIAL PRIMARY KEY,
    cluster_key VARCHAR(255) UNIQUE NOT NULL,  -- e.g. hash or basename
    basename VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Artifact registry: one row per variant file found anywhere
CREATE TABLE canonical_artifacts (
    id SERIAL PRIMARY KEY,
    cluster_id INTEGER REFERENCES canonical_clusters(id),
    source_path TEXT NOT NULL,              -- absolute original path
    content_hash VARCHAR(64) NOT NULL,      -- SHA-256 of content
    file_size INTEGER,
    line_count INTEGER,
    language VARCHAR(50),
    system_name VARCHAR(100),               -- which system it came from
    variant_index INTEGER,                  -- preference rank (1 = best)
    is_canonical BOOLEAN DEFAULT FALSE,
    canonical_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit log: every canonicalization decision
CREATE TABLE canonicalization_log (
    id SERIAL PRIMARY KEY,
    cluster_key VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 3. First Canonical Cluster Migrated: `e8_lattice.py`

**Source**: SQLite `yard_inventory.sqlite`  
**Destination**: PostgreSQL `unification_hub`  
**Migration script**: `scripts/migrate_to_postgres.py`

**Migrated data**:
- 1 cluster (`e8_lattice.py`, cluster_key: `7156caf2b3568b9a`)
- 16 artifacts (15 real variants + 1 canonical destination file)
- 3 marked canonical (2 source variants with identical hash + 1 canonical destination)
- 1 log entry documenting the canonicalization decision

**Canonical chosen from**:
- CMPLXUNI `src/cmplx/mdhg/e8_lattice.py` (315 lines, 9,698 bytes)
- CMPLX-1T `docs/1_intake/.../cmplxuni_deps/mdhg/e8_lattice.py` (identical content)

**13 rejected variants** range from 10-line stubs to 254-line partial implementations.

**Line-ending fix applied**: The canonical file written to `src/canon/tools/e8_lattice.py` initially received CRLF line endings from Windows WriteFile, causing a hash mismatch (10,013 bytes vs expected 9,698 bytes). File was normalized to LF endings and hash now matches the database record (`d74f398c...`).

---

## 4. Database State Summary

### PostgreSQL `unification_hub` (port 5432, Docker)
```
canonical_clusters:     1 row   (e8_lattice.py)
canonical_artifacts:    16 rows (3 canonical — 2 sources + 1 destination, 13 rejected)
canonicalization_log:   1 row   (canonicalize action)
mmdb_crystals:          present (pre-existing)
research_notes:         present (pre-existing)
research_queries:       present (pre-existing)
research_results:       present (pre-existing)
research_sessions:      present (pre-existing)
```

### PostgreSQL `unification_aggregator` (port 55432, Docker)
- 17 tables (ai_memory_*, mdhg_*, speedlight_*, pipeline_*, etc.)
- This is the "cache" database, not currently used for canonicalization

### SQLite `data/yard_inventory.sqlite`
- Still holds original canonicalization data (clusters, artifacts, canonical_file)
- Should be considered **read-only source of truth** until all clusters migrated

### SQLite `data/canonicalization.sqlite`
- Empty (0 rows in all tables) — schema exists but never populated
- Consider deprecating in favor of PostgreSQL

---

## 5. Active Issues & Next Steps

| Priority | Issue | Status |
|----------|-------|--------|
| **P0** | Postgres port 5432 conflict (WSL2 native vs Docker) | **Documented** — use containers |
| P1 | Migrate remaining SQLite clusters to PostgreSQL | Ready — script exists |
| P2 | Identify next cluster for canonicalization | Blocked — need cluster selection logic |
| P3 | GitNexus 1,985 reports stuck at `evidence` | Unresolved — build from source failed |
| P4 | 178 orphan zips in PartsFactory | Unresolved — may contain unique content |
| P5 | `opencode-session` container unhealthy | Unresolved — port 4096 |
| P6 | `cmplx-live` container exited 22h ago | Unresolved — port 8850 |

**Immediate next action**: Select next cluster for canonicalization. Candidates by frequency across spaces:
- `server.py` (7 systems)
- `Dockerfile` (6 systems)
- `AGENTS.md` (6 systems)
- `registry.py` / `engine.py` / `thinktank.py` (4 systems each)

---

## 6. Work Window Compliance

- **0–12.5%**: ✅ Knowledge gate passed — reviewed brain state, memory tests, defined contract
- **Current**: Infrastructure accounting complete, first canonical cluster in PostgreSQL
- **Next 12.5% target**: Canonicalize second cluster (likely `server.py` or `AGENTS.md`)
- **Final 12.5%**: Accounting, manifest, risks, next-start knowledge test

---

*Agent: CMPLX Agent | Space: PartsFactory | Constitution: AGENTS.md v1.0*
