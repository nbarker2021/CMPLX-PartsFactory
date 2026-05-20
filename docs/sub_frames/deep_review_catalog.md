# Sub-Frame: Deep Review — What's Still on the Table (v1)

**Status:** v1 frozen — catalog only; closing items happens via the parent frame's merge protocol.
**Parent frame:** [ATTRACTOR_FRAME.md](../ATTRACTOR_FRAME.md)
**Trigger:** user direction 2026-05-17 — "after [Wave 5] is done, lets plan a new deep review of what we are still not considering and leaving on the table in these plans and process steps we have in place."

---

## 0. Why this sub-frame exists

After Waves 0 through 5 (plus Layer-4 slots + port-trigger map), the substrate has matured fast and the merge ledger reads clean. But fast progress always leaves things half-named, half-wired, or quietly assumed. This sub-frame is a deliberate audit pass — for each category, what's been touched, what's been *imagined* but not *handled*, and what's been quietly excluded from the work surface entirely.

Items here aren't bugs or todos — they're **structural gaps** the merge protocol hasn't named yet. The act of naming them is the work this sub-frame does. Closing them is for later waves.

The catalog is grouped into six categories, each with concrete entries. Each entry has:

- **What we have** — the current state
- **What's not considered** — the structural gap
- **Why it matters** — the consequence of leaving it on the table
- **Suggested resolution path** — one of (a) future merge in parent frame, (b) new sub-frame, (c) explicit close-as-out-of-scope, (d) needs user input

---

## 1. Empty stub modules in `src/cmplx/`

### 1.1 `src/cmplx/cognition/`

- **What we have:** [src/cmplx/cognition/](../../src/cmplx/cognition/) — only `_constants.py`, `__init__.py`. Skeleton, no `INTERFACE.md`, no `BRIDGE.md`, no real implementation. Not in any port. Empty package.
- **What's not considered:** what cognition *means* in this build. The parts-catalog [CMPLXAgentEngine](../../CMPLX-1T/SHOWROOM/RESEARCH/unification-reports/AGENT-UNIFICATION-REPORT.md) is conceptually adjacent (multi-agent orchestration), and [project-manny-role](../../../../C:/Users/borke/.claude/projects/d--PartsFactory/memory/project_manny_role.md) marks Manny as the user-facing LLM channel — but neither has been wired to cognition.
- **Why it matters:** cognition is the natural home for the "thinking" layer that consumes diagnostic + symbolic + embed reports and decides what the agent *does* next. Without it, the runtime is a registered-port substrate with no behavior layer.
- **Resolution (user-confirmed 2026-05-17):** (a) future merge — explicitly **"a new way to use transformers inside this basis,"** deferred until the rest of the substrate is in proper shape and place. It is NOT out-of-scope; it is a real component awaiting the right substrate state. Tied to §4.6 (Geometric Transformer) as the implementation vehicle.

### 1.2 `src/cmplx/interrogation/`

- **What we have:** [src/cmplx/interrogation/](../../src/cmplx/interrogation/) — `_constants.py`, `_functions.py`, `__init__.py`. Stub.
- **What's not considered:** what interrogation does. The name suggests "ask questions of a morphon" — possibly a structured query interface over MMDB + receipt chain. Not in any port; no design refs in the formalization corpus we've ingested.
- **Resolution:** (c) close-as-out-of-scope unless a use case surfaces. Mark as parking-lot; revisit if the cognition layer needs it.

### 1.3 `src/cmplx/lambda/`

- **What we have:** [src/cmplx/lambda/LambdaTerm.py](../../src/cmplx/lambda/LambdaTerm.py) — Λ⊗E₈ draft only. Mentioned as Slot 22 in parent frame.
- **What's not considered:** the formalization corpus describes Λ⊗E₈ as a *full* lambda calculus with E8 geometric operations as primitives — typed AST with `Arrow`, `Prod`, `Bool`, `Nat`, `Grade` types, plus modal operators (`Box`, `Diamond`), and a `LambdaE8Evaluator` that wires beta reductions into E8 + Leech operations. The current `LambdaTerm.py` is only an AST sketch.
- **Why it matters:** parent frame Slot 22 + sub-frame F-7 are blocked on this. The port-trigger map design has it spec'd (class-A + class-D), but the implementation work is multi-week.
- **Resolution:** (a) future merge — when a user-facing reason demands it (e.g., dispatch-tree IR needing lambda-as-program semantics).

