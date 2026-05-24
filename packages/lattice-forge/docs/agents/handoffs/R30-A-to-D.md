# R30-A → D handoff (PR2: prize core + Tier A falsify)

- **Branch:** feature/rule30-prize-core
- **PR:** PR2 — `feat(prize-core): claims registry and falsify Tier A`
- **Verify:** `verify_lattice_forge_family.ps1` + `lattice-forge falsify --tier-a --quick`

## claim_id export

| claim_id | honesty_label | verifier_id |
|----------|---------------|-------------|
| T1 | PROVEN | verify_octonion_axioms |
| T2 | PROVEN | verify_j3o_axioms |
| T3 | PROVEN | verify_chart_j3o_isomorphism |
| T4 | PROVEN | verify_n3_su3_closure_exact |
| T5 | PROVEN | search_for_su3_closure_scale |
| T6 | PROVEN | decompose_8x8_via_block_action_exact |
| T7 | PROVEN | closed_form_rule30_8x8_transition_exact |
| T8 | PROVEN | forge.can_close |
| BONUS | PROVEN | verify_rule30_chart_local_readout |
| P1 | TRANSPORTED | transport:IT1 |
| P2 | TRANSPORTED | transport:IT2 |
| P3 | CONJ | engineering:Weyl-table-lookup |
| rule30.prize.depth_only_shortcut | CONJ | verify_rule30_proof_obligation_ledger |
| rule30.prize.nonperiodicity_density | CONJ | verify_rule30_proof_obligation_ledger |

## Notes for manifest v1

- Registry path: `claims/registry.jsonl`
- Falsification doc: `docs/prize/FALSIFICATION.md`
- PR3 adds `SCOPE_LOCK.md`, `REVIEWER_PACK.md`, optional Tier B scripts
- **Never** map CONJ or `pass_with_open_gaps` to unconditional pass
