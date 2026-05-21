# Git push review — bootstrap + integration wave (2026-05-21)

Scope: **CMPLX-PartsFactory** working tree (not yet committed). `identity_review/` scripts/reports are sibling — commit separately if desired.

## Suggested commit title

```
Bootstrap registry (17 ports), integration profile, hash-lanes, AGRM wiring, Docker fixes
```

## What this push does

| Theme | Change |
|-------|--------|
| **W0** | `bootstrap_registry.py`, catalog emit, `register_all` smoke (17 ports) |
| **W1** | `crystal` port, batch done gates, test fixes (`identity_kind`) |
| **W1c/W2** | repo-kernel `morphonic_bridge` fix, receipt compose YAML, Docker smoke scripts |
| **W3** | AGRM NN `solve()`, `staging_loader`, materialized refactored reference |
| **B1/B4/B5** | Phase H refresh, `hash_lanes` port, quarantine `_composed_DO_NOT_IMPORT.py` |
| **B3** | `integration_profile.py` — host mesh + receipt bridges on by default |

## Spine files to commit (CMPLX-PartsFactory)

### Runtime / bootstrap
- `src/runtime/bootstrap_registry.py` (new)
- `src/runtime/integration_profile.py` (new)
- `src/runtime/cmplx_bootstrap.py` — routing, crystal, hash_lanes; registry guard
- `src/runtime/persistent_agent.py` — `register_for_startup()`
- `src/cmplx/transform/bridge.py` — honors `CMPLX_INTEGRATION_PROFILE`

### Ports
- `src/cmplx/hash_lanes/` (new)
- `src/cmplx/routing/tsp_heuristic.py`, `staging_loader.py`, `provider.py`
- `src/cmplx/routing/agrm/_composed_DO_NOT_IMPORT.py` (renamed from `AGRMController.py`)
- `src/cmplx/routing/agrm/__init__.py` — no broken export
- `src/cmplx/morphon/controller.py` — `hash_lanes` in `KNOWN_PORTS`

### Docker / repo-kernel
- `services/repo-kernel/Dockerfile` — COPY `morphonic_bridge.py`
- `docker-compose.repo-kernel.yml` — bind-mount bridge module
- `docker-compose.receipt.yml` — fix command YAML

### Tests
- `tests/integration/test_register_all_ports_smoke.py`
- `tests/integration/test_integration_profile.py`
- `tests/integration/test_crystal_bootstrap.py`
- `tests/hash_lanes/test_provider.py`
- `tests/routing/test_routing_stub.py` (NN solve)
- `tests/runtime/test_cmplx_bootstrap.py` — 17 ports
- `tests/constraints`, `tests/embed`, `tests/engine` — `identity_kind` alignment

### Do NOT commit (unless intentional)
- `CON`, `l0-gate.txt`, `pytest-*.txt`, `docs/RECEIPT_SALE_CANDIDATES.md`
- `catalog/` (gitignored — local manufacturing manifests)
- `staging/by-family/agrm/` (materialized reference — consider gitignore or commit once)

## Enable integration profile locally

```powershell
$env:CMPLX_INTEGRATION_PROFILE='1'
$env:PYTHONPATH='D:\PartsFactory\CMPLX-PartsFactory\src'
python D:\PartsFactory\identity_review\scripts\run_b3_integration_smoke.py
```

Expected when stack is up: **5 remote ports** (memory, addressing, symbolic, snap, cache) + 12 in-process.

## Pre-push verification

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
$env:PYTHONPATH='src'; $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/runtime/test_cmplx_bootstrap.py tests/integration/ tests/hash_lanes/ tests/routing/ -q
python D:\PartsFactory\identity_review\scripts\run_bootstrap_w1_done_gates.py
python D:\PartsFactory\identity_review\scripts\run_w2_compose_profile_smoke.py
```

## identity_review (optional second commit)

Scripts: `emit_bootstrap_catalog_parts.py`, `run_w1c_docker_smoke.py`, `run_w2_compose_profile_smoke.py`, `run_b3_integration_smoke.py`, `materialize_agrm_staging.py`, `emit_promotions_bootstrap.py`, `phase_h_slots_pluggability.py` (updated).

Reports: `w1c-*`, `w2-*`, `b3-*`, `timidity-review-*`, `checkpoint-b1-b5-b4-*`, `slots-pluggability-*` (refreshed), `promotions-bootstrap.jsonl`.

## Risk notes for reviewers

1. **Remote mesh on host** — uses `localhost:8823–8825,8843–8844`; inside Docker use service DNS via `MeshOrchestrator` instead.
2. **Receipt volume** — integration profile enables MDHG/MMDB mint; fine for dev, watch noise in prod.
3. **AGRM** — geographic solve is heuristic; refactored file is MDHG sweeps only.
