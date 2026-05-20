# Repo Kernel Control Layer

Use this note when an agent, hook, or directory injector needs to orient itself
inside CMPLX-PartsFactory.

## Runtime

- Controller: `http://localhost:8786`
- Compose file: `docker-compose.repo-kernel.yml`
- Health: `GET /api/health`
- Workbook: `GET /api/global-tool-workbook`
- Compact state: `GET /api/global-state`
- GitNexus status: `GET /api/gitnexus/status`

## Current Named Capabilities

- `GET /api/global/knowledge/devkit-ingest`
- `GET /api/global/mcp/local-os`
- `GET /api/global/code-execution/octa64`
- `GET /api/global/validation/mcp-os`
- `GET /api/global/synthesis/cqe-modular`

All three are read-only, adapter-backed, and plan-only for execution. Use their
`/call-plan` routes to describe execution intent; do not run repo-local source
directly unless a later promotion explicitly enables it.

## Agent Rule

Prefer the repo-kernel global API over direct upstream ports. Treat `403` as an
intentional safety block and `409` as disabled evidence requiring a runtime
decision.