### 1.4 `src/cmplx/routing/agrm/`

- **What we have:** [AGRMController.py](../../src/cmplx/routing/agrm/AGRMController.py) — stub. Sub-frame F-6.
- **What's not considered:** the Navigator/PathBuilder/SalesmanValidator three-phase TSP machinery described in the formalizations. The port-trigger map design has it spec'd (class-A `solve` + class-C `ingest_orientation`). Daemon channel `tmn2_pulse` is reserved for it.
- **Resolution:** (a) future merge — bounded work (~300-500 LOC). Worth a focused build session.

## 2. Service-layer parallels still un-consolidated

### 2.1 `src/thinktank/` vs the proposed `thinktank` port

- **What we have:** [src/thinktank/agent.py](../../src/thinktank/agent.py) is the service-layer ThinkTank — 6-role deliberation (PLANNER/IMPLEMENTER/CRITIC/RESEARCHER/VALIDATOR/SYNTHESIST) per [THINKTANK-UNIFICATION-REPORT.md](../../CMPLX-1T/SHOWROOM/RESEARCH/unification-reports/THINKTANK-UNIFICATION-REPORT.md). Parent frame Slot 23 marks it as ◐ multi-candidate.
- **What's not considered:** elevating ThinkTank to a port. The parent-frame slot proposed a `thinktank` port; the port-trigger map doesn't add it to KNOWN_PORTS. Right now ThinkTank is consumable only by service-layer code, not by other cmplx ports.
- **Why it matters:** deliberation is a natural class-A operation for embed-consumer code. If `MorphonController.get("thinktank").deliberate(morphon)` existed, Aletheia laws could call it for ambiguous admissions. Today they can't.
- **Resolution:** (a) future merge — promote to port, with the existing service-layer impl as the in-process provider.

### 2.2 `src/governance/dna.py`, `src/governance/snapdna.py`, `src/governance/thinktank.py`

- **What we have:** [src/governance/dna.py](../../src/governance/dna.py) (DNAEncoder), [src/governance/snapdna.py](../../src/governance/snapdna.py), [src/governance/thinktank.py](../../src/governance/thinktank.py) — service-layer pieces still parallel to cmplx tree.
- **What's not considered:** whether DNA encoding is a port (it's the AGENT-UNIFICATION-REPORT's `dna_encode` reverse of `dna_decode`), and whether the governance/thinktank wrapper duplicates `src/thinktank/`.
- **Resolution:** (b) new sub-frame — "Service-layer cmplx-promotion audit." Same shape as the port-provider-facades sub-frame, but for the `src/*` modules.

### 2.3 `src/snapdna/` factory and `src/expertise/`

- **What we have:** [src/snapdna/factory.py](../../src/snapdna/factory.py), [src/expertise/](../../src/expertise/) — sap, expert lifecycle. Service-layer only.
- **What's not considered:** mapping these onto port operations. The expertise pipeline has lineage + creator + recall + synthesizer; some operations would naturally fire as class-D triggers on Morphon state transitions.
- **Resolution:** (b) included in the same service-layer-promotion sub-frame as 2.2.

## 3. Imported parts catalog — un-mined material

### 3.1 [CMPLX-1T/Wolfram study/](../../CMPLX-1T/Wolfram%20study/) — ~100 experiment files

- **What we have:** experiment_01.py through experiment_100form.py, plus `e8_projection.py`, `e8_roots.py`, `cmplx_wolfram_poc.py`. Most never read in this build.
- **What's not considered:** what each experiment proves or implements. The `experiment_03_quorum_cmply.py`, `experiment_04_triadic_morphon.py`, `experiment_100form.py` names suggest specific algorithms or proofs that may be canonical implementations of pieces we've built generically.
- **Why it matters:** we may be re-deriving things that already exist in the parts catalog. The Wolfram study was likely the substrate for the prior CMPLX work.
- **Resolution:** (b) new sub-frame — "Wolfram experiments inventory." Read each file, classify into (a) experimental/discarded, (b) reference implementation worth absorbing, (c) test/demo.

### 3.2 [CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/](../../CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/) — 10-tool suite

