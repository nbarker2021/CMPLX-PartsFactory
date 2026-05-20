# Master Build Template

A unified layout for the new system, synthesized from how the 12
historical CMPLX-* repos solved the same problem each in their own way.
The patterns below are convergent — features that appeared in multiple
repos and that fit our atomic-constructed canonicals cleanly.

## What was learned from the 12 historical repos

| Repo | Strongest pattern it contributed |
|---|---|
| **CMPLX** | Clear separation of `core/`, `src/`, `reference/`, `tools/`, `tests/`, with `pyproject.toml` + `tox.ini` for package discipline. |
| **CMPLX-1T** | The "knowledge layer" idea — `docs/`, `plans/`, `Wolfram study/`, `SHOWROOM/`, `intake-system/` as first-class siblings of code. |
| **CMPLX-Monorepo** | Sub-projects (`projects/`), backlog adapters, product/services split. Showed that domain projections deserve their own folders. |
| **CMPLX-TMN-main** | Minimal-clean: `capsules/`, `configs/`, `scripts/`, `src/`. The smallest viable shape. |
| **CMPLX-TMN1** | Domain-spec dirs (`infrastructure/`, `databases/`, `hooks/`, `showcase/`) — design-first. |
| **CMPLXMCP** | Service decomposition: one folder per concern (`adapters/`, `client/`, `codec/`, `controllers/`, `server/`, `validation/`). |
| **CMPLXUNI** | Layered library shape (`src/`, `lfai/`, `the-library/`, `mmdb/`), with `cmplx-nextjs/` as a frontend sibling. |
| **CMPLXDevKit** | Meta-toolkit pattern — nested namespace packages (`CMPLXDevKit/`, `CMPLXLOCALMCP/`) for shipping multiple distributable units. |
| **CMPLX-Manny** | Persona-and-orchestration repo: PowerShell launchers + `Working Prototyping/` + `INIT_RUNBOOK.md`. |
| **CMPLX-Formalization** | Documentation-as-source: `formal-specs/`, `mathematical-framework/`, `papers/`, `presentations/`. No `src/` at all. |
| **scout-demo-service** | Service-as-deployable: `Dockerfile`, `app.js`, `package.json`. Lean runtime container. |

## Universal conventions (in 8+ repos out of 12)

- `README.md` at root
- `.gitignore` (already drafted from yard noise)
- `AGENTS.md` or `CLAUDE.md` for AI-agent instructions
- `LICENSE` / `LICENSE.md`
- `CONTRIBUTING.md`
- `DISCLAIMER.md`
- `LICENSES/` (REUSE-compliant per-file license attribution)
- `REUSE.toml`
- `NOTICE`
- `NAVIGATION.md` — cross-reference index that lets a reader hop between
  the major doctrines and the major code locations

The new repo should keep these — they are the *contract* the historical
repos already shipped with, and dropping any of them is a regression.

---

## Proposed master layout

