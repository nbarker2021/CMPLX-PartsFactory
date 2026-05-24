# R30-C → D handoff (PR6: umbrella P0 code)

**Branch:** `feature/rule30-umbrella-port`  
**Agent:** R30-C (Umbrella port)  
**PR:** PR6 — `feat(umbrella): P0 modules and proof gates`  
**Source:** `D:\tmp\umbrella-submission\src\lattice_forge\` (P0 only)

## Ported modules (work/lattice-forge → packages/lattice-forge via sync)

| Module | proof_id / gate | honesty |
|--------|-----------------|---------|
| `rule90_linearization.py` | `RULE90_LINEARIZATION` | PROVEN (bit-exact identity + Lucas + decomposition) |
| `f2_majorana.py` | `F2_MAJORANA` | PROVEN (Arf + edge-glue over F₂) |
| `oloid_rolling.py` | `OLOID_ROLLING` | PROVEN (dyad bijection + K₆ invariants) |
| `oloid_dual_path.py` | `OLOID_DUAL_PATH`, `OLOID_READ_THEN_VERIFY` | PROVEN structural; per-dyad roll rule **open** |
| `oloid_octonionic.py` | `OLOID_OCTONIONIC` | PROVEN (e₄ ¼-spin generator) |
| `quad_oloid.py` | *(no harness key yet)* | structural helper; defer companion |
| `contributions_registry.py` | *(no harness key yet)* | registry only |
| `contribution_validators.py` | *(no harness key yet)* | validators only |
| `voa_lookup.py` | *(no harness key yet)* | CONJ / deferred (WP-MOONSHINE) |
| `core.py` | *(no harness key)* | exploration primitives; not Ring 1 |

## New proof keys in `run_all_proofs.py`

- `RULE90_LINEARIZATION`
- `F2_MAJORANA`
- `OLOID_ROLLING`
- `OLOID_DUAL_PATH`
- `OLOID_READ_THEN_VERIFY`
- `OLOID_OCTONIONIC`

Regression baseline: `expected_outputs_umbrella.json` (checked when `verify_lattice_forge_family.ps1 -Umbrella`).

## Tests ported

- `tests/test_rule90_linearization.py`
- `tests/test_f2_majorana.py`
- `tests/test_oloid_rolling.py`
- `tests/test_oloid_dual_path.py`
- `tests/test_oloid_octonionic.py`

## pyproject extra

```toml
[project.optional-dependencies]
umbrella = []
```

Install: `pip install -e "packages/lattice-forge[umbrella]"`

## Honesty invariants (unchanged)

- **`rule30.prize.depth_only_shortcut`** remains **CONJ** — not mapped to PROVEN in harness or receipts.
- Umbrella modules carry **`not_in_ring1: true`** in `expected_outputs_umbrella.json`.
- `OLOID_DUAL_PATH.tape_readout_match_rate` ~0.528 is documented as structural-only; status is `pass` on involution/addressing checks, not full kinematic closure.

## Deferred (PR7 / sidecar)

| Item | Trigger |
|------|---------|
| `docs/umbrella/` paper corpus | PR7 (Agent C) |
| WP-OLOID companion | Sidecar deferred list; quad_oloid + full kinematic roll |
| WP-MOONSHINE | `voa_lookup.py` without proof key |
| `contributions_registry` / `contribution_validators` harness keys | After manifest v1 implicated_by edges |

## Verify commands

```powershell
.\scripts\sync_lattice_forge_package.ps1
.\scripts\verify_lattice_forge_family.ps1 -CheckSync -Umbrella
cd packages\lattice-forge
python scripts\run_all_proofs.py --quick
```

## For manifest v1 (Agent D)

Suggested companion slot: **WP-UMBRELLA-01** (`not_in_ring1: true`), claims tied to the six proof keys above. Link deferred: WP-OLOID-01, WP-MOONSHINE.
