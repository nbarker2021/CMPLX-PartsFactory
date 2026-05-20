# Expanded rebuild playbook bodies for morphonic handoff package.
from __future__ import annotations

REBUILD_FROM_SCRATCH_EXPANDED = """# Rebuild from scratch (expanded)

Use this playbook with the full handoff package (`00`–`13`). Each step lists **failure modes** and **recovery**.

## 1. Environment and toolchain

```powershell
git clone <CMPLX-PartsFactory>
cd CMPLX-PartsFactory
pip install -e ".[dev]"
$env:PYTHONPATH = "src"
```

**Failure modes:** Python < 3.10 → syntax errors on union types. Missing `numpy` → transformer import fails.

**Recovery:** `python --version`; reinstall with `pip install -e ".[dev]"`.

## 2. Read architecture before coding

1. `01_DOCTRINE_AND_STATUS/DESIGN_VS_REALITY.md`
2. `02_ARCHITECTURE/DATA_MODEL.md`
3. `02_ARCHITECTURE/diagrams/architecture_layers.mmd`
4. `11_SOURCE_CORPUS/code/CODE_READING_ORDER.md`

**Failure mode:** Treating this as a weight-trained LLM → wrong dependencies and fake training loops.

## 3. Schema bootstrap

Apply DDL from `04_DATA_AND_SCHEMA/ddl/token_index_schema.sql` **or** let ingest create tables via `TokenIndexStore`.

Tables: `token_bonds`, `build_runs`, `address_meaning`, `translation_links`, `token_geometry`, `morph_signatures`.

**Failure modes:** Missing `stream` column on old DB → multistream ingest fails. Wrong UNIQUE on bonds → duplicate insert errors.

**Recovery:** Drop test DB and recreate; never drop production without backup.

## 4. Rule libraries

```powershell
Copy-Item -Recurse export/morphonic-rebuild-handoff-2026-05-19/04_DATA_AND_SCHEMA/rule_libs data/rule_libs
python -m cmplx.transform lib-validate --lib data/rule_libs
```

**Failure mode:** Empty `data/rule_libs` → crystallize packs no rules.

## 5. SUPERPERM spine (supervisor only)

Copy `04_DATA_AND_SCHEMA/superpermutations/` → `data/superpermutations/`. Verify `n4.json` and `coverage_check()` in tests.

**Failure mode:** Using superpermutation digits **inside** ribbon content — breaks shell arity law.

## 6. Template index (optional bootstrap)

```powershell
python -m cmplx.transform build-index --levels 1,2 --db data/token_index.sqlite
```

For identity_review operational path, prefer ingest over full Cartesian L1–L3 product.

**Failure mode:** Building full alphabet index on laptop → hours + GB SQLite.

## 7. Multistream ingest

```powershell
python identity_review/scripts/morphonic_ingest_identity_review.py `
  --root <corpus> --db data/token_index_identity_review.sqlite `
  --streams en,native --max-files 100 `
  --stats-export data/ingest_identity_review_stats.json
```

See `05_METHODS/METHOD_INGEST.md` and `02_ARCHITECTURE/INGEST_TRACE_WALKTHROUGH.md`.

**Failure modes:** `CMPLX_TRANSLATE_HUB=noop` (default) — no DeepL sidecars. Admit latency on huge files — use `--max-files`. Stream mismatch — links not joined on `translation_key`.

**Recovery:** Inspect `04_DATA_AND_SCHEMA/stats/STREAM_BREAKDOWN.md` patterns; reduce corpus; run bounded tool pass.

## 8. Bounded tool pass

```powershell
python scripts/_phase1_tool_pass.py 40
```

**Failure mode:** Running unbounded pass on 120k+ keys → multi-hour run.

**Recovery:** Increase N in phases; check `morph_signatures` growth in stats JSON.

## 9. Index refinement

```powershell
python -m cmplx.transform refine --db data/token_index_identity_review.sqlite `
  --target-coverage 0.25 --limit 500 --allow-partial
```

**Failure modes:** Coverage stuck below target — template frame gaps. `--allow-partial` required for MVP indexes.

## 10. Crystallize bundle

```powershell
python -m cmplx.transform crystallize --name identity_review `
  --db data/token_index_identity_review.sqlite --lib data/rule_libs `
  --out crystals/identity_review.crystal
```

Expect `manifest.json` → `schema_version: "2.1.0"`. Read `04_DATA_AND_SCHEMA/crystal/OPERATIONAL_MANIFEST_ANNOTATED.json`.

**Failure modes:** Crystal sqlite out of sync with live DB — reload from stale bundle. Missing sidecars — pack step skipped jsonl export.

## 11. Production forward pass

```powershell
python -m cmplx.transform forward --ribbon "<admitted_8char>" `
  --production --crystal crystals/identity_review.crystal
```

Uses `ProductionTransformerConfig`: 8 layers, `shell_bind`, ports on init. **Do not** use `--no-ports` with production preset.

**Failure modes:** `ShellViolation` — ribbon not admitted. `speedlight_hit=False` on first call only — second identical call should hit cache (see tests).

See `02_ARCHITECTURE/FORWARD_TRACE_WALKTHROUGH.md`.

## 12. Compose pipeline (supervisor + shell)

```powershell
python -m cmplx.transform compose --help
```

IndexSupervisor walks SUPERPERM_N4; mutations via `index_mutations`; `MorphonShell.complete` gates output.

**Failure mode:** Skipping `shell.complete` → downstream forward receives incomplete state.

## 13. Platform adapters (partial)

HF admit-mask stub: `tests/transform/test_hf_adapter.py`. PyTorch wrapper: `test_torch_smoke.py`.

**Failure mode:** Expecting full `PreTrainedModel` export — not shipped (GAP_AND_TODO).

## 14. Verification gate

```powershell
python -m pytest tests/transform/ tests/primitives/ -q
python scripts/morphonic_e2e_smoke.py --quick
```

Paste output to `12_TEST_SPEC/PYTEST_LAST_RUN.txt` for regression compare.

## 15. Optional full SQLite tier

If host DB > upload limit, use `12_OPTIONAL_BUNDLE/` chunked sqlite + manifest. See `10_BINARIES_MANIFEST/OPTIONAL_FULL_ARTIFACTS.json`.

**Failure mode:** Uploading 94MB sqlite to web AI — rejected; use samples + DDL instead.

## 16. External AI handoff

Upload **standard tier** (see `HANDOFF_COVER.md`): playbook + architecture + `08_RAG_AND_GRAPH` manifest + samples. Point retrieval at `TAG_INDEX.json`.

See `00_REBUILD_PLAYBOOK/ACCEPTANCE_EVIDENCE.md` for exact JSON keys.
"""

