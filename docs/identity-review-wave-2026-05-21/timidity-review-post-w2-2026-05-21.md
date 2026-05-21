# Timidity vs boldness review (post W0–W3, 2026-05-21)

Compared to the prior “plug in now” assessment, this pass scores **what changed**, **what is still unnecessarily timid**, and **what should stay cautious**.

## Executive summary

| Era | Posture |
|-----|---------|
| **Pre-W0** | Timid on **integration** (bootstrap, catalog mirror, smoke) while code already existed |
| **Post-W0–W3** | Bold on **wiring** (16 ports, Docker smoke, crystal, NN routing, staging materialized) |
| **Remaining timidity** | Mostly **narrative + ceremony + dual-stack ops**, not missing spine code |

**Verdict:** You are **no longer bashful about plugging in manufactured ports**. Residual timidity clusters around **escrow psychology**, **stale reports**, **optional provenance/mesh**, and **not promoting the 10 spine packages without `provider.py` at top level**.

---

## Scorecard (integration readiness)

| Layer | Status | Timid? |
|-------|--------|--------|
| `register_all()` / 16 ports | Green + smoke tests | **No** — fixed W0/W1 |
| Catalog `bootstrap_manifest.json` | 16 parts emitted | **No** |
| Batch done gates (bootstrap parts) | 9/9 intent_met | **No** |
| Docker HTTP profile (W2) | All GET + receipt mint + snap triad | **No** |
| repo-kernel `:8786` | Up after morphonic_bridge fix | **Was** timid (infra left broken) |
| AGRM geographic TSP | NN heuristic + tour cost | **Was** timid; **still** not agent-stack TSP |
| AGRM MDHG sweeps | Staging ref loads; optional probe | **Appropriate** split |
| SNAP escrow 53 defer | Correct (already on spine) | **Sounds** timid in reports |
| AGRM escrow 64 defer | Correct (CQE dupes) | **Sounds** timid in reports |
| Hash-lanes (16) | Not started | **Timid** if treated as blocked on AGRM |
| `cognition` / `tools` ports | Not in bootstrap | **Timid** only if role is clear |
| Phase H markdown | Still says “3 parts / kernel offline” | **Stale = timid narrative** |

---

## What we stopped being bashful about (evidence)

1. **Bootstrap as SoT** — `bootstrap_registry.py` + `emit_bootstrap_catalog_parts.py` + `test_register_all_ports_smoke.py`.
2. **Routing registration bug** — `routing` was defined but never registered; fixed (W0).
3. **Crystal port** — was in `KNOWN_PORTS` but skipped by `register_all`; wired W1.
4. **Catalog gates for “partial” slots** — geometry, nsl, morsr, constraints, engine, transport, embed, atlas, crystal gated without new gathers.
5. **Docker deferred work** — repo-kernel crash loop, receipt compose YAML, W2 profile smoke, SNAP receipt e2e with live `:8010`.
6. **AGRM** — materialized refactored reference; `staging_loader` loads it; `solve()` returns real tours (NN), not `not_implemented`.

---

## Where we are still bashful (unnecessary)

### 1. Ceremony ahead of motion

| Habit | Cost | Bold replacement |
|-------|------|------------------|
| 150-row witness cap per slot before wire | Weeks of JSONL | One `register_all` smoke + port pytest dir |
| Re-running gathers when indexes exist | Noise | `atomic_query.py` / workbook at need |
| Escrow triage reports read as “64 defer = blocked” | Morale | Relabel: **“already on spine”** vs **“corpus only”** |
| Duplicate gate runners | Friction | Single `run_bootstrap_gates.py` from manifest |

### 2. Stale “system offline” story

- `slots-pluggability-analysis-2026-05-21.md` still claims **3 catalog parts** and **repo-kernel offline**.
- `slots-pluggability-aggregate-2026-05-21.json` `phase_h` still **timed out** (script not re-run after kernel fix).
- **Timid narrative:** readers think nothing is pluggable when **16 parts + live Docker** already are.