```
CMPLX-PartsFactory/                              # workspace root
├── README.md                                     # what this repo is, top-level entry
├── NAVIGATION.md                                 # the cross-reference index
├── AGENTS.md                                     # universal agent instructions
├── CLAUDE.md                                     # Claude-specific
├── LICENSE                                       # primary
├── LICENSES/                                     # REUSE attribution
├── REUSE.toml
├── CONTRIBUTING.md
├── DISCLAIMER.md
├── NOTICE
├── pyproject.toml                                # build config
├── .gitignore                                    # already drafted from noise tags
│
├── src/                                          # PRIMARY namespace package
│   └── cmplx/
│       ├── __init__.py
│       │
│       ├── morphon/                              # the primitive
│       │   ├── __init__.py
│       │   ├── morphon.py                        # ← atomic_constructed/morphon.py
│       │   └── ...
│       │
│       ├── geometry/                             # substrate
│       │   ├── __init__.py
│       │   ├── e8.py                             # ← atomic_constructed/e8.py
│       │   ├── leech.py                          # ← atomic_constructed/leech.py
│       │   ├── niemeier.py                       # ← atomic_constructed/niemeier.py
│       │   └── golay.py
│       │
│       ├── addressing/                           # MDHG
│       │   ├── __init__.py
│       │   └── mdhg.py                           # ← atomic_constructed/mdhg.py
│       │
│       ├── memory/                               # MMDB
│       │   ├── __init__.py
│       │   └── mmdb.py                           # ← atomic_constructed/mmdb.py
│       │
│       ├── transport/                            # chirp + transports
│       │   ├── __init__.py
│       │   └── chirp.py                          # ← atomic_constructed/chirp.py
│       │
│       ├── routing/                              # AGRM
│       │   ├── __init__.py
│       │   └── agrm.py                           # ← atomic_constructed/agrm.py
│       │
│       ├── cognition/                            # Brain + experts
│       │   ├── __init__.py
│       │   └── brain.py                          # (atomic-construct next iteration)
│       │
│       ├── constraints/                          # Aletheia
│       │   ├── __init__.py
│       │   └── aletheia.py                       # ← atomic_constructed/aletheia.py
│       │
│       ├── engine/                               # CQE / MORSR
│       │   ├── __init__.py
│       │   └── cqe.py                            # ← atomic_constructed/cqe.py
│       │
│       ├── symbolic/                             # Tarpit / MLambda
│       │   ├── __init__.py
│       │   └── tarpit.py                         # ← atomic_constructed/tarpit.py
│       │
│       ├── pipeline/                             # morphonic pipeline + lambda controllers
│       │   ├── __init__.py
│       │   └── pipeline.py
│       │
│       ├── snap/                                 # SNAP clustering
│       │   ├── __init__.py
│       │   └── snap.py                           # ← atomic_constructed/snap.py
│       │
│       ├── arena/                                # selection
│       │   ├── __init__.py
│       │   └── arena.py
│       │
│       ├── economy/                              # merit / coin
│       │   ├── __init__.py
│       │   └── economy.py
│       │
│       ├── daemon/                               # orchestration
│       │   ├── __init__.py
│       │   └── daemon.py
│       │
│       ├── tmn/                                  # gateway
│       │   ├── __init__.py
│       │   └── tmn.py                            # ← atomic_constructed/tmn.py
│       │
│       ├── agenthub/                             # inter-agent bus
│       │   ├── __init__.py
│       │   └── agenthub.py
│       │
│       ├── mannyai/                              # persona
│       │   ├── __init__.py
│       │   └── mannyai.py
│       │
│       └── cmplx/                                # umbrella spec
│           ├── __init__.py
│           └── cmplx.py                          # ← atomic_constructed/cmplx.py
│
├── projections/                                  # domain projections (CMPLX-Monorepo pattern)
│   ├── sciencepack/
│   ├── researchcraft/
│   ├── swarm/                                    # ← atomic_constructed/swarm.py
│   ├── document_decomposer/
│   └── interrogation/
│
├── adapters/                                     # external surfaces (CMPLXMCP pattern)
│   ├── http/
│   ├── mcp/
│   ├── chirp/                                    # UDP/MIDI/WAV/audio
│   └── codex/                                    # the repo-kernel
│
├── services/                                     # runtime containers (CMPLX-TMN-main pattern)
│   ├── gateway/
│   ├── core/
│   ├── brain/
│   ├── memory/
│   ├── arena/
│   ├── economy/
│   ├── daemon/
│   └── persona/
│
├── infrastructure/                               # k8s / docker / observability (CMPLX-TMN1 pattern)
│   ├── docker/
│   │   ├── Dockerfile                            # base image
│   │   ├── docker-compose.yml                    # the service constellation
│   │   └── docker-compose.gateway.yml
│   ├── kubernetes/
│   ├── monitoring/                               # prometheus, grafana
│   └── nginx/
│
├── configs/                                      # configuration (CMPLX-TMN-main)
│   ├── subsystems/
│   └── surfaces/
│
├── scripts/                                      # one-off + maintenance (universal)
│   └── ...
│
├── tools/                                        # developer tools (CMPLX pattern)
│   └── ...
│
├── tests/                                        # tests (universal)
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/                                         # documentation (CMPLX-1T weight)
│   ├── REPORT/                                   # ← existing per-family report
│   ├── REPORT_REPOS/                             # ← existing per-repo report
│   ├── PRODUCTION/                               # ← existing 5-document production reference
│   ├── architecture/
│   ├── playbooks/
│   └── runbooks/
│
├── formal/                                       # mathematical foundation (CMPLX-Formalization)
│   ├── lattices/
│   ├── codes/
│   └── proofs/
│
├── data/                                         # local fixed data (not Kimi catalogs — those stay gitignored)
│   ├── lattice_tables/                           # E8 root system, Leech codewords, etc.
│   ├── golay_codewords/
│   └── superpermutations/
│
├── work/                                         # operating ground for the atomic merger + Kimi tools
│   ├── merge_scripts/                            # ← already there
│   ├── atomic_constructed/                       # ← already there: the 15 canonicals + decisions
│   ├── unified_e8_v2/, unified_morphon/, ...     # ← Kimi's domain unifications
│   └── staging/                                  # ← hardlink staging (gitignored body, manifest kept)
│
└── repo_kernel/                                  # historical mirrors (gitignored, kept for provenance)
    └── repos/                                    # the 12 source-of-record repos
```

## Mapping from current atomic_constructed/ to the master layout

