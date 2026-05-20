# Three-Space Catalog Status - 2026-05-13

## Roots

- PartsFactory active yard: `D:/PartsFactory`
- Manny evidence substrate: `D:/Manny Unification 2`
- OC build doctrine/evidence: `D:/OC build`

Manny and OC build remain evidence/doctrine inputs. Cataloging writes only to
PartsFactory-managed SQLite files and staging paths.

## What The Interrupted Scan Produced

The stopped Manny scan did produce useful partial rows in
`data/three_space_catalog.sqlite`; it was not wasted.

Current file inventory rows:

| Space | Files | Code files | Zip archives | Bytes represented |
| --- | ---: | ---: | ---: | ---: |
| `manny` | 815,000 | 324,099 | 4,767 | 420,542,186,317 |
| `partsfactory` | 110,992 | 64,067 | 338 | 8,834,313,053 |
| `ocbuild` | 808 | 76 | 0 | 1,942,982,508 |

The Manny root scan is marked interrupted in `scan_log` with this handling note:
use region/deferred scans rather than full-root recursion.

Biggest observed issue: Manny contains very large duplicate archive families,
including repeated `UNIBUILD.zip`, `CQEDevKit.zip`, and `Work Files-Historic.zip`
copies. These should be manifested and deduped before extraction. Extraction
should stay staged under `data/extracted_zips/...`.

## GitNexus State

Live GitNexus registry currently has 8 indexed repos:

- `cmplx-partsfactory-root`
- `cqe-unified-runtime-v8`
- `cqe-organized`
- `manny-full-datasets-from-previous-review-cmplx-tmn1-98629466`
- `manny-full-output-reports-code-reports-2f431eff`
- `manny-full-output-reports-db-reports-dda695cd`
- `manny-full-output-reports-doc-reports-6b119236`
- `manny-full-output-reports-sql-reports-a35212fd`

`cmplx-partsfactory-root` indexed successfully with 279 files, 9,930 symbols,
16,640 edges, 318 clusters, and 256 processes.

GitNexus should be used on bounded targets from `gitnexus_target` and
`git_repo`, not as a raw walker across all three roots.

## Git Repo Catalog

New script:

```powershell
python scripts\git_repo_catalog.py --import-github --import-prior --scan partsfactory --report
python scripts\git_repo_catalog.py --scan manny --scan-rel "historical builds\CMPLX-TMN2\repos" --report
```

Tables added to `data/three_space_catalog.sqlite`:

- `github_repo`: authenticated `nbarker2021` repo list from `gh`
- `git_repo`: local and prior GitNexus repo records

Current repo rows:

| Source | Rows |
| --- | ---: |
| Manny prior GitNexus inventory | 64 |
| Manny local targeted scans | 33 |
| PartsFactory local scan | 7 |

Authenticated GitHub repos for `nbarker2021`: 12.

Important local findings:

- `D:/PartsFactory/CMPLX-PartsFactory` is a local git workspace with no remote configured.
- `D:/PartsFactory/-main` is also a local git repo with no remote configured.
- Nested PartsFactory imports with `nbarker2021` remotes:
  - `CMPLX-1T`
  - `CMPLX-Manny`
  - `CMPLX-TMN-main`
  - `CMPLXMCP`
  - `CMPLXUNI`
- Manny contains many duplicate live repo copies and extracted repo copies.
- `CMPLX-PartsFactory` and `scout-demo-service` exist on GitHub but are not matched
  to a local remote in the current catalog.
- A stale/extra remote `nbarker2021/CMPLXZIP` appears locally but is not in the
  current authenticated GitHub repo list.

## Recommended Next Handling

1. Treat each repo as a catalog entity before any code aggregation.
2. Do not recursively extract all zips. Manifest, size-rank, dedupe, then extract
   only bounded candidates into PartsFactory staging.
3. Use top-level Manny regions as scan units:
   - `Working Prototyping`
   - `agent ecosystem`
   - `historical builds/CMPLX-TMN2/repos`
   - selected `datasets from previous review/...` slices only after dedupe
4. Add GitNexus targets from `git_repo` after classification, especially the
   currently active GitHub-owned repos and high-priority historical-system repos.
5. Keep `.git` repo identity intact. Do not flatten, copy over, or canonicalize
   repo folders until their remote/head/dirty state has been recorded.
