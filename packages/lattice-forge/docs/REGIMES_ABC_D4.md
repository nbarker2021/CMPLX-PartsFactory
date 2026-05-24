# Regimes A / B / C / C′ — Rule 30 Sublinear Solver (Honest Status)

**Date:** 2026-05-23  
**Tree:** `D:\PartsFactory\work\lattice-forge`  
**Obligation:** `rule30.prize.depth_only_shortcut` remains **CONJ** — no log-time prize claim.

---

## Regime A — Block-addressed I/O (checkpoint tower)

**Modules:** `block_tower.py`, `rule30_block_extractor.py`

The Rule 30 center column is empirically full-entropy. A 3-bit `(L,C,R)` Markov lookup cannot predict 64-bit futures (verified in umbrella diagnostics). Regime A does **not** compress the ribbon below Shannon; it amortizes **query** cost:

- Build: O(N × width) one-shot checkpoint store
- Query: O(base_page × width) per bit, bounded by page size (64), not depth N
- Verification: **100% match** vs brute force at depth 4096 (`verify_block_tower`, `verify_extractor`)

**Not copied from Downloads:** `Downloads/block_tower.py` and `Downloads/rule30_block_extractor.py` implement the old D₄ transition-table tower with `INITIAL_STATE = (1,1,1)` — a broken prediction path. Umbrella's checkpoint design is canonical for Regime A.

---

## Regime B — (Reserved)

Empirical entropy diagnostics and transition-table experiments live in Downloads / split staging but are **not** promoted. They document why local 8-state lookup fails, not a working extractor.

---

## Regime C — Triadic S₃ chart codec

**Module:** `chart_codec.py`

Encodes the **shell=2 sub-trajectory** as a word in S₃ (Weyl group of SU(3) ⊂ F₄). Lossless round-trip on shell=2 visits only; **collapses** the rest of the 8-state chart.

At depth 4096 (probe_logtime):
- Word length: 1568 symbols
- H(symbol) ≈ 1.88 bits (max 2.0)
- H(symbol | prev 4) ≈ 1.19 bits — some memory, not periodic
- Zlib ratio ≈ 0.28 — **compressible** vs uniform 4-symbol i.i.d., but still O(N) information

---

## Regime C′ — Quadratic D₄ full-chart codec

**Module:** `chart_codec_d4.py`

Lossless decomposition of the **full** 8-state chart into parallel streams:

| Stream | Alphabet | Role |
|--------|----------|------|
| **Label** | 4 axes (antipodal pairs) | Which D₄ doublet |
| **Sheet** | 2 (popcount ≤1 vs ≥2) | Which sheet within the pair |

Round-trip verified at depth 4096. Label stream ≈ full entropy (H ≈ 2.0). Sheet stream globally structured (H ≈ 1.0, LZ ≈ 0.14).

### Axis-3 “second sheet” (T_BIJECTIVE doublet)

At depth 16,384 (`experiments/probe_d4_recursive.py`):

| Level | Signal | H(1) | H(2\|1) | LZ ratio |
|-------|--------|------|---------|----------|
| 0 | labels_all | 2.00 | 1.82 | 0.23 |
| 0 | sheets_all | 1.00 | 0.89 | 0.14 |
| 1 | axis3_sheet | 1.00 | **0.74** | **0.139** |
| 1 | axis0_sheet | 1.00 | 0.96 | 0.17 |
| 1 | axis1_sheet | 1.00 | 1.00 | 0.18 |
| 1 | axis2_sheet | 1.00 | 0.90 | 0.16 |
| 2 | axis3_rule30_pass1 | 0.99 | 0.86 | 0.14 |
| 2 | axis3_or_neighbor_pass4 | 0.42 | 0.41 | **0.063** |
| 2b | axis3_iter_rule30_pass3 | 0.99 | 0.97 | 0.16 |

**Findings:**
- Axis-3 sheet at LEVEL 1 shows the strongest memory (H(2|1) ≈ 0.74 vs ~1.0 on other axes) — the measurable “second sheet.”
- Reapplying Rule 30 as full-row passes (LEVEL 2) does **not** collapse entropy; H stays ~1 bit/symbol.
- OR-neighbor passes artificially compress (H → 0.42) — artifact of monotone operator, not Rule 30 structure.
- Label stream remains incompressible; no period ≤ 1024 in S₃ word (probe_logtime).

---

## What compresses vs what does not

| Object | Compresses? | Notes |
|--------|-------------|-------|
| Center column bits | **No** (Shannon floor) | Regime A = honest I/O only |
| S₃ shell=2 word | Partially | Named group elements; still O(N) bits |
| D₄ label stream | **No** | H ≈ 2 bits/symbol |
| D₄ sheet stream (global) | Slightly | LZ ~14% of raw |
| Axis-3 sheet subsequence | **Most structured** | H(2|1) ≈ 0.74; not enough for log-time addressing |
| LEVEL 2 Rule 30 reapply | **No further win** | Entropy returns to ~1 bit |

---

## Artifacts

- `experiments/probe_logtime.py` → `results_probe_logtime.json`
- `experiments/probe_d4_recursive.py` → `results_probe_d4_recursive.json`
- `scripts/run_all_proofs.py` → `proofs_report.json`
- Tests: `tests/test_block_tower.py`, `test_chart_codec.py`, `test_chart_codec_d4.py`

---

## Recommended next step

Pursue **iterative scalar reapply on axis-3 sheet** only if a principled operator (not OR-neighbor artifact) is identified — current Rule 30 passes do not deepen compression. Parallel track: **W(E₈) O(1) addressing** requires a finite-Weyl element `addr(N)` not derivable from incompressible label/sheet streams alone; treat as separate conjecture from D₄ decomposition. Do not merge Downloads D₄ tower extractor until Regime A checkpoint path is the only promoted I/O layer.
