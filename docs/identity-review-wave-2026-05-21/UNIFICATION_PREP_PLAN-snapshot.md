# Unification Prep Plan (Living)

**Goal:** Eventually merge by **role**, not folder name — into `work/<target>/unified/` per `WORK_PROTOCOL.md`.  
**Now:** Intel, staging, exposure — **not** mass file moves.

**Update rule:** Every session that discovers new evidence → add/adjust items below + optional checkpoint.

---

## Phase A — Exposure (current)

| ID | Task | Source layer | Status | Notes |
|----|------|--------------|--------|-------|
| A1 | Maintain `EVIDENCE_LAYER_MAP.md` | All | **active** | This file's companion |
| A2 | Session bootstrap script + hook | Docker + SQLite | **done** | `scripts/session_bootstrap.py`, `.cursor/hooks/` |
| A3 | Delete/rename partial `kb.sqlite` | kb scaffold | **blocked** | File busy; renamed when idle → `kb.sqlite.partial-abandoned` |
| A4 | Wire agents to query atomic in place | atomic_index | **done** | `cqe_query.py`; no kb full ingest |
| A5 | GitNexus unification-hints → plan items | :8786 API | **ongoing** | Top repos: CMPLXDevKit, CMPLXUNI, cqe-organized |
| A6 | Cursor env wiring | `.cursor/*` | **done** | mcp.json, hooks.json, 3 skills, evidence-intel agent, 2 rules, plugin.json |
| A7 | B6/B7 probe pass | evidence + GitNexus | **partial** | B6 complete in `probe-b6-b7.json`; B7 graph was null at first probe — re-verify each session (`graph-summary` after kernel restart) |

---

## Phase B — Registers (intel completeness)

| ID | Task | Source | Status | Notes |
|----|------|--------|--------|-------|
| B1 | Lineage register | User narrative | **done** | `LINEAGE_REGISTER.md` |
| B2 | Unification attempts register | Workspace scan | **done** | |
| B3 | cqe_organized reading guide | file_registry + FILE_INDEX | **done** | MONOLITHS missing on disk in PF mirror; GitNexus has full `cqe-organized` index on Manny path |
| B4 | Genesis / superpermutation layer | three_space + grep | **ongoing** | `superperm.py`, `n4.json`, doctrine docs landed; NHyperTower body still PENDING_REVIEW |
| B5 | Map HARDENED vs PENDING canonicals to roles | `HARDENED_INDEX.md`, `PENDING_REVIEW_INDEX.md` | **open** | 8 hardened, ~888 pending — tie to promotion manifest |
| B6 | evidence_dedupe `cqe` cluster review | 65,590 files | **ongoing** | Probed: `system_of_origin='cqe'`; top clusters `__init__.py`, `sqlite_store.py`, `hash_system.py` — see probe-b6-b7.md |
| B7 | Manny monolith bodies | GitNexus `cqe-organized` | **ongoing** | Graph: 4497 files, 1928 communities, 300 processes; top communities TESTS, Python, Other — use graph-summary before disk walk |

---

## Phase C — Unification manifest (build before merge)

Thin SQLite or JSONL — **links only**, no statement copy:

| Field | From |
|-------|------|
| `role` | lineage + cqe reading guide |
| `canonical_target` | HARDENED_INDEX / user decision |
| `witness_paths[]` | atomic_index.files + file_registry |
| `atomic_file_id` | atomic_index |
| `gitnexus_repo` | graph-summary |
| `replica_count` | inventory_query |
| `promote` / `defer` / `conflict` | orphan_decisions, validation |

| ID | Task | Status |
|----|------|--------|
| C1 | Schema for `unification_manifest` | **not started** |
| C2 | Seed from HARDENED_INDEX (8 rows) | **not started** |
| C3 | Seed from PENDING_REVIEW (888 rows) | **not started** |
| C4 | Join file_registry monoliths → atomic paths | **not started** |

---

