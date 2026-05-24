# Empirical testing platforms

Each row in `claims/registry.jsonl` (plus umbrella harness keys) maps to an **empirical platform**: a depth ladder, verifier binding, and honesty-aware pass criteria.

## Materialize manifest

```bash
lattice-forge empirical materialize
# or: python scripts/materialize_empirical_platforms.py
```

Writes `empirical/platforms.manifest.jsonl`.

## Run matrix

```bash
lattice-forge empirical run --quick          # CI-friendly [256]
lattice-forge empirical run --exhaustive   # [64,256,1024,4096]
lattice-forge empirical run --claim T3 --quick
```

Report: `empirical_matrix_report.json`

## Exhaustion modes

| Mode | Depth ladder | Use |
|------|----------------|-----|
| quick | 256 | CI, Proof Lab default |
| standard | 64, 256, 1024 | nightly |
| exhaustive | 64, 256, 1024, 4096 | presentation / prize packet |
| full | +8192 | manual only |

**CONJ** claims never upgrade to PROVEN; passes accept `conj` / `pass_with_open_gaps` only.

## Proof Lab + MCP

- `POST http://localhost:8871/api/empirical/run?mode=quick`
- Testkit MCP: `run_empirical_platform(claim_id="T1", mode="quick")`

## Accounting

Split documented in repo `proof-lab/accounting/proof_surfaces.yaml`. Proven lib = lattice-forge; exhaustive empirical matrix = formal artifact alongside `proofs_report.json`.
