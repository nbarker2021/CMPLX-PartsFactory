---
name: hook-pause-gates
description: "Use for CMPLX hook behavior, pause gates, continuation discipline, and translating native/generic hooks into project-specific memory/provenance/safety behavior."
---

# Hook Pause Gates

## Purpose

Hooks are the CMPLX linear pause layer. They force the agent to stop at boundaries, inform itself, apply policy, inject memory, record provenance, and then continue.

## Gates

Use these gates during substantial work:

1. Session start: read local control and latest identity memory.
2. User prompt: classify the request and translate names into concepts.
3. Pre-tool: state what will be read/probed/searched and why.
4. Post-tool: report what was learned and what remains unknown.
5. Pre-edit: confirm writable boundary and search existing implementations.
6. Post-edit: verify and record durable memory if needed.
7. Stop/final: sanity-check newest user request and unfinished work.
8. Compaction/continuation: preserve sources, user corrections, next reads, and risks.

## Underinformed Work Rule

Trigger a refresh anywhere a normal AI would continue from stale, generic, missing, name-only, or tool-output-only context. The hook boundary itself is the warning sign.

Use this routing:

| Boundary | Refresh To | Why |
|---|---|---|
| Session start/resume | `cmplx-memory-review`, `repo-kernel-control` | Prevent stale cold-start context. |
| User prompt / chat message | `cmplx-memory-review` | Translate names into concepts before acting. |
| Skill reminder / category selection | matching CMPLX skill | Avoid raw-tool work without procedure. |
| Before read/search/tool | `cmplx-tool-discovery`, existing indexes | Prevent broad blind scans and wrong-tree reads. |
| Before edit/write/shell mutation | `cmplx-memory-review`, `cmplx-tool-discovery` | Confirm boundary and existing lineage. |
| After tool output | `hook-pause-gates`, `cmplx-memory-review` | Absorb findings into the working map. |
| Catalog/composition work | `cmplx-catalog-build`, `cmplx-composition-test` | Preserve provenance and conservation checks. |
| Compaction/resume/stop | `hook-pause-gates`, durable checkpoint | Preserve continuation state. |

The machine-readable version of this map lives in `.opencode\oh-my-opencode.jsonc` under `cmplx_control.hooks.trigger_routes`.

## Native Hook Translation

- `agent-usage-reminder`: pause before delegation; do not spawn agents unless explicitly requested.
- `category-skill-reminder`: check applicable skills before tools.
- `keyword-detector`: CMPLX/CQE/Manny/TMN/SNAP/MMDB/MDHG/MORSR/TarPit/SpeedLight/Aletheia terms trigger memory review.
- `think-mode`: use a plan or reading map for deep review/merge/design.
- `start-work`: announce the first read/probe.
- `ralph-loop`: keep read -> synthesize -> checkpoint cadence.
- `comment-checker`: add comments only when they clarify non-obvious logic.
- `todo-continuation-enforcer`: keep task status current.
- `auto-update-checker`: browse only when current/external facts require it; otherwise use local evidence.
- `prometheus-md-only` and `sisyphus-junior-notepad`: write durable markdown checkpoints/registers under `D:\PartsFactory\identity_review`.

## Output

State which gate mattered and what it changed in the work.