- **What we have:** protein_fold_morphon, quantum_circuit_lambda, economic_phase_boundary, drug_interaction_morphon, niemeier_genomic_aligner, materials_entropy_classifier, triadic_neural_topology, leech_climate_embedder, regex_lambda, rule30_lambda_shortcut, emergent_stability_classifier — 11 tools.
- **What's not considered:** these are domain-applied versions of cmplx primitives. They could be:
  - Reference applications: "this is what cmplx is FOR" — kept as documentation
  - Test cases: round-trip them through the substrate to verify it actually does what was promised
  - Showcase deliverables: a separate `applications/` tree for demos
- **Resolution:** (c) close-as-out-of-scope for the substrate work, but mark as candidates for a future "showcase regression suite."

### 3.3 [CMPLX-Manny/Working Prototyping/db/ai_memory/canonical_records.jsonl](../../CMPLX-Manny/Working%20Prototyping/db/ai_memory/canonical_records.jsonl) — 13,829 named entities

- **What we have:** prior-AI's catalogued entity registry (used during the initial inventory pass).
- **What's not considered:** are all 13,829 names accounted for in the current frame? We named ~50 in [ATTRACTOR_FRAME.md](../ATTRACTOR_FRAME.md). The delta is probably noise + duplicates + service-layer details, but it could contain entities the formalization corpus mentions that we haven't surfaced.
- **Resolution:** (b) new sub-frame — "Canonical-records delta review." Sample-based audit: pick 100 random records, classify each against the current frame.

### 3.4 [CMPLX-Manny/Working Prototyping/services/python-agent-runtime/](../../CMPLX-Manny/Working%20Prototyping/services/python-agent-runtime/) + node-agent-runtime/

- **What we have:** per-language agent runtimes from the prior repo. Not touched.
- **What's not considered:** these may be the canonical pre-cmplx runtimes for AgentProcess + the language-specific surface for Manny. If so, the current `src/runtime/persistent_agent.py` could be missing features they had.
- **Resolution:** (a) when AgentProcess gets its next substantial revision, diff against these to see what's missing.

## 4. Formalization-corpus pieces never surfaced

### 4.1 zk-SNARK chamber-membership proofs (Slot 50)

- **What we have:** ○ not-built. Parent frame Slot 50.
- **What's not considered:** the formalization (CMPLX2 Implementation Extension §12.6) places this in Phase 6. It's the cryptographic verification layer that lets a chamber's operations be proven without revealing internals. Today nothing in the build needs this.
- **Why it matters:** if/when the build needs external verification of operations (e.g., a remote agent proving it executed within its assigned chamber), this is the right shape. Out of scope until then.
- **Resolution:** (c) parking-lot.

### 4.2 K8s Custom Resource Definitions (Slot 51)

- **What we have:** ○ not-built. Parent frame Slot 51 — `GeometricAgent`, `WeylChamber`, `CQERoute` CRDs spec'd in CMPLX2 Implementation Extension §12.5.2.
- **What's not considered:** the build doesn't deploy to K8s today. The CRDs are forward-looking infrastructure.
- **Resolution:** (c) parking-lot.

### 4.3 Forge — VM-capsule space-control typing mechanism (Slot 49)

- **What we have:** ○ not-built. The "Forge" concept previously summarized as an in-house dependency builder.
- **User correction (2026-05-17):** "Forge is really just a typing mechanic template for vm capsule space control based around the system concepts. The goal is to assemble a baseline to start with for bootstrapping and then let the system both create and supplement using the forge concept beyond that."
- **What's not considered:** Forge is NOT a dependency resolver. It is the **typed-capsule mechanism** that lets the running system describe, instantiate, and govern VM-capsule space using its own system concepts (Morphons / Atlas chambers / port contracts). The PEP-X compliance reading was incorrect framing. Real shape: once the bootstrap baseline is assembled, Forge takes over as the self-extending mechanism — the system creates new capsules (services, sub-runtimes, isolated execution domains) typed against its own ontology.
- **Why it matters:** this is the bootstrap→self-extending transition. The substrate without Forge is "everything users explicitly build." With Forge, the substrate self-supplements: as the runtime accumulates morphons and their chambers, Forge instantiates new typed capsules to host them.
- **Resolution:** (a) future merge — not parking-lot. Needs a real design pass (likely its own sub-frame) once the substrate baseline is complete enough to know what's being typed.

