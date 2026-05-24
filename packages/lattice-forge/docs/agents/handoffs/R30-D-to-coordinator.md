# R30-D → Coordinator handoff (PR8 + PR9)

- **Branch:** feature/rule30-formalization-meta
- **PRs:** PR8 sidecar + manifest v1; PR9 transport tower stub
- **Verify:** `verify_lattice_forge_family.ps1` green; `run_whitepaper_sidecar.py` refreshes YAML

## Recommended merge order

After PR #1 (`feature/lattice-forge-0.2.0-family-hardening`) merges to `main`:

1. **A PR2** — `claims/registry.jsonl` + falsify Tier A (manifest dependency)
2. **D PR8** — whitepaper sidecar + manifest v1
3. **C PR6** — umbrella P0 modules + merged `run_all_proofs`
4. **B PR4** — `[regimes]` extra + `run_regimes_proofs`
5. **A PR3** — scope lock + reviewer pack
6. **C PR7** — umbrella docs corpus
7. **B PR5** — witness state keys + `witnessed_lookup` stub
8. **D PR9** — transport lemma registry stub

Rebase each agent branch onto `main` weekly if PR #1 remains open.

## manifest delta

- `total_companions_beyond_core: 3` (WP-HONEST-03, WP-REGIMES-01, WP-DECOMP-01)
- **Deferred:** WP-OLOID-01, WP-MOONSHINE, WP-TOWER-01 (2 TO_ADD transport rows)

## Next phase

- Umbrella P1 experiments (deferred WP-MOONSHINE)
- O1 lookup table — **separate branch** `feature/rule30-o1-lookup` only after manifest approves
- Transport tower: close ≥5 TO_ADD lemmas before WP-TOWER-01 companion

## Honesty invariant (program-wide)

Never map `pass_with_open_gaps` or `rule30.prize.depth_only_shortcut` (CONJ) to unconditional
`pass` in harness, receipts, or paper abstracts.
