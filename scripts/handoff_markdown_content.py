# Generated markdown bodies for morphonic rebuild handoff package.
from __future__ import annotations

GAP_AND_TODO = """# Gap and future work register

| Item | Status | Notes |
|------|--------|-------|
| Template index refresh (~155k rows) | todo | Phase 4 follow-on on `data/token_index.sqlite` |
| Full HF PreTrainedModel | todo | Admit-mask stub only |
| SUPERPERM_N5 validated string | blocked | `n5.json` status pending — do not invent |
| NHyperTower promotion | blocked | See RESEARCH_ESCROW.md |
| DeepL TranslateHub | todo | `CMPLX_TRANSLATE_HUB=noop` default |
| Niemeier E6 full embedding | todo | `e6_lift.py` witness-only |
| Repo-kernel HTTP smoke | partial | Compose env ready; curl not recorded |
| SpeedLight second-hit (scenario E) | partial | Not in operational checkpoint |
| N-ladder deep geometry per stage | partial | Config tags; not separate solvers |
| Learned transformer weights | out of scope | Substrate-first by design |
| Ingest per-chunk admit latency | partial | `_iter_files` fixed; admit path still slow |
| Crystal vs live DB drift | partial | Re-crystallize after ingest/tool pass |
| Math/notation streams at scale | partial | Encoders exist; not full corpus pass |
"""

RESEARCH_ESCROW = """# Research escrow (do not promote without review)

- **NHyperTower.py** — combinatorial hyperpermutation tower; see `docs/NHYPER_TOWER_ESCROW.md` in repo.
- **SUPERPERM_N5** — `data/superpermutations/n5.json` has `"status": "pending"`; octad layout documented, string not shipped.
- **CQE hyperperm_update** — operator-order oracle in `engine/cqe/`; not the same as NHyperTower.

Promote only after explicit human approval and validation checkpoints.
"""

EXTERNAL_AI_INSTRUCTIONS = """# Instructions for web-based AIs (ChatGPT, Claude, Gemini, etc.)

## Prompt template

```
You are rebuilding the CMPLX Morphonic Slot 48 stack from the attached handoff package only.
This is NOT a weight-trained LLM. It is substrate-first: token index + Morphon shell + port orchestration.

Read order:
1. README_START_HERE.md
2. 01_DOCTRINE_AND_STATUS/DESIGN_VS_REALITY.md
3. 00_REBUILD_PLAYBOOK/REBUILD_FROM_SCRATCH.md
4. 02_ARCHITECTURE/diagrams/architecture_layers.mmd
5. 09_FUTURE_WORK/GAP_AND_TODO.md

Use 08_RAG_AND_GRAPH/rag_manifest.jsonl to retrieve chunks by tag.
Full SQLite databases are NOT in the upload bundle; use 10_BINARIES_MANIFEST/OPTIONAL_FULL_ARTIFACTS.json for host paths.
```

## Upload priority (under 50 MB)

1. README_START_HERE.md
2. DESIGN_VS_REALITY.md + NORTH_STAR.md
3. architecture_layers.mmd + forward_dataflow.mmd
4. GAP_AND_TODO.md
5. REBUILD_FROM_SCRATCH.md
6. PACKAGE_INDEX.json (machine index)

## What you cannot infer without the package

- Exact pytest list — use 07_VERIFICATION/TEST_MATRIX.md
- DDL — use 04_DATA_AND_SCHEMA/ddl/
- Row samples — use 04_DATA_AND_SCHEMA/samples/*.jsonl
"""

