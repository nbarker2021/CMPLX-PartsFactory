# Morphonic Substrate → Transformer Platform → Crystal

> **New work (2026-05-19):** Open gaps in §3.2 below are superseded by the unified roadmap. Start with [`MORPHONIC_UNIFIED_DOCTRINE.md`](MORPHONIC_UNIFIED_DOCTRINE.md) and [`HP_NHYPER_TOWER_INTEGRATION.md`](HP_NHYPER_TOWER_INTEGRATION.md) for SP/octad, metrics, multistream, and compose phases.

**Status:** Living plan (2026-05-19)  
**North star:** A **plug-in geometric transformer** backed by a **growable local rule library** and **living token index**, where **every emitted token is shell-valid**, and the **entire state ships as one Crystal**.

**Related:** Slot 48 (`docs/ATTRACTOR_FRAME.md`), `src/cmplx/transform/`, `src/cmplx/crystal/`, `data/token_index.sqlite` (template frame ~155k rows).

> **Superseded sections:** Open gaps in **§3.2** below are tracked in [`docs/MORPHONIC_UNIFIED_DOCTRINE.md`](MORPHONIC_UNIFIED_DOCTRINE.md) and the Morphonic Unified Roadmap (Phases 0–9). Prefer the unified doctrine for N-ladder, multistream, HP tower, and compose pipeline status.

---

## 1. Problem statement

Standard transformers learn validity from corpus scale. This stack inverts that:

| Traditional | Morphonic substrate |
|-------------|---------------------|
| Train weights on billions of tokens | **Derive once** → receipt → cache → calibrate |
| Vocab is static file | **Living index** + local libs you extend by re-running ingest |
| Any string can be a token ID | **Morphon shell** admits only legal bond/case/language combinations |
| Checkpoint = weights only | **Crystal** = index + libs + labels + substrate + receipts + cache keys |

The transformer platform (PyTorch / HF / custom) sees familiar layers; CMPLX supplies **law** (shell + NSL), **memory** (index + SpeedLight + MMDB), and **provenance** (receipts + crystal).

---

