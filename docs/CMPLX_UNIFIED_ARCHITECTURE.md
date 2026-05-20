# CMPLX Unified Architecture — Evidence-Based Canonical Design

**Date**: 2026-05-12  
**Derived from**: 1,093,022 artifacts (Manny) + 33,523 real files (PartsFactory)  
**Deduplication result**: 36,029 clusters → 19 capability domains  

---

## 0. Design Principle

**No historical form is canon.** Every file is raw material. The architecture below is derived entirely from what exists across all builds, not from training priors or conventional patterns.

---

## 1. Evidence Summary

| Space | Artifacts | Unique Basenames | In Both | Unique to Space |
|-------|-----------|------------------|---------|-----------------|
| Manny (cache) | 1,093,022 | 29,110 | 7,911 | 21,199 |
| PartsFactory | 33,523 | 18,761 | 7,911 | 10,850 |
| **Combined** | **1,126,545** | **47,971** | — | — |

**Exact duplicates (size+name) across spaces**: 8,289  
**Most duplicated basenames**:
- `__init__.py`: 18,855 copies
- `types.py`: 1,941 copies
- `app.py`: 1,502 copies
- `config.py`: 1,461 copies
- `controller.py`: 1,123 copies
- `registry.py`: 463 copies

---

## 2. Capability Domains (Evidence-Derived)

From 47,971 unique basenames, 19 capability domains emerge:

| Domain | Unique Basenames | Canonical Role | Priority |
|--------|------------------|----------------|----------|
| `python_module` | 11,351 | Supporting modules, utilities, adapters | P3 |
| `other` | 18,431 | Unclassified / misc | P4 |
| `configuration` | 6,550 | YAML/JSON configs, service definitions | P2 |
| `documentation` | 1,256 | Design docs, specs, history | P2 |
| `geometry_lattice` | 1,006 | E8 lattice, root systems, Leech | **P0** |
| `frontend` | 660 | UI components, JS/TS | P2 |
| `governance_snap` | 184 | SNAP/AGRM governance, policy enforcement | **P0** |
| `mmdb_memory` | 124 | Crystal memory, MMDB addressing | **P0** |
| `morphonic` | 114 | Morphonic controllers, field dynamics | **P0** |
| `mdhg_hierarchy` | 102 | MDHG tree, hierarchy traversal | **P0** |
| `infrastructure` | 47 | Docker, compose, deployment | P1 |
| `policy` | 46 | Policy engine, rules, budget | P1 |
| `speedlight` | 36 | Receipt lineage, caching | P1 |
| `identity_wallet` | 15 | Identity, wallet, auth | P1 |
| `database_schema` | 12 | SQL schemas, migrations | P1 |
| `server_runtime` | 4 | Server, app, runtime | **P0** |
| `core_engine` | 4 | Registry, engine, thinktank, pipeline | **P0** |
| `frontend_markup` | 10 | HTML templates | P2 |
| `frontend_style` | 7 | CSS/SCSS | P2 |

---

## 3. Target Architecture

```
cmplx-unified/
├── canon/                          # Canonical implementations (ONE per capability)
│   ├── runtime/
│   │   ├── server.py              # Unified HTTP/WS server (from 1,502 app.py variants)
│   │   ├── registry.py            # Component registry (from 463 registry.py variants)
│   │   ├── engine.py              # Execution engine
│   │   ├── pipeline.py            # Data flow pipeline
│   │   └── thinktank.py           # Orchestration / reasoning
│   ├── geometry/
│   │   ├── e8_lattice.py          # E8 root system, lattice (DONE — canonicalized)
│   │   ├── leech_projection.py    # Leech lattice mapping
│   │   └── weyl_group.py          # Weyl group operations
│   ├── governance/
│   │   ├── snap_core.py           # SNAP protocol
│   │   ├── agrm_runtime.py        # AGRM governance loop
│   │   └── policy_engine.py       # Policy evaluation
│   ├── memory/
│   │   ├── mmdb_crystal.py        # Crystal memory structure
│   │   ├── address_space.py       # MDHG addressing
│   │   └── recall_index.py        # Memory recall / retrieval
│   ├── morphonic/
│   │   ├── field_controller.py    # Morphonic field dynamics
│   │   └── state_transition.py    # State machine transitions
│   ├── hierarchy/
│   │   ├── mdhg_tree.py           # MDHG tree operations
│   │   └── traversal.py           # Tree traversal algorithms
│   ├── speedlight/
│   │   ├── receipt.py             # Receipt lineage
│   │   └── cache_layer.py         # Caching infrastructure
│   ├── identity/
│   │   ├── wallet.py              # Wallet / credential store
│   │   └── identity_core.py       # Identity management
│   └── tools/                     # Composable tool interface
│       └── __init__.py
│
├── config/                         # Unified configuration
│   ├── services.yml               # Service topology (from 6,550 config variants)
│   ├── capsules.yml               # Capsule registry
│   └── policies.yml               # Global policies
│
├── docs/                           # Living documentation
│   ├── design/                    # Architecture decisions
│   ├── history/                   # Evidence history
│   └── api/                       # API documentation
│
├── frontend/                       # UI layer
│   ├── components/                # Reusable components
│   ├── pages/                     # Route pages
│   └── styles/                    # Global styles
│
├── infra/                          # Infrastructure
│   ├── docker/
│   │   ├── Dockerfile.base        # Base image (from 47 Dockerfile variants)
│   │   └── docker-compose.yml     # Stack definition
│   ├── postgres/                  # Schema migrations
│   └── scripts/                   # Deployment scripts
│
└── tests/                          # Unified test suite
    ├── unit/
    ├── integration/
    └── property/                   # Geometric property tests
```

