# Superpermutation build (n=4–8)

## Artifacts

| Path | Role |
|------|------|
| `data/superpermutations/n4.json` | Minimal n=4 (bundled constant + checksum) |
| `data/superpermutations/n5.json` | Minimal n=5: palindrome + 7 trees (8 Johnston lines, labeled) |
| `data/superpermutations/octad_n5.json` | Octad slot → alternate mapping + journal refs |
| `data/superpermutations/n6.json` | Best-known n=6 (`record`) |
| `data/superpermutations/n7.json` | Best-known n=7 (`record`) |
| `data/superpermutations/n8.json` | Best-known n=8 (`record`) |
| `data/superpermutations/octad_n4.json` | Octad sheet for n=4 spine |
| `src/cmplx/primitives/superperm.py` | `superperm_n(n)`, `coverage_check`, schedule cursor |

## Published sources

| n | Length | `provenance_class` | URL |
|---|--------|-------------------|-----|
| 5 | 153 | `minimal` | http://www.njohnston.ca/superperm5.txt |
| 6 | 873 | `record` | http://www.njohnston.ca/superperm6_1wasted.txt |
| 7 | 5908 | `record` | https://gregegan.net/SCIENCE/Superpermutations/7_5908.txt |
| 8 | 46205 | `record` | https://gregegan.net/SCIENCE/Superpermutations/8_46205.txt |

n=6–8 are **not** claimed minimal—only best-known records.

## Ingest

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
python scripts/ingest_superpermutations.py --all
python scripts/validate_superpermutations.py --require 4,5,6,7,8
```

Local override: `python scripts/ingest_superpermutations.py --n 7 --from-file path\to\7.txt`

## n=5 octad (palindrome + 7 trees)

Johnston lists **8** length-153 minimals (Ben Chaffin, March 2014). Exactly one is palindromic; the other **seven** are the tree alternates. Ingest writes:

- `labeled_alternates[]` with `label`, `journal_ref`, `role`, `is_palindrome`
- `octad_n5.json` mapping phase 0 → palindrome, phases 1–7 → one tree each

`IndexSupervisor` with `active_n=5` walks 153 steps: at step `i`, phase `i % 8`, digit from **that phase’s** superpermutation string (not the palindrome alone).

## Runtime

- `IndexSupervisor` resolves `active_n` from crystal manifest or `nhyper_tower.tower_level` (`n = level + 4` for levels 0–4).
- Re-crystallize after ingest so `identity_review.crystal` records `active_n`, `sp_length`, `sp_checksum`, `n5_alternate_labels`, and status fields.

```powershell
python -m cmplx.transform crystallize --name identity_review `
  --db data/token_index_identity_review.sqlite `
  --out crystals/identity_review.crystal
```

## Tests

```powershell
python -m pytest tests/transform/test_superperm_invariants.py tests/primitives/test_superperm.py tests/primitives/test_superperm_n5_n8.py -q
```
