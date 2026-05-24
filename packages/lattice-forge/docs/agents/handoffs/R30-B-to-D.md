# R30-B → R30-D handoff (PR4: regimes subpackage)

**From:** Agent B (`feature/rule30-regimes`)  
**To:** Agent D (meta / whitepaper sidecar)  
**PR:** PR4 — `feat(regimes): subpackage extra and regression split`  
**Date:** 2026-05-23

## Summary

Ring 2 regimes are installable via `[regimes]` extra with a dedicated proof harness
(`scripts/run_regimes_proofs.py`) and regression file `expected_outputs_regimes.json`.
Documentation index: `docs/regimes/README.md` → `docs/REGIMES_ABC_D4.md`.

## Regime claim_ids (for registry / manifest)

| claim_id | proof_key | status | honesty_label | verifier_id |
|----------|-----------|--------|---------------|-------------|
| `regime.substrate.map` | `SUBSTRATE_MAP` | PROVEN | `bounded_exec` | `verify_substrate_map` |
| `regime.a.block_tower` | `BLOCK_TOWER` | PROVEN | `bounded_exec` | `verify_block_tower` |
| `regime.a.block_extractor` | `BLOCK_EXTRACTOR` | PROVEN | `bounded_exec` | `verify_extractor` |
| `regime.c.chart_codec` | `CHART_CODEC` | PROVEN | `bounded_exec` | `verify_chart_codec` |
| `regime.cprime.chart_codec_d4` | `CHART_CODEC_D4` | PROVEN | `bounded_exec` | `verify_chart_codec_d4` |

All five are **bounded finite-window** checks at declared `max_depth`. They do **not**
promote `rule30.prize.depth_only_shortcut` from CONJ.

## Obligation ledger wiring (obligation_id → claim_id)

| obligation_id | ledger status | maps_to claim_id | sidecar honesty |
|---------------|---------------|------------------|-----------------|
| `rule30.scalar_coverage.no_unassigned_tested_n` | BOUNDED_EXEC | `regime.substrate.map` (supporting) | bounded_exec |
| `rule30.scalar_formula.nth_bit_expression` | EXPRESSIBLE | `regime.a.block_extractor` (formula over legal state; not depth-only) | expressible |
| `rule30.ribbon.feedback_closure` | BOUNDED_EXEC | `regime.substrate.map` (supporting) | bounded_exec |
| `rule30.dihedral.block_closure` | BOUNDED_EXEC | `regime.a.block_tower` | bounded_exec |
| `rule30.extension.relative_table_stability` | BOUNDED_EXEC | `regime.a.block_tower`, `regime.a.block_extractor` | bounded_exec |
| `rule30.sheet_operator.power_law` | CONJ | *(none — do not pair)* | conj |
| `rule30.prize.depth_only_shortcut` | CONJ | *(none — do not pair)* | conj |
| `rule30.prize.nonperiodicity_density` | CONJ | *(none — do not pair)* | conj |
| `rule30.turing_universality` | CONJ | *(none — do not pair)* | conj |

## Whitepaper pairing hint (for Agent D)

- **WP-REGIMES-01** companion: pair to `regime.*` claim_ids above; `not_in_ring1: true`.
- Do **not** list regime proofs as Ring 1 T1–T8 substitutes.
- `rule30.prize.depth_only_shortcut` must remain in manifest `deferred` or `open_gaps`, not PROVEN.

## Verify commands

```powershell
.\scripts\verify_lattice_forge_family.ps1
.\scripts\verify_lattice_forge_family.ps1 -Regimes
```

## Open for PR5 (not in this handoff)

- Witness state key grammar `lf/state/{regime}/...`
- `Forge.witnessed_lookup` stub returning `NOT_WITNESSED`
- B-WITNESS falsification row (coordinate with Agent A FALSIFICATION.md)
