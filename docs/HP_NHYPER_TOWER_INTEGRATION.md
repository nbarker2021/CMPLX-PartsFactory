# HP / NHyper Tower Integration

**Source spec:** `docs/external/CMPLX_INTERNAL_SYSTEMS_SPEC.md` §9 (HyperPermutations and HyperTowers)  
**Compose hook:** `IndexSupervisor` + `OctadSheet` before Slot 48 forward

## Tower definition

```
Level 0: base tokens
Level 1: all permutations of level 0
Level k: superpermutation of level k−1
```

Each tower level maps to an MDHG scale (atom → room → floor → building …). Tower journals (SNAP L5) record level transitions — crystal export stub: `snap_ledger.jsonl` optional copy in bundles.

## n=4 spine in PartsFactory

| Artifact | Path |
|----------|------|
| SUPERPERM_N4 constant | `src/cmplx/primitives/superperm.py` |
| Verified JSON | `data/superpermutations/n4.json` |
| Octad sheet | `data/superpermutations/octad_n4.json` |
| Supervisor | `src/cmplx/transform/index_supervisor.py` |

`coverage_check()` validates all 4! permutations appear in the n=4 string.

## Compose integration (v0)

1. `IndexSupervisor.walk()` — phase digit → `{template, convolve, involute, abstract}`.
2. `OctadSheet.pick_tree()` — schedule sidecar tree id (stubs until corpus trees land).
3. `compose_pipeline()` — supervisor report → `shell.complete` → optional `GeometricTransformer.forward`.

SP **never** enters ribbon content (Decision D3).

## CQE hyperperm oracle (separate)

`hyperperm_update` in `engine/cqe/_functions.py` updates operator-order oracles. Import of `glyphs_lambda.HyperpermOracle` is **gated** — returns `skipped` when the module is absent. This is not the combinatorial tower.

## Pending promotion

Full `NHyperTower.py` body remains in PENDING_REVIEW — see `NHYPER_TOWER_ESCROW.md`. No promotion without explicit user approval.
