# Global Live Slices Pass - 2026-05-14

Repo-kernel now routes four more live service families behind `/api/global/<system>` without moving their existing ports.

## New Routed Slices

- `ai-runtime`
- `validation`
- `synthesis`
- `external-ai-portal`

Each slice exposes:

- `GET /api/global/{system}/upstreams`
- `GET /api/global/{system}/health`
- `GET /api/global/{system}/read/{service}`
- `GET /api/global/{system}/read/{service}/{path}`

## Upstreams

`ai-runtime`:

- `research-api`
- `manny-manifold-api`

`validation`:

- `speedlight-api`
- `db-aggregator-api`

`synthesis`:

- `manny-manifold-api`
- `unique-systems-api`

`external-ai-portal`:

- `ngrok-cmplx`
- `opencode-session` is disabled evidence until an auth-safe status/read contract is defined.

## Policy

These are read-only control routes. Repo-kernel proxies only allowlisted health, status, catalog, summary, and tunnel-inspection paths. Execution, generation, validation mutation, portal control, and auth-gated actions stay blocked.

Existing upstream ports remain unchanged. Public callers should use repo-kernel on port `8786`.
