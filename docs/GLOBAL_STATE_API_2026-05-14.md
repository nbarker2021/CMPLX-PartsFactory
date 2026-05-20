# Global State API

Generated: 2026-05-14

## Purpose

`/api/global-state` is the fast compact state endpoint for the control layer.
It exists because full all-repo coverage and health scans can be slow enough to
time out during normal live work.

Use it when the question is:

- what is routed now?
- what is ready?
- what is disabled?
- what should be routed next?
- what API-layer needs remain?

## API

- `GET /api/global-state`
- MCP tool `repo_kernel_global_state`

Query parameters:

- `check_health`: optional targeted health for routed systems
- `timeout_seconds`: per-upstream health timeout

## Response

The compact state returns:

- routed system count
- ready system count
- available live tool count
- disabled upstream count
- routed systems with upstream/tool counts
- next routing candidates
- active API-layer needs
- fast paths for workbook/query/runtime slices

## Policy

This endpoint intentionally avoids full all-repo coverage scans. Use
`/api/global-coverage` only when a slower complete scan is acceptable.
