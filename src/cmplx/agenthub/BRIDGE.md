# agenthub — Bridge

## Dependencies consumed

| Port | Purpose | Required |
|------|---------|----------|
| `memory` | MMDB-backed ingest/query for session memory | No |
| `runtime` | Agent task execution (`run_task`, `get`) | No |

Both are optional. The hub is fully functional for registration and
status tracking without them.

## Dependencies provided

| Port | Symbol |
|------|--------|
| `agenthub` | `AgentHubProvider` |

## Cross-component semantics

- **cognition.brain** — brain states may be updated by `run_agent_task`
- **memory.mmdb** — backing store for `append_memory` / `recall`
- **routing.agrm** — may route messages between hub sessions

## Static imports

None — pure Python standard library.
