# Repo Kernel Promotion Cycle

Generated: 2026-05-13T14:14:13.878439+00:00

## Summary

| Module | Status | Readiness | Capabilities |
| --- | --- | ---: | --- |
| `CMPLXUNI` | adapter_ready | 100.0 | fastapi_surface, mcp_surface, nextjs_api_routes, python_api_routes, src_tree |
| `CMPLX-TMN-main` | adapter_ready | 81.2 | fastapi_surface, python_api_routes, src_tree |
| `CMPLXMCP` | adapter_ready | 76.2 | fastapi_surface, mcp_surface, python_api_routes |

## Surface Catalog

| Module | FastAPI Routes | MCP Tools | Next.js Routes | Skipped |
| --- | ---: | ---: | ---: | ---: |
| `CMPLXUNI` | 176 | 83 | 8 | 19 |
| `CMPLX-TMN-main` | 633 | 0 | 0 | 1 |
| `CMPLXMCP` | 14 | 34 | 0 | 1 |

## Actions

### CMPLXUNI

- `adapter`: create a read-only CMPLXUNI adapter under the repo-kernel controller
- `api`: map discovered FastAPI/APIRouter endpoints into a controller route registry
- `mcp`: wrap MCP tools as delegated module capabilities
- `frontend-api`: catalog Next.js API route handlers as secondary service surfaces
- `tests`: add a capability smoke test before any source promotion

### CMPLX-TMN-main

- `adapter`: create a read-only CMPLX-TMN-main adapter under the repo-kernel controller
- `api`: map discovered FastAPI/APIRouter endpoints into a controller route registry
- `tests`: add a capability smoke test before any source promotion

### CMPLXMCP

- `adapter`: create a read-only CMPLXMCP adapter under the repo-kernel controller
- `api`: map discovered FastAPI/APIRouter endpoints into a controller route registry
- `mcp`: wrap MCP tools as delegated module capabilities
- `tests`: add a capability smoke test before any source promotion
