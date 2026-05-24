# agenthub — Interface

**AgentHub** is the broadcast network. Where TMN handles requests,
AgentHub handles the *between* — the message bus that ties agents
together.

## Port

- **`agenthub`** on `MorphonController` (not yet registered in `register_all()`)

## Public surface

```python
from cmplx.agenthub import AgentHubProvider

hub = AgentHubProvider()
hub.create_session(name="demo")
hub.register_agent(session_id="...", agent_id="alice", role="planner", goal="plan")
hub.session_status(session_id="...")
```

## Optional async surface

When `memory_pipeline` and `runtime` are injected at construction:

```python
await hub.append_memory(session_id="...", content="hello", role="user")
await hub.recall(session_id="...", query="hello")
await hub.run_agent_task(session_id="...", agent_id="alice", task_description="...")
```

If dependencies are absent, these methods return `{"error": "... not configured"}`.

## State types

- `HubSession` — session container with agents and memory event counter
- `AgentRecord` — agent identity within a session
- `HubState` — top-level mutable state

## HTTP adapter

FastAPI service on port **8846** (planned; `_adapters/http_service.py` stub).
