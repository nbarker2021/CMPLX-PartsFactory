# CMPLX Deep Bookkeeping — Turn 1 Complete Synthesis
**Date:** 2026-05-12
**Agent:** CMPLX-PartsFactory canonicalization engine
**Scope:** PartsFactory + OC build inventory, Manny partial survey, generation catalog, historical builds, GitNexus aggregation

---

## Executive Summary

You do not have 6 million files of authored code. You have:
- **~15,000 real files** in PartsFactory (after removing 21,265 noise files)
- **~1M pipeline-generated files** in Manny `output/` (46 GB of archive-staging dumps)
- **13,634 generation attempts** in Manny `archive-staging/` — each a UUID-named snapshot
- **4,791 code evidence reports** from GitNexus, **1,985 indexed**
- **41 historical builds**, only 2 are git repos, **CMPLX-TMN1 is 271 GB**

The actual authored codebase is **much smaller than it appears**. The noise is mechanical duplication from pipeline outputs.

---

## PartsFactory + OC Build

| Metric | Value |
|--------|-------|
| Total files inventoried | 55,140 |
| Total bytes | 8.9 GB |
| Noise (archive-staging, UUID dirs, pycache) | 21,265 files (38.6%) |
| Real files | 33,523 (60.8%) |
| Real files (unique by basename+size) | 22,767 |
| Zip archives | 190 |
| Orphan zips (no extracted dir) | 178 |
| Largest orphan zip | 1.6 GB |

**First canonicalization completed:** `e8_lattice.py`
- 212 total variants → 15 real variants → 1 canonical file (315 lines)
- 197 archive-staging copies excluded
- Lineage recorded in `data/yard_inventory.sqlite`

---

## Manny Unification 2 — Surveyed Folders

| Folder | Files | Size | Verdict |
|--------|-------|------|---------|
| `output/` | 1,010,256 | 46.0 GB | Pipeline dump. 354K Python files, 8K zips |
| `agent ecosystem/` | 15,866 | 0.83 GB | 3rd party tools (GitNexus, oh-my-claudecode) |
| `Manny Unification 2 Implementation/` | 242 | 0.38 GB | Prior dedup evidence (312 MB dedupe JSON) |
| `Working Prototyping/` | 211 | 0.03 GB | Active workspace |
| `artifacts/` | 3 | 7 KB | Trivial |
| `historical builds/` | 41 dirs | ~400+ GB | See detailed survey below |
| `datasets from previous review/` | UNKNOWN | UNKNOWN | Needs chunked scan |

---

## Historical Builds Survey (C)

**41 top-level directories** in `D:\Manny Unification 2\historical builds`

### Git Repos (only 2 of 41)

| Repo | Worktree Size | .git Size | Commits | Branches | Notes |
|------|--------------|-----------|---------|----------|-------|
| **CMPLX-TMN1** | **271.5 GB** | 4.3 MB | 7 | 5 | MASSIVE. Almost no git history. Likely a snapshot/export, not developed in-repo |
| **CMPLX-TMN2** | 29.9 GB | 7.7 MB | 96 | 8 | More legitimate history. Still enormous |

### Non-Git Directories (extracted archives, staging, drive downloads)

| Directory | Size | Type |
|-----------|------|------|
| CMPLX-Monorepo | **88.6 GB** | Extracted archive (no .git) |
| Builds | 5.2 GB | Build output directory |
| mannyunification_staging | 5.2 GB | Staging directory (28 subdirs, 71 files) |
| CQE fully expressed-20260422... | 1.0 GB | Extracted archive |
| MannyAI | 938 MB | AI-related files |
| CMPLX Retool-Main | 153 MB | Retooling workspace |
| Family Builds-legacy | 144 MB | Legacy family builds |
| CMPLXUNI-main (1) | 35.9 MB | Extracted CMPLXUNI |
| CMPLX-Monorepo-main (1) | 27.8 MB | Extracted monorepo |
| CQE Website Build | 26.9 MB | Website build output |
| Claude Build-20260422... | 23.0 MB | Claude-generated build |
| CMPLX-TMN3 | 2.2 MB | Small directory |
| Aletheia2 | 1.9 MB | Aletheia v2 |
| CMPLX-main (1) | 1.0 MB | Extracted CMPLX main |
| CMPLX-1T-master (1) | 0.8 MB | Extracted CMPLX-1T |
| CMPLXMCP-main (1) | 0.5 MB | Extracted CMPLXMCP |
| ...and 22 more | various | Drive downloads, small packages |

