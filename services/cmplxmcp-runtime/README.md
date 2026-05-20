# CMPLXMCP Runtime Shim

Purpose: provide a dedicated runtime wrapper for the promoted `CMPLXMCP` repo
without editing the cloned historical source.

Why this exists:

- `CMPLXMCP` README references an HTTP client target at `localhost:8900`.
- `mcp-server-entry.py` appears to start a stdio MCP server, not an HTTP server.
- Historical entry points reference `mcp_os`, but the repo currently exposes
  `server/` and `client/` packages directly.
- Direct imports require dependencies such as `numpy` that are intentionally not
  installed in the generic repo-kernel image.

This shim treats `CMPLXMCP` as a mounted module at `/module` and starts the
known-good internal package path directly:

```text
from server.server import CMPLXMCPServer
```

## Files

- `runtime_probe.py` verifies imports and server construction.
- `stdio_entry.py` starts the stdio MCP server.
- `Dockerfile` builds an isolated runtime image with CMPLXMCP dependencies.

## Build Probe

From the workspace root:

```powershell
docker build -t cmplxmcp-runtime:probe services/cmplxmcp-runtime
docker run --rm -v ${PWD}/repo_kernel/repos/CMPLXMCP:/module:ro cmplxmcp-runtime:probe python /app/runtime_probe.py
```

## Runtime

The initial supported transport is stdio MCP:

```powershell
docker run --rm -i -v ${PWD}/repo_kernel/repos/CMPLXMCP:/module:ro cmplxmcp-runtime:probe
```

HTTP/SSE transport should be added only after we confirm the intended MCP
transport bridge. Do not assume port `8900` is valid until that bridge exists.