TROUBLESHOOTING = """# Troubleshooting — morphonic rebuild

## Import / bootstrap

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No provider registered for diagnostic` | `ensure_bootstrapped()` not called | Construct transformer or call `bridge.ensure_bootstrapped()` |
| `runtime.cmplx_bootstrap` ImportError | PYTHONPATH missing `src` | `$env:PYTHONPATH="src"` |
| MorphonController singleton bleed | Prior test didn't reset | `bridge.reset_bootstrap_state()` in tests |

## Shell / admit

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ShellViolation` on forward | Ribbon segment >8 arity or illegal quad | Use admitted 8-char window from index |
| `admit` rejects valid-looking token | Wrong stream/language filter | Check `token_bonds` row for stream |
| Empty ribbon slices | Content has no bondable windows | Ingest more corpus; check case_mode |

## Index / ingest

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `UNIQUE constraint failed` on bonds | Re-ingest same concat+stream | Use fresh DB or skip duplicates |
| Low link count vs bonds | Tool pass not run | `_phase1_tool_pass.py N` |
| `translation_key` orphan rows | Stream column mismatch | Verify EN-first policy in ingest |

## Forward / ports

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| NSL gate always blocks | phi budget exceeded | Check layer `nsl_budget` in config |
| No SpeedLight hit on repeat | Cache key includes config digest | Same ribbon + same config |
| TarPit derive empty | Rule lib gap | `lib-validate` and warmstart |

## Crystal

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `schema_version` not 2.1.0 | Old crystal | Re-crystallize from current DB |
| Sidecar line count mismatch | Partial copy in handoff | Use host paths in OPTIONAL manifest |
| manifest digest mismatch | Edited files after pack | Re-run crystallize |

## CI / tests

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| 1 failure in multistream | Fixture path | Run from repo root |
| HF adapter skip | Optional torch | `pip install torch` for full matrix |

## Docker / repo-kernel (optional)

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `:8786` connection refused | repo-kernel down | `docker compose -f docker-compose.repo-kernel.yml up -d` |
| GitNexus empty | Graph not rebuilt | Use bridge read-only routes only |
"""

ACCEPTANCE_EVIDENCE = """# Acceptance evidence — exact commands and keys

Run from `CMPLX-PartsFactory` with `PYTHONPATH=src`.

## A. Pytest transform + primitives

```powershell
python -m pytest tests/transform/ tests/primitives/ -q 2>&1 | Tee-Object 12_TEST_SPEC/PYTEST_LAST_RUN.txt
```

**Expect:** exit code `0`; summary line contains `passed` and no `failed`.

## B. E2E smoke

```powershell
python scripts/morphonic_e2e_smoke.py --quick
```

**Expect:** exit code `0`; stdout mentions forward and/or crystal load without traceback.

## C. Crystal info

```powershell
python -m cmplx.transform crystal-info --bundle crystals/identity_review.crystal
```

**Expect JSON keys (stdout or structured):**

- `schema_version` → `"2.1.0"`
- `crystal_id` → 12-char hex (e.g. `bc00ac8ee26c`)
- `bond_count` → order of `10^4`
- `link_count` → order of `10^5`

## D. Production forward

```powershell
python -m cmplx.transform forward --ribbon "12341234" --production --crystal crystals/identity_review.crystal
```

**Expect keys in result dict:**

- `layer_traces` → list length **8** (production N-ladder)
- `shell_bound` → `true` when shell_bind enabled
- `speedlight_hit` → `false` first call, `true` on immediate repeat (same process)

## E. Lib validate

```powershell
python -m cmplx.transform lib-validate --lib data/rule_libs
```

**Expect:** exit `0`; no `ERROR` lines.

## F. Ingest stats export (after ingest)

File: `data/ingest_identity_review_stats.json`

**Expect keys:**

- `files_seen`, `bonds_stored`, `links_stored`
- `streams` → object with per-stream counts

## G. Handoff package self-check

```powershell
python scripts/build_morphonic_handoff_package.py
```

**Expect:** printed JSON with `files` > 400, `mb` between 5 and 25 (standard tier without optional sqlite chunks).

## H. RAG manifest

File: `08_RAG_AND_GRAPH/rag_manifest.jsonl`

**Expect:** ≥250 lines; each line valid JSON with `chunk_id`, `file`, `tags`.

File: `08_RAG_AND_GRAPH/TAG_INDEX.json`

**Expect:** keys include `morphonic`, `handoff`, `module-dive`, `source-corpus`.
"""