**Key Finding:** Only 2 of 41 "historical builds" are actual git repositories. The rest are **extracted archives, staging directories, and drive downloads**. CMPLX-TMN1 at 271 GB with only 7 commits is almost certainly a bulk export/snapshot, not a living repo.

**Next Pass for Historical Builds:**
- Determine which of the non-git directories are extracted from zips that exist elsewhere
- Check if CMPLX-TMN1 and CMPLX-TMN2 have remote origins or are local-only
- Compare CMPLX-Monorepo (88 GB, no git) against the git-tracked CMPLX-Monorepo in other locations

---

## GitNexus Report Aggregation (D)

**1,985 reports indexed** from `output/reports/code-reports/`

### Coverage by System

| System | Reports | Languages |
|--------|---------|-----------|
| cmplx-tmn1 | 1,000 | C, Python |
| cqe | 524 | C, Python, Batch |
| aletheia | 426 | Python, C |
| cmplx-tmn2 | 35 | Python, C |

### Coverage by Language

| Language | Reports |
|----------|---------|
| C | 1,144 |
| Python | 477 |
| Batch | 330 |
| JavaScript | 34 |

### Critical Finding: ALL Reports are Status `evidence`

**0 of 1,985 reports have been promoted to `implement`.** The GitNexus catalog was built but never activated. Every file is still marked as "evidence" waiting for promotion.

### Shared Capabilities Across Systems

| Capability | Systems | Interpretation |
|------------|---------|----------------|
| `__init__` | aletheia, cmplx-tmn2, cqe | Package initialization (boilerplate) |
| `main` | aletheia, cmplx-tmn2, cmplx-tmn1 | Entry points |
| `setup` | cqe, aletheia, cmplx-tmn1 | Build/install configuration |
| `app` | cmplx-tmn2, aletheia | Application layer |
| `cli` | cmplx-tmn1, aletheia | Command-line interfaces |
| `inverse` | aletheia, cmplx-tmn2 | Mathematical operations |
| `receipts` | aletheia, cmplx-tmn2 | Token economy / audit trail |

### CQE Python Capabilities (sample)

- **CQE_GVS_MONOLITH** — Generative Video System (67.7 KB)
- **CQE_TESTING_HARNESS_COMPLETE** — Validation pipeline (13.6 KB)
- **STAGING_COMBINED** — Morphonic Staging read-only composite (17.3 KB)
- **cqe_governance** — Governance layer (3.3 KB)
- **cqe_math** — Mathematical core (3.9 KB)

### Aletheia Python Capabilities (sample)

- **cqe_modules/cqe_system** — CQE Core System (33.4 KB)
- **numba_typed/dictobject** — Compiler-side dictionary (40.0 KB)
- **scipy_signal/savitzky_golay** — Signal processing (13.1 KB)
- **cuda_core/postproc** — CUDA post-processing (9.2 KB)
- **simulator_cudadrv/error** — CUDA error handling

---

## Generation Catalog (100 samples from 13,634)

### Project Type Distribution