## Phase D — Execute unification (future)

Only after B + C sufficient for a **family slice** (e.g. CQE spine symbols).

| ID | Task | Status |
|----|------|--------|
| D1 | Pick first merge slice (suggest: CQE hardened canonicals) | blocked on C |
| D2 | `work/cqe-unify/manifest.md` decisions | not started |
| D3 | Copy to `work/.../unified/` per WORK_PROTOCOL | not started |
| D4 | Run validation_report / atomic match on promoted set | not started |

---

## Findings queue (append here)
| 2026-05-21 | **B3 integration profile** — `integration_profile.py`; `CMPLX_INTEGRATION_PROFILE=1`; host mesh + receipt bridges; 5 remote ports on smoke; `GIT_PUSH_REVIEW-2026-05-21.md` | Commit CMPLX + identity_review scripts |
| 2026-05-21 | **B1+B5+B4** — Phase H refresh script; `AGRMController` → `_composed_DO_NOT_IMPORT.py`; `hash_lanes` port (17 bootstrap); `promotions-bootstrap.jsonl`; gate green | B3 mesh defaults; B6 agent TSP shards |
| 2026-05-21 | **Timidity review (post-W2)** — integration bold; timidity now = stale Phase H, escrow narrative, mesh/receipt defaults off, dual SNAP HTTP; see `reports/timidity-review-post-w2-2026-05-21.md` | B1–B7 promotion register + hash-lanes |
| 2026-05-21 | **W2+W3** — `run_w2_compose_profile_smoke.py` (HTTP+mints); AGRM staging materialized; `tsp_heuristic` + `staging_loader`; routing solve live | Hash-lanes; full agent TSP from escrow shards |
| 2026-05-21 | **W1c Docker live** — repo-kernel fixed (`morphonic_bridge` in image+mount); receipt compose YAML fix; smoke green (receipt/snap/speedlight/tarpit/mdhg/mmdb/kernel); `w1c-docker-smoke` + `w1c-bootstrap-kernel-sync` reports; Phase H script timeout bumped | Re-run phase_h when kernel idle; optional snap receipt mint e2e |
| 2026-05-21 | **W1 crystal + batch gates** — `crystal` port via `CrystalRegistry` (16 bootstrap ports); `run_crystal_done_gate.py`, `run_bootstrap_w1_done_gates.py`; gates green for nsl/morsr/geometry/transport/atlas/crystal; test fixes for `identity_kind` in constraints/embed/engine | W1c repo-kernel manifest when :8786 up |
| 2026-05-21 | **W0 bootstrap source of truth** — `bootstrap_registry.py` (15 ports); `emit_bootstrap_catalog_parts.py` → 15 catalog parts + `catalog/bootstrap_manifest.json`; smoke tests green; **routing** bug fixed (factory was in `_with_remote_factories` but not `_PORTS_WITH_REMOTE`); audit `reports/w0-bootstrap-startup-audit-2026-05-21.md` | W1: crystal port; repo-kernel ingest manifest |
| 2026-05-21 | **MDHG slot-12 deep gather** — 150 JSONL witnesses (249 pre-cap); spine 11 / remote_service 101; 48 addressing pytest; aggregate + baseline audit | Tighten atomic SQL for spine-first; :8825 remote stub; identity_review/data DBs missing → repo/data fallback |
| 2026-05-20 | **Atom/Atomic terminology map** — homonyms (Morphon vs TarPit Atom vs fabric vs atomic_index) | `registers/atom-terminology-map.md` |
| 2026-05-20 | **Morphon gather pass** — 111 JSONL rows, dual-grammar register, done gate green, consumers wave | Staging escrow (0 local morphonic py found) |
| 2026-05-20 | **Morphon slots 10–11 receipt bridge** — BIRTH/CROSSING/ASSIGN/GATE, 37 morphon pytest, gather 97 rows | Staging escrow review, done gate |
| 2026-05-20 | **TarPit slot-18 handoff** — `run_chemistry`, `mdhg_bridge`, monolith gather (40 rows), `TODO_TARPIT_SLOT18_HANDOFF.md`, 95 pytest | Morphon / Docker smoke |
| 2026-05-20 | **TarPit atom + MDHG slice** — `atoms.py`, `mdhg_tape.py`, `/atom`, `/tape/*`, 90 pytest; pushed after `7d12767` | Docker smoke `:8844` when Desktop up |
| 2026-05-20 | **TarPit aggregation merge** — `glyphic.py`, `aggregation.py`, three-form modes, crystal `mount_triad`, 79 symbolic pytest | Push + Docker smoke |
| 2026-05-20 | **TarPit slot-18 manufactured** — `fff8012`; forms evolving/glyphic/unified; :8844 HTTP; 70 pytest; witness 123 | Docker smoke; Morphon receipts |
| 2026-05-20 | **Manufactured slots committed + pushed** — `00bbb6a` on `main`; TODO: `identity_review/TODO_MANUFACTURING_NEXT.md`, next slot: `TODO_NEXT_SLOT_MORPHON_TARPIT.md` (TarPit first) | Docker smoke; TarPit manufacturing |
| 2026-05-20 | **Manufactured slots committed** — `CMPLX-PartsFactory` commit wires receipt/speedlight/snap + crystal←snap; 241 pytest | superseded by pushed row |
| 2026-05-20 | **SNAP slot-17 closure pass** — `run_snap_done_gate.py` intent_met; witness gather refreshed (150 rows); checkpoint `checkpoints/2026-05-21-004-snap-deep-pass.md`; Docker smoke pending | Docker up → `docker-compose.snap.yml`; next slot or crystal/CQE consumer escrows |
| 2026-05-20 | **Datasets doc review `handoff-batch-08`** — 50 docs offset 350; 50 OK; 41 interests; 226 followups opened; merged | Next: handoff-batch-09 (offset 400) |
| 2026-05-20 | **Datasets doc review `handoff-batch-07`** — 50 CMPLX-TMN1 session DOCX; 49 reviewed, 1 extract error (`Perplexity Session 3 100825.docx`); 46 interest flags; merged | Next: handoff-batch-08 (offset 350) |
| 2026-05-20 | **Datasets doc review `handoff-batch-06`** — 50 CQE documentation PDFs literal-reviewed; 0 errors; merged to index | Next: handoff-batch-07 (offset 300) |
| 2026-05-20 | **Datasets doc review handoff batches 01–05 merged** — 250 assigned, 228 reviewed, 22 errors; report `identity_review/reports/datasets-doc-review-handoff-250-2026-05-20.md`; interests `document reviews/handoffs/INTERESTS_SYNTHESIS.md` | Continue registered queue offset 250; filter interest noise |
| 2026-05-20 | **Datasets doc review `wave-001-manny`** — 50 documents literal-reviewed; 133 follow-up tasks open | Continue wave queue per MANIFEST.md |
| 2026-05-20 | **Datasets doc review `wave-000-root`** — 10 documents literal-reviewed; 143 follow-up tasks open | Continue wave queue per MANIFEST.md |

