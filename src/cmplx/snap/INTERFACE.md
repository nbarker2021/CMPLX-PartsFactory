# snap — Interface

The semantic-decomposition layer. SNAP labels items along multiple
dimensions, evaluates them through polarity-aware lenses, and runs
the **3→6→9 selection protocol** (Gate369) that crystallizes a
candidate set into a `EnneadPackage`. The whole pipeline emits an
append-only `SNAPLedger` for provenance.

## Surface

### Labels (dimensional)

- `SNAPRole` — enum of process roles: INPUT, OUTPUT, TRANSFORM,
  VALIDATE, PERSIST, TRANSMIT, RECEIVE, ORCHESTRATE.
- `SNAPLabel` — dataclass with five dimensions (`structural`,
  `semantic`, `quality`, `risk`, `domain`) plus a `custom` map.
  Methods: `all_labels`, `has(label)`, `to_dict()`.
- `LabelRule` — a named, prioritized predicate + dimension + label
  set. The unit of registration in `SNAPLabeler`.

### Labeler

- `SNAPLabeler` — exhaustive rule-based labeler. Builtin rules cover
  structural (class/function/dict/list/...), domain (e8, leech,
  morphon, governance, geometric, conservation, ...), quality
  (documented, typed), and risk (exec/eval usage, subprocess usage).
- `label(item, key, context) -> SNAPLabel`
- `label_batch(items, keys) -> list[SNAPLabel]`
- `query_by_label(label) -> list[SNAPLabel]`
- `add_rule(LabelRule) -> None`

### Lenses (polarity-aware evaluation)

- `BaseLens.evaluate(state) -> "pass" | "refine"` — checks
  `mirror_pass`, `polarity_conflict`, `containment_c` against
  thresholds.
- `BaseLens.score_reward(before, after) -> float` — utility delta
  with edbsu_growth penalty.
- `LegalityLens` — fails on `violates_policy=True`.
- `NoveltyLens` — adds 0.2 × novelty bonus.
- `SymmetryLens` — adds 0.15 × symmetry_score bonus.
- `LensBank` — name → lens registry; `best_lens(state)` picks by
  context.

### Gate 3→6→9

- `Body`, `Predicate`, `HexadInvariant`, `EnneadPackage`,
  `SNAPRecord` — the data types the gates operate on.
- `Gate369Engine`:
  - `triad(bodies, predicates, state) -> SNAPRecord` — top-3
    lens-scored bodies.
  - `hexad(records) -> list[HexadInvariant]` — pairwise polarity
    invariants.
  - `ennead(records, lens_name) -> EnneadPackage` — 9-body containment
    package with reversibility check.
  - `process(bodies, predicates, state)` — full 3→6→9 sequence
    returning a structured trace.

### Ledger (provenance)

- `SNAPTransaction` — one ledger entry: `tx_id, op, payload,
  prev_hash, hash, timestamp`.
- `SNAPLedger.append(op, payload) -> SNAPTransaction` — chains the
  new entry's hash onto the previous one.
- `SNAPLedger.verify() -> bool` — walks the chain and checks all
  hashes hold.

### Provider

- `SNAPEngine` — the port provider. Bundles a `SNAPLabeler`, a
  `LensBank`, a `Gate369Engine`, and a `SNAPLedger`. Registers on the
  `snap` port of `MorphonController`.

## What's NOT in this layer

- The recursive 8-angle Stratifier (planned next; needs an LLM or
  static rule cascade for the angles).
- SNAPDNA / RAG encoding — separate `cmplx.snap.dna` planned.
- SNAPSuperperm (the chirp/wave bridge) — belongs in the carrier
  layer once SNAP-driven shape rendering lands.
