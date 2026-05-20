# Global Operations System API

Generated: 2026-05-14

## Purpose

The third live routed slice is `operations`. It exposes safe control-plane
status through `repo-kernel` while leaving the underlying repo-kernel and
GitNexus containers on their existing ports.

This is a read-only routing pass. Restarts, scale operations, service mutation,
GitNexus writes, and backend commands remain approval-gated.

## API

- `GET /api/global/operations`
- `GET /api/global/operations/tools`
- `GET /api/global/operations/routes`
- `GET /api/global/operations/ports`
- `GET /api/global/operations/skills`
- `POST /api/global/operations/call-plan`
- `GET /api/global/operations/upstreams`
- `GET /api/global/operations/health`
- `GET /api/global/operations/read/{service}/{path}`

MCP mirrors:

- `repo_kernel_global_operations_upstreams`
- `repo_kernel_global_operations_read`

## Live Routed Upstreams

The current Docker-backed operations slice is healthy behind repo-kernel:

- `repo-kernel`
- `gitnexus-rebuild-server`
- `gitnexus-rebuild-web`

Approved read examples:

- `repo-kernel`: `/`, `/api/health`
- `gitnexus-rebuild-web`: `/`

`repo-kernel` self reads are synthesized in-process instead of recursively
calling the repo-kernel HTTP server from inside its own request. This avoids the
self-call timeout observed during runtime health planning.

The GitNexus backend container is health-tracked as an upstream, but it is not
read-proxied yet because it did not expose a clean safe REST status/OpenAPI
surface during this pass.

## Examples

```powershell
Invoke-RestMethod http://localhost:8786/api/global/operations/upstreams
Invoke-RestMethod http://localhost:8786/api/global/operations/health
Invoke-RestMethod http://localhost:8786/api/global/operations/read/repo-kernel/api/health
Invoke-RestMethod http://localhost:8786/api/global/operations/read/gitnexus-rebuild-web/
```

## Policy

1. Public callers use `repo-kernel` on port `8786`.
2. Existing upstream ports and settings remain untouched.
3. GET reads are allowlisted.
4. Backend writes, restarts, and mutation paths remain blocked.
5. GitNexus backend route discovery is a follow-up before write or command
   routing.
