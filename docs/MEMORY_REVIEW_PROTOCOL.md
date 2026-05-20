# Brain & Memory Review Protocol

## Mandatory Before All Work

Before beginning any substantial design, coding, or composition task, you **must** complete a deep memory review. This is not optional warmup. The brain files and historical work across this ecosystem contain the accumulated weights of previous sessions. Working without them is working blind.

## The Three Brain Sources

### 1. Session Memory (Immediate Context)

Read the most recent work-window files to understand what was happening when the last session ended:

- `/mnt/d/PartsFactory/work/unified/STATUS.md` — current build status
- `/mnt/d/PartsFactory/work/unified/DESIGN.md` — design decisions and architecture
- `/mnt/d/PartsFactory/CMPLX-PartsFactory/AGENTS.md` — this repo's current state
- `/mnt/d/OC build/journal/sessions/` — OC Build session logs
- `/mnt/d/OC build/scratch/work-window-current.md` — active work window

### 2. Historical Brain Files (Accumulated Weights)

These are the persistent brain implementations that hold the system's accumulated knowledge. Read them deeply, not just headers:

**Primary Brains:**
- `/mnt/d/PartsFactory/work/unified/src/cmplx/cmplx_brain.py` (48K lines) — The unified brain with E8 experts, Hebbian learning, triads, gating
- `/mnt/d/PartsFactory/work/unified/src/cmplx/memory.py` (63K lines) — Lane-first memory with full tool integration
- `/mnt/d/PartsFactory/work/unified/src/cmplx/mcp.py` (26K lines) — Master Control Program
- `/mnt/d/PartsFactory/work/unified/src/cmplx/unified_api.py` (42K lines) — Master API process tree

**Supporting Cognitive Systems:**
- `/mnt/d/PartsFactory/work/unified/src/cmplx/nanoclaw.py` — Nano-agent claw
- `/mnt/d/PartsFactory/work/unified/src/cmplx/orchestrator.py` — Orchestration layer
- `/mnt/d/PartsFactory/work/unified/src/cmplx/field_experts.py` — Expert domain matching
- `/mnt/d/PartsFactory/work/unified/src/cmplx/knowledge_synthesizer.py` — Knowledge synthesis
- `/mnt/d/PartsFactory/work/unified/src/cmplx/data_reasoner.py` — Data reasoning

**Legacy Brain References (for understanding evolution):**
- `/mnt/d/Manny Unification 2/proposals/manny-unified-build-2026-05-09/manny_runtime/brain.py` — Most complete unified brain spec
- `/mnt/d/Manny Unification 2/historical builds/MannyAI/brain/brain.py` — Production brain
- `/mnt/d/Manny Unification 2/historical builds/CMPLX-TMN3/src/claude_brain_hub.py` — Claude brain hub
- `/mnt/d/Manny Unification 2/Working Prototyping/services/brain-unified/brain.py` — OpenCMPLX brain service

### 3. Database Memories (External Knowledge)

Query these for tool capabilities, historical outputs, and expert definitions:

**PostgreSQL (if available):**
- `unification_hub.manny_experts.expert` — 453 experts with E8 positions
- `unification_aggregator` — 8 schemas of artifacts and sources

**SQLite:**
- `/mnt/d/Manny Unification 2/ai_memory/ai_memory/memory.db` — 254 tools from ability_map + 63 capabilities

**Query before claiming a tool doesn't exist:**
```python
# From discovery harness
from src.discovery import PostgresDiscovery, SQLiteDiscovery
pg = PostgresDiscovery()
sqlite = SQLiteDiscovery("/mnt/d/Manny Unification 2/ai_memory/ai_memory/memory.db")
```

## Deep Review Requirements

### What "Deep" Means

- **Read full docstrings and class definitions**, not just file headers
- **Trace inheritance and composition** relationships between components
- **Understand data flow**: where does input enter, how is it transformed, where does output go
- **Know the lane system**: HARMONIC (DR=3), COEXACT (DR=6), EXACT (DR=9)
- **Know the phase system**: INGEST → PROCESS → STORE → RETRIEVE → BOND
- **Understand ΔΦ ≤ 0 constraint** and how morphon dynamics enforce it
- **Know the E8 routing**: how inputs map to expert activations

### What To Extract

For each brain file reviewed, record:

1. **Core purpose** — What does this component do in one sentence?
2. **Input/output contracts** — What does it accept, what does it produce?
3. **Dependencies** — What other components must be present for this to work?
4. **State management** — What does it remember between calls?
5. **Extension points** — Where can new behavior be added?
6. **Current gaps** — What is stubbed, TODO, or incomplete?
7. **Usage pattern** — How would another component call this?

### Review Output

Write findings to:
- `docs/brain-review-<component>-<date>.md`
- Update `docs/MEMORY_INDEX.md` with cross-references

## The Review Checklist

Before claiming you understand the system, verify you can answer:

- [ ] What are the 8 tool families and their capabilities?
- [ ] How does the memory lane system classify data?
- [ ] What is the full pipeline from raw input to stored memory?
- [ ] How do E8 coordinates get assigned to content?
- [ ] What triggers expert spawning in the brain?
- [ ] How are bonds formed between memory entries?
- [ ] What is the receipt chain and why does it matter?
- [ ] How does the personal_node concept relate to the brain?
- [ ] What Docker services are currently live?
- [ ] What databases exist and what do they contain?
- [ ] What was the last work window trying to accomplish?
- [ ] What blocked the last session from completing?

## Anti-Patterns (Do Not Do)

- **Skimming**: Reading only the first 50 lines of a 48K-line brain file
- **Assuming absence**: Claiming a capability doesn't exist without querying the database
- **Rebuilding from scratch**: Ignoring existing implementations to write new stubs
- **Shallow testing**: Running demos without understanding the full data flow
- **Forgetting constraints**: Violating ΔΦ ≤ 0, lane rules, or phase ordering

## Work Window Integration

The 0-12.5% knowledge gate must include:

1. **Brain state check**: What do the brain files say about current system state?
2. **Memory continuity**: What was the last operation and its result?
3. **Expert availability**: Which experts are loaded and what do they know?
4. **Database snapshot**: What has changed in Postgres/SQLite since last session?
5. **Container health**: What services are running and what are their statuses?

Only after this review is complete may you proceed to the work contract and scheduler.

## Emergency Override

If a critical issue requires immediate action before full review:

1. State explicitly that you are overriding the review protocol
2. Record what review steps were skipped
3. Schedule a catch-up review for the next checkpoint
4. Document what assumptions you are making without verification