REBUILD_FROM_SCRATCH = """# Rebuild from scratch

## 1. Environment

```powershell
git clone <CMPLX-PartsFactory>
cd CMPLX-PartsFactory
pip install -e ".[dev]"
$env:PYTHONPATH = "src"
```

Python 3.10+ required. Optional Docker for repo-kernel (:8786).

## 2. Schema (Table 1 + links + meaning)

Apply DDL from `04_DATA_AND_SCHEMA/ddl/` or run ingest which creates tables via `TokenIndexStore`.

Tables: `token_bonds`, `build_runs`, `address_meaning`, `translation_links`, `token_geometry`, `morph_signatures`.

## 3. Rule libraries

Copy `04_DATA_AND_SCHEMA/rule_libs/` to `data/rule_libs/`. Validate:

```powershell
python -m cmplx.transform lib-validate --lib data/rule_libs
```

## 4. Build template index (optional bootstrap)

```powershell
python -m cmplx.transform build-index --levels 1,2 --db data/token_index.sqlite
```

For identity_review path use ingest instead of full alphabet Cartesian product.

## 5. Multistream ingest

```powershell
python identity_review/scripts/morphonic_ingest_identity_review.py `
  --root <corpus> --db data/token_index_identity_review.sqlite `
  --streams en,native --max-files 100 `
  --stats-export data/ingest_identity_review_stats.json
```

Bounded tool pass:

```powershell
python scripts/_phase1_tool_pass.py 40
```

## 6. Refine + crystallize

```powershell
python -m cmplx.transform refine --db data/token_index_identity_review.sqlite `
  --target-coverage 0.25 --limit 500 --allow-partial
python -m cmplx.transform crystallize --name identity_review `
  --db data/token_index_identity_review.sqlite --lib data/rule_libs `
  --out crystals/identity_review.crystal
```

Expect manifest `schema_version: 2.1.0`.

## 7. Production forward

```powershell
python -m cmplx.transform forward --ribbon "<admitted_8char>" `
  --production --crystal crystals/identity_review.crystal
```

Do not use `--no-ports` with production preset.

## 8. Verify

```powershell
python -m pytest tests/transform/ tests/primitives/ -q
python scripts/morphonic_e2e_smoke.py --quick
```

See VERIFICATION_CHECKLIST.md.
"""

VERIFICATION_CHECKLIST = """# Verification checklist

- [ ] `pip install -e ".[dev]"` succeeds
- [ ] `PYTHONPATH=src` set
- [ ] `pytest tests/transform/ tests/primitives/` — expect 122+ passed
- [ ] `python scripts/morphonic_e2e_smoke.py --quick` exit 0
- [ ] `python -m cmplx.transform crystal-info --bundle crystals/identity_review.crystal` shows schema 2.1.0
- [ ] Production forward: 8 layer traces
- [ ] `admit --token invalid!!` rejected
- [ ] Optional: repo-kernel `GET /api/morphonic/status` with MORPHONIC_* env set
"""

NORTH_STAR = """# North star (condensed)

**Substrate-first geometric transformer:** derive once → receipt → cache → calibrate.

- **Slot 48** (`cmplx.transform`) orchestrates MORSR attention, TarPit FFN, NSL gates, SpeedLight cache, eversion head.
- **Morphon shell** admits only legal quad bonds (≤8 arity, involution rings, language filters).
- **Living index** in SQLite (`token_bonds`) + **address_meaning** + **translation_links** (multistream).
- **Crystal 2.1.0** ships reloadable workstate (index + libs + jsonl sidecars + digest).
- **SUPERPERM_N4** schedules `IndexSupervisor`; never enters ribbon content.
- **Not in scope:** billion-token weight training; full HF PreTrainedModel.

See GLOSSARY.md and DESIGN_VS_REALITY.md.
"""

GLOSSARY = """# Glossary

| Term | Meaning |
|------|---------|
| Quad bond | 8-char window `1234|4321` — F4 cell on 1D ribbon |
| Ribbon | Input string; split by shell into ≤8 arity segments |
| SP / superpermutation | Schedule cursor for IndexSupervisor (n=4 spine in `n4.json`) |
| Stream | `en`, `native`, `math`, `notation` — column on `token_bonds` |
| translation_key | Links EN and sidecar rows (e.g. `doc:chunk:0`) |
| Crystal | Directory bundle with manifest 2.1.0 + sqlite copy + rule libs |
| Tool pass | TarPit→NSL→SNAP→NLAECNF→cache per translation_key |
| N-ladder | Eight layer policies (N=2..8); production preset enables |
| shell_bind | Post-head `shell.admit` on ribbon_out |
| Admit mask | HF stub export: bool per token for external trainers |
"""

