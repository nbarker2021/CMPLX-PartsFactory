# Lattice space exhaustion — canonical job definition

## Task (single assignment)

> Enumerate all **lattice forms accessible to any 24D Niemeier form** (terminal, product, byproduct, component instances), all **associated proof/capture obligations**, prior **library_needs** captures, and **E₈ Weyl conjugate assignments** for podal side bonds — **minimum** coverage |W(E₈)| = **696,729,600** via **bijective index** (not 696M literal SQLite rows).

## Method (only)

**Quadrant-sharded D₄ chart search** — four independent axes, construct **middle-in**, read **middle-out**, concatenate `weyl_bond_result_tree`. No monolithic 8-lane octet job.

## Phases

| Phase | Output | Rows (typical) |
|-------|--------|----------------|
| 1 `lattice_catalog` | `lattice_form_registry` | ~150–400 per 24 terminals |
| 2 `weyl_quadrant` | `exceptional_weyl_bond` + checkpoints | 200 batches, ~400–800 bonds |
| 3 `weyl_concat` | `weyl_bond_result_tree` | 1 root + 4 quadrant branches |
| 4 `e8_pod_assign` | `podal_side_bond_assignment` | terminal + product forms × bonds |
| 5 `proof_capture` | `proof_capture_queue` | library_needs (cap 200) + structural obligations |

## E₈ honesty

| Claim | Status |
|-------|--------|
| `e8_weyl_group_catalog.weyl_order` = 696729600 | **exact** (classical |W(E₈)|) |
| Every pod bond has `weyl_element_index` ∈ [0, 696729600) | **bounded_exec** surjection |
| Full group multiplication table materialized | **no** — bijection provides cover; expand on demand |

## Resource baseline

| Guard | Value |
|-------|--------|
| Docker memory | 768 MiB |
| CPU | 1 |
| Weyl batches | 200 (50 × 4 quadrants) |
| library_needs ingest | ≤ 200 lines |
| Pod assign | terminal_24d + product forms only (not every component instance) |

## Operator

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
.\Start-BackwalkLatticeSpace.ps1
```

Report: `/data/lattice_space_exhaustion_report.json` on volume `niemeier-backwalk-data`.

## Prior docs

- Pilot / full24 Niemeier backwalk: `BASELINE_PILOT.md`, `FULL24_RUN.md`
- Quadrant Weyl detail: `WEYL_BOND_DUAL_JOB.md` (subsumed by this job)
