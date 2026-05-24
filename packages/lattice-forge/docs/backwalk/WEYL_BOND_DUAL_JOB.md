# Weyl bonded chamber dual enumeration — job definition

> **Superseded by** [`LATTICE_SPACE_EXHAUSTION_JOB.md`](LATTICE_SPACE_EXHAUSTION_JOB.md) — run `.\Start-BackwalkLatticeSpace.ps1`.

## Intent (your assignment)

Enumerate **bonded Weyl chamber locations** between exceptional start points (G₂, F₄, E₆, E₇, E₈) as a dedicated table, using:

| Principle | Implementation |
|-----------|----------------|
| **Quadrant-sharded search** | Four D₄ axes = four independent searches (2 chart states each); **concatenate** into `weyl_bond_result_tree` |
| **Not one giant job** | **50 batches per quadrant** (200 total for `--all-quadrants`), each checkpointed |
| **Construct toward middle** | `construct_in` waves, depth **2 → 1 → 0** (poles → E₆ / axis-2 chart hub) |
| **Read from middle out** | `read_out` waves, depth **0 → 1 → 2** |
| **Podal \| antipodal** | Chart sheet 0/1 + D₄ axis pairs from `chart_codec_d4` |
| **Top \| bottom** | E₇/E₈ vs G₂/F₄; **middle** = E₆ + chart indices `{2,5}` |
| **2 lanes per quadrant** | Each batch only touches chart states on that axis (e.g. Q2 = `{2,5}`) — same O(1) `route()` table |
| **Linked oloid mirror** | Optional `WEYL_13` antipodal mirror row per lane (`weyl_chamber_bond_mirror`) |

## Resource baseline (safe on desktop)

| Guard | Default |
|-------|---------|
| Docker memory | **512 MiB** cap |
| CPU | **1** core |
| Rows per batch | **≤ 64** (`WEYL_BOND_MAX_ROWS_PER_BATCH`) |
| Inter-batch sleep | **50 ms** (`WEYL_BOND_BATCH_SLEEP_MS`) |
| SQLite commits | Every **500** inserts (existing backwalk store) |
| No recursion | Iterative lane loop only |
| Seed DB | **Read-only**; all writes on `/data/backwalk_work.db` |

| Quadrant | Axis | Chart states | Active dual_depth |
|----------|------|--------------|-------------------|
| Q0 | shell extremes | 0, 7 | 2 |
| Q1 | left doublet | 1, 6 | 1 |
| Q2 | center (middle) | 2, 5 | 0 |
| Q3 | right / T_bijective | 3, 4 | 1 |

Expected total rows: ≤ **~800** with mirror (200 batches × ≤4 rows). DB growth **≪ 50 MB**.

## Schema

| Table | Role |
|-------|------|
| `exceptional_weyl_bond` | Rows tagged with `quadrant` 0..3 |
| `weyl_bond_batch_checkpoint` | Per-batch resume |
| `weyl_bond_result_tree` | Concatenated forest (`weyl_bond_root` + `weyl_quadrant:0..3`) |

## Operator

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
# All four quadrants + concatenate (default)
.\Start-BackwalkWeylBondWaves.ps1

# Single quadrant (agent assignment) — 150 batches only
docker compose -f docker-compose.backwalk-weyl-bond.yml run --rm `
  -e PROOF_LAB_MODE=backwalk-weyl-orchestrate `
  niemeier-weyl-bond-orchestrator `
  python packages/lattice-forge/scripts/orchestrate_weyl_bond_waves.py `
  --work-db /data/backwalk_work.db --resume --quadrant 2

# Merge only (after four parallel quadrant runs)
python packages/lattice-forge/scripts/orchestrate_weyl_bond_waves.py `
  --work-db /data/backwalk_work.db --concat-only
```

Resume after interrupt: same command (`--resume` skips `done` batches).

## Outputs

| File | Role |
|------|------|
| `/data/backwalk_work.db` | Niemeier + exceptional spine + weyl bonds |
| `/data/weyl_bond_manifest.jsonl` | Batch plan |
| `/data/weyl_bond_orchestrator_report.json` | Run summary |

## Evidence

- `weyl_chamber_bond`: **exact** (substrate `route()` table)
- Cross-group path metadata: **template** via E₆ hub composition
- Not full E₈ Weyl group enumeration
