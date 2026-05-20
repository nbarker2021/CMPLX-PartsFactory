# Global Knowledge System API

Generated: 2026-05-14

## Purpose

The fourth live routed slice is `knowledge`. It routes safe knowledge/search and
catalog reads through `repo-kernel` while keeping the existing research and
database aggregator services on their current ports.

This is a read-only routing pass. Discovery, indexing, imports, report
generation, and other mutation paths remain approval-gated.

## API

- `GET /api/global/knowledge`
- `GET /api/global/knowledge/tools`
- `GET /api/global/knowledge/routes`
- `GET /api/global/knowledge/ports`
- `GET /api/global/knowledge/skills`
- `POST /api/global/knowledge/call-plan`
- `GET /api/global/knowledge/upstreams`
- `GET /api/global/knowledge/health`
- `GET /api/global/knowledge/search?q=<term>`
- `GET /api/global/knowledge/prototype-claims?q=<term>`
- `GET /api/global/knowledge/read/{service}/{path}`

MCP mirrors:

- `repo_kernel_global_knowledge_upstreams`
- `repo_kernel_global_knowledge_read`
- `repo_kernel_prototype_evidence_search`

## Live Routed Upstreams

Enabled upstreams:

- `research-api`
- `db-aggregator-api`

Disabled evidence:

- `research-api-jupyter`: observed at `localhost:8888`, but refused container
  connections from repo-kernel; kept as evidence until explicitly started,
  fixed, or removed.

Approved read examples:

- `research-api`: `/health`
- `db-aggregator-api`: `/`, `/health`, `/mcp/tools`, `/search`,
  `/ingest/status`, `/discovery/checkpoints`, `/restore`, `/receipts`,
  catalog list/read paths, and catalog stats paths

Blocked examples include `/discover`, `/enqueue-discovery`, `/persist`, `/sync`,
report generation, status updates, and other mutation routes.

## API Layer Needs

The routed slice records the next API-layer work directly in its contract:

1. Define one canonical `/api/global/knowledge/search` response over
   db-aggregator results, repo surfaces, and future indexes.
2. Add or identify real read/query endpoints for `research-api`; it currently
   exposes health only.
3. Resolve or retire `research-api-jupyter` so disabled evidence does not remain
   ambiguous.
4. Promote prototype claim evidence into the durable knowledge index after the
   read-only search shape proves stable.

## Examples

```powershell
Invoke-RestMethod http://localhost:8786/api/global/knowledge/upstreams
Invoke-RestMethod http://localhost:8786/api/global/knowledge/health
Invoke-RestMethod "http://localhost:8786/api/global/knowledge/search?q=adapter&limit=5"
Invoke-RestMethod "http://localhost:8786/api/global/knowledge/prototype-claims?q=adapter&limit=5"
Invoke-RestMethod http://localhost:8786/api/global/knowledge/read/research-api/health
```

## Policy

1. Public callers use `repo-kernel` on port `8786`.
2. Existing upstream ports and settings remain untouched.
3. GET reads are allowlisted.
4. Indexing, import, discovery, and report-generation writes remain blocked.
5. The new global API shape can diverge from the upstream APIs as needs are
   implemented.