### 4.4 BLS12-381 SNAP 7-role quorum signatures

- **What we have:** the formalization corpus (CMPLX2 Implementation Extension §12.3.2) specifies BLS12-381 aggregate signatures for the 7-role SNAP consensus. Currently SNAPEngine + SNAPDNA exist, but no signing.
- **What's not considered:** receipt signing. cmplx.receipt uses SHA-256 chaining. The formalization wants Ed25519 (already noted as a gap) and BLS for multi-role consensus.
- **Resolution:** (a) future merge — signing layer over `cmplx.receipt`. Bigger than just adding signatures; touches every receipt callsite.

### 4.5 CivSim (Slot 47)

- **What we have:** ○ not-built. Parent frame Slot 47 — described as "5-resource economy + bounded-rational agents."
- **User correction (2026-05-17):** "In the most advanced forms of the ideas, the CivSim does a lot of other things beyond the named use." CivSim is NOT a demo — it is a required runtime component. The "civilization simulation" name undersells it. Specific extended capabilities are not yet enumerated here; surface in the reality-calibration pass (§7 below).
- **What's not considered:** what those "other things" are. The earliest CMPLX work used CivSim as the substrate where bounded-rational agents + causal DAG + economy were *first proven to work*. Need to read the existing CivSim implementations in CMPLX-1T / Wolfram study to see what they actually do beyond economy simulation.
- **Resolution:** (a) future merge — not parking-lot. Promote to required component. Calibrate against the existing CivSim implementations in the parts catalog before re-implementing.

### 4.6 Standalone Geometric Transformer (Slot 48)

- **What we have:** ○ not-built. Reference document exists ([Standalone_Geometric_Transformer.docx](../../../../C:/Users/borke/Downloads/Formalizations%20and%20Direct%20Build%20Guides/Formalizations%20and%20Direct%20Build%20Guides/Standalone_Geometric_Transformer.docx)) describing a NumPy-only transformer with E₈ constraints + ΔΦ ≤ 0 conservation.
- **User correction (2026-05-17):** the Geometric Transformer is "part of the solution to answer 1" — it is the implementation vehicle for cognition (§1.1). NOT a demo. Required component.
- **What's not considered:** the integration topology between cognition (§1.1) and the geometric transformer. The transformer doesn't just *use* the cmplx substrate — it IS the "thinking" surface that consumes embed + diagnostic + atlas reports and produces decisions, with ΔΦ ≤ 0 enforcement at every layer.
- **Resolution:** (a) future merge — required component. Paired with §1.1 (cognition) and §4.5 (CivSim) as the trio that completes the "behavior" layer above the registered-port substrate.

## 5. Process steps quietly assumed

### 5.1 Receipt-chain replay determinism

- **What we have:** the receipt chain mints, indexes, and walks. But we haven't tested "given a sealed receipt chain from run N, can run N+1 reproduce it bit-identically?"
- **What's not considered:** the determinism diagnostic from Aletheia Full Stack Ref §A-7. The merge protocol uses "G4 — Determinism" but the gate is per-merge, not end-to-end.
- **Resolution:** (a) future merge — write a `tests/replay/test_chain_determinism.py` that runs a fixed scenario twice with controlled seeds and diffs the receipts.

### 5.2 Cross-port dependency cycle detection

- **What we have:** MorphonController port registration is order-aware (some ports check `MorphonController.has(other_port)` to know whether to delegate). No structural detection of cycles.
- **What's not considered:** if two ports each try to delegate to the other for ETP encoding (e.g., addressing → symbolic → atlas → addressing), no warning fires today. The fallback paths break the cycle in practice, but the structure could rot.
- **Resolution:** (a) low-priority future merge — a `MorphonController.audit_dependencies()` that walks every registered provider's `encode_to_etp` etc. and flags cycles.

### 5.3 Receipt port's chain growth → memory pressure

- **What we have:** [ReceiptProvider](../../src/cmplx/receipt/provider.py) grows monotonically. No retention policy.
- **What's not considered:** long-running agents will eventually exhaust memory. The port-trigger map proposes `receipt.verify_chain` on `governance_check` channel (period 31), but no `receipt.compact` or `receipt.window` operation exists.
- **Resolution:** (a) future merge — `ReceiptProvider.compact(keep_recent=10000)` + binding to a daemon channel as class-C.

