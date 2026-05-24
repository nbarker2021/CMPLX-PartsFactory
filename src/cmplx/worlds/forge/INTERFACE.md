# Worlds Forge — interface

## Port

- **Name:** `worlds`
- **Part id:** `lattice-forge`
- **Provider:** `cmplx.worlds.forge.WorldsForgeProvider`
- **Package:** `lattice_forge.Forge` (`pip install -e packages/lattice-forge`)

## Registration

```python
from cmplx.morphon import MorphonController
from cmplx.worlds.forge import WorldsForgeProvider

MorphonController.get().register("worlds", WorldsForgeProvider())
```

Or via `runtime.cmplx_bootstrap.register_all()` after bootstrap registry includes `worlds`.

## Primary methods (reduced-depth CI defaults)

| Method | Purpose |
|--------|---------|
| `health()` | Seed integrity + overlay root |
| `status()` | Forward to `Forge.status()` |
| `verify_rule30_proof_obligations(...)` | Submission ledger verify; mints receipt when enabled |
| `rule30_proof_obligations(...)` | Ledger model (honest `pass_with_open_gaps`) |
| `verify_morphonics()` | Morphonics DAG self-check |
| `witness_classify(...)` | Ledger witness query + optional mint |
| `witness_regime_a_query(...)` | Regime A block-tower query + optional mint |
| `witness_regime_c_encode(...)` | Regime C S₃ codec encode |
| `witness_regime_cprime_encode(...)` | Regime C′ D₄ codec encode |
| `witness_syndrome(...)` | ECC/shed syndrome report |
| `witness_proof_bundle(...)` | Ledger proof bundle + optional mint |
| `witness_proof_bundle_full(...)` | Full umbrella proofs via `run_all_proofs` |

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `FORGE_MINT_RECEIPT` | `1` | Mint verify events on receipt port |
| `FORGE_OVERLAY_ROOT` | temp dir | Project overlay `.lattice_forge/` parent |
| `FORGE_PORT` | `8845` | HTTP manufacturing port |
| `FORGE_WITNESS_MAX_DEPTH` | `4096` | Cap on witness proof-bundle/full depth |

## Honesty

Verify returns `pass_with_open_gaps` when CONJ obligations remain blocking; do not map to unconditional `pass` in CMPLX gates.

## Witness HTTP routes

See `packages/lattice-forge/docs/WITNESS.md` for ledger vs readout classify distinction and the full route table on `:8845`.

## Local verification

```powershell
.\scripts\verify_lattice_forge_family.ps1
```
