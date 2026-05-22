# Lattice-forge port review (2026-05-21)

Dual-home port: develop in `D:\PartsFactory\work\lattice-forge`, publish
`CMPLX-PartsFactory/packages/lattice-forge`, manufacture `cmplx.worlds.forge`
(slot-19, HTTP :8845).

## Recent functional updates

Beyond the earlier 14 harness verify pairs, three prize surfaces landed in
`rule30.py` with CLI/server/smoke wiring (23 smoke steps):

| Surface | Model id | Role |
|---------|----------|------|
| `rule30_sheet_operator` | `rule30_sheet_operator_v0_1` | Multi-page extension as powers of one sheet operator; depends on `rule30_hypervisor_extension_tape` |
| `rule30_nth_bit_expression` | `rule30_nth_bit_expression_v0_1` | Witness at depth `n` with `pair_product_key`, `scalar_syndrome`, `scalar_emitted_bit` (relational readout) |
| `rule30_proof_obligation_ledger` | `rule30_proof_obligation_ledger_v0_1` | Status ladder + explicit `blocks_release` for prize submission |

Interpretation: work shifted from more harness layers to **submission-grade
obligation accounting** — expression vs extraction vs bounded exec vs open
theorems — without collapsing claims into a single gap string.

## Harness table (Rule 30 + verify)

| # | Model / verify | Smoke depth (typical) | Verify status pattern |
|---|----------------|----------------------|------------------------|
| 1 | morphon / verify | max_depth=5 | pass* |
| 2 | vignettes / verify | max_order=4 | pass* |
| 3 | moving_frame / verify | 8 | pass* |
| 4 | color_chirality / verify | 8 | pass* |
| 5 | discrete_lagrangian / verify | 8 | pass* |
| 6 | lagrangian_depth_trace / verify | 64 | pass* |
| 7 | mandelbrot_scalar / verify | 64 | pass* |
| 8 | reduced_alphabet / verify | 128 | pass* |
| 9 | symmetry_environment / verify | 128 | pass* |
| 10 | physics_method_stack / verify | 128 | pass* |
| 11 | whole_integer_n_coverage / verify | 1024 | pass* |
| 12 | readout_ribbon_machine / verify | 1024 | pass* |
| 13 | dihedral_block_hypervisor / verify | 512 | pass* |
| 14 | hypervisor_extension_tape / verify | page 512 | pass* |
| 15 | sheet_operator / verify | page 128 | pass* |
| 16 | nth_bit_expression / verify | n=129, page 128 | pass* |
| 17 | proof_obligation_ledger / verify | max_depth 128 | **pass_with_open_gaps** |

\* `startswith("pass")` in smoke — includes `pass_with_open_gaps` on ledger only.

Parallel spine (not smoke-linear): `terminal_tree`, `morphonics_model`, Niemeier
ledger — `failure:leech_construction_pending` remains honest.

## Proof obligation blockers (`blocks_release: true`)

From `rule30_proof_obligation_ledger` at default construction:

| obligation_id | status | blocks_release |
|---------------|--------|----------------|
| `rule30.sheet_operator.power_law` | CONJ | yes |
| `rule30.prize.depth_only_shortcut` | CONJ | yes |
| `rule30.prize.nonperiodicity_density` | CONJ | yes |
| `rule30.turing_universality` | CONJ | yes |

Bounded-exec obligations (scalar coverage, ribbon feedback, dihedral blocks,
extension table stability) are **not** release blockers. Nth-bit is
**EXPRESSIBLE** (not blocking).

Verify ledger enforces required obligation ids and warns when
`blocking_obligations` non-empty — schema **pass_with_open_gaps**, not silent pass.

## Three DAG families

1. **Harness** — `docs/lattice-forge-harness-dag.mmd` (foundation → scale → prize).
2. **Morphonics + obligations** — `morphonics.py` bridges/failures; ledger is canonical export for repo-kernel (Phase 2: `proof.tarpit_witness` etc. not implemented).
3. **CMPLX port** — `docs/lattice-forge-cmplx-port-dag.mmd`; `PORT_DEPENDENCY_DAG` includes `cmplx.worlds.forge` → receipt, geometry, symbolic.

## Dual-home model

| Home | Path | Role |
|------|------|------|
| Dev | `work/lattice-forge` | Experiments, sheet/nth/ledger, future `proof/` |
| Package A | `packages/lattice-forge` | `pip install -e` for external consumers |
| Slot B | `src/cmplx/worlds/forge` | Thin provider + receipt bridge + :8845 HTTP |

Sync: `scripts/sync_lattice_forge_package.ps1` (work → packages). **Do not**
move `rule30.py` into `cmplx` — package only.

## Delta vs checkpoints 023–024

Worldsheet / relational pole obligations called out in 023–024 remain **open**
in code (CONJ prize rows; no `PAPER_PROOF` on Leech). Port does not upgrade
`pending_import` Leech rows to proven.

## Baseline

See `identity_review/reports/lattice-forge-baseline-2026-05-21.json` (reduced
depth verify snapshot). Work tree: smoke OK, pytest 27 passed (2026-05-21).