### 5.4 Atlas deployed-set persistence

- **What we have:** [AtlasProvider](../../src/cmplx/atlas/provider.py) keeps `_deployed: dict[str, complex]` in memory.
- **What's not considered:** restart erases the deployment. A real production runtime needs deployed-set snapshots, probably persisted via `memory` port.
- **Resolution:** (a) future merge — `AtlasProvider.snapshot_to_memory_port()` + reverse `restore_from_memory_port()`.

### 5.5 Speedlight test flake

- **What we have:** `tests/speedlight/test_speedlight.py::test_provider_query_proximity` occasionally fails in full-sweep runs (passes in isolation). Documented across multiple merge receipts.
- **What's not considered:** what state is leaking. Likely a module-level singleton or imported-side-effect from another test module that runs before speedlight.
- **Resolution:** (a) future merge — narrow-scope debugging session; not blocking.

## 6. Conceptual surface not yet typed

### 6.1 ΔΦ ≤ 0 conservation enforcement at port boundaries

- **What we have:** [NSL](../../src/cmplx/nsl/) computes ΔΦ. Aletheia laws can read it. But no port boundary *automatically* checks ΔΦ ≤ 0.
- **What's not considered:** the formalization's CQE Law 2 (Boundary-Only Entropy) implies every cross-port operation should have a ΔΦ check. Today this is opt-in (Aletheia law authors decide).
- **Why it matters:** the system can drift into ΔΦ > 0 states silently if no law enforces it.
- **Resolution:** (a) future merge — a `cmplx.constraints.aletheia.laws.PhiNotIncreasingLaw` that Aletheia registers by default; auto-evaluates against the morphon's NSL state.

### 6.2 The `crystal` port elevation

