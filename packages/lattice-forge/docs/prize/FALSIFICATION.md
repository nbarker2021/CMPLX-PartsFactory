# Ring 1 prize-core falsification

Machine-falsifiable breaks for peer review. **Honesty invariant:** never map
`pass_with_open_gaps` or `rule30.prize.depth_only_shortcut` (CONJ) to unconditional
`pass` in harness output, receipts, or paper abstracts.

## Tier A (required)

Runs breaks **B-T1** through **B-T8**, **B-BONUS**, and **B-decomp** (decomposition
is `not_in_ring1` but included for falsification coverage).

| Break | Verifier | Ring |
|-------|----------|------|
| B-T1 | `verify_octonion_axioms` | 1 |
| B-T2 | `verify_j3o_axioms` | 1 |
| B-T3 | `verify_chart_j3o_isomorphism` | 1 |
| B-T4 | `verify_n3_su3_closure_exact` | 1 |
| B-T5 | `search_for_su3_closure_scale` | 1 |
| B-T6 | `decompose_8x8_via_block_action_exact` | 1 |
| B-T7 | `closed_form_rule30_8x8_transition_exact` | 1 |
| B-T8 | `Forge.can_close` Niemeier paths | 1 |
| B-BONUS | `verify_rule30_chart_local_readout` | 1 |
| B-decomp | `decomposition.verify_all_theorems` | 2 (separate paper) |

```powershell
lattice-forge falsify --tier-a --quick
```

Exit **0** only when every break reports `passed: true` with honest status labels.

## Tier B (optional, non-blocking)

Documented scripts for period search and density estimate — **not** gate merge:

- `scripts/tier_b_period_search.py` — finite period scan (CONJ obligations unchanged)
- `scripts/tier_b_density_estimate.py` — empirical density window

```powershell
lattice-forge falsify --tier-b
```

Emits JSON with both script reports; **does not** upgrade CONJ or gate CI.

## Witness (Ring 2, Agent B)

| Break | Scope |
|-------|-------|
| B-WITNESS | After regime C encode, primary state key resolves `WITNESSED` via in-memory store (stub suffix stays `NOT_WITNESSED`) |

## Regime coordination

Regime falsification lives in `scripts/run_regimes_proofs.py` (`[regimes]` extra).
See `docs/regimes/README.md`.

## Claim registry

Authoritative claim IDs: `claims/registry.jsonl`. Sidecar manifest v1 consumes this
file via `scripts/run_whitepaper_sidecar.py`.
