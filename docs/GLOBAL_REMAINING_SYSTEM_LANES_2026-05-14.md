# Global Remaining System Lanes

Generated: 2026-05-14

## Purpose

This note records the next batch of global system lanes added behind the same
controller used for MCP, memory, agent orchestration, and knowledge.

These lanes use existing repo-kernel workflow evidence. They aggregate tools,
routes, ports, skills, and repo-local source paths without moving source,
starting services, importing data, or mutating runtimes.

## Added Lanes

| System | Global API | Primary Runtime Evidence |
| --- | --- | --- |
| `geometry` | `/api/global/geometry` | `tmn2-morphon`, `tmn2-glyph`, `tmn2-crystal`, `tmn2-morsr`, `tmn2-morphon-field` |
| `training` | `/api/global/training` | `tmn2-teaching`, `tmn2-trainer`, `tmn2-rl-trainer` |
| `code-execution` | `/api/global/code-execution` | `tmn2-portal`, `tmn2-portal-companion`, `tmn2-sandbox-interface`, `tmn2-mdhg-sandbox`, `tmn2-kb-code`, `tmn2-cmplxcode` |
| `pipeline` | `/api/global/pipeline` | `tmn2-intake`, `tmn2-harvester`, `tmn2-ingress-egress`, `tmn2-staging`, `tmn2-pipeline`, `tmn2-intake-reviewer` |
| `external-ai-portal` | `/api/global/external-ai-portal` | `tmn2-gateway`, `tmn2-portal`, `tmn2-portal-companion`, `tmn2-ngrok` |

## API Shape

Each lane exposes:

- `GET /api/global/<system>`
- `GET /api/global/<system>/tools`
- `GET /api/global/<system>/routes`
- `GET /api/global/<system>/ports`
- `GET /api/global/<system>/skills`
- `POST /api/global/<system>/call-plan`

Each lane is also available through the generic form:

- `GET /api/global-systems/<system>`
- `GET /api/global-systems/<system>/tools`
- `GET /api/global-systems/<system>/routes`
- `GET /api/global-systems/<system>/ports`
- `GET /api/global-systems/<system>/skills`
- `POST /api/global-systems/<system>/call-plan`

## Policy

The global controller aggregates same-name capabilities instead of overwriting
them. Local source references are normalized to
`repo_kernel/repos/<module>/...`.

Tool, route, and service call plans remain planning-only. Service activation
requires explicit approval after selecting a runtime slice and checking health.