_New items from probes, GitNexus, or user — move to B/C when triaged._

| Date | Finding | Action |
|------|---------|--------|
| 2026-05-21 | **Triangle spine pass** — MDHG `hierarchical_address` + receipt bridges; MMDB `dr_channel` on store; triangle + routing stub tests; bootstrap `routing`; AGRM escrow triage **66** defer; gates green | Recompose AGRMController from reference shards |
| 2026-05-21 | **AGRM slot-15 prep** — gather, homonym, INTERFACE; superseded by triangle row | — |
| 2026-05-21 | **External index SQL v2** — three_space/evidence/yard `_external_file_sql_clause`; MDHG **124** rows (addressing_noise **0**); MMDB **106** (memory_noise **0**); gates green | Escrow triage remote_* rows; mesh smoke |
| 2026-05-21 | **MMDB homonym + gather v2** — superseded by external-index row | — |
| 2026-05-21 | **MDHG homonym + gather v2** — superseded by external-index row | capability matrix |
| 2026-05-21 | **MMDB witness gather (slot-13)** — initial gather; superseded by v2 row | — |
| 2026-05-21 | **MDHG homonym register** — initial register; superseded by v2 re-gather row | — |
| 2026-05-21 | **MDHG witness gather (slot-12)** — `gather_mdhg_witnesses.py`; **150** rows; baseline audit; catalog witness wired; gate green; pushed `8163ae6` forge fix | (superseded by homonym + MMDB rows) |
| 2026-05-21 | **High-leverage catalog parts (7 total)** — added `morphon-substrate`, `tarpit-symbolic`, `mdhg-addressing`, `mmdb-memory` under `catalog/parts/`; shared `catalog_done_gate.py`; gates **51+95+48+30** pytest all green; `run_high_leverage_catalog_gates.py` | Witness gather for mmdb; repo-kernel catalog ingest |
| 2026-05-21 | **Phase H slots pluggability** — 51 ATTRACTOR slots vs **7** catalog parts / 16 ports; 14+ packages instant via `register_all()`; report `slots-pluggability-analysis-2026-05-21.md`; repo-kernel offline | Start repo-kernel; remaining ATTRACTOR slots → catalog |
| 2026-05-21 | **SNAP Phase E+F** — `morphon_context` ingest labels; escrow triage 13 absorb / 53 defer; **79** snap pytest | Cherry-pick escrow skills; Docker smoke |
| 2026-05-21 | **SNAP gather + gate closure** — 403→150 witness JSONL; **72** pytest; done gate green; receipt test isolates `snap_*` mints; checkpoint `005-snap-gather-closure`; chain `TODO_SNAP_SLOT17_CHAIN.md` | Docker :8823 smoke; Phase E consumer wiring |
| 2026-05-21 | **Morphon slots 10–11 production slice** — explicit TarPit linkage (`links.py`), substrate pipeline, six `CombineMethod`s, `MorphonController.store`/`fetch`, transform ingest `inherit_link` bonds; **54** morphon + ingest pytest | Push `main`; SNAP gather refresh; staging escrow / HTTP port deferred |
| 2026-05-21 | **slot-17 SNAP deep pass** — `mint_run_snapshot`, HTTP ledger/lenses/run-snapshot, OpenAPI, homonym register, matrix JSON, **72** pytest; see `2026-05-21-004-snap-deep-pass.md` | **Closure 2026-05-20:** done gate green; checkpoint in `checkpoints/`; Docker smoke when Desktop up; homonym corpus stays in escrow register only |
| 2026-05-21 | **slot-17 SNAP manufactured** — merge `src/cmplx/snap` (`_receipt_bridge` → receipt port, `SNAPLedger` mirror); witness gather **150** rows (homonym-capped); `docker-compose.snap.yml` :8823; catalog `snap-stratification.json`; `snap-ledger` escrow resolved | (superseded by deep-pass row for verification) |
| 2026-05-21 | **slot-04 SpeedLight manufactured** — merge to `src/cmplx/speedlight` (controller→ReceiptChain, `_persistence/sidecar_ledger`, HTTP :8843); witness gather capped ≤150 rows; **76** pytest in `tests/speedlight/` (5 files); `docker-compose.speedlight.yml`; catalog `speedlight-worldline.json`; checkpoint `2026-05-21-002`; escrow row `speedlight-controller-receipt` resolved | `pytest tests/speedlight/`; receipt suite; `run_l0_done_gate.py`; Docker smoke when Desktop up (`reports/speedlight-docker-smoke-2026-05-21.md`) |
| 2026-05-21 | **Escrow wiring register** — doctrine + `escrow-wiring-register.jsonl`; receipt residue migrated from delegation-gaps; SpeedLight is next manufactured part | Use register when wiring slot-04+ ; append rows each pass |
| 2026-05-21 | **Receipt Chain completion pass (slot-01)** — witness v2 JSONL (101 rows, 4 waves), `_persistence` owns JSONL/HMAC impl, signing fix, 5 run-ledger tests, wallet `payload.wallet_op`, matrix 2026-05-21, 72 tests green; Docker smoke doc (daemon offline this session) | Run Docker smoke when Desktop up; broadcast/MMDB still deferred |
| 2026-05-20 | **Receipt Chain manufacturing (slot-01)** — Phases 0–6: baseline audit, witness JSONL (22 rows gather script), Gate B matrix/design, merge to single `ReceiptChain` spine + HTTP delegate, `docker-compose.receipt.yml` :8010, catalog `catalog/parts/receipt-chain.json`, checkpoint `2026-05-20-001-receipt-chain-production.md` | Run `pytest tests/receipt/`; compose smoke; wallet/broadcast delegation deferred |
| 2026-05-19 | **Superperm n=4–8 ingest + NHyper map + train-window CLI** — Johnston/Egan ingest → `data/superpermutations/n5–n8.json`; `superperm_n`/`IndexSupervisor.active_n`; `nhyper_active_n` + `src/cmplx/transform/nhyper/` minimal API; `validate_superpermutations.py` CI; `train-window` CLI + `data/train_windows/` reports | Re-crystallize `identity_review.crystal`; full `NHyperTower.py` promotion still PENDING_REVIEW |
| 2026-05-19 | **Morphonic escrow closure (HF train window, NHyper, superperm)** — superseded by ingest row above | done |
| 2026-05-19 | **Morphonic transformer production hardening (P0–P6)** — `docs/MORPHONIC_HARDENING_TOOL_REGISTRY.jsonl`; `substrate_epoch` in forward cache keys; `test_production_contract` (8 traces, SpeedLight second-hit, cache bust); `tool-pass` CLI; `hf_on_demand` + `TrainerHarnessSketch`; dual-DB runbook; CI `morphonic-pytest.yml` | `pytest tests/transform/` + `morphonic_e2e_smoke.py --quick`; re-crystallize after ingest/tool-pass |
| 2026-05-19 | **Morphonic Rebuild Handoff Suite** — tiered package `CMPLX-PartsFactory/export/morphonic-rebuild-handoff-2026-05-19/` (+ zip): DDL, stratified JSONL samples, stats/crystal/rule_libs/superperm, PORT DAG, 97 RAG chunks, rebuild playbook, 122-test matrix; scripts `build_morphonic_handoff_package.py`, `export_morphonic_module_dag.py`, `export_morphonic_rag_chunks.py`; checkpoint `2026-05-19-009-morphonic-rebuild-handoff-suite.md` | Upload to web AIs; optional full DB via OPTIONAL_FULL_ARTIFACTS.json |
| 2026-05-19 | **Morphonic unified roadmap Phases 0–2** — doctrine docs, `superperm`/`OctadSheet`/`IndexSupervisor`, `TokenMetrics`/`MorphSignature`, `morph-probe` CLI, `data/superpermutations/n4.json` | See `docs/MORPHONIC_UNIFIED_DOCTRINE.md`; triage B4 genesis/superpermutation → **ongoing** |
| 2026-05-19 | **Morphonic unified roadmap (Phases 0–9)** — doctrine (`MORPHONIC_UNIFIED_DOCTRINE.md`, `HP_NHYPER_TOWER_INTEGRATION.md`), `superperm`/`OctadSheet`/`IndexSupervisor`, metrics+morph-probe, multistream schema+ingest, tool_pass/e6_lift, compose_pipeline, N-ladder+shell_bind, HF stub; checkpoint `checkpoints/2026-05-19-002-morphonic-unified-e2e.md` | B4 morphonic unified; `python -m pytest tests/transform/ tests/primitives/` |
| 2026-05-19 | **Morphonic production hardening (P1–P7) test/review** — 115 pytest passed; P1–P7 integration 18 passed; fixed `multistream_compose_demo` TranslateHub; review `docs/MORPHONIC_TEST_REVIEW_2026-05-19.md`; crystal manifest still 1.0.0 until re-crystallize | `forward --production`, repo-kernel `/api/morphonic/*` when stack up |
| 2026-05-19 | **Morphonic Operational v1 Phase 1** — bounded en+native ingest (123k links, 1.3k dual-stream keys, 1.6k morph_signatures); ingest `_iter_files` fix; crystal **2.1.0** `bc00ac8ee26c`; refine at 2.66 coverage; production forward 8 traces; checkpoint `docs/MORPHONIC_OPERATIONAL_V1_CHECKPOINT.md` | Phase 2 e2e/CI/repo-kernel; template-index refresh deferred |
| 2026-05-19 | **Morphonic rebuild handoff suite** — `export/morphonic-rebuild-handoff-2026-05-19/` + zip (~1 MB, 172 files); RAG 97 chunks, DDL/samples, PORT DAG, rebuild playbook; `scripts/build_morphonic_handoff_package.py` | Upload README + DESIGN_VS_REALITY + GAP_AND_TODO to web AIs; full DBs in `10_BINARIES_MANIFEST/OPTIONAL_FULL_ARTIFACTS.json` |
| 2026-05-19 | **Morphonic crystal MVP (Phases 1–4, 7)** — `MorphonShell`, `address_meaning`, `CorpusIngester`, `CrystalPackager`; pytest 72 passed; ingest 10-file sample → `data/token_index_morphonic.sqlite`; bundle `crystals/identity_review.crystal/` | See `docs/MORPHONIC_SUBSTRATE_CRYSTAL_PLAN.md`; CLI `ingest`, `meaning-query`, `crystallize`, `lib-validate` |
| 2026-05-19 | **External toolkits wired** — Manus + `files (1)` morphon kit; `verify_toolkit_wiring.py` intent_met (11 pytest) | `integrate_external_toolkits.py`, `src/cmplx/tools/manus/`, `tools/wire.py` |
| 2026-05-19 | **L1 geometry wave** — slots 05–08 witnessed; escrow 14 rows; batch landed 14 files; `run_l1_done_gate.py` | `execute_l1_escrow_batch.py`; `niemeier_analysis.py` remains script-at-import (use `__main__` or refactor) |
| 2026-05-19 | **Viewer24 from Downloads** — `Viewer24_Controller_v2_CA_Residue.zip` → `geometry/viewer24/` | `integrate_viewer24_download.py`; run `python -m cmplx.geometry.viewer24.server` |
| 2026-05-19 | **Shared embed** — `geometry/_embed_common.py`; e8/leech `embed_escrow` re-export; batch keys `(slot_id, sha256)` | fixes duplicate-SHA skip for leech slot |
| 2026-05-19 | **Monolith distribution plan** — `unified_e8.py` + large files → `e8/canonical/*` stubs | `distribute_geometry_monoliths.py --apply`; bodies still in `unified_e8.py` |
| 2026-05-19 | **L1 wave-pull duplicate runs** — two PIDs pulled 602 attractors; Windows lock used `kill(0)` (unreliable) | Stopped PIDs 21108+24008; fixed lock via `OpenProcess`; L1 uses `--frame-only --pending-only` |
| 2026-05-19 | **Eversion tempering in manifold** | `ManifoldPipeline.process(..., eversion=True)` → `MorphonicEversionNetwork.forward`; test in `test_tools_wiring.py` |
| 2026-05-18 | GitNexus live: 17 repos; `cqe-organized` 169k nodes on Manny mount | Use graph-summary before filesystem walks |
| 2026-05-18 | atomic_index: 6,465 CQE-related files, 443k statements | Primary mechanical truth |
| 2026-05-18 | three_space: 926k files catalogued; Manny 815k | Path resolver for cross-root witnesses |
| 2026-05-18 | evidence_dedupe: 65k cqe-tagged evidence files | Phase B6 sample |
| 2026-05-18 | kb ingest duplicate abandoned | Do not rerun; query atomic |
| 2026-05-18 | repo-kernel promotion ledger: CMPLX-1T needs_slice_index, CMPLXMCP/CMPLXUNI promoted_candidate | Align with GitNexus priority scores |
| 2026-05-18 | B6: evidence_dedupe `evidence_file.system_of_origin='cqe'` — 65,590 files; clusters span cqe+tmn1+datasets-review | Promote hash/shell/sqlite_store families in manifest Phase C |
| 2026-05-18 | B7: GitNexus `cqe-organized` — 66k functions, comm_213 TESTS (1192 symbols), comm_1948 Python | Slice intake via `/api/gitnexus/slice-intake-plan` not filesystem |
| 2026-05-18 | Cursor wired: `.cursor/mcp.json`, hooks, skills, agents, `.cursor-plugin/plugin.json` | Reload Cursor; approve MCP servers |
| 2026-05-18 | Session handoff bootstrap `213718Z`: all six SQLite layers on disk; repo-kernel `ok`, 12 repos, mutation off; GitNexus priorities unchanged (DevKit > UNI > cqe-organized) | Use `reports/session-bootstrap-2026-05-18T213718Z.md` as session entry |
| 2026-05-18 | atomic CQE **quick** count (bootstrap path filter) = **6,206** vs survey constant **6,465** — different queries; treat survey/KIMI_KNOWLEDGE_SURVEY as authoritative for planning | Do not overwrite 6465 with quick count |
| 2026-05-18 | Parallel Cursor thread `263256f1` runs D: filesystem audit (`_unification_audit_*`); separate from identity_review intel in `d1e7c4d4` | Triage audit output against `three_space_catalog` before new walks |
| 2026-05-18 | OpenCode/Codex hook→skill routing (`checkpoints/021–027`, `cmplx-context-router.mjs`) | Agent procedure layer; routes read/search → memory-review + tool-discovery |
| 2026-05-18 | Attractor wave pull started; **landing pad = `CMPLX-PartsFactory/src/cmplx`** | All merges fold into frame occupants; `work/attractor-assembly/LANDING_PAD.md` + `landing-pad-index.json` |
| 2026-05-18 | **Expandable registry** — `registry/extensions.jsonl`, `discovered.jsonl`, `src/cmplx/_extensions/L00–L10/` | New attractors without frame edit; witness sharding; 5k prior scan/layer |
| 2026-05-18 | **corpus-visible** junctions + per-attractor `external/*.jsonl` | Manny/OC/Retool visible under `work/attractor-assembly/corpus-visible/roots/`; rule `partsfactory-corpus-visible.mdc` |
| 2026-05-18 | **L0 substrate witness wave complete** — 112/112 attractors indexed (**not** escrow merge) | `L00-substrate/attractors.json`, witnesses; merge **1/27** — see `reports/completion-honesty-audit-2026-05-18.md` |
| 2026-05-18 | **L0 escrow merge** — hold model up, absorb new skills, shred dupes | `attractor_escrow_merge.py` → `L00-substrate/escrow/*.jsonl`, `reports/attractor-gap-L00-actionable.md`, `ESCROW_PROTOCOL.md` |
| 2026-05-18 | **Agent relearn phase 2** — promotion tiers, frame G1–G5, orphan_decisions counts, checkpoint corpus 007–029 | `checkpoints/2026-05-18-029-agent-relearn-synthesis-phase2.md`; repo-kernel refresh blocked this session |
| 2026-05-18 | **Merge triage proof** — L0: 9,897 witnesses vs **27** escrow merges (~0.27%); GitNexus hints/worklist live after `docker restart repo-kernel` | `reports/merge-triage-agent-task-craft-2026-05-18.md`, `scripts/merge_triage_demo.py` |
| 2026-05-18 | **slot-01 receipt pilot** — evidence table for 9 escrow rows; **1/9 merged** (`receipts_bridge.py`); **8 open** + misroutes | `reports/slot-01-receipt-chain-evidence-intel-2026-05-18.md`, `escrow-completed.jsonl`, `audit_escrow_completion.py` |
| 2026-05-18 | **Completion honesty audit** — 26/27 escrow still open; plan wording corrected | `reports/completion-honesty-audit-2026-05-18.md`, `reports/escrow-completion-audit-2026-05-18.json` |
| 2026-05-18 | **slot-02 nsl evidence-intel** — 6 escrow + 5 shred verified; 0 promoted; 3 real merges + 3 defer/wrong-slot | `reports/slot-02-nsl-phi-evidence-intel-2026-05-18.md`, `escrow-deferred.jsonl` |
| 2026-05-18 | **slot-03 aletheia evidence-intel** — 6 escrow; 0 promoted; bridge + dimensional priority | `reports/slot-03-aletheia-law-chain-evidence-intel-2026-05-18.md` |
| 2026-05-18 | **slot-04 speedlight evidence-intel** — 6 escrow + 5 shred; shred verify before sidecar merge | `reports/slot-04-speedlight-worldline-evidence-intel-2026-05-18.md` |
| 2026-05-18 | **L0 batch escrow execution** — 27/27 landed; stubs for pipeline/CQE/runtime; 186 tests pass | `scripts/execute_l0_escrow_batch.py`, `tests/escrow/test_l0_batch_smoke.py` |

