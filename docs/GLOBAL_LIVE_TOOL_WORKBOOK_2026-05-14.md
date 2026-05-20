# Global Live Tool Workbook

Generated: 2026-05-14

## Purpose

This workbook is the working inventory of what I can actually use through the
live `repo-kernel` control layer.

It is intentionally not just a prose note. The same inventory is exposed by the
controller:

- `GET /api/global-tool-workbook`
- MCP tool `repo_kernel_global_tool_workbook`

Use this at the start of live work to refresh what is available, what is blocked
by design, and what still needs API-layer work.

## Control Layer

- Service: `repo-kernel`
- Public base URL: `http://localhost:8786`
- Rule: use `/api/global/...` routes for live work instead of directly calling
  upstream service ports.

## Routed Slices Available Now

### Global Query

Available through:

- `GET /api/global/query?q=<term>`
- `POST /api/global/query`
- MCP tool `repo_kernel_global_query`

Useful examples:

- `/api/global/query?q=receipt&limit=10`
- `/api/global/query?q=adapter&systems=memory&systems=knowledge`
- `/api/global/query?q=receipt&dry_run=true`

### Memory

Available through:

- `GET /api/global/memory/upstreams`
- `GET /api/global/memory/health`
- `GET /api/global/memory/search?q=<term>`
- `GET /api/global/memory/read/{service}/{path}`

Useful examples:

- `/api/global/memory/search?q=receipt&limit=5`
- `/api/global/memory/read/pocket-memory-api/health`
- `/api/global/memory/read/mmdb-unified/stats`

### Geometry

Available through:

- `GET /api/global/geometry/upstreams`
- `GET /api/global/geometry/health`
- `GET /api/global/geometry/read/{service}/{path}`

Useful examples:

- `/api/global/geometry/read/tarpit-api/stats`
- `/api/global/geometry/read/unique-systems-api/summary`
- `/api/global/geometry/read/snap-unified/health`

### Operations

Available through:

- `GET /api/global/operations/upstreams`
- `GET /api/global/operations/health`
- `GET /api/global/operations/read/{service}/{path}`

Useful examples:

- `/api/global/operations/read/repo-kernel/api/health`
- `/api/global/operations/read/gitnexus-rebuild-web/`

### Knowledge

Available through:

- `GET /api/global/knowledge/upstreams`
- `GET /api/global/knowledge/health`
- `GET /api/global/knowledge/search?q=<term>`
- `GET /api/global/knowledge/read/{service}/{path}`

Useful examples:

- `/api/global/knowledge/search?q=adapter&limit=5`
- `/api/global/knowledge/read/research-api/health`

### Named Capabilities

These are actual tool surfaces promoted from noisy repo slices. They are
read-only and execution is exposed only as a call plan.

Knowledge ingest:

- `GET /api/global/knowledge/devkit-ingest`
- `GET /api/global/knowledge/devkit-ingest/tree`
- `GET /api/global/knowledge/devkit-ingest/files/ingest/ocr_pipeline.py`
- `POST /api/global/knowledge/devkit-ingest/call-plan`

Code execution:

- `GET /api/global/code-execution/octa64`
- `GET /api/global/code-execution/octa64/tree`
- `GET /api/global/code-execution/octa64/files/pack.py`
- `POST /api/global/code-execution/octa64/call-plan`

Validation:

- `GET /api/global/validation/mcp-os`
- `GET /api/global/validation/mcp-os/tree`
- `GET /api/global/validation/mcp-os/files/system_validator.py`
- `POST /api/global/validation/mcp-os/call-plan`

Synthesis:

- `GET /api/global/synthesis/cqe-modular`
- `GET /api/global/synthesis/cqe-modular/tree`
- `GET /api/global/synthesis/cqe-modular/files/cqe_sdk.py`
- `POST /api/global/synthesis/cqe-modular/call-plan`

MCP:

- `GET /api/global/mcp/local-os`
- `GET /api/global/mcp/local-os/tree`
- `GET /api/global/mcp/local-os/files/MCP_OS_INVENTORY.md`
- `POST /api/global/mcp/local-os/call-plan`

## Safety Blocks

- Mutating upstream paths are blocked in these first routed slices.
- `403` means the controller intentionally blocked a path.
- `409` means a known upstream is disabled evidence rather than a routable
  service.
- `research-api-jupyter` is disabled until it is explicitly fixed or removed.
- `gitnexus-rebuild-server` is health-tracked but not read-proxied until a safe
  backend status route is identified.
- Host port reassignment remains deferred.

## API-Layer Needs

The workbook currently tracks these needs:

1. Tune `/api/global/query` ranking and add snippets after canonical result
   schema v2.
2. Define a canonical `/api/global/knowledge/search` response shape over
   db-aggregator results, repo surfaces, and future indexes.
3. Add or identify real `research-api` read/query endpoints; it is health-only
   right now.
4. Fix/start/remove `research-api-jupyter`.
5. Keep this workbook updated whenever a routed slice or allowlist changes.

## Client Notes

Repeated query parameters need to be encoded as repeated keys:

```text
modules=CMPLXUNI&modules=CMPLX-TMN-main
```

Do not encode them as a list string when talking to FastAPI from a simple
client.