---

## 4. Canonicalization Rules

### 4.1 Rule: One File Per Capability
For every domain, there shall be **exactly one canonical implementation**. All variants are:
- Cataloged in `canonicalization_log`
- Stored in `canonical_artifacts` (PostgreSQL)
- Referenced in `canonical_clusters`

### 4.2 Rule: Preserve Lineage
Every canonical file must record:
- All source variants that contributed to it
- The selection rationale
- The geometric coordinate of the capability in E8 space

### 4.3 Rule: Cross-Space Deduplication
Files with identical `basename + size_bytes` across spaces are **the same file mechanically copied**. Canonicalization chooses the best variant based on:
1. Completeness (line count, functionality)
2. Purity (no staging artifacts, no noise)
3. Source authority ( PartsFactory > Manny pipeline dumps)

### 4.4 Rule: Noise Elimination
The following are **not canonicalized**:
- `__init__.py` (18,855 copies — package boilerplate)
- `types.py` (1,941 copies — type stubs)
- `migrations.py` (1,123 copies — database migration history)
- Test fixtures, demo files, generated code
- Archive-staging copies, UUID-named directories

---

## 5. Migration Path

### Phase A: Deduplicate Existing (Current)
- ✅ Cache postgres surveyed (1M artifacts)
- ✅ PartsFactory inventoried (55K files)
- ✅ Cross-reference complete (8,289 exact duplicates identified)
- ✅ Clusters built (36,029 basename groups)

### Phase B: Select Canonicals (Next)
For each of the 19 domains:
1. Review all variants in the cluster
2. Select the most complete, cleanest implementation
3. Normalize line endings (LF)
4. Write to `src/canon/<domain>/<file>.py`
5. Record lineage in PostgreSQL

### Phase C: Build Unified Runtime
1. Compose canonical modules into `canon/runtime/`
2. Wire services via `config/services.yml`
3. Register capsules in `config/capsules.yml`
4. Deploy via `infra/docker/docker-compose.yml`

### Phase D: Activate Cache Pipeline
1. Unlock stalled ingest queue
2. Process remaining 476K queued jobs
3. Compute SHA-256 for all artifacts
4. Promote `evidence` → `canonical` in `catalog.code_source`

---

## 6. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CMPLX Unified System                     │
├─────────────────────────────────────────────────────────────┤
│  Frontend (NextJS/React)                                    │
│  ├─ pages/                                                  │
│  └─ components/                                             │
├─────────────────────────────────────────────────────────────┤
│  Runtime Layer                                              │
│  ├─ server.py     ← HTTP/WS gateway                        │
│  ├─ registry.py   ← Component discovery                    │
│  ├─ engine.py     ← Execution controller                   │
│  ├─ pipeline.py   ← Data flow orchestration                │
│  └─ thinktank.py  ← Reasoning / agent hub                  │
├─────────────────────────────────────────────────────────────┤
│  Capability Domains (Manifold)                              │
│  ├─ geometry/     ← E8, Leech, Weyl (P0)                   │
│  ├─ governance/   ← SNAP, AGRM, Policy (P0)                │
│  ├─ memory/       ← MMDB, Crystal, Recall (P0)             │
│  ├─ morphonic/    ← Field dynamics (P0)                    │
│  ├─ hierarchy/    ← MDHG tree (P0)                         │
│  ├─ speedlight/   ← Receipts, cache (P1)                   │
│  ├─ identity/     ← Wallet, auth (P1)                      │
│  └─ tools/        ← Composable interface                   │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├─ PostgreSQL (unification_hub)   ← Canonical lineage     │
│  ├─ PostgreSQL (unification_aggregator) ← Evidence cache   │
│  └─ SQLite (local)                 ← Agent state           │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Immediate Next Actions

| Priority | Action | Estimated Effort |
|----------|--------|------------------|
| P0 | Unlock stalled ingest queue | 5 min |
| P0 | Canonicalize `server.py` cluster | 1 hour |
| P0 | Canonicalize `registry.py` cluster | 1 hour |
| P0 | Canonicalize `engine.py` cluster | 1 hour |
| P0 | Canonicalize `pipeline.py` cluster | 1 hour |
| P1 | Ingest PartsFactory into cache postgres | 2 hours |
| P1 | Compute SHA-256 for all artifacts | 4 hours |
| P2 | Build unified `docker-compose.yml` | 2 hours |
| P2 | Create unified test suite | 3 hours |

---

## 8. Risks

1. **Hash coverage**: Only 0.4% of cache artifacts have SHA-256. Without hashes, deduplication relies on basename+size heuristics.
2. **Queue stall**: 476K jobs blocked. Until unlocked, no new data enters the cache.
3. **CRLF drift**: Windows WriteFile introduces CRLF line endings, causing hash mismatches.
4. **Cross-space contamination**: Zips contain paths from other spaces. Extraction may pollute.
5. **WSL2 port conflict**: `127.0.0.1:5432` hits WSL2 native postgres, not Docker container.

---

*Architecture derived from 1,126,545 artifacts across 3 spaces.*  
*No historical form promoted to canon without evidence.*
