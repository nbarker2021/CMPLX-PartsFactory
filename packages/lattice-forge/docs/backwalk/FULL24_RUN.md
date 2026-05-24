# Niemeier backwalk — full-24 runbook

## Context

Pilot (2026-05-24) materialized four terminals on volume `niemeier-backwalk-data` in **0.36 s** / **~264 KiB** with unlimited involutions. The forward `terminal_tree` peel depths were validated (Leech 1 state; D4^6 7; A2^12 13; A1^24 25). Seed ledger remained immutable.

Full-24 completes the remaining **20** Niemeier terminals on the same work DB using **`--resume`** (skips `run_checkpoint.status=done`).

## Operator (Windows)

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
.\Start-BackwalkFull24.ps1
```

Or manually:

```powershell
docker compose -f docker-compose.backwalk-builder.yml `
  -f docker-compose.backwalk-builder.full24.yml up --build --abort-on-container-exit
```

## Environment

| Variable | Full-24 value | Rationale |
|----------|---------------|-----------|
| `BACKWALK_PHASE` | `full24` | All `NIEMEIER_FORMS` terminals |
| `BACKWALK_RESUME` | `1` | Reuse pilot slices; no duplicate work |
| `BACKWALK_INVOLUTION_LIMIT` | `50` | Caps per-component generator/diagram rows (pilot A1^24 had 300 involutions uncapped) |
| `BACKWALK_EXCEPTIONALS` | `g2,f4,e6,e7,e8` | G2/F4 conjugate + E6 shell + single-step E7/E8 Cartan templates |

Entrypoint also defaults `BACKWALK_INVOLUTION_LIMIT=50` when phase is `full24` and the env is unset.

## Outputs (persistent volume)

| Path | Purpose |
|------|---------|
| `/data/backwalk_work.db` | Writable category + exceptional spine |
| `/data/baseline_report.json` | Latest run summary (overwritten each run) |
| `/data/progress.jsonl` | Append-only run events |

Inspect after completion:

```powershell
docker run --rm -v niemeier-backwalk-data:/data alpine ls -la /data
docker run --rm -v niemeier-backwalk-data:/data alpine cat /data/baseline_report.json
```

## Acceptance

- Container exit code **0**
- `baseline_report.json` → `"status": "pass"`
- `seed_verify_before` / `seed_verify_after` → pass
- **24** rows in `run_checkpoint` with `status=done` (query via local Python or sqlite3 on copied DB)
- Work DB size: re-profile if **> 50 MB** (raise cap only with explicit approval)

## Honesty (unchanged)

- Overlattice glue remains **template** / **bounded_exec** — not PROVEN
- E7/E8 edges are **cartan_extension** templates, not full reflection action tables
- `rule30.prize.depth_only_shortcut` and transport tower claims are out of scope

## Full-24 completed (2026-05-24)

| Field | Value |
|-------|--------|
| `run_id` | `15c63b2a-5188-4d48-b92c-4339f8d4103b` |
| Wall time | **0.97 s** (resume skipped 4 pilot terminals) |
| Work DB size | **860,160 bytes** (~840 KiB) — well under 50 MB cap |
| Checkpoints `done` | **24** / 24 |
| `BACKWALK_INVOLUTION_LIMIT` | 50 (D4^6 involutions dropped 147→42 vs uncapped pilot) |
| Exceptional spine | G2, F4, E6, E7, E8; morphisms G2→F4, E6→E7, E7→E8 |
| Seed verify | pass before/after |
| Status | **pass** |

Re-run anytime:

```powershell
.\Start-BackwalkFull24.ps1
```

## After full-24

1. Phase 2 consumers: `hydrate(work_db, terminal_id)` + `glue_project_weyl` integration tests.
2. Optional: export work DB snapshot for package_data freeze (user approval required).