| Type | Freq | Description |
|------|------|-------------|
| lattice_system | 11% | `lattice_ai/core/` — geometric computing, semantic hash, shell governance |
| agrm | 9% | Governance/hierarchy, golden-angle sweep, beam-search builder |
| e8_tools | 2% | Version merger, unification scripts, import rewriters |
| snapos | 2% | Agent operating system (agent_center, agent_mgmt, atomic) |
| docker_build | 2% | Containerized builds |
| ml_model | 2% | AllenNLP/PyTorch artifacts (weights.th, config.json) |
| cqe | 1% | Complete Universal Computational Framework |
| morphonic | 1% | Controllers (geo_ops, speedlight, mmdb_ingest, viewer24_probe) |
| speedlight | 1% | Fast inference/service layer |
| mmdb | 1% | Memory database |
| snap_configs | 1% | JSON5 configs (SnapScratchBoot, AGRM_SessionOrigin) |
| tsp_benchmark | 22% | Test data (a280.tsp, rl1323.tsp, etc.) |
| unknown | 48% | Small files, configs, single artifacts |

### Key READMEs Harvested

- **Version Merger Kit (v14 ↔ v20, E8-first)** — `merge_versions.py`, `unify_e8.py`
- **CQE Ultimate System v1.0.0 (Oct 2025)** — 172 files, 22 MB
- **Lattice System Base v9** — Trainable Tier-2 semantic hash
- **agrm2** — Cleaned modular rebuild with golden-angle sweep
- **SNAPLAT Reimagined v18** — Agentic Centers (E2E lifecycle)
- **Integration Surface Pack v1 (Feb 2026)** — Self-contained CQE integration surface
- **CMPLX EXPORT PACKAGE** — All frozen elements tagged FINAL/PARTIAL/STUB

---

## Cross-Space Duplication Patterns

1. **EMCP_TQF_FullBundle_v1.zip** — PartsFactory and Manny output/
2. **dimensional-forms__e8-archives__part00X.zip** — series in both spaces
3. **archive-staging/<UUID>** — identical pattern in both spaces
4. **shell_lifecycle.py** — 1,458 copies, all inside archive-staging
5. **e8_lattice.py** — 212 copies, 197 in archive-staging

**Conclusion:** The same pipeline(s) have been dumping into both spaces for months.

---

## What Needs Future Passes

| Item | Reason | Effort |
|------|--------|--------|
| `datasets from previous review/` | Massive files, timeouts | Chunked shell audit |
| `output/` zip audit | 8,065 zips, find orphans | Batch processing |
| `output/` postgres-recovery-inspect | 1GB+ database files | Determine if needed |
| CMPLX-TMN1 (271 GB) | Is it a snapshot? Has a git origin? | Git remote check |
| CMPLX-Monorepo (88 GB, no git) | Compare against other monorepo copies | Hash comparison |
| GitNexus promotion | 1,985 reports all `evidence` | None promoted yet |
| `CMPLXUNI/` full inventory | 2,814 Python files, largest codebase | Systematic canonicalization |
| `CMPLXMCP/` full inventory | 100 Python files | Quick win |

---

## Artifacts Produced This Turn

| Artifact | Path | Purpose |
|----------|------|---------|
| Yard inventory DB | `data/yard_inventory.sqlite` | 55K files classified |
| Classification engine | `scripts/classify_yard.py` | noise/template/blob/real |
| Zip auditor | `scripts/zip_audit.py` | orphan zip detection |
| Manny lab notebook | `scripts/manny_lab.py` | folder analyzer |
| Generation catalog | `scripts/catalog_generations.py` | archive-staging sampler |
| Historical builds survey | `scripts/survey_historical_builds.py` | git-aware scanner |
| Historical builds DB | `data/historical_builds.sqlite` | 41 entries |
| GitNexus aggregator | `scripts/aggregate_gitnexus.py` | report parser/indexer |
| GitNexus index DB | `data/gitnexus_index.sqlite` | 1,985 reports |
| Canonical e8_lattice | `src/canon/tools/e8_lattice.py` | first canonical file |
| Lab notebook | `docs/MANNY_LAB_NOTEBOOK_2026-05-12.md` | living log |

---

*Turn 1 Complete — Deep Bookkeeping Phase*