- **What we have:** crystal-fabric lives in [src/cmplx/crystal/](../../src/cmplx/crystal/), in KNOWN_PORTS, but no provider. Not registered by bootstrap. Currently consumed by snap as a composite primitive.
- **What's not considered:** what `crystal.tier_promote` actually does. The port-trigger map design proposes "one channel per fabric layer" (10 daemon channels for the 10 SNAP layers) but doesn't specify the promotion algorithm.
- **Resolution:** (a) future merge — design promotion semantics (probably activity-based: a crystal that's referenced N times across M ticks promotes to next tier), implement provider, bind to daemon channels.

### 6.3 Cross-channel ETP receipt provenance

- **What we have:** `encode_to_etp(morphon)` is byte-identical across all facade fallbacks (verified by parity tests). But a morphon decoded via `symbolic.decode_from_etp(ledger)` vs `memory.decode_from_etp(ledger)` produces *different* morphons in some cases — the decoders share a fallback but the providers may evolve their decoders differently.
- **What's not considered:** there's no contract requirement that decoders ALSO produce byte-identical outputs. Only encoders are parity-tested.
- **Resolution:** (a) future merge — add decoder parity tests to the facade test suites.

### 6.4 Test-suite shadowing rule (NOT discoverable in the codebase)

- **What we have:** the rule that `tests/X/__init__.py` shadows `src/X/` for top-level packages is now recorded in [reference-memory](../../../../C:/Users/borke/.claude/projects/d--PartsFactory/memory/feedback_test_dir_init_shadowing.md), discovered during Wave 5.
- **What's not considered:** there's no automated check. Next time someone adds tests/governance/ or tests/wallet/ with `__init__.py`, the same trap fires.
- **Resolution:** (a) future merge — a tiny `tests/conftest.py`-level audit that warns about test-dir-named-after-top-level-package directories with `__init__.py`.

---

## 7. Disposition summary

| Category | (a) future merge | (b) new sub-frame | (c) parking-lot | (d) needs user input |
|---|---|---|---|---|
| 1. Empty cmplx stubs | 1.3 lambda, 1.4 AGRM | — | 1.2 interrogation | 1.1 cognition |
| 2. Service-layer parallels | 2.1 thinktank-as-port | 2.2-2.3 service-promotion sub-frame | — | — |
| 3. Parts catalog | 3.4 manny runtimes | 3.1 Wolfram inventory, 3.3 canonical-records audit | 3.2 showcase suite | — |
| 4. Formalization pieces | 4.4 BLS signing, 4.6 transformer | — | 4.1 zk-SNARK, 4.2 K8s CRDs, 4.3 Forge, 4.5 CivSim | — |
| 5. Process steps | 5.1-5.5 all listed | — | — | — |
| 6. Conceptual surface | 6.1-6.4 all listed | — | — | — |

**Top three actionable next builds** (small-bounded, structurally clarifying):

1. **§6.1 ΔΦ-monotonicity Aletheia law** — auto-registers, single new law class, ~30 LOC. Closes a "Law 2 not enforced" gap.
2. **§5.1 Receipt-chain replay determinism test** — write the fixture and assert, no new code, finds whatever determinism we're already getting for free.
3. **§3.1 Wolfram experiments inventory sub-frame** — half a day of explore-agent work, opens up potentially substantial reusable material.

**Top three structural questions** for the user:

1. What does **cognition** mean in this build (1.1)? It's the natural home for the "behavior" layer above the substrate, and it interacts with Manny's role.
2. Is **CivSim / Geometric Transformer** demo-only (4.5, 4.6) or do they become part of the runtime?
3. When does **hermetic build / Forge** (4.3) bite? It's a parking-lot item unless an external trust requirement forces it.

---

**End of deep-review v1. The work is to close items, not just list them — but listing them is what makes them closeable.**

---

## 8. Reality calibration — the gap I was missing

**Triggered by user direction 2026-05-17:** "Most everything we have now is still not even fully representing the repos we have as real examples of the real system working. Review starting there."

### 8.1 The framing error

The previous version of this catalog treated the existing repos (CMPLX-1T, Wolfram study, CMPLX-Manny) as **inventory to mine for parts**. That's the wrong frame. They are **operational evidence that the system works** — code that, when run, produces specific, measurable, verifiable behavior. The merge protocol's gates (G1 contract, G2 admission, G3 properties, G4 determinism) check that our substrate is *internally consistent*. They don't check that our substrate produces the *same external behavior* as the prior repos.

That's the missing gate. Call it **G5 — Reality calibration**: does running a known working example through our substrate produce the same observable result the prior repo produced?

Without G5, we've been building a coherent abstraction that may have quietly drifted from the system it's supposed to represent. The substrate works; we don't know whether it's the right substrate.

### 8.2 What the prior repos actually claim (with measurable signatures)

The Explore-agent reality-pass found verifiable behavioral claims across the repos. Selected by calibration value:

#### 8.2.1 [cmplx_wolfram_poc.py](../../CMPLX-1T/Wolfram%20study/cmplx_wolfram_poc.py) — Rule 30 / E8 equivalence

Claims:
- E8 geometric forms (rotated vectors + Weyl reflections) produce a digital-root sequence whose center-column entropy matches Rule 30's center column at ≈ **0.865 bits**
- Representational space explodes at the **100-form level** (genuine phase transition, not just growth)
- Triadic bonds emerge from morphon collisions

**Calibration question:** If we feed equivalent inputs into our `cmplx.geometry` + Atlas + morphon collision flow, do we measure 0.865 ± noise? Does our 100-form curve show the same explosion?

If yes → our substrate is faithful at the geometric core.
If no → either our E8 is wrong, our digital-root path is wrong, or our morphon-collision semantics drifted.

#### 8.2.2 [experiment_03_quorum_cmply.py](../../CMPLX-1T/Wolfram%20study/experiment_03_quorum_cmply.py) — Multi-agent E8 consensus

Claims:
- N agents with E8-snapped belief vectors converge to a single root under confidence-weighted centroid updates
- The convergence is **observable as entropy collapse** in the agents' vote distribution

**Calibration question:** Can our substrate (`MorphonController.get("snap").label(...)` + addressing.channel_for + repeated admit cycles with shared morphons) reproduce the convergence dynamics?

This is a *behavioral* test, not a *geometric* one. It exercises the integration of admission + addressing + snap + memory — the assembled substrate, not any one port.

#### 8.2.3 [experiment_04_triadic_morphon.py](../../CMPLX-1T/Wolfram%20study/experiment_04_triadic_morphon.py) — Morphon collision → ordered triples

Claims:
- Two-form collisions produce a third form geometrically positioned by the first two
- The three forms have specific inner-product / Cartan-matrix relationships
- Forth-element search (what would complete a natural grouping) is deterministic and unique

**Calibration question:** Do our morphon transitions + atlas placements reproduce the geometric ordering? Are Cartan-matrix relationships preserved through our pipeline?

#### 8.2.4 [experiment_100form.py](../../CMPLX-1T/Wolfram%20study/experiment_100form.py) — 100-form phase transition

Claims:
- At cycle orders 2/4/8 and levels 25/50/75/100, the representational space grows at quantifiable rates
- The growth has a **discontinuity at level 100** — that's what makes it a phase transition, not a smooth curve

**Calibration question:** Does our substrate reproduce the discontinuity?

This is one of the load-bearing structural claims of the whole system. If our substrate produces a smooth curve where the original showed a discontinuity, the 100-form phase-transition hypothesis isn't (operationally) something our build supports.

#### 8.2.5 [economic_phase_boundary.py](../../CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/artifacts/CMPLX_Tool_Suite/tool03_economic/economic_phase_boundary.py) — E8 generalization beyond physics

Claims:
- An 8D economic time series, snapped to nearest E8 root → digital-root sequence → rolling entropy produces a "Phase Boundary Proximity Score" (PBPS)
- PBPS peaks **just before** known economic transitions (recessions, regime changes)
- The same machinery (E8 snap + DR + rolling entropy) works without domain-specific tuning

**Calibration question:** Run economic time-series through our snap + addressing + diagnostic ports and check whether PBPS curves emerge correctly. This is the cross-domain generalization test.

### 8.3 What we *don't know* about our substrate right now

These are the open answers G5 would surface:

1. Does our `cmplx.geometry.e8.embed` produce the same root projections as the prior implementation?
2. Does our `cmplx.snap.label` produce the same labels for the same input?
3. Does our pipeline (admit_and_store + downstream) preserve the geometric relationships the original demonstrated?
4. Does our atlas Mandelbrot membership map onto the prior repo's "in-set" notion?
5. Does our receipt chain produce the same provenance trail an equivalent run on the prior repo would have produced?

We've never asked these. The merge protocol's G4 (determinism) ensures *we* produce the same result twice; it doesn't ensure we produce the result the *prior repo* would have produced.

### 8.4 Proposed resolution — Reality Calibration sub-frame

This deserves its own sub-frame: `docs/sub_frames/reality_calibration.md`. Shape:

- **For each calibration target** (start with §8.2.1–§8.2.5 above): a test that imports the prior example, runs it on our substrate, and compares outputs against the prior repo's claimed values.
- **G5 acceptance criterion** added to the merge protocol: a slot is `✅ canonical` only when its behavioral contribution to the calibration suite passes.
- **Calibration receipts** as a new receipt kind (or convention) — every calibration run mints a receipt with `expected_value` + `observed_value` + `delta` + `pass/fail`.

### 8.5 Other operational evidence found

The Explore-pass also surfaced material that's evidence of system shape rather than calibration targets per se:

- **[geometric_transformer_standalone.py](../../CMPLX-1T/docker/unified/aletheia2/geometric_transformer_standalone.py)** — pure-Python+NumPy transformer with E8-based attention. This is the reference implementation that §4.6 (Slot 48) and §1.1 (cognition) should be built against, not just the .docx spec.
- **[CMPLX-financial predictor.py](../../CMPLX-1T/SHOWROOM/DEPLOYMENTS/cmplx-financial/services/predictor/predictor.py)** — production-shape deployment template (Redis + TimescaleDB + E8MarketEmbedder + MORSRTemporalAnalyzer + ThinkTankConsensus). High integration value once the components exist; not a calibration target itself.
- **[python-agent-runtime](../../CMPLX-Manny/Working%20Prototyping/services/python-agent-runtime/server.py)** + node-agent-runtime — thin subprocess orchestration. Low calibration value, high deployment value.
- **[integration_demo.py](../../CMPLX-1T/docker/integration_demo.py)** — Docker Compose dependency-resolver. Pure orchestration; not calibration.

These move from §3 (un-mined material) to §8.5 (operational shape evidence). Different category, different disposition.

---

**End of deep-review v2 — §8 added per 2026-05-17 user direction.**
**Next sub-frame to write: reality_calibration.md** — defines G5, enumerates the calibration targets, structures the receipt grammar for calibration outcomes.
