# arena — Interface

**Arena** is the competitive evaluation layer. It runs morphons
against each other in scheduled ticks, scores them, and assigns
reward.

## Port

- **`arena`** on `MorphonController` (not yet registered in `register_all()`)

## Public surface

```python
from cmplx.arena import ArenaProvider, TRAINING_SYSTEMS

arena = ArenaProvider(db_path="arena.db")
arena.list_modules()          # 17 training modules
arena.signup("alice", "delve")
party = arena.form_party("delve")
arena.complete_session(party["session_id"], results={...})
arena.get_leaderboard("delve")
arena.economy_stats()
```

## Module registry

17 modules: `assembly_dtt`, `delve`, `gati`, `gauntlet`, `permutate`,
`snap_workshop`, `scene8`, `whatifwhy`, `workshop`, `worldforge`,
`cartographer`, `doctoral`, `escape_room`, `guru`, `launchpad`,
`reflex`, `tilt`.

Each has `min_party`, `max_party`, `base_cost`, `description`.

## HTTP adapter

FastAPI service on port **8847** (planned; `_adapters/http_service.py` stub).
