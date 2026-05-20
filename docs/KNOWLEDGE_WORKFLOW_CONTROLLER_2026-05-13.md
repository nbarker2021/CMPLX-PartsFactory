# Knowledge Workflow Controller

Generated: 2026-05-13

## Purpose

The knowledge controller gives local agents a bounded way to ask what search,
retrieval, KB, corpus, semantic, and code-context surfaces exist across the
promoted repos.

It is part of the repo-kernel agentic offload layer: use Docker to answer
capability and planning questions before recursively scanning the wider source
universe.

## API

- `GET /api/unified/knowledge`
- `GET /api/unified/knowledge/capabilities`
- `POST /api/unified/knowledge/plan`
- `GET /api/unified/knowledge/runtime-preflight`

MCP mirrors:

- `repo_kernel_knowledge_capabilities`
- `repo_kernel_knowledge_plan`
- `repo_kernel_knowledge_runtime_preflight`

## Verified Surface

- 162 route candidates
- 25 MCP tool candidates
- 13 runtime targets

Roles:

- `library`
- `query`
- `semantic`
- `kb`
- `code_context`
- `ingestion`
- `atlas`

## Policy

Search, query, lookup, retrieve, and read-style routes are planning candidates.

Index, ingest, store, insert, update, train, sync, and delete-style operations
are returned as mutating candidates only. Do not execute them without explicit
approval.

Runtime services are still compose/README evidence. The controller health-checks
ports, but it does not start services.

## Example

```powershell
$body = @{
  task = 'knowledge search and retrieval'
  role = 'query'
  query = 'mmdb corpus evidence'
  dry_run = $true
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://localhost:8786/api/unified/knowledge/plan `
  -ContentType 'application/json' `
  -Body $body
```
