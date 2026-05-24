# Lattice Forge CMPLX Family

Monolith package `lattice-forge` with optional extras. Dev canonical:
`D:/PartsFactory/work/lattice-forge`. Git package:
`CMPLX-PartsFactory/packages/lattice-forge` (sync via
`scripts/sync_lattice_forge_package.ps1`).

Submission snapshot source: `D:/tmp/submission` (zip1 theory, zip2 executable
core, sibling `rule30-decomposition-paper`).

## Spaces

| Space ID | Extra | Honesty | Source |
|----------|-------|---------|--------|
| `lf-core` | (default) | PROVEN substrate | zip2 + work |
| `lf-algebra` | `[algebra]` | PROVEN at depth 4096 | zip2 |
| `lf-ledger` | `[algebra]` | `pass_with_open_gaps` | zip2 + work |
| `lf-solver` | `[solver]` | engineering; prize CONJ | work-only |
| `lf-theory` | `[theory]` | human contract | zip1 `docs/submission/` |
| `lf-proofs` | `[proofs]` | CI regression | `expected_outputs.json` |
| `lf-service` | `[server]` | HTTP manufacturing | `:8845` |
| `lf-witness` | `[witness]` | canonical readout API | `/witness/*` |
| `r30-decomposition` | `[decomposition]` | separate paper claims | `lattice_forge.decomposition` |

Witness route table: `docs/WITNESS.md`. Local CI: `scripts/verify_lattice_forge_family.ps1` (repo root).

Open obligations: see `docs/submission/04_OPEN_OBLIGATIONS.md`.

## Install

```bash
pip install -e "packages/lattice-forge[all]"
```

## CMPLX port

Bootstrap port `worlds` → `cmplx.worlds.forge.WorldsForgeProvider`. Family
manifest: `catalog/families/lattice-forge.json`.