DESIGN_VS_REALITY = """# Design vs reality (May 2026)

## Intended design

Substrate-first morphonic transformer: law (shell + NSL) + memory (index + SpeedLight) + provenance (receipts + crystal). Eight N-ladder policies. Multistream ingest EN-first. Compose via IndexSupervisor + shell.complete.

## What is built (~65–80% of substrate MVP)

| Area | Status |
|------|--------|
| token_bonds + template frame | Done |
| MorphonShell admit/complete | Done |
| CorpusIngester + multistream | Done |
| Tool pass + geometry + morph_signatures | Done (bounded) |
| Index mutations + refine CLI | Done |
| Crystal 2.1.0 pack/load | Done |
| ProductionTransformerConfig (8 layers, shell_bind) | Done |
| HF admit-mask stub | Partial |
| n5 / NHyperTower | Blocked / escrow |

## Operational v1 evidence (identity_review)

| Metric | Value |
|--------|------:|
| token_bonds | 37,271 |
| translation_links | 123,147 |
| morph_signatures | 1,639+ |
| crystal_id | bc00ac8ee26c |
| schema_version | 2.1.0 |

## What this is NOT

- Not a GPT-style learned attention model (no trainable weight matrices in `GeometricTransformerModule`).
- Not a complete HF training integration.
- Not full template-index (155k) refresh yet.

## Realistic next work

See `09_FUTURE_WORK/GAP_AND_TODO.md`.
"""

PHASE_MATRIX = """# Phase completion matrix

| Phase | Name | Status |
|-------|------|--------|
| 0 | Foundation lock | done |
| 1 | Morphon Shell API | done |
| 2 | Rule library system | done |
| 3 | address_meaning | done |
| 4 | Corpus ingest | done |
| 5 | Shell bind transformer | done |
| 6 | Index refinement | done |
| 7 | Crystal pack/load | done |
| 8 | Platform adapters | partial |
| 9 | E2E validation | partial |
| P1–P7 | Production hardening | done |
| Op v1 | identity_review operational | done |
| Handoff | This package | done |
"""

PORTS_OVERVIEW = """# CMPLX ports consumed by transform

| Port | Package | Role in forward |
|------|---------|-----------------|
| diagnostic | cmplx.morsr | MorphonicAttention pulse/traverse/scan |
| symbolic | cmplx.symbolic.tarpit | MorphonicFFN derive |
| conservation | cmplx.nsl | Layer NSL gates |
| cache | cmplx.speedlight | Forward + residual cache |
| receipt | cmplx.receipt | Audit trail |
| snap | cmplx.snap | Tool pass labels |
| atlas | cmplx.atlas | Tokenizer / morphon |
| geometry | cmplx.geometry | Coordinates witness |
| memory | cmplx.memory.mmdb | Optional MMDB |
| engine | cmplx.engine | Eversion head |
| constraints | cmplx.constraints.aletheia | NSL-related constraints |

Bootstrap: `runtime.cmplx_bootstrap.register_all()` via `transform.bridge.ensure_bootstrapped()`.
"""

ALL_MARKDOWN: dict[str, str] = {
    "09_FUTURE_WORK/GAP_AND_TODO.md": GAP_AND_TODO,
    "09_FUTURE_WORK/RESEARCH_ESCROW.md": RESEARCH_ESCROW,
    "00_REBUILD_PLAYBOOK/EXTERNAL_AI_INSTRUCTIONS.md": EXTERNAL_AI_INSTRUCTIONS,
    "00_REBUILD_PLAYBOOK/REBUILD_FROM_SCRATCH.md": REBUILD_FROM_SCRATCH,
    "00_REBUILD_PLAYBOOK/VERIFICATION_CHECKLIST.md": VERIFICATION_CHECKLIST,
    "01_DOCTRINE_AND_STATUS/NORTH_STAR.md": NORTH_STAR,
    "01_DOCTRINE_AND_STATUS/GLOSSARY.md": GLOSSARY,
    "01_DOCTRINE_AND_STATUS/DESIGN_VS_REALITY.md": DESIGN_VS_REALITY,
    "01_DOCTRINE_AND_STATUS/PHASE_MATRIX.md": PHASE_MATRIX,
    "06_PORTS_ECOSYSTEM/PORTS_OVERVIEW.md": PORTS_OVERVIEW,
}