## 2. Target architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TRANSFORMER PLATFORMS (PyTorch, HF, custom trainers)                   │
│  GeometricTransformerModule │ optional: export admit-mask / embeddings  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────┐
│  SLOT 48: GeometricTransformer                                          │
│  tokenize → embed → L×(MORSR attn + NSL gate + TarPit FFN + SL residual)│
│  → eversion head → ribbon_out                                           │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ reads / writes
┌───────────────────────────────▼─────────────────────────────────────────┐
│  MORPHON SHELL (constraint engine — NOT optional at emit time)          │
│  • max 8 arity per bonded segment (| splits longer ribbons)             │
│  • involution rings L1/L2/L3 + case modes                               │
│  • language filters (pluggable libs)                                    │
│  • NSL gate on every state change                                       │
│  • TarPit walls + MirrorOperator on violation                           │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ TABLE 1       │     │ TABLE 2         │     │ RULE LIBS       │
│ token_bonds   │     │ address_meaning │     │ token/*.yaml    │
│ (substrate)   │     │ snap→semantics  │     │ language/*.yaml │
│ warm-start    │     │ dynamic SNAP    │     │ user extensions │
└───────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │ CRYSTAL BUNDLE        │
                    │ .crystal/ or sqlite   │
                    │ committed + reloadable│
                    └───────────────────────┘
```

---

## 3. What exists today (inventory)

### 3.1 Built and verified

| Component | Location | Evidence |
|-----------|----------|----------|
| Geometric transformer stack | `src/cmplx/transform/` | Tests in `tests/transform/` |
| PyTorch wrapper | `transform/torch/module.py` | `test_torch_smoke.py` |
| Token index builder | `transform/token_index/builder.py` | Warm-start ~0.016% cold |
| SQLite substrate | `token_index/store.py` | `token_bonds`, `build_runs` |
| Template frame analysis | `token_index/template_frame.py` | CLI `template-stats` |
| Quad bonds + involution + case | `bonds.py`, `case.py` | Unit tests |
| Language filter interface | `language.py` | English bigrams default |
| ALENA / NSL / MORSR / TarPit / SNAP / Receipt / SpeedLight | respective packages | `scripts/see_tools_in_action.py` |
| Walls + Mirror + NLAECNF | `symbolic/tarpit`, `primitives` | `scripts/see_walls_and_mirror.py` |
| Crystal types + registry | `src/cmplx/crystal/` | In-process CRUD |
| SNAP crystallize hook | `snap/provider.py` | containment_c > 0.7 |

### 3.2 Gaps (must build)

| Gap | Why it blocks the north star |
|-----|------------------------------|
| **`address_meaning` table** | Substrate has geometry; no persistent snap→label/doc map |
| **Corpus ingest pipeline** | Cannot "add your lib by running index once" on user docs |
| **MorphonShell emit API** | No single `admit(token) → bool` / `complete(partial) → candidates` |
| **Dynamic SNAP label minting** | Labeler is rule-only; empty domain on new vocabulary |
| **Crystal bundle format** | Registry is in-memory; no pack/unpack of index+libs+ledger |
| **Transformer ↔ shell binding** | Forward pass does not require shell-valid ribbon_out |
| **Platform export hooks** | No HF `PreTrainedModel` adapter or admit-mask export |
| **Long-token `|` slicer** | TarPit/mirror slicing not wired into tokenizer path |
| **Supervisory convolution/abstraction/involution** | Described conceptually; not on index products |

---

## 4. Data model

### 4.1 Table 1 — `token_bonds` (exists)

Substrate rows: concat, quads, level, case, language, morphon_id, snap_key, lane, digital_root, e8_signature, cache_key, warmstart class.

**Role:** geometric address + bond legality for enumerated (or ingested) tokens.

### 4.2 Table 2 — `address_meaning` (new)

```sql
CREATE TABLE address_meaning (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snap_key        TEXT NOT NULL,
    lane            TEXT NOT NULL,
    digital_root    INTEGER NOT NULL,
    label           TEXT NOT NULL,          -- SNAP label or user term
    label_source    TEXT NOT NULL,          -- snap | user | ingest | inferred
    source_doc      TEXT,                   -- path or doc id
    source_span     TEXT,                   -- optional offset / chunk id
    ennead_id       TEXT,                   -- optional Gate369 package ref
    receipt_hash    TEXT,
    created_at      REAL NOT NULL,
    UNIQUE(snap_key, lane, digital_root, label, source_doc)
);
CREATE INDEX idx_meaning_snap ON address_meaning(snap_key);
CREATE INDEX idx_meaning_label ON address_meaning(label);
```

**Role:** answer "what does this address mean in *my* work?" — grows on every ingest.

### 4.3 Rule libraries (new, filesystem)

```
data/rule_libs/
  token/
    default_bonds.yaml      # alphabet, max_level, case_modes
    custom_involution.yaml  # user overrides
  language/
    english_bigrams.yaml
    identity_review_terms.yaml   # user adds, re-run ingest
  shell/
    morphon_shell.yaml      # max_arity: 8, bond_separator: "|", gate_mode: govern
```

**Contract:** Running `cmplx.transform ingest --lib data/rule_libs/language/my_terms.yaml` merges rules and re-indexes only **new** addresses (warm-start preserves prior work).

### 4.4 Crystal bundle (new)

Single artifact directory or sqlite sidecar:

```
my_workstate.crystal/
  manifest.json           # crystal_id, e8_root, created_at, schema_version
  token_index.sqlite      # copy or ATTACH of token_bonds + build_runs
  address_meaning.sqlite  # or merged into token_index.sqlite
  rule_libs/              # frozen copy of libs used at commit time
  snap_ledger.jsonl       # SNAP transactions
  receipt_chain.jsonl     # Receipt chain head + tail
  speedlight_index.json    # optional: hot cache keys
  template_stats.json       # slot coverage snapshot at commit
  substrate_digest.sha256   # integrity over all files
```

**States:** `growing` → `committed` → `active` (matches `Crystal.state`).

---

## 5. Core APIs (to implement)

### 5.1 `MorphonShell`

```python
class MorphonShell:
  def __init__(self, config: ShellConfig, store: TokenIndexStore, meaning: AddressMeaningStore): ...

  def slice_ribbon(self, text: str) -> list[str]: ...       # ≤8 chars; | breaks; mirror on wall
  def admit(self, token: str, *, lang: str = "any") -> AdmitResult: ...
  def complete(self, partial: str, *, max_candidates: int = 64) -> list[str]: ...
  def propagate(self, template: PartialWindow) -> AdmitSet: ...  # TemplateFrame-backed
```

**Invariant:** `complete()` and transformer `ribbon_out` never return strings where `admit()` is false.

### 5.2 `CorpusIngester`

```python
class CorpusIngester:
  def ingest_path(self, root: Path, *, lib_paths: list[Path], labeler: SNAPLabeler): ...
  # For each chunk: slice → canonicalize → upsert token_bonds (if new)
  #                  → mint SNAP labels (dynamic) → upsert address_meaning
  #                  → warmstart.publish_entry → receipt.mint
```

### 5.3 `CrystalPackager`

```python
class CrystalPackager:
  def pack(self, crystal_name: str, *, db: Path, libs: Path, out: Path) -> Crystal: ...
  def load(self, bundle: Path) -> LoadedCrystal: ...  # rehydrate stores + register ports
  def commit(self, crystal_id: str) -> dict: ...       # seal digest, state=committed
```

### 5.4 Platform adapters

| Adapter | Purpose |
|---------|---------|
| `GeometricTransformerModule` | Already exists — ensure `forward` accepts `shell=` |
| `HuggingFaceGeometricAdapter` | `PreTrainedModel`-compatible wrapper; config in `config.json` |
| `AdmitMaskExporter` | Export boolean mask over vocab slice for external trainers |
| `CrystalCheckpoint` | `from_pretrained("./my.crystal/")` loads bundle not `.safetensors` |

---

## 6. Phased delivery plan

### Phase 0 — Foundation lock (DONE)

**Deliverables:** Morphonic transformer, token index, template frame, tool demos.

**Acceptance:** `pytest tests/transform/`, `python -m cmplx.transform template-stats`, demo scripts exit 0.

---

### Phase 1 — Morphon Shell API (2–3 days)

| Task | Detail |
|------|--------|
| 1.1 | `ShellConfig` dataclass in `transform/shell.py` |
| 1.2 | Wire `slice_ribbon` using TarPit `WallEmitter` + `MirrorOperator` loop (max 3 reflections) |
| 1.3 | `admit()` = bonds parse + language filter + optional NSL check on forged morphon |
| 1.4 | `complete()` = TemplateFrame.admit_set + forced cells for single-char holes |
| 1.5 | Unit tests: reject >8 arity, reject illegal bigram, accept template completions |

**Acceptance:** `MorphonShell.complete("th")` returns only substrate-admitted strings when template coverage ≥ threshold.

**Depends on:** existing `template_frame.py`, `bonds.py`, `language.py`.

---

### Phase 2 — Rule library system (2 days)

| Task | Detail |
|------|--------|
| 2.1 | YAML schema for token + language rules |
| 2.2 | `RuleLibraryLoader.merge()` — additive, versioned |
| 2.3 | CLI `cmplx.transform lib-list`, `lib-validate` |
| 2.4 | Builder accepts `--lib path` to extend language filters without code change |

**Acceptance:** Dropping `identity_review_terms.yaml` and re-running build changes admit set for doc-specific tokens.

---

### Phase 3 — `address_meaning` + dynamic SNAP (3–4 days)

| Task | Detail |
|------|--------|
| 3.1 | Migration: add `address_meaning` table to index DB (or sibling sqlite) |
| 3.2 | `AddressMeaningStore` CRUD + query by snap_key / label / doc |
| 3.3 | Extend `SNAPLabeler` with `register_dynamic_label(snap_key, label)` |
| 3.4 | On ingest: if no rule match, mint label from doc heading / filename / user map |
| 3.5 | CLI `cmplx.transform meaning-query --snap-key ...` |

**Acceptance:** Ingest `identity_review/*.md` → query "morphonic transformer" returns rows with snap_key + source_doc.

---

### Phase 4 — Corpus ingest pipeline (3–4 days)

| Task | Detail |
|------|--------|
| 4.1 | `CorpusIngester` — walk txt/md/py; chunk ≤512 chars |
| 4.2 | Tokenize chunks through `MorphonicTokenizer` + `NLAECNFChain` |
| 4.3 | Upsert new bonds; skip duplicates via warm-start |
| 4.4 | Stats: new_rows, new_meanings, new_labels, cache_hits |
| 4.5 | CLI `cmplx.transform ingest --root PATH --lib ... --db ...` |

**Acceptance:** Second ingest of same corpus is mostly warm-start; third-party lib only adds delta.

**Evidence hook:** Append row to `identity_review/UNIFICATION_PREP_PLAN.md` findings queue.

---

### Phase 5 — Bind shell to transformer (2 days)

| Task | Detail |
|------|--------|
| 5.1 | `TransformerConfig.shell: ShellConfig | None` |
| 5.2 | Post-head: validate `ribbon_out` segments via `shell.admit` |
| 5.3 | On reject: trigger mirror loop or return `ShellViolation` in trace |
| 5.4 | `forward(..., mode="complete")` optional path for constrained generation |

**Acceptance:** Forward on illegal ribbon records violation in `layer_traces`; legal ribbon passes.

---

### Phase 6 — Supervisory index refinement (optional, 3–5 days)

User-described: convolution, abstraction, involution on index products.

| Task | Detail |
|------|--------|
| 6.1 | `IndexSupervisor` reads template coverage; targets 25% → 45% milestones |
| 6.2 | `convolve()` — combine bond neighborhoods → updated warmstart hints |
| 6.3 | `abstract()` — collapse snap_keys to class representatives (Table 2 boost) |
| 6.4 | `involute()` — apply ring swaps to seed missing bond levels |
| 6.5 | CLI `cmplx.transform refine --target-coverage 0.45` |

**Acceptance:** `template-stats` forced-cell ratio increases without full alphabet Cartesian product.

---

### Phase 7 — Crystal pack / load (3–4 days)

| Task | Detail |
|------|--------|
| 7.1 | `CrystalPackager.pack()` — copy DBs, libs, ledgers, write manifest + digest |
| 7.2 | `CrystalPackager.load()` — register ports, attach stores to shell |
| 7.3 | Bridge `SNAPEngine.crystallize()` → `CrystalRegistry.create()` + nodes for each meaning row |
| 7.4 | CLI `cmplx.transform crystallize --name my_workstate --db ... --out my.crystal/` |
| 7.5 | Optional MMDB mirror via `memory` port |

**Acceptance:** Load crystal → `GeometricTransformer(shell=loaded.shell)` runs forward using only bundled substrate.

---

### Phase 8 — Platform adapters (2–3 days)

| Task | Detail |
|------|--------|
| 8.1 | Document HF integration pattern in `transform/INTERFACE.md` |
| 8.2 | `HuggingFaceGeometricAdapter` minimal stub |
| 8.3 | `examples/crystal_load_forward.py` |
| 8.4 | Export `AdmitMask` numpy array for external vocab alignment |

**Acceptance:** `python examples/crystal_load_forward.py` loads bundle and prints `ribbon_out`.

---

### Phase 9 — End-to-end validation (2 days)

| Scenario | Steps |
|----------|-------|
| **A. Palindrome template** | Existing index → template-stats → complete partials |
| **B. User corpus** | ingest `identity_review/` → meaning query → crystallize |
| **C. Custom lib** | Add yaml terms → re-ingest → new labels appear |
| **D. Transformer** | Load crystal → forward doc question → shell-valid output |
| **E. Cache proof** | Second forward hits SpeedLight; receipt chain links |

**Acceptance:** Written report in `identity_review/checkpoints/YYYY-MM-DD-NNN-morphonic-crystal-e2e.md`.

---

## 7. CLI surface (complete target)

```bash
# Libraries
python -m cmplx.transform lib-validate --lib data/rule_libs/
python -m cmplx.transform lib-list --lib data/rule_libs/

# Index (exists + extensions)
python -m cmplx.transform build-index --levels 1,2,3 --lib ...
python -m cmplx.transform index-stats --db data/token_index.sqlite
python -m cmplx.transform template-stats --db data/token_index.sqlite

# Ingest + meaning
python -m cmplx.transform ingest --root identity_review --lib ... --db ...
python -m cmplx.transform meaning-query --label "morphonic" --db ...

# Shell
python -m cmplx.transform admit --token "morphon|forge"
python -m cmplx.transform complete --partial "th___on"

# Refine (phase 6)
python -m cmplx.transform refine --target-coverage 0.45

# Crystal
python -m cmplx.transform crystallize --name workstate --db ... --out crystals/workstate.crystal/
python -m cmplx.transform crystal-info --bundle crystals/workstate.crystal/

# Transformer (exists)
python -m cmplx.transform forward --crystal crystals/workstate.crystal/ --ribbon "..."
```

---

## 8. Port registration map

At crystal load time, `cmplx_bootstrap.register_all()` plus:

| Port | Provider | Crystal load attaches |
|------|----------|------------------------|
| `diagnostic` | MORSRProvider | policy from manifest |
| `conservation` | NSLProvider | gate_mode from shell yaml |
| `symbolic` | TarPitSymbolicProvider | — |
| `cache` | SpeedLightProvider | optional warm cache file |
| `memory` | MMDBMemoryProvider | path inside bundle |
| `receipt` | ReceiptProvider | chain replay head |
| `snap` | SNAPEngine | ledger jsonl |
| `crystal` | CrystalRegistry | manifest nodes |

---

## 9. Decision log (resolve before Phase 5)

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| D1 | Merge Table 2 into index sqlite? | single DB vs twin | **Single DB** — simpler crystal bundle |
| D2 | Dynamic label authority | SNAP only vs user override | **User override wins** on conflict |
| D3 | Generation strategy | enumerate vs constraint propagate | **Propagate first**; enumerate only for small holes |
| D4 | Crystal storage default | directory vs zip vs sqlite | **Directory** `.crystal/` for inspectability |
| D5 | HF scope | full PreTrained vs thin wrapper | **Thin wrapper** first; full HF in Phase 8+ |
| D6 | Ingest chunk size | 256 / 512 / 1024 | **512** chars default; shell slices to ≤8 |

---

## 10. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Index explosion on full alphabet L3 | Dependency-ordered build + warm-start (proven); ingest-only for user vocab |
| 0% hit on non-palindromic text | Expected until ingest; template is seed not prison |
| SNAP rule gaps | Dynamic labels + address_meaning |
| Mirror loop non-convergence | Cap reflections; fall back to `|` slice at midpoint |
| Crystal drift | `substrate_digest.sha256` verified on load |
| Platform trainers ignore shell | Export admit-mask; document that foreign vocabs must map through shell |

---

## 11. Success metrics

| Metric | Target |
|--------|--------|
| Warm-start hit rate on re-ingest | ≥ 95% |
| `admit()` false positive rate | 0% (strict) |
| Template forced-cell @ partial palindrome | maintain ~100% on covered slots |
| Meaning rows per 100 doc chunks | monotonic on re-ingest |
| Crystal load → forward latency | < 2× cold forward (cache warms) |
| Receipt chain integrity | 100% verify on `crystal-info` |

---

## 12. Suggested execution order

```
Phase 0 ✓ → Phase 1 (shell) → Phase 2 (libs) → Phase 3 (meaning)
    → Phase 4 (ingest) → Phase 7 (crystal) → Phase 5 (bind transformer)
    → Phase 8 (platforms) → Phase 6 (supervisor, optional depth) → Phase 9 (e2e)
```

**Minimum viable product (MVP):** Phases **1 + 3 + 4 + 7** — shell, ingest your docs, crystallize, load.

**Full product:** through Phase 9 + platform adapters.

---

## 13. First concrete slice (recommended start)

1. Add `address_meaning` schema + store (**Phase 3.1–3.2**).  
2. Implement `CorpusIngester` on `identity_review/` only (**Phase 4**).  
3. Implement `MorphonShell.admit/complete` (**Phase 1**).  
4. `crystallize` → `crystals/identity_review.crystal/` (**Phase 7**).  
5. One demo: load crystal, ask "what is the morphonic transformer workstate?" via meaning query + optional forward.

This proves the loop you described without waiting for full HF integration.

---

## 14. Findings queue hook

When a phase completes, append to `identity_review/UNIFICATION_PREP_PLAN.md`:

```markdown
| 2026-MM-DD | Morphonic crystal phase N done | See docs/MORPHONIC_SUBSTRATE_CRYSTAL_PLAN.md |
```

---

*End of plan.*
