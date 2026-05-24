# Ring 2 execution plan

Ring 2 is the **engineering proof layer** that unlocks deferred companions and downstream
unification work.

## Ring 1 is not “frozen”

Earlier notes used **frozen** to mean **scope-locked**, not “do not run or extend Ring 1”:

| Meaning | What it is |
|---------|------------|
| **Scope lock** | Ring 1 *abstract* lists only T1–T8 + BONUS + honest transport labels; CONJ obligations are never promoted to PROVEN in papers (`docs/prize/SCOPE_LOCK.md`). |
| **Separate harness** | `run_regimes_proofs.py` is Ring 2 only so regime depth runs do not blur the prize-core report. |
| **Work order** | Always **Ring 1 → Ring 2**: `scripts/run_ring1_ring2_pipeline.py` |

Ring 1 can and should be re-run whenever Docker/CI is up. Ring 2 proceeds when the Ring 1
**gate** passes (T1–T8 + BONUS `pass`; overall `pass`). CONJ rows (`depth_only_shortcut`,
`nonperiodicity_density`, `P3`, sheet power law) stay documented open under **WP-HONEST-03**.

## Companions (manifest)

| ID | Subpackage | Claims | Gate |
|----|------------|--------|------|
| **WP-REGIMES-01** | `regimes` | 5× `regime.*` BOUNDED_EXEC | `scripts/run_regimes_proofs.py` |
| **WP-DECOMP-01** | `decomposition` | `DECOMP-PAPER` | `lattice-forge decomposition verify` |
| **WP-TOWER-01** | `transport-tower` | 5 transport lemmas | `scripts/run_transport_tower_proofs.py` — **deferred** until ≥5 **PROVEN** |
| WP-OLOID-01 | umbrella | — | deferred |
| WP-MOONSHINE | umbrella | — | deferred |

## Canonical command (Ring 1 first)

```powershell
cd packages/lattice-forge
pip install -e ".[all]"
python scripts/run_ring1_ring2_pipeline.py --quick
```

Ring 2 only (after Ring 1 already green):

```powershell
python scripts/run_ring2_bundle.py --quick
```

Full depth (local nightly):

```powershell
python scripts/run_ring2_bundle.py --max-depth 4096
python scripts/run_ring2_bundle.py --include-monster
```

CLI:

```powershell
lattice-forge ring2 run --quick
```

## Workstreams (priority order)

### W2-A — Regimes (unblocks substrate/codec tooling)

- Keep `expected_outputs_regimes.json` green at `--quick` and full depth.
- Document entropy non-compression in `docs/REGIMES_ABC_D4.md`.
- **Never** promote `rule30.prize.depth_only_shortcut` from CONJ.

### W2-B — Decomposition paper (unblocks checkpoint narrative)

- `verify_all_theorems` + `verify_checkpoint_store` via bundle or CLI.
- Pair witness receipts when Proof Lab runs empirical matrix for `DECOMP-PAPER`.

### W2-C — Transport tower (unblocks WP-TOWER-01)

- Run `run_transport_tower_proofs.py`; track `promotion_status` per lemma.
- Close open gaps lemma-by-lemma until `proven_count >= 5` (see `TRANSPORT_TOWER_POLICY.md`).
- `pass_with_open_gaps` counts as harness **pass** but not companion **PROVEN**.

### W2-D — Monster / residual (Ring 2 claims, optional)

- `monster_d4_lift_claim`, `residual_window_lift` — `--include-monster` on bundle.
- Register rows in `claims/registry.jsonl`; empirical platforms for depth sweeps.

### W2-E — Deferred Ring 3 prep (after W2-A..C stable)

- WP-OLOID-01: `QUAD_OLOID` + kinematic roll keys in `run_all_proofs`.
- WP-MOONSHINE: `VOA_LOOKUP` harness CONJ closure.
- Proof Lab: add Ring 2 surface to `proof-lab/accounting/proof_surfaces.yaml`.

## CI / family verify

- GHA: `lattice-forge-family.yml` — regimes + transport regression.
- Host: `.\scripts\verify_lattice_forge_family.ps1 -Regimes -Ring2`

## Honesty invariants

1. `pass_with_open_gaps` ≠ unconditional `pass` in papers or abstracts.
2. Transport **PROVEN** requires `status == pass` and `open_gap_count == 0`.
3. Ring 2 reports set `not_in_ring1: true` where applicable.
