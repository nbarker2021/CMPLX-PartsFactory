# NHyperTower Escrow Ticket

**Date:** 2026-05-19  
**Status:** Escrow — do not promote without user approval

## Summary

Combinatorial **NHyperTower** implementation (`NHyperTower.py`) is indexed in `PENDING_REVIEW_INDEX` but not merged into `src/cmplx/`. This session ships:

- Doctrine + integration docs
- `superperm` primitive + `n4.json`
- `IndexSupervisor` / `OctadSheet` v0 compose hooks

## What is in tree now

| Deliverable | Location |
|-------------|----------|
| n=4 superpermutation | `primitives/superperm.py`, `data/superpermutations/n4.json` |
| Octad metadata | `data/superpermutations/octad_n4.json` |
| Supervisor | `transform/index_supervisor.py` |
| Escrow wiring | `transform/nhyper_tower.py`, crystal `manifest.nhyper_tower` |
| HP integration note | `HP_NHYPER_TOWER_INTEGRATION.md` |

## Promotion checklist (when approved)

1. Run PENDING_REVIEW path on `NHyperTower.py` witness.
2. Wire tower level picker into `compose_pipeline` (beyond v0 SP walk).
3. Enable SNAP L5 tower journal writes (not just optional ledger copy).
4. Re-run `pytest tests/transform/ tests/primitives/` and identity_review ingest gate.

## Blockers

- Full level-1..N Cartesian builds remain out of scope (use ingest + supervisor milestones).
- CQE `glyphs_lambda` module absent — `hyperperm_update` gated, not tower promotion.