**Fix:** Re-run `phase_h_slots_pluggability.py` (45s timeouts) or patch report header from `w1c-bootstrap-kernel-sync-2026-05-21.json`.

### 3. Under-using what is already running

| Capability | Running | Timid choice |
|------------|---------|--------------|
| Mesh services (mdhg, mmdb, snap, tarpit, speedlight) | Healthy on Docker network | `register_all()` without mesh → always in-process |
| Receipt bridges | Implemented | `MDHG_MINT_RECEIPT` / `MMDB_MINT_RECEIPT` default **off** |
| repo-kernel workbook | Slow but works | Not default session start |
| GitNexus bridge | Via 8786 | Phase H still prefers SQLite fallback in docs |

**Bold:** Default smoke profile: `register_all(mesh=...)` when stack is up; enable receipt mint env in integration compose profile.

### 4. Dual HTTP stacks (ops timidity)

- **snap-unified** (`:8823`) ≠ **cmplx-snap** compose profile (`gate369` vs `triad` rules).
- W2 papered over with triad fallback — correct smoke, **timid product story** (two SNAP faces).

**Bold:** One labeled profile: `stack=unified` vs `stack=manufactured` in smoke script; document port ownership.

### 5. Spine packages not promoted to ports

**26** `src/cmplx/*` dirs, **16** bootstrap ports. Unwired top-level packages include e.g. `cognition`, `tools`, `pipeline`, `lambda`, `interrogation` — not bashful **until** ATTRACTOR assigns a port. **Timid** if we keep treating them as “51 slots missing” instead of “10 optional extensions.”

### 6. AGRM naming

- `solve()` is **nearest_neighbor**, not refactored TSP.
- Composed `routing/agrm/AGRMController.py` still in tree (import trap).

**Bold:** Rename health `mode` in docs; add `routing/AGRMController.py` → re-export warning or move to `_witness/`; never import from package `__init__`.

### 7. Promotion register not updated

- `cmplx_pending` 235 families; bootstrap manifest lists 16 parts — **no machine-readable “family → promoted”** link.
- **Timid:** another gather wave instead of marking families with existing `provider.py` as **done**.

---

## Where caution is correct (not bashful)

| Item | Why keep deferring |
|------|-------------------|
| Bulk merge CQE `agrmmdhg` (40 rows) | Harm / dupes |
| `agrmmdhg_manus` witness | never_merge |
| Composed `AGRMController.py` repair in place | Unmaintainable merge artifact |
| `kb.py ingest --all` | Duplicates atomic_index |
| Manny / OC build writes | Three-space RO |
| repo-kernel `allow_mutation=0` | Safety |
| SNAP 53 escrow file copies | Skills already in spine |

---

## Bold next program (ranked)

| Priority | Work | Days | Replaces timidity |
|----------|------|------|-------------------|
| **B1** | Refresh Phase H + pluggability MD from live kernel sync report | hours | “offline” narrative |
| **B2** | `promotions-bootstrap.jsonl` — map `bootstrap_manifest.parts` → family status `wired` | hours | pending-family fog |
| **B3** | Integration profile: mesh-aware `register_all` + receipt bridges on in CI smoke | 1 day | in-process-only default |
| **B4** | Hash-lanes thin port (16) — channel lanes from MDHG + routing tour metadata | 1–2 days | “blocked on AGRM” |
| **B5** | Quarantine composed `AGRMController.py` (rename to `_composed_DO_NOT_IMPORT.py`) | minutes | import trap |
| **B6** | Agent-stack TSP shard import (2 escrow adapters only) | 2–3 days | NN as only story |
| **B7** | Unify SNAP HTTP profile or document two stacks in catalog housings | 1 day | triad fallback forever |

---

## One-line answer

**You were right to push W0–W3:** most timidity was **integration and reporting**, not missing algorithms. **Remaining bashfulness** is mostly **acting as if escrow deferrals block wiring**, **stale Phase H text**, and **not turning on mesh/receipt defaults** — not lacking code.
