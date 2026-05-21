# W0 bootstrap startup audit (2026-05-21)

## Source of truth

| Artifact | Role |
|----------|------|
| `src/runtime/bootstrap_registry.py` | 15 ports → part_id, package, pytest_target |
| `src/runtime/cmplx_bootstrap.py` | `register_all()` factories |
| `catalog/bootstrap_manifest.json` | Emitted index of wired parts |
| `identity_review/scripts/emit_bootstrap_catalog_parts.py` | Merge catalog JSON from registry |

Refresh catalog after registry edits:

```powershell
python D:\PartsFactory\identity_review\scripts\emit_bootstrap_catalog_parts.py
python D:\PartsFactory\identity_review\scripts\emit_bootstrap_catalog_parts.py --check
```

## Smoke tests

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
$env:PYTHONPATH='src'; $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests/runtime/test_cmplx_bootstrap.py tests/integration/test_register_all_ports_smoke.py -q
```

## `register_all` / `ensure_bootstrapped` call sites (production)

| Path | Mechanism |
|------|-----------|
| `src/runtime/persistent_agent.py` | `AgentProcess.__init__` → `register_all(mesh=..., mmdb_path=...)` |
| `src/cmplx/transform/bridge.py` | `ensure_bootstrapped()` → lazy `register_all` on first transformer use |
| `src/cmplx/transform/ingest.py`, `transformer.py`, `token_index/builder.py`, `index_mutations.py` | call `ensure_bootstrapped()` |

No additional agent entry points found under `src/` without bootstrap (2026-05-21 scan).

## Not bootstrap-wired (by design)

| Port | Status |
|------|--------|
| Manny mesh services | `mesh.request()` only — not a MorphonController port |

## B3 integration profile (2026-05-21)

```powershell
$env:CMPLX_INTEGRATION_PROFILE='1'
python D:\PartsFactory\identity_review\scripts\run_b3_integration_smoke.py
```

- Enables `MDHG_MINT_RECEIPT`, `MMDB_MINT_RECEIPT`, and related bridges.
- Probes localhost compose; prefers remote registration for mmdb/mdhg/snap/tarpit/speedlight when healthy.

## W1 (2026-05-21)

| Item | Status |
|------|--------|
| `crystal` port | `CrystalRegistry` in `register_all` — 16 bootstrap ports |
| `run_crystal_done_gate.py` | catalog gate for `crystal-registry` |
| `run_bootstrap_w1_done_gates.py` | batch gates for bootstrap parts without witness bundles |

## Gaps closed in W0

- Registry documents all 15 bootstrap ports (was 12 in old test set).
- Catalog parts merged with `bootstrap_ports`, `pluggability`, `bootstrap_source`.
- Integration smoke asserts every registry port registers in-process without mesh.