| Current file | Destination |
|---|---|
| `work/atomic_constructed/morphon.py` | `src/cmplx/morphon/morphon.py` |
| `work/atomic_constructed/e8.py` | `src/cmplx/geometry/e8.py` |
| `work/atomic_constructed/leech.py` | `src/cmplx/geometry/leech.py` |
| `work/atomic_constructed/niemeier.py` | `src/cmplx/geometry/niemeier.py` |
| `work/atomic_constructed/mdhg.py` | `src/cmplx/addressing/mdhg.py` |
| `work/atomic_constructed/mmdb.py` | `src/cmplx/memory/mmdb.py` |
| `work/atomic_constructed/chirp.py` | `src/cmplx/transport/chirp.py` |
| `work/atomic_constructed/agrm.py` | `src/cmplx/routing/agrm.py` |
| `work/atomic_constructed/aletheia.py` | `src/cmplx/constraints/aletheia.py` |
| `work/atomic_constructed/cqe.py` | `src/cmplx/engine/cqe.py` |
| `work/atomic_constructed/tarpit.py` | `src/cmplx/symbolic/tarpit.py` |
| `work/atomic_constructed/snap.py` | `src/cmplx/snap/snap.py` |
| `work/atomic_constructed/tmn.py` | `src/cmplx/tmn/tmn.py` |
| `work/atomic_constructed/cmplx.py` | `src/cmplx/cmplx/cmplx.py` |
| `work/atomic_constructed/swarm.py` | `projections/swarm/swarm.py` |
| `work/atomic_constructed/*.decisions.jsonl` | `docs/provenance/<family>.decisions.jsonl` |

Each `.py` keeps its sibling `.decisions.jsonl` reachable through
`docs/provenance/` so the audit chain from any line of code back to the
specific source-file it came from remains discoverable in one place.

## Naming discipline

- **Module-level**: one canonical per family (no `e8_v2`, `e8_old`, etc.)
- **Class names**: keep the AST-extracted name, no prefixes/suffixes
- **Function names**: snake_case, no module prefix (it's already in the
  module path)
- **Constants**: `UPPER_SNAKE_CASE` for module-level immutables
- **Private**: leading underscore for module-internal helpers

## What changes vs. the current shape

1. **`src/cmplx/` becomes the canonical package** (instead of scattered
   `work/atomic_constructed/`). Everything else points at it.
2. **Adapters move out of the core** into `adapters/` so the core has
   no protocol dependencies (HTTP, MCP, audio all become optional).
3. **Services become deployable units** under `services/<role>/` with
   their own Dockerfile and entry-point. No service holds production
   logic — they all import from `src/cmplx/`.
4. **`docs/` absorbs the existing report bodies** (`REPORT/`,
   `REPORT_REPOS/`, `PRODUCTION/`) and gets a new `provenance/`
   subdir holding the `.decisions.jsonl` per canonical.
5. **`formal/` is a new top-level for the mathematical foundation** —
   one place for E8/Leech/Niemeier/Golay lattice data, proofs, papers.
6. **`work/` is preserved** as the *operating ground* — it's where the
   merger tools live, where staging happens, where Kimi works. Most of
   its content is gitignored; the tools and the constructed outputs
   are tracked.

## Why this layout

Every historical repo solved a piece of this and dropped something
else. The master template adopts what each one got right:

- From **CMPLX**: package discipline (`pyproject.toml`, `tests/`, `tools/`).
- From **CMPLX-1T**: docs-as-source weight, knowledge layer first-class.
- From **CMPLX-Monorepo**: domain projections deserve their own root.
- From **CMPLX-TMN-main**: minimal core, clean separation.
- From **CMPLXMCP**: service decomposition per concern.
- From **CMPLXUNI**: layered library, frontend siblings allowed.
- From **CMPLXDevKit**: meta-toolkit pattern, multiple distributables.
- From **CMPLX-Formalization**: math/docs as a peer of code.
- From **CMPLX-Manny**: persona + orchestration scripts at root.
- From **CMPLX-TMN1**: infrastructure as a top-level concern.
- From **scout-demo-service**: lean deployable services.

What's discarded: the noise — the staging dirs, the UUID-named caches,
the historical generations, the `.gemini/history/` chains. Those go
in `.gitignore` per the noise classifications already mined from
`yard_inventory.file_classification`.

## Next steps after the bisector finishes

1. Re-index with `partsfactory` hangs skipped — extends the pool to the
   true scope.
2. Regenerate specs against the wider index.
3. Re-plan + re-drain.
4. Begin **physically placing** canonicals into `src/cmplx/<family>/`
   per the mapping above.
5. Wire up `__init__.py` files (auto-generatable from spec qualnames).
6. Write minimal smoke tests under `tests/unit/<family>/` for each
   canonical's top class.
7. Produce a `migration_manifest.json` mapping every old path under the
   12 historical repos to its destination in the new layout.

The atomic merger's `.decisions.jsonl` files become the **migration's
truth log** — each line of code in `src/cmplx/<family>/<file>.py`
traces back to a specific witness path in one of the 12 historical
repos.
