# Repo Kernel Control

Use this skill for CMPLX-PartsFactory repo unification work, especially when
surfacing tools from noisy repos behind the repo-kernel controller.

## Control Plane

- Base URL: `http://localhost:8786`
- Compose file: `docker-compose.repo-kernel.yml`
- Workbook: `/api/global-tool-workbook`
- Compact state: `/api/global-state`
- GitNexus evidence: `/api/gitnexus/status`

## Current Surfaced Tools

- `/api/global/knowledge/devkit-ingest`
- `/api/global/mcp/local-os`
- `/api/global/code-execution/octa64`
- `/api/global/validation/mcp-os`
- `/api/global/synthesis/cqe-modular`

Use each capability's `/tree`, `/files/{path}`, and `/call-plan` routes rather
than importing or executing source directly.

## Policy

The clean repo checkouts remain the source of implementation evidence. The
controller is the runtime authority. Execution and mutation stay blocked until
a named capability has sandbox, input, output, and test gates.