---

## GitNexus-driven next reads (from unification-hints)

1. `GET /api/gitnexus/graph-summary?repo=rk-cmplxdevkit&limit=10`
2. `GET /api/gitnexus/graph-summary?repo=rk-cmplxuni&limit=10`
3. `GET /api/gitnexus/graph-summary?repo=cqe-organized&limit=10`
4. `GET /api/gitnexus/repo-unification-worklist`
5. `GET /api/gitnexus/slice-candidate-matrix`

---

## Session checklist

- [x] Run `python identity_review/scripts/session_bootstrap.py` (latest: `235111Z`)
- [x] Read latest `reports/session-bootstrap-*.md`
- [x] Agent relearn pass (registers + checkpoints 007–029 synthesis) — **not** line-by-line all checkpoints
- [x] Completion honesty audit — `reports/completion-honesty-audit-2026-05-18.md`
- [ ] L0 escrow merges: **26 / 27 open** (`audit_escrow_completion.py`)
- [x] Evidence-intel: slot-02 — `reports/slot-02-nsl-phi-evidence-intel-2026-05-18.md`
- [x] Evidence-intel: slot-03 — `reports/slot-03-aletheia-law-chain-evidence-intel-2026-05-18.md`
- [x] Evidence-intel: slot-04 — `reports/slot-04-speedlight-worldline-evidence-intel-2026-05-18.md`
- [x] L0 **batch escrow merge**: **27/27** `DONE_PROMOTED` — gate: `python identity_review/scripts/run_l0_done_gate.py`
- [x] **Done confirmation:** `reports/l0-done-confirmation-2026-05-19.md` (`intent_met: true`, 186 tests)
- [ ] L0 **runtime wiring** (HTTP adapters → repo-kernel / compose) — land complete, wire not
- [x] **External toolkits** — Manus dev/review + `files (1)` → `src/cmplx/tools`, `primitives`, `engine/eversion`, `deploy/` (`integrate_external_toolkits.py`)
- [ ] L1–L10 attractor waves (geometry pull next)
- [ ] Query/GitNexus refresh each working session (kernel restart if disconnect)
- [x] Update this plan + findings queue
- [ ] Checkpoint 030+ when escrow rows complete or misroutes fixed
