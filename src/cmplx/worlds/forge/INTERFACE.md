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

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `FORGE_MINT_RECEIPT` | `1` | Mint verify events on receipt port |
| `FORGE_OVERLAY_ROOT` | temp dir | Project overlay `.lattice_forge/` parent |
| `FORGE_PORT` | `8845` | HTTP manufacturing port |

## Honesty

Verify returns `pass_with_open_gaps` when CONJ obligations remain blocking; do not map to unconditional `pass` in CMPLX gates.
