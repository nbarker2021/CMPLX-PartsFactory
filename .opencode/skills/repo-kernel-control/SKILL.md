# Repo Kernel Control

Use this skill when working in CMPLX-PartsFactory on repo unification, surfaced
tools, GitNexus evidence, or global controller routes.

## First Reads

1. Check controller health:
   `GET http://localhost:8786/api/health`
2. Refresh the live inventory when needed:
   `GET http://localhost:8786/api/global-tool-workbook`
3. Check compact state when you need the short version:
   `GET http://localhost:8786/api/global-state`
4. Check GitNexus evidence before broad scans:
   `GET http://localhost:8786/api/gitnexus/status`

If workbook or global-state routes time out, record the timeout and fall back
to bounded filesystem/index reads. Do not let an expensive route block the
review loop.

## Named Capabilities

- Knowledge ingest evidence: `/api/global/knowledge/devkit-ingest`
- MCP local OS evidence: `/api/global/mcp/local-os`
- Code execution evidence: `/api/global/code-execution/octa64`
- Validation evidence: `/api/global/validation/mcp-os`
- Synthesis evidence: `/api/global/synthesis/cqe-modular`

These capabilities are read-only and call-plan only. Do not execute underlying
repo-local code from these slices until the controller exposes an approved
execution route.

## Safety

- Prefer `/api/global/...` routes over direct service ports.
- Use `/call-plan` to describe intended mutations or executions.
- Treat `403` as a designed policy block.
- Treat `409` as disabled runtime evidence.
- Treat `allow_mutation: false` as the normal safe state.
- Do not bypass the controller with direct mutation because filesystem access is available.
- Keep `D:\Manny Unification 2` and `D:\OC build` read-only unless the user explicitly promotes a mutation.

## Report

Always report:

- controller health result
- route used
- timeout or policy block if any
- whether evidence came from controller or filesystem fallback
