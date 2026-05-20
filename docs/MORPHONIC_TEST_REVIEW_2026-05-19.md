# Morphonic production hardening — test & review (2026-05-19)

## Test matrix

| Suite | Command | Result |
|-------|---------|--------|
| Full transform + primitives | `PYTHONPATH=src python -m pytest tests/transform/ tests/primitives/ -q` | **115 passed** (~3.7s) |
| P1–P7 integration slice | `pytest tests/transform/test_index_mutations.py test_compose_pipeline.py test_multistream_ingest.py test_tool_pass_integration.py` | **18 passed** (~1.5s) |

## CLI / demo smoke

| Check | Outcome |
|-------|---------|
| `morph-probe --concat-a baaaaaab --concat-b BaaaaAab` | `verdict=intentional`, `warmstart_outcome=case_base`, `geometry_invariant=true` |
| `examples/multistream_compose_demo.py` | **Fixed** — was instantiating abstract `TranslateHub()`; now `translate_hub_from_env()` (NoOpHub). Runs; supervisor 33 steps on temp DB |
| `forward --production --ribbon baaaaaab --db data/token_index_morphonic.sqlite` | 8 layer traces, ports registered, JSON summary emitted |
| `crystal-info --bundle crystals/identity_review.crystal` | OK; manifest still **1.0.0** (pre-2.1.0 bundle — re-crystallize to pick up 2.1.0 schema) |
| `GET http://localhost:8786/api/morphonic/status` | **Not verified** — timeout (repo-kernel down or slow) |

## Code review (P1–P7)

### P1 — Index mutations (`index_mutations.py`, `index_supervisor.py`)

- **Strengths:** Real `convolve` / `involute` / `abstract` / `refine_to_coverage`; supervisor runs each mutation once per walk; `partial_seed` merged into octad template patterns.
- **Risks:** `convolve` scans full `token_bonds` — O(n) on large DBs; use `refine --limit` in ops. Coverage metric uses template frame percentages (can exceed 100% in reports — documented in template stats).

### P2 — Tool pass (`tool_pass.py`)

- **Strengths:** TarPit `derive()` wired; geometry + morph_signature upsert; SNAP labels in receipts.
- **Risks:** Receipt mint failures swallowed; TarPit mean_mass fallback keys (`final_mass` vs `mean_mass`) — monitor if summaries change upstream.

### P3 — Multistream (`lib_encoder.py`, `ingest_multistream`)

- **Strengths:** `NoOpHub` + `translate_hub_from_env()`; EN-first ingest + `translation_links`; tests cover re-ingest warmstart ratio.
- **Gaps:** DeepL hub not implemented (env `deepl` raises); identity_review ingest script not run in this review pass.

### P4 — Production inference (`config.py`, `compose_pipeline.py`, attention)

- **Strengths:** `ProductionTransformerConfig` (`use_n_ladder=True`, `shell_bind=True`); compose runs supervisor before `shell.complete()`; forward CLI `--production`.
- **Risks:** Base `TransformerConfig` still conservative (4 layers, shell_bind off) — intentional; callers must opt in.

### P5 — Ops surfaces

- **Strengths:** `MORPHONIC_PRODUCTION_RUNBOOK.md`; repo-kernel routes registered in `server.py`.
- **Gaps:** Bridge default DB path is container-centric (`/sources/PartsFactory/...`); set `MORPHONIC_TOKEN_INDEX_DB` on host. Existing crystal manifest not upgraded to 2.1.0.

### P6 — Combinatorics slots

- `data/superpermutations/n5.json` pending; octad tree stubs present; `tower_level` filters supervisor digits — tested in unit tests only.

### P7 — Integration tests

- All planned modules have dedicated test files; compose + mutations + multistream + tool_pass covered.

## Issues found & disposition

| ID | Severity | Issue | Action |
|----|----------|-------|--------|
| R1 | **Medium** | `multistream_compose_demo.py` used abstract `TranslateHub()` | **Fixed** in this review |
| R2 | Low | Sample crystal `schema_version` 1.0.0 vs code `SCHEMA_VERSION` 2.1.0 | Re-run `crystallize` when promoting bundle |
| R3 | Low | repo-kernel morphonic routes not smoke-tested | Start `docker compose -f docker-compose.repo-kernel.yml up -d` and curl status |
| R4 | Info | urllib3/chardet RequestsDependencyWarning in tests | Environment pin; non-blocking |

## Recommended follow-ups

1. Re-crystallize `identity_review` after next ingest/refine to manifest 2.1.0 + optional `morph_signatures.jsonl`.
2. Run `identity_review/scripts/morphonic_ingest_identity_review.py` on a bounded corpus and record stream counts in checkpoint.
3. CI: add `pytest tests/transform/ tests/primitives/` to default pipeline if not already present.
4. With repo-kernel up: verify `/api/morphonic/template-stats?db=...` against host path.

## Sign-off

**Automated tests:** pass (115 + focused 18).  
**Manual smoke:** pass except repo-kernel HTTP and full identity_review ingest.  
**Production v1 blockers unchanged:** SUPERPERM_N5, Niemeier E6, DeepL hub, full L3 build-index.
