# Morphonic Operational v1 — Phase 1 checkpoint

**Date:** 2026-05-19  
**Scope:** identity_review bounded multistream ingest → tool pass → refine → crystallize 2.1.0 → production forward  
**DB:** `data/token_index_identity_review.sqlite`  
**Crystal:** `crystals/identity_review.crystal/`  
**Mirror:** intended `identity_review/checkpoints/2026-05-19-008-morphonic-operational-v1.md` (workspace write blocked)

## Commands

```powershell
cd D:\PartsFactory\CMPLX-PartsFactory
$env:PYTHONPATH = "src"
$env:CMPLX_TRANSLATE_HUB = "noop"

python D:\PartsFactory\identity_review\scripts\morphonic_ingest_identity_review.py `
  --root D:\PartsFactory\identity_review `
  --db data/token_index_identity_review.sqlite `
  --streams en,native --max-files 100 `
  --stats-export data/ingest_identity_review_stats.json

python scripts/_phase1_tool_pass.py 40

python -m cmplx.transform template-stats --db data/token_index_identity_review.sqlite > data/template_stats_before.json
python -m cmplx.transform refine --db data/token_index_identity_review.sqlite --target-coverage 0.25 --limit 500 --allow-partial
python -m cmplx.transform template-stats --db data/token_index_identity_review.sqlite > data/template_stats_after.json

python -m cmplx.transform crystallize --name identity_review `
  --db data/token_index_identity_review.sqlite --lib data/rule_libs `
  --out crystals/identity_review.crystal

python -m cmplx.transform forward --ribbon '"""(saaa' --production `
  --crystal crystals/identity_review.crystal
```

**Fix applied:** `src/cmplx/transform/ingest.py` — `_iter_files` streams `rglob` with early `max_files` stop (avoids full-tree materialization).

## Ingest / link metrics

| Metric | Value |
|--------|------:|
| translation_links | 123,147 |
| — en | 81,226 |
| — native | 41,921 |
| dual-stream translation_keys | 1,277 |
| token_bonds | 37,271 (en 32,046 / native 5,225) |
| token_geometry | 37,271 |
| morph_signatures | 1,639 |

Tool pass: 40 dual-stream keys, 20,360 receipts, ~665 s.

## Refine / template-stats

| | aggregate slot coverage | forced_pct (lower_any sweep) |
|--|--:|--:|
| before | 2.66 | 68.5% |
| after | 2.66 | 68.5% |

Refine: target 0.25 already met; zero mutation rounds.

## Crystal manifest

- `schema_version`: **2.1.0**
- `crystal_id`: **bc00ac8ee26c**
- `streams[]`: en, native
- `translation_link_count`: **123,147**

## Production forward

Admitted ribbon `"""(saaa` → 8 layer traces, `lane: transformative`, `digital_root: 7`.

## Production hardening 2026-05-19

Phases 0–6 (transformer hardening plan): tool registry, substrate_epoch cache bust, production contract tests, dual-DB runbook, tool-pass CLI, port contracts, superperm/N-ladder invariants, HF on-demand lane, CI smoke.

| Gate | Command / artifact |
|------|-------------------|
| Dual DB policy | `docs/MORPHONIC_PRODUCTION_RUNBOOK.md` — identity_review + crystal vs template `token_index.sqlite` |
| Host env pair | `MORPHONIC_TOKEN_INDEX_DB` + `MORPHONIC_CRYSTAL_BUNDLE` set together |
| Repo-kernel defaults | `morphonic_bridge.py` → repo-relative `data/token_index_identity_review.sqlite` when env unset |
| E2E fixture + schema | `python scripts/morphonic_e2e_smoke.py --quick` |
| E2E production gate | `python scripts/morphonic_e2e_smoke.py --quick --production-db` (when DB/crystal present) |
| HF lane default off | `CMPLX_HF_LANE=off`; `on_demand` wakes stub only |
| HF tests | `pytest tests/transform/test_hf_on_demand.py -q` |
| CI | `.github/workflows/morphonic-pytest.yml` — pytest + `--quick` smoke |

**Re-crystallize gate:** after any ingest, tool-pass, or refine on `token_index_identity_review.sqlite`, run `crystallize --name identity_review` before production forward or repo-kernel crystal reads.

## Superpermutation + NHyper + train window (2026-05-19)

| Item | State |
|------|--------|
| Ingested n | 4–8 validated JSON in `data/superpermutations/` (n≥6 `provenance_class: record`) |
| Scheduler | `IndexSupervisor.active_n` + `tower_level` → `nhyper_active_n` (level k → n=k+4) |
| Validation | `python scripts/validate_superpermutations.py --require 4,5` (CI gate) |
| Train window CLI | `python -m cmplx.transform train-window --crystal ...` |
| NHyper body | Minimal API `src/cmplx/transform/nhyper/`; full `NHyperTower.py` still pending review |

Re-crystallize `identity_review.crystal` after ingest so manifest carries `active_n`, `sp_length`, `sp_checksum`.

**Blockers / deferred:** full HF `PreTrainedModel` training; template DB `build-index` L3 wave on CI runners (local ops); repo-kernel HTTP smoke requires Docker up.
