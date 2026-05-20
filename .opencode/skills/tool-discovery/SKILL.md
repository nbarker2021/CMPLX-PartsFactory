---
name: tool-discovery
description: "Discover CMPLX tools/capabilities across existing indexes, repo-kernel evidence, SQLite, PostgreSQL, and filesystem sources with provenance. Use when the user asks what tools exist, catalog coverage is unknown, or a concept needs implementation discovery."
---

# Tool Discovery Skill

## When to Use

- "What tools do we have?"
- "Scan the catalog"
- "Index the manifold"
- "Discover new tools"
- concept implementation discovery
- before saying a capability does not exist

## Workflow

```
1. Run cmplx-memory-review gate
2. Read existing indexes and manifests first
3. Probe repo-kernel health and targeted evidence routes if relevant
4. Query SQLite sources only if indexes do not answer the question
5. Query PostgreSQL only with explicit approval when writes or sensitive DB access are possible
6. Scan filesystem with bounded roots and exclusions
7. Update catalog/artifact_index.sqlite only when the user asked for persistence
8. Record provenance and unresolved gaps
```

## Checklist

```
- [ ] Memory gate completed
- [ ] Existing indexes checked
- [ ] Repo-kernel evidence checked if relevant
- [ ] SQLite sources checked if needed
- [ ] PostgreSQL read/write risk assessed
- [ ] Filesystem roots bounded
- [ ] Discovery harness executed if needed
- [ ] Catalog manifest updated only if requested
- [ ] Artifact index persisted only if requested
- [ ] Report generated
```

## Tools

**PostgresDiscovery** — scan_unification_hub(), scan_unification_aggregator()
**SQLiteDiscovery** — scan_memory_db(), scan_all()
**FileSystemDiscovery** — scan_brain_files(), scan_key_systems()

## Example: "Discover all tools"

```
1. Check identity_review and existing catalog/index files.
2. Search bounded roots with rg/rg --files.
3. Query repo-kernel or local SQLite when useful.
4. Report tools found by source and provenance.
5. Persist only when requested or clearly part of catalog-build.
```
