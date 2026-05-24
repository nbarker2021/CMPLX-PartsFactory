# Rule 30 decomposition paper (vendored)

Vendored from `D:/tmp/submission/rule30-decomposition-paper` into
`lattice_forge.decomposition`. Covers **Sections 1–10** of `PAPER.md` only.

## Honesty

This space holds **separate paper claims**. It is **not** part of the PROVEN
lattice-forge umbrella proof set in `scripts/run_all_proofs.py`.

Family manifest marks `r30-decomposition` with `separate_paper_claims`.

## CLI verify

```powershell
lattice-forge decomposition verify
```

## Tests

```powershell
python -m pytest tests/test_decomposition.py -q
```

## Modules

| Module | Role |
|--------|------|
| `rule30_decomposition.py` | Theorems 2.1–5.1 |
| `checkpoint_store.py` | Construction 7.1 |
| `fast_rule30.py` | Big-int empirical evolution |
| `empirical.py` | Sections 6 and 8 measurements |
