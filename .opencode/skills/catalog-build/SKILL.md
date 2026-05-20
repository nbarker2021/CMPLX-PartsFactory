---
name: catalog-build
description: "Build, repair, or migrate PartsFactory catalog evidence after checking existing indexes first. Use when the catalog is empty, corrupted, stale after confirmed new evidence, or needs schema migration."
---

# Catalog Build Skill

## When to Use

- "Build the catalog"
- "Rebuild the index"
- "Initialize catalog database"
- "Migrate catalog schema"
- confirmed catalog corruption
- a new evidence family has no existing index coverage

## Workflow

```
1. Run cmplx-memory-review gate
2. Inspect existing indexes before rebuilding
3. Confirm rebuild/migration scope and writable target
4. Ensure catalog/ directory exists
5. Create or migrate artifact_index.sqlite schema
6. Run tool-discovery skill with bounded roots
7. Populate schema with discovered tools and lineage
8. Generate catalog/manifest.json
9. Validate random entries, lineage links, and counts
10. Record checkpoint/register update if this changes the corpus map
```

## Checklist

```
- [ ] Memory gate completed
- [ ] Existing indexes checked
- [ ] Rebuild scope is explicit
- [ ] catalog/ directory exists
- [ ] artifact_index.sqlite created or migrated
- [ ] tool-discovery completed
- [ ] All tools inserted into database
- [ ] manifest.json generated
- [ ] Validation queries pass
- [ ] identity_review updated if findings changed
```

## Schema

```sql
CREATE TABLE IF NOT EXISTS tools (
    tool_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source TEXT,
    source_type TEXT,
    file_path TEXT,
    table_name TEXT,
    schema_name TEXT,
    description TEXT,
    families TEXT,        -- JSON array
    capabilities TEXT,    -- JSON array
    e8_routing TEXT,      -- JSON object
    discovered_at TEXT,
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 1.0,
    compositions_tested TEXT  -- JSON array
);

CREATE TABLE IF NOT EXISTS compositions (
    composition_id TEXT PRIMARY KEY,
    tool_ids TEXT,        -- JSON array
    composition_type TEXT,
    description TEXT,
    success INTEGER,
    execution_time_ms REAL,
    output_quality REAL,
    delta_phi REAL,
    bonds_formed INTEGER,
    receipts_generated INTEGER,
    tested_at TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS lineage (
    lineage_id TEXT PRIMARY KEY,
    tool_id TEXT,
    ancestor_id TEXT,
    relationship TEXT,    -- "variant_of", "supersedes", "forked_from"
    provenance_path TEXT
);
```

## Example: "Build catalog from scratch"

```
1. Read identity_review registers and current catalog files.
2. Confirm existing indexes do not already answer the request.
3. Create or migrate catalog/artifact_index.sqlite.
4. Execute tool-discovery with bounded roots.
5. Insert results into tools and lineage tables.
6. Generate manifest.json.
7. Validate and report counts plus provenance.
```
