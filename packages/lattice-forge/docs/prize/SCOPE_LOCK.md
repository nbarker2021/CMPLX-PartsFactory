# Ring 1 scope lock

**Version:** 2026-05-23  
**Branch base:** `feature/lattice-forge-0.2.0-family-hardening` (PR #1)

## In scope (Ring 1 abstract)

The prize-core envelope lists **only**:

- **T1–T8** — proven theorems in `scripts/run_all_proofs.py` / `expected_outputs.json`
- **BONUS** — chart local readout (`BONUS_chart_local_readout`)
- **P1–P3 transport** — sheet lift, torsor functor, Julia glue — labeled **`pass_with_open_gaps`**, not unconditional pass
- **Honest P3** — transport lemmas documented in `docs/tower/TRANSPORT_LEMMAS.md`; companion WP-TOWER-01 deferred until ≥5 TO_ADD rows close

## Explicitly out of scope (Ring 1 abstract)

| Item | Ring | Status |
|------|------|--------|
| `rule30.prize.depth_only_shortcut` | 1 | **CONJ** — never promoted |
| `rule30.prize.nonperiodicity_density` | 1 | **CONJ** |
| Regime A/C/C′ proofs | 2 | `[regimes]` companion WP-REGIMES-01 |
| Umbrella oloid / Rule 90 modules | 3 | `[umbrella]` — `not_in_ring1: true` |
| Decomposition paper Sections 1–10 | 2 | WP-DECOMP-01 — separate paper |
| VOA / moonshine lookup | 3 | deferred WP-MOONSHINE |
| Full Oloid kinematic closure | 3 | deferred WP-OLOID-01 |

## Falsification path

Reviewers run:

```powershell
pip install -e "packages/lattice-forge[prize-core,proofs]"
lattice-forge falsify --tier-a --quick
.\scripts\verify_lattice_forge_family.ps1
```

## Cap

Whitepaper sidecar caps companions at **1 core + ≤4** (`docs/prize/whitepaper_manifest.yaml`).
