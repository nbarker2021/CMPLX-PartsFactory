# Honesty promotion harness

Machine-checkable path from **CONJ** to **BOUNDED_EXEC** (and explicit remaining CONJ).

## Command

```powershell
cd packages/lattice-forge
python scripts/run_open_claims_harness.py --quick
python scripts/run_open_claims_harness.py --quick --write-registry
```

Wired into Ring 1 pipeline: `run_ring1_ring2_pipeline.py` (stage `open_claims_harness`).

## Promotion map

| Claim | Was | Now | Proof key |
|-------|-----|-----|-----------|
| `rule30.sheet_operator.power_law` | CONJ | BOUNDED_EXEC | `SHEET_POWER_LAW_BOUNDED` |
| `rule30.prize.nonperiodicity_density` | CONJ | BOUNDED_EXEC | `NONPERIODICITY_DENSITY_BOUNDED` |
| `rule30.extraction.block_addressed` | — | BOUNDED_EXEC | `DEPTH_EXTRACTION_ACCOUNTING` |
| `P3` | CONJ | BOUNDED_EXEC | `P3_WEYL_ENGINEERING` |
| `VOA_LOOKUP` | CONJ | BOUNDED_EXEC | `VOA_HARNESS` |
| `monster.d4_lift.*` | CONJ | BOUNDED_EXEC | harness verifiers |
| `monster.residual_window.*` | CONJ | BOUNDED_EXEC | when all checks pass |
| `rule30.prize.depth_only_shortcut` | CONJ | **CONJ** | sublinear theorem still open |

## Still CONJ (by design)

- `rule30.prize.depth_only_shortcut` — no O(1)/sublinear extraction from n alone
- `rule30.turing_universality` — simulation theorem not attached
- All-page sheet operator induction (narrowed claim is bounded only)

## Regression

`expected_outputs_open_claims.json` + family verify `-Ring2` / pipeline.
