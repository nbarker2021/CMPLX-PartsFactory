# GitNexus PartsFactory Review - 2026-05-13

## Scope

Reviewed the active PartsFactory workspace with GitNexus as a graph aid, while preserving the three-space rule:

- `D:\PartsFactory` -> active working yard
- `D:\Manny Unification 2` -> historical evidence substrate
- `D:\OC build` -> prior OpenCode doctrine/history

## Mount Update

Added `docker-compose.gitnexus-three-space.yml` in `CMPLX-PartsFactory`.

This override extends the existing Manny GitNexus service with:

- `/workspace/current-partsfactory` -> `D:\PartsFactory`
- `/workspace/current-oc-build` -> `D:\OC build` read-only

Existing mounts remain:

- `/workspace/current-manny-root` -> `D:\Manny Unification 2`
- `/workspace/current-implementation` -> `D:\Manny Unification 2\Manny Unification 2 Implementation`
- `/data/gitnexus` -> `D:\Manny Unification 2\data\gitnexus`

GitNexus was recreated with the override and came back healthy.

## Existing GitNexus State

Live registry now has 8 indexed repositories:

- 7 prior Manny-side indexes:
  - `cqe-unified-runtime-v8`
  - `cqe-organized`
  - `manny-full-datasets-from-previous-review-cmplx-tmn1-98629466`
  - `manny-full-output-reports-code-reports-2f431eff`
  - `manny-full-output-reports-db-reports-dda695cd`
  - `manny-full-output-reports-doc-reports-6b119236`
  - `manny-full-output-reports-sql-reports-a35212fd`
- 1 new PartsFactory root index:
  - `cmplx-partsfactory-root`

## New PartsFactory Root Graph

Command:

```powershell
docker exec gitnexus-rebuild-server sh -lc 'cd /workspace/current-partsfactory/CMPLX-PartsFactory && node /app/gitnexus/dist/cli/index.js analyze --skip-agents-md --no-stats --name cmplx-partsfactory-root --max-file-size 512'
```

Result:

- 279 files
- 9,930 symbols
- 16,640 edges
- 318 clusters
- 256 flows

Warnings:

- Git ownership needed a container-local `safe.directory` entry for the Windows bind mount.
- Several Python files reported scope-extraction warnings but the index completed.
- GitNexus text query currently reports FTS write attempts against a read-only DB. Cypher and context queries work.

## Archive Recursion Finding

The user suspected nested zips and recursive extracted folders were causing massive parse pressure. Evidence supports this.

From `data/yard_inventory.sqlite`:

- 190 zip archives in the PartsFactory inventory
- Approx. 4.4 GB total zip payload
- 178 marked as orphan zips by `scripts/zip_audit.py`
- Largest archive: `dimensional-forms-lowd-e8-highd-curated-20260508-164720.zip` at approx. 1.6 GB

Many archive top entries point into `output/archive-staging/<uuid>/...`, which means the system is carrying packaged pipeline sediment as well as extracted/generated descendants.

## Boundary Added

Added root `.gitnexusignore` so the active `CMPLX-PartsFactory` graph stays focused on the current framework instead of recursively absorbing imported systems, corpora, local DBs, and archive payloads.

Ignored from the root graph:

- `.gitnexus/`, `.opencode/`, `.pytest_cache/`, `docker-cache/`
- `data/`, `corpus_extracted/`
- imported systems (`CMPLX-1T/`, `CMPLX-Manny/`, `CMPLX-TMN-main/`, `CMPLXMCP/`, `CMPLXUNI/`)
- archives, SQLite/DB files, PDFs, DOCX, images, binary/model weights, logs, pycache

Imported systems should be indexed as separate named GitNexus targets, not folded into the root graph.

## Recommended Indexing Strategy

Do not run a full-root GitNexus analyze over `D:\PartsFactory`, `D:\Manny Unification 2`, or `D:\OC build`.

Use this sequence instead:

1. Archive inventory first: zips are catalog records, not parse input.
2. Deduplicate or fingerprint extracted folders before indexing.
3. Index bounded code-rich targets with explicit aliases.
4. Keep large historical variants as separate repos/groups.
5. Promote evidence only after graph findings are cross-checked against the catalog and source files.

Candidate next indexes:

- `CMPLXUNI` as `partsfactory-cmplxuni`
- `CMPLXMCP` as `partsfactory-cmplxmcp`
- `CMPLX-TMN-main` as `partsfactory-cmplx-tmn-main`
- selected corpus extractions only after archive/orphan review

GitNexus is evidence infrastructure. It should guide relationship review, not decide canon.
