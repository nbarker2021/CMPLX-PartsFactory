# arena — Bridge

## Dependencies consumed

| Port | Purpose | Required |
|------|---------|----------|
| `economy` | Entry-fee / reward coin ops | No (uses internal economy table) |
| `receipt` | Session completion provenance | No |

## Dependencies provided

| Port | Symbol |
|------|--------|
| `arena` | `ArenaProvider` |

## Cross-component semantics

- **cognition.brain** — brain states updated by module graduation
- **economy** — external economy may back the arena treasury
- **routing.agrm** — may route agents to optimal modules

## Static imports

`sqlite3` (stdlib) — no external dependencies.
