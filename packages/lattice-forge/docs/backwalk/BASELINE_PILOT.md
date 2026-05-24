# Niemeier backwalk — pilot baseline (2026-05-24)

Batch builder: `docker compose -f docker-compose.backwalk-builder.yml up --build --abort-on-container-exit`

Persistent volume: `niemeier-backwalk-data` → `/data/backwalk_work.db`, `/data/baseline_report.json`, `/data/progress.jsonl`

## Run

| Field | Value |
|-------|--------|
| `run_id` | `8599603f-2401-43dc-9266-0f917c28a95c` |
| `phase` | `pilot` |
| `BACKWALK_EXCEPTIONALS` | `g2,f4,e6` |
| `BACKWALK_INVOLUTION_LIMIT` | *(unset — unlimited for pilot)* |
| Total wall time | **0.36 s** |
| Work DB size | **270,336 bytes** (~264 KiB) |
| Seed verify before/after | `pass` (unchanged) |
| Acceptance | **pass** |

## Per-terminal metrics

| Terminal | States | Peel morphisms | Involution morphisms | Max rank | Wall (s) | Slice SHA-256 (prefix) |
|----------|--------|----------------|----------------------|----------|----------|-------------------------|
| `Niemeier:Leech` | 1 | 0 | 0 | 0 | 0.010 | `200ca104…` |
| `Niemeier:D4^6` | 7 | 6 | 147 | 24 | 0.019 | `fe7057fe…` |
| `Niemeier:A2^12` | 13 | 12 | 234 | 24 | 0.027 | `eeaef60a…` |
| `Niemeier:A1^24` | 25 | 24 | 300 | 24 | 0.044 | `ed565ad9…` |

Counts match forward `terminal_tree` peel depth (`len(route)` / `len(route)-1` peel steps).

## Exceptional spine (pilot)

| Nodes | Morphisms |
|-------|-----------|
| G2, F4, E6 | G2→F4 (`weyl_conjugate`, exact) |

E6→E7→E8 `cartan_extension` rows are emitted only when `BACKWALK_EXCEPTIONALS` includes `e7,e8`.

## Evidence honesty

- Peel (`remove_component`): **exact**
- Root-shell route objects: **exact** where `terminal_tree` status is canonical
- Involutions: **exact** / **computed_profile** / **template** from seed generator status
- `glue_project_weyl`: **bounded_exec** (substrate `WEYL_13_TABLE`)

## Full-24 tuning note

Pilot completed under 512 KiB with no involution cap. For `BACKWALK_PHASE=full24`, default CLI cap is **50 involutions per component** (`--involution-limit` / `BACKWALK_INVOLUTION_LIMIT=50`). Re-profile if work DB growth exceeds ~50 MB.

**Completed:** see [`FULL24_RUN.md`](FULL24_RUN.md) — **840 KiB** / **0.97 s** / 24 checkpoints; run via `.\Start-BackwalkFull24.ps1`.

## Local CI

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory\packages\lattice-forge
$env:PYTHONPATH = "src"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
python -m pytest tests/test_backwalk_pilot.py -q -k "not docker"
```

Optional Docker smoke: `BACKWALK_DOCKER_SMOKE=1` (same compose file).
