# CMPLX-PartsFactory Attractor Frame (v1)

**Status:** v1 frozen — slots open for merge proposals
**Authority:** This document is the canonical naming, typing, and slot-assignment authority for the unified CMPLX build. When any agent (human or AI) finds an implementation that "fits a named piece," they propose a merge against this frame. The frame is itself a Morphon — each slot is a sub-Morphon with a fixed identity that implementations attract toward.

---

## 0. Why an attractor frame

Across this repo there are three concurrent trees (clean `src/cmplx/`, service-layer `src/*`, imported parts catalog under `CMPLX-1T/` and `CMPLX-Manny/`), 22 formalization documents describing the same architecture under different lenses, and a prior-AI canonical registry of 13,829 named entities with 15,335 linking edges. The naming and typing across all of these is already *substantially convergent* — the same architecture is implicit in every source. This document makes that convergence explicit.

The frame is not a roadmap. It is the **shape that already exists in the corpus**, named and typed clearly enough that implementations can be matched against it. Once a slot is filled, the slot accepts replacement implementations whenever the acceptance gates pass.

## 1. Sources of authority (priority order)

1. **In-place code** — `D:\PartsFactory\CMPLX-PartsFactory\src\` and the parts catalog under `CMPLX-1T\` and `CMPLX-Manny\`. The strongest opinion: if it exists and is consumed, it is real.
2. **Designs** — the 22 formalization documents in `C:\Users\borke\Downloads\Formalizations and Direct Build Guides\Formalizations and Direct Build Guides\`. Authoritative for contracts, mathematics, and structural intent.
3. **Prior-AI canonical catalogs** — `CMPLX-Manny\Working Prototyping\db\ai_memory\` (13,829 named entities, 15,335 edges) and the 8 unification reports in `CMPLX-1T\SHOWROOM\RESEARCH\unification-reports\`. Encodes what every prior AI agent identified as canonical and how they grouped scattered implementations.
4. **Current build state** — what this repo's clean tree (`src/cmplx/`, 14 KNOWN_PORTS, ~400 tests) has actually proven works.

When sources conflict, higher-priority source wins, but conflicts are recorded in the slot's notes rather than silently resolved.

## 2. Merge protocol

A merge is a typed boundary-crossing operation. To propose merging implementation `S` into slot `K`:

```
propose_merge(slot_id=K, source=S, contract_hash=H) → admission_receipt | rejection_receipt
```

The proposal carries:
- `slot_id` — the target slot from this document
- `source` — path to the candidate implementation
- `contract_hash` — SHA256 of the implementation's exported signature surface (class names, public methods, type annotations)
- `evidence` — what tests pass, what receipts the implementation can mint/consume, what dependencies it pulls in

The proposal is evaluated against four gates in order. **If any gate fails, the merge is rejected and a `DEATH` receipt is minted explaining why.** If all pass, an `ASSIGN` receipt is minted recording the merge and the source becomes the slot's occupant.

### 2.1 The four acceptance gates

| Gate | Check | Failure mode |
|---|---|---|
| **G1 — Contract** | Does the implementation expose the slot's required INTERFACE methods with compatible signatures? | Signature mismatch → reject; propose adapter shim instead |
| **G2 — Admission** | Does `MorphonController.get("constraints").admit(reference_morphon)` still pass for the slot's reference morphons after this implementation is wired in? | Aletheia law-chain rejection → reject |
| **G3 — Properties** | Do the slot's invariant property tests (isometry preservation, commutativity, idempotency, Voronoi membership, etc. as applicable) still hold? | Invariant violation → reject |
| **G4 — Determinism** | Does the determinism diagnostic produce bit-identical output for the slot's reference replay set? | Replay drift → reject |

A slot that is currently `not-built` skips G2–G4 for its first occupant (there is no prior reference to compare against) — that first merge establishes the references. Replacement merges (existing occupant being swapped out) must pass all four gates.

### 2.2 Receipt grammar for merges

| Operation | Receipt type | Payload |
|---|---|---|
| Slot first-fill | `BIRTH` | `{slot_id, source_path, contract_hash, gate_outputs}` |
| Slot replacement | `ASSIGN` | `{slot_id, prior_occupant, new_occupant, gate_outputs}` |
| Rejection | `DEATH` | `{slot_id, source_path, failed_gate, reason}` |
| Slot deprecation | `GATE` | `{slot_id, reason, successor_slot_id?}` |

All merge receipts chain into the `MorphonController.get("receipt")` ledger. The merge audit trail is grep-able and replay-able like any other system event.

### 2.3 Adapter shims

When a candidate's contract is *close* to the slot but not exact (different method names, equivalent semantics), the proposal can include an adapter spec. The adapter is itself a small implementation that must independently pass G1 against both the slot contract and the source's actual surface. Adapters live in `src/cmplx/<port>/_adapters/`. They are first-class merge-tracked artifacts, not hidden glue.

## 3. How to read a slot entry

Every slot below specifies:

- **Canonical name** + aliases (every name the prior corpus uses for this thing)
- **Port** — the `MorphonController` port this slot registers on, if any
- **INTERFACE** — the path to the slot's INTERFACE.md (created if absent)
- **Receipt grammar** — what receipt types this slot mints, what it consumes
- **Depends on** — other slots whose providers this slot calls
- **Current occupant** — the path that is closest to canonical right now, with a confidence score (0.0–1.0)
- **Candidate alternatives** — other implementations in the repo that could be merged in
- **Prior-AI catalog** — what the prior unification reports / canonical_records say about this entity
- **Design refs** — which formalization documents specify the contract
- **Status** — `✅ canonical` (filled, gates passing) / `◐ multi-candidate` (≥2 implementations, not yet collapsed) / `⊙ stub-only` (slot exists, no real occupant) / `○ not-built` (no implementation anywhere yet)
- **Gap to canonical** — what specific work is needed to bring this slot to `✅`

## 4. SNAP layer stratification

Slots are organized by the 10-layer SNAP fabric that prior-AI unification reports established and that the clean `src/cmplx/crystal/` tree implements. From substrate up:

- **L0 — Substrate**: receipts, conservation, law-chain, time
- **L1 — Geometry**: lattices and exceptional structures
- **L2 — Addressing & carrier**: morphon, controller, addressing, memory
- **L3 — Decomposition**: snap, tarpit, embedding channels
- **L4 — Engine & reasoning**: CQE, MORSR, lambda, thinktank
- **L5 — Atlas & dispatch**: boundary, julia, hash-lanes, IR
- **L6 — Transport**: physical channels (chirp/pixel/etc.)
- **L7 — Services**: governance, mesh, runtime, daemon, sidecar, wallet, identity
- **L8 — Canonical engines**: prior-AI's unified document/agent/atom/training/family engines
- **L9 — Channels & portals**: showroom, devkit, mcp-library, mainline
- **L10 — Applications & speculative**: civsim, geometric transformer, forge, K8s, zk-SNARK

Slots within a layer can depend on each other and on lower layers but **must not** depend on slots in higher layers (enforcement: any merge that imports a higher-layer slot fails G1).

---

# Layer 0 — Substrate

## Slot 01 — receipt-chain

- **Canonical name:** Receipt Chain
- **Aliases:** Receipts, CMPLXReceiptEngine, W5H receipts, boundary-event ledger
- **Port:** `receipt`
- **INTERFACE:** [src/cmplx/receipt/INTERFACE.md](../src/cmplx/receipt/INTERFACE.md)
- **Receipt grammar:** Mints all types (MINT, POST, BOND, PROCESS, ASSIGN, VOTE, BIRTH, DEATH, GATE, CROSSING). The slot itself IS the receipt grammar.
- **Depends on:** nothing (L0 root)
- **Current occupant:** [src/cmplx/receipt/](../src/cmplx/receipt/) — 10-type grammar, 5 indexes, DAG support, ReceiptProvider port-registered, 48 tests passing (confidence **0.95**)
- **Candidate alternatives:** [src/wallet/receipts.py](../src/wallet/receipts.py) — 7-type token-payment subset, hard-coupled to `governance.BoundaryEvent`, SHA256-only. Should become a domain adapter, not an alternative.
- **Prior-AI catalog:** RECEIPT-UNIFICATION-REPORT unified 20+ receipt files into CMPLXReceiptEngine with 10 receipt types and 6 relationship types (CAUSED_BY/DEPENDS_ON/PARENT_OF/CHILD_OF/PRECEDES/FOLLOWS) — matches current implementation's DAG edge store.
- **Design refs:** Aletheia_CQE_Operational_Package §Receipt Contract; Atlas Microkernel Architecture §receipt; cmplx_2_unified_build_plan §receipts.*
- **Status:** ✅ canonical
- **Gap:** Add Ed25519 signing (currently SHA256-only). Wallet receipts and governance BoundaryEvent need to migrate to this provider in Wave 0.

## Slot 02 — nsl-phi

- **Canonical name:** NSL (Noether-Shannon-Landauer) ΔΦ scalar
- **Aliases:** dphi, phi_total, delta_phi, conservation scalar, ΔΦ ≤ 0 law
- **Port:** `conservation`
- **INTERFACE:** [src/cmplx/nsl/INTERFACE.md](../src/cmplx/nsl/INTERFACE.md)
- **Receipt grammar:** Mints `GATE` receipts (admit/reject) with `{phi_before, phi_after, delta_phi, sector}` payload.
- **Depends on:** receipt-chain
- **Current occupant:** [src/cmplx/nsl/](../src/cmplx/nsl/) — phi computation, sectors with 24D Leech triad embedding, gate modes, ledger, NSLProvider port-registered, 51 tests passing (confidence **0.9**)
- **Candidate alternatives:** none significant. [src/governance/engine.py](../src/governance/engine.py) computes entropy in `BoundaryEvent.entropy_delta` but that's a parallel calc that should be replaced by nsl-phi consumption.
- **Prior-AI catalog:** Not directly named in unification reports. Implicit in TRAINING-UNIFICATION (layer-weighted loss) and ATOM-UNIFICATION (phase coherence). Memory note `[[reference-nsl-phi]]` confirms this is the canonical scalar.
- **Design refs:** Aletheia Full Stack Ref Law 2 (Boundary-Only Entropy); cmplx_2_unified_build_plan §ΔΦ; CQE_Classified_Formalizations.THERMODYNAMIC bucket.
- **Status:** ✅ canonical
- **Gap:** governance/engine entropy path should defer to this provider.

## Slot 03 — aletheia-law-chain

- **Canonical name:** Aletheia Conservation Law Chain
- **Aliases:** CQE Laws, admission gate, four-laws enforcement, policy gate
- **Port:** `constraints`
- **INTERFACE:** [src/cmplx/constraints/aletheia/INTERFACE.md](../src/cmplx/constraints/aletheia/INTERFACE.md)
- **Receipt grammar:** Returns `(bool, str)` tuples; rejection emits `DEATH` via caller; admission is silent. Caller responsible for `GATE` receipt with admission outcome.
- **Depends on:** receipt-chain
- **Current occupant:** [src/cmplx/constraints/aletheia/](../src/cmplx/constraints/aletheia/) — ConservationLaw protocol, 5 default laws, `admit/admit_strict`, 12 tests passing (confidence **0.85**)
- **Candidate alternatives:** [src/governance/engine.py](../src/governance/engine.py) `GeometricGovernance` is a parallel implementation. Should be replaced by a wrapper that runs Aletheia first, then adds entropy/invariant pass on top.
- **Prior-AI catalog:** Not in unification reports by name. Reference impl [_history_reference/Aletheia3ConservationLaw.py](../src/cmplx/constraints/aletheia/_history_reference/Aletheia3ConservationLaw.py) preserved.
- **Design refs:** Aletheia Full Stack Ref Part 1 (the 4 Laws); Aletheia_CQE_Operational_Package §Controller Contract.
- **Status:** ✅ canonical
- **Gap:** Register on `constraints` port at startup (presently a clean module that nothing has wired). Add 4-law-specific laws (Quadratic Invariance, Boundary Entropy, Auditable Governance, Optimized Efficiency) as concrete `ConservationLaw` subclasses.

## Slot 04 — speedlight-worldline

- **Canonical name:** Speedlight worldline cache
- **Aliases:** speedlight, receipt cache, worldline, deterministic replay cache
- **Port:** `cache`
- **INTERFACE:** [src/cmplx/speedlight/INTERFACE.md](../src/cmplx/speedlight/INTERFACE.md)
- **Receipt grammar:** Consumes all receipt types for indexing. Mints `POST` receipts on cache snapshot.
- **Depends on:** receipt-chain
- **Current occupant:** [src/cmplx/speedlight/](../src/cmplx/speedlight/) — address, cache, tiers, index, equivalence, worldline, SpeedlightProvider port-registered, 59 tests (confidence **0.9**)
- **Candidate alternatives:** none in cmplx tree; [src/mesh/cache.py](../src/mesh/cache.py) is an unrelated mesh-layer cache.
- **Prior-AI catalog:** RECEIPT-UNIFICATION L9 layer mapped to Speedlight. Confirmed.
- **Design refs:** Aletheia Full Stack Ref §A-7 Deterministic Run Identity; cmplx_2_unified_build_plan §replay.
- **Status:** ✅ canonical
- **Gap:** none for L0 purposes.

---

# Layer 1 — Geometry

## Slot 05 — e8-lattice

- **Canonical name:** E₈ Lattice
- **Aliases:** CMPLXLatticeProjector, E8 root system, e8_projection, quantize_e8
- **Port:** `geometry` (E8 sub-component)
- **INTERFACE:** [src/cmplx/geometry/e8/](../src/cmplx/geometry/e8/) — INTERFACE inherited from parent `geometry`
- **Receipt grammar:** No direct mint. Geometry operations consumed by snap/morphon trigger `CROSSING` receipts via callers.
- **Depends on:** receipt-chain (indirect)
- **Current occupant:** [src/cmplx/geometry/e8/embed.py](../src/cmplx/geometry/e8/embed.py) + [_history_reference/composed_E8Lattice.py](../src/cmplx/geometry/e8/_history_reference/composed_E8Lattice.py) + [_history_reference/composed_E8Root.py](../src/cmplx/geometry/e8/_history_reference/composed_E8Root.py) — registered via [src/cmplx/geometry/provider.py](../src/cmplx/geometry/provider.py) (confidence **0.85**)
- **Candidate alternatives:** [CMPLX-1T/Wolfram study/e8_projection.py](../CMPLX-1T/Wolfram%20study/e8_projection.py), [CMPLX-1T/Wolfram study/e8_roots.py](../CMPLX-1T/Wolfram%20study/e8_roots.py), [CMPLX-1T/SHOWROOM/SHOWCASES/case-02-e8-lattice/artifacts/CMPLXLatticeProjector.py](../CMPLX-1T/SHOWROOM/SHOWCASES/case-02-e8-lattice/artifacts/CMPLXLatticeProjector.py) — 20+ variants per prior-AI report
- **Prior-AI catalog:** E8-LATTICE-UNIFICATION-REPORT consolidated 20 E8 files into CMPLXLatticeProjector with three projection methods (Babai nearest-plane, exhaustive, Weyl chamber).
- **Design refs:** CMPLX2 Implementation Extension §12.1.2 (Leech CVP via E8 construction); Aletheia Full Stack §M-3 (240 Basin Partition); cmplx_2_unified_build_plan §E8.
- **Status:** ✅ canonical
- **Gap:** Add Babai nearest-plane and Weyl-chamber projection methods (current is D8+shift only).

## Slot 06 — leech-lattice

- **Canonical name:** Leech Lattice Λ₂₄
- **Aliases:** leech24, Leech minimal vectors, 196,560 kissing
- **Port:** `geometry` (Leech sub-component)
- **INTERFACE:** [src/cmplx/geometry/leech/](../src/cmplx/geometry/leech/)
- **Receipt grammar:** None directly. Consumed by atlas-mandelbrot, hash-lanes.
- **Depends on:** e8-lattice
- **Current occupant:** [src/cmplx/geometry/leech/embed.py](../src/cmplx/geometry/leech/embed.py) + [_history_reference/composed_LeechLattice.py](../src/cmplx/geometry/leech/_history_reference/composed_LeechLattice.py) (confidence **0.8**)
- **Candidate alternatives:** [CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/artifacts/CMPLX_Tool_Suite/tool08_climate/leech_climate_embedder.py](../CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/artifacts/CMPLX_Tool_Suite/tool08_climate/leech_climate_embedder.py)
- **Prior-AI catalog:** Implicit in E8-LATTICE-UNIFICATION (Construction A: Golay → Leech).
- **Design refs:** CMPLX2 Implementation Extension §12.1.2; Atlas Microkernel Architecture §kissing number 196,560.
- **Status:** ◐ multi-candidate (current works, tool08 candidate has richer methods)
- **Gap:** Full Leech CVP via Construction A' multilevel decomposition (target 953 ops avg per CMPLX2 Implementation Extension).

## Slot 07 — niemeier-types

- **Canonical name:** 23 Niemeier Even Unimodular Lattices in 24D
- **Aliases:** niemeier_specs, Niemeier card probe, Viewer24 stress chamber
- **Port:** `geometry` (Niemeier sub-component)
- **INTERFACE:** [src/cmplx/geometry/niemeier/__init__.py](../src/cmplx/geometry/niemeier/__init__.py) — needs INTERFACE.md
- **Receipt grammar:** Mints `POST` receipts per type-projection in stress chamber.
- **Depends on:** leech-lattice
- **Current occupant:** [src/cmplx/geometry/niemeier/_constants.py](../src/cmplx/geometry/niemeier/_constants.py) + [_functions.py](../src/cmplx/geometry/niemeier/_functions.py) (confidence **0.6**)
- **Candidate alternatives:** [CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/artifacts/CMPLX_Tool_Suite/tool05_genomic/niemeier_genomic_aligner.py](../CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/artifacts/CMPLX_Tool_Suite/tool05_genomic/niemeier_genomic_aligner.py)
- **Prior-AI catalog:** Not directly in unification reports. Mentioned in Aletheia Creative Permutations #2 "Niemeier Hypothesis Stress Chamber."
- **Design refs:** Aletheia Full Stack §M-10 (23 Niemeier Completeness); Aletheia Creative Permutations §2.
- **Status:** ◐ multi-candidate
- **Gap:** All 23 type strings + Cartan matrices in `_constants.py` exist but no projection function from E8 subspace → each Niemeier type's root system. Needs ~60 lines per projection.

## Slot 08 — alena-coupling

- **Canonical name:** Alena Tensor / Syndrome
- **Aliases:** Alena, anomaly detection tensor, rank-k coupling
- **Port:** `geometry` (Alena sub-component)
- **INTERFACE:** [src/cmplx/geometry/alena/INTERFACE.md](../src/cmplx/geometry/alena/INTERFACE.md)
- **Receipt grammar:** Mints `GATE` on syndrome ≠ 0 (anomaly detected).
- **Depends on:** e8-lattice
- **Current occupant:** [src/cmplx/geometry/alena/ops.py](../src/cmplx/geometry/alena/ops.py) (confidence **0.7**)
- **Candidate alternatives:** none in repo
- **Prior-AI catalog:** Not in unification reports.
- **Design refs:** Aletheia Full Stack §1.6 Alena Tensor / Syndrome; CQE_CORE_MONOLITH ALENA references.
- **Status:** ✅ canonical (provisional)
- **Gap:** Wire syndrome receipts into receipt-chain.

## Slot 09 — viewer24-probe

- **Canonical name:** Viewer24 / Dihedral CA / 23-Niemeier card probe
- **Aliases:** viewer24, dihedral cellular automaton, Julia probe, complex z²+c with dual-rail inverse
- **Port:** uses `geometry` (does not register its own port)
- **INTERFACE:** *to be created* — `src/cmplx/geometry/viewer24/INTERFACE.md`
- **Receipt grammar:** Mints `POST` per card-probe run, `GATE` on hypothesis-survival fail.
- **Depends on:** niemeier-types, e8-lattice
- **Current occupant:** none in cmplx tree
- **Candidate alternatives:** referenced by Aletheia Creative Permutations §2, §8 (Dihedral Hash), §13 (Time-Crystal Knowledge)
- **Prior-AI catalog:** Not in unification reports.
- **Design refs:** Aletheia Full Stack Ref Viewer24 subsystem (~600 lines per part-2); Aletheia Creative Permutations §2/8/13.
- **Status:** ○ not-built
- **Gap:** Entirely. Build target. Mine dihedral_ca dual-rail inverse logic from Aletheia Creative Permutations §8.

---

# Layer 2 — Addressing & carrier

## Slot 10 — morphon

- **Canonical name:** Morphon (universal information carrier)
- **Aliases:** Atom (per prior-AI), CQEAtom, morphon, atomic unit, lattice node carrier
- **Port:** none (the morphon IS the substrate that ports operate on)
- **INTERFACE:** [src/cmplx/morphon/INTERFACE.md](../src/cmplx/morphon/INTERFACE.md)
- **Receipt grammar:** Mints `BIRTH` on `Morphon.forge()`. Mints `CROSSING` on every state transition.
- **Depends on:** receipt-chain
- **Current occupant:** [src/cmplx/morphon/morphon.py](../src/cmplx/morphon/morphon.py) + [state.py](../src/cmplx/morphon/state.py) + [_history_reference/composed_morphon_v3.py](../src/cmplx/morphon/_history_reference/composed_morphon_v3.py) — extended with CQE fields (quad_encoding, parity_channels, sacred_frequency, digital_root, fractal_coordinate), 18 tests (confidence **0.95**)
- **Candidate alternatives:** [src/cmplx/engine/cqe/atom.py](../src/cmplx/engine/cqe/atom.py) is the CQEAtom view *of* Morphon, not an alternative
- **Prior-AI catalog:** ATOM-UNIFICATION-REPORT unified 25+ atom files into CMPLXAtomicEngine with 6 combination methods (Resonant Binding, Harmonic Coupling, Geometric Fusion, Fractal Nesting, Quantum Entanglement, Phase Coherence). Per user direction: CQEAtom IS Morphon.
- **Design refs:** Atlas Microkernel §Morphon-Mandelbrot Isomorphism; Aletheia Full Stack Ref L4-L6.
- **Status:** ✅ canonical
- **Gap:** Add the 6 combination methods from ATOM-UNIFICATION as composable operators.

## Slot 11 — morphon-controller

- **Canonical name:** MorphonController (port registry)
- **Aliases:** controller, kernel registry, port multiplexer
- **Port:** itself (it IS the port registry)
- **INTERFACE:** [src/cmplx/morphon/BRIDGE.md](../src/cmplx/morphon/BRIDGE.md)
- **Receipt grammar:** Mints `ASSIGN` on `register(port, provider)`; mints `GATE` on `get(port)` for ports not yet registered.
- **Depends on:** morphon, receipt-chain
- **Current occupant:** [src/cmplx/morphon/controller.py](../src/cmplx/morphon/controller.py) — singleton, 14 KNOWN_PORTS, `register`/`get` (confidence **0.85**)
- **Candidate alternatives:** [src/mesh/mesh.py](../src/mesh/mesh.py) `MeshOrchestrator` is the network-layer twin — complementary, not alternative. See Slot 31.
- **Prior-AI catalog:** Not in unification reports as a named entity. FAMILY-UNIFICATION's `router.py` is conceptually adjacent.
- **Design refs:** Atlas Microkernel §6-tier Controller Hierarchy; cmplx_2_unified_build_plan §kernel.
- **Status:** ✅ canonical
- **Gap:** `register_remote_provider(port, mesh, service_name)` to enable mesh bridge (Wave 0 gate A).

## Slot 12 — mdhg

- **Canonical name:** MDHG Multi-Scale Hash Graph
- **Aliases:** mdhg, addressing, MDHGAddress, MDHGMultiScale, 3-timescale cache addressing
- **Port:** `addressing`
- **INTERFACE:** [src/cmplx/addressing/mdhg/INTERFACE.md](../src/cmplx/addressing/mdhg/INTERFACE.md)
- **Receipt grammar:** Mints `POST` per address bind; `BOND` per cross-scale link.
- **Depends on:** morphon-controller, receipt-chain
- **Current occupant:** [src/cmplx/addressing/mdhg/](../src/cmplx/addressing/mdhg/) — 32 tests, hash.py + composed_mdhg_v3 reference (confidence **0.85**)
- **Candidate alternatives:** [src/cmplx/addressing/mdhg/_history_reference/composed_mdhg_v3.py](../src/cmplx/addressing/mdhg/_history_reference/composed_mdhg_v3.py) reference, remote mdhg service at port 8825
- **Prior-AI catalog:** Implicit in tier mapping; not directly named in unification reports.
- **Design refs:** Aletheia Creative Permutations §5 (Drift Detector); Aletheia Full Stack §6.5 CivSim integration; Aletheia Creative Permutations §14.
- **Status:** ✅ canonical (in-process); ⊙ stub-only (port registration absent)
- **Gap:** Register on `addressing` port at startup.

## Slot 13 — mmdb

- **Canonical name:** MMDB Lattice Graph Store
- **Aliases:** mmdb, memory, lattice_nodes/lattice_edges/receipts tables, geometric persistence
- **Port:** `memory`
- **INTERFACE:** [src/cmplx/memory/mmdb/INTERFACE.md](../src/cmplx/memory/mmdb/INTERFACE.md)
- **Receipt grammar:** Mints `POST` per node insert; `BOND` per edge insert; `CROSSING` per graph traversal.
- **Depends on:** morphon-controller, addressing (mdhg), receipt-chain
- **Current occupant:** [src/cmplx/memory/mmdb/store.py](../src/cmplx/memory/mmdb/store.py) + [_history_reference/composed_MMDB.py](../src/cmplx/memory/mmdb/_history_reference/composed_MMDB.py) — 11 tests (confidence **0.8**)
- **Candidate alternatives:** remote mmdb service at port 8824 via mesh bridge
- **Prior-AI catalog:** Implicit. Schema (lattice_nodes, lattice_edges, receipts) from Aletheia_CQE_Operational_Package §MMDB Storage Contract.
- **Design refs:** Aletheia_CQE_Operational_Package §MMDB Storage; Aletheia Full Stack Ref §6.5.
- **Status:** ✅ canonical (in-process); ⊙ stub-only (port registration absent)
- **Gap:** Register on `memory` port. Wire mesh-bridge to optionally route to remote mmdb when in-process is bypassed.

## Slot 14 — crystal-fabric

- **Canonical name:** 10-Level Crystal Fabric
- **Aliases:** crystal, snap-stratification, L0-L10 substrate, data + tool crystals, CrystalRegistry
- **Port:** none (composite primitive consumed by snap and engine)
- **INTERFACE:** [src/cmplx/crystal/INTERFACE.md](../src/cmplx/crystal/INTERFACE.md)
- **Receipt grammar:** Mints `BIRTH` on crystal forge; `BOND` on registry registration.
- **Depends on:** morphon, e8-lattice, leech-lattice
- **Current occupant:** [src/cmplx/crystal/](../src/cmplx/crystal/) — fabric.py, registry.py, types.py, 30 tests (confidence **0.9**)
- **Candidate alternatives:** none significant
- **Prior-AI catalog:** This IS the SNAP layer stratification that prior-AI's unification reports used (L0-L10).
- **Design refs:** Aletheia Full Stack Ref SNAP 10-level; Atlas Microkernel §10-level SNAP hierarchy.
- **Status:** ✅ canonical
- **Gap:** Populate L8-L10 crystal types as services / engines / channels come online.

## Slot 15 — agrm

- **Canonical name:** AGRM Adaptive Geometric Routing Manager
- **Aliases:** agrm, geometric routing, three-phase TSP solver, hash-lane geometric layer
- **Port:** `routing`
- **INTERFACE:** *to be created* — `src/cmplx/routing/agrm/INTERFACE.md`
- **Receipt grammar:** Mints `POST` per solve; `CROSSING` per traversal step.
- **Depends on:** e8-lattice, mdhg, morphon-controller
- **Current occupant:** [src/cmplx/routing/agrm/AGRMController.py](../src/cmplx/routing/agrm/AGRMController.py) (confidence **0.3** — stub-only)
- **Candidate alternatives:** Wolfram study experiment files (Hamiltonian paths, e8_projection.py); daemon channel weight computation (orientation UP/DOWN/SIDE)
- **Prior-AI catalog:** Not in unification reports.
- **Design refs:** Aletheia Full Stack Ref §6.4 Atlas Lanes; CMPLX2 Implementation Extension §12.2.1 TMN geodesic.
- **Status:** ⊙ stub-only
- **Gap:** Implement Navigator sweep → bidirectional PathBuilder → SalesmanValidator. Accept `orientation_weight` from daemon. Register on `routing` port.

## Slot 16 — hash-lanes

- **Canonical name:** Hash Lanes / Atlas Lanes
- **Aliases:** hash_lanes, atlas_lane_router, deterministic content-addressed routing
- **Port:** sub-port of `routing` (uses AGRM)
- **INTERFACE:** *to be created*
- **Receipt grammar:** Mints `CROSSING` per lane traversal.
- **Depends on:** agrm, mdhg
- **Current occupant:** none in cmplx tree
- **Candidate alternatives:** [src/daemon/orchestrator.py](../src/daemon/orchestrator.py) coprime channel scheduling (when, not where — see Slot 33); referenced by Aletheia Full Stack Ref §A-1 atlas lanes
- **Prior-AI catalog:** Not in unification reports by name.
- **Design refs:** Aletheia Full Stack Ref Atlas Lane vocabulary entry; CMPLX2 Implementation Extension §11 Voronoi Cell Organization.
- **Status:** ○ not-built
- **Gap:** Design + build atop AGRM. Mine cataloguer.py (456 compose files) for routing patterns observed in prior infrastructure.

---

# Layer 3 — Decomposition

## Slot 17 — snap

- **Canonical name:** SNAP — labels, lenses, Gate369, ledger
- **Aliases:** snap, SNAP decomposition, 10-level hierarchy probe
- **Port:** `snap`
- **INTERFACE:** [src/cmplx/snap/INTERFACE.md](../src/cmplx/snap/INTERFACE.md)
- **Receipt grammar:** Mints `POST` per label assignment; `GATE` on Gate369 fail.
- **Depends on:** morphon-controller, crystal-fabric, nsl-phi
- **Current occupant:** [src/cmplx/snap/](../src/cmplx/snap/) — labels, lenses, Gate369, ledger, 41 tests, SnapProvider registered (confidence **0.95**)
- **Candidate alternatives:** remote snap service at port 8823 via mesh bridge
- **Prior-AI catalog:** SNAP IS the layer-stratification scheme used throughout unification reports (L0-L10).
- **Design refs:** Atlas Microkernel §10-level SNAP; Aletheia Full Stack Ref §M-5 four-shell classification.
- **Status:** ✅ canonical
- **Gap:** none for core operation. SNAPDecompositionController (Atlas-2 build step) is a higher-layer consumer (see Slot 32).

## Slot 18 — tarpit

- **Canonical name:** TarPit symbolic substrate
- **Aliases:** tarpit, grain/dust/triad, walls, mirror, jot, ecology
- **Port:** `symbolic`
- **INTERFACE:** [src/cmplx/symbolic/tarpit/INTERFACE.md](../src/cmplx/symbolic/tarpit/INTERFACE.md)
- **Receipt grammar:** Mints `BIRTH` per grain; `BOND` per triad; `CROSSING` per mirror reflection.
- **Depends on:** morphon, receipt-chain
- **Current occupant:** [src/cmplx/symbolic/tarpit/](../src/cmplx/symbolic/tarpit/) — 44 tests, full grain/dust/triad + ecology (confidence **0.9**)
- **Candidate alternatives:** remote tarpit service at port 8844
- **Prior-AI catalog:** Not in unification reports by this name.
- **Design refs:** Aletheia Creative Permutations §6 (Agents That Think in Lambda Calculus has tarpit-adjacent grammar).
- **Status:** ✅ canonical (in-process); ⊙ stub-only (port registration absent)
- **Gap:** Register on `symbolic` port.

## Slot 19 — four-embed

- **Canonical name:** 4-Embed Model (Constraint + State + Evidence + Operator)
- **Aliases:** four-embed, 4E, typed-channel separation, fact/assumption split
- **Port:** none (a typed view over morphon payloads)
- **INTERFACE:** *to be created* — `src/cmplx/embed/INTERFACE.md`
- **Receipt grammar:** Mints `POST` per channel populate; `GATE` on channel inconsistency.
- **Depends on:** morphon, aletheia-law-chain
- **Current occupant:** none
- **Candidate alternatives:** [src/governance/engine.py](../src/governance/engine.py) `BoundaryEvent` has implicit constraint/state/evidence but not separated
- **Prior-AI catalog:** Not in unification reports.
- **Design refs:** Aletheia_CQE_Operational_Package §4-Embed Model; Aletheia Full Stack Ref §6.1 Semantic Embedding Fix.
- **Status:** ○ not-built
- **Gap:** Entire build. New package `src/cmplx/embed/`. Wire as decomposition step before aletheia admission.

---

# Layer 4 — Engine & reasoning

## Slot 20 — cqe-engine

- **Canonical name:** CQE Engine (mandelbrot + toroidal + banding + domain adapter + atom + objective + governance + modes + runner)
- **Aliases:** cqe, Cartan Quadratic Equivalence engine, CQEProvider, CQE orchestrator
- **Port:** `engine`
- **INTERFACE:** [src/cmplx/engine/cqe/INTERFACE.md](../src/cmplx/engine/cqe/INTERFACE.md)
- **Receipt grammar:** Mints all 10 types depending on sub-operation; `PROCESS` is the common outer wrapper.
- **Depends on:** morphon, e8-lattice, snap, nsl-phi, aletheia-law-chain, mdhg, mmdb, receipt-chain
- **Current occupant:** [src/cmplx/engine/cqe/](../src/cmplx/engine/cqe/) — 72 tests, provider.py exposing CQEProvider, mandelbrot/toroidal/banding/atom/objective/governance/modes/runner (confidence **0.85**)
- **Candidate alternatives:** [CMPLX-1T/Wolfram study/cmplx_wolfram_poc.py](../CMPLX-1T/Wolfram%20study/cmplx_wolfram_poc.py) reference
- **Prior-AI catalog:** Implicit. The 90-controller V21 dispatch tree from Aletheia Full Stack Ref §2.2 enumerates CQE controller families.
- **Design refs:** Aletheia Full Stack Ref §2 (the running codebase, 60/69 pass); Aletheia_CQE_Operational_Package §Controller Contract.
- **Status:** ✅ canonical
- **Gap:** Register on `engine` port. Add full V21 dispatch tree (currently has runner; tree IR is Slot 28).

## Slot 21 — morsr

- **Canonical name:** MORSR — Measure / Observe / Reflect / Synthesize / Refine
- **Aliases:** morsr, ripple/subripple/pulse/handshake/sonar, diagnostic loop, originally "Middle Out, Ripple, SubRipple"
- **Port:** `diagnostic`
- **INTERFACE:** [src/cmplx/morsr/INTERFACE.md](../src/cmplx/morsr/INTERFACE.md)
- **Receipt grammar:** Mints `POST` per pulse; `GATE` on ΔΦ ≤ 0 fail; `CROSSING` per traversal step.
- **Depends on:** morphon, e8-lattice, nsl-phi, snap, receipt-chain
- **Current occupant:** [src/cmplx/morsr/](../src/cmplx/morsr/) — 63 tests, overlay/operators/shell/handshake/pulse/traversal/sonar, MORSRProvider registered (confidence **0.95**)
- **Candidate alternatives:** none significant
- **Prior-AI catalog:** Not in unification reports as a named entity. Memory note `[[reference-morsr-origin]]` confirms diagnostic-loop interpretation.
- **Design refs:** Aletheia Full Stack Ref §morsr; Aletheia Creative Permutations §H module.
- **Status:** ✅ canonical
- **Gap:** none.

## Slot 22 — lambda

- **Canonical name:** Λ⊗E₈ Lambda Calculus Bridge
- **Aliases:** lambda, morphonic_lambda, e8_bridge, LambdaE8Evaluator, GeometricLambdaCapture
- **Port:** *to be added* — proposed new port `lambda` (not in current KNOWN_PORTS)
- **INTERFACE:** *to be created*
- **Receipt grammar:** Mints `PROCESS` per beta reduction; `GATE` on type-error.
- **Depends on:** morphon, e8-lattice, mmdb, receipt-chain
- **Current occupant:** [src/cmplx/lambda/LambdaTerm.py](../src/cmplx/lambda/LambdaTerm.py) (confidence **0.2** — draft)
- **Candidate alternatives:** [CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/artifacts/CMPLX_Tool_Suite/tool02_quantum/quantum_circuit_lambda.py](../CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/artifacts/CMPLX_Tool_Suite/tool02_quantum/quantum_circuit_lambda.py), [tool09_regex_lambda/regex_lambda.py](../CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/artifacts/CMPLX_Tool_Suite/tool09_regex_lambda/regex_lambda.py), [tool09_rule30/rule30_lambda_shortcut.py](../CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/artifacts/CMPLX_Tool_Suite/tool09_rule30/rule30_lambda_shortcut.py)
- **Prior-AI catalog:** Not in unification reports.
- **Design refs:** Aletheia Full Stack Ref §morphonic_lambda; Aletheia Creative Permutations §1, §4, §6, §10, §15 (lambda calculus uses).
- **Status:** ⊙ stub-only
- **Gap:** Build out AST (Var, Lam, App), normal-order evaluator, type system (Arrow, Prod, Bool, Nat, Grade), modal logic (Box/Diamond), glyphs, e8_bridge wiring. Add `lambda` to KNOWN_PORTS.

## Slot 23 — thinktank

- **Canonical name:** ThinkTank — quorum deliberation engine
- **Aliases:** thinktank, CMPLXThinkTankEngine, quorum_engine, 6-role deliberation
- **Port:** *to be added* — proposed new port `thinktank` (or sub-port of `diagnostic`)
- **INTERFACE:** *to be created*
- **Receipt grammar:** Mints `VOTE` per role response; `POST` per consensus; `GATE` on quorum fail.
- **Depends on:** morphon, morsr, snap, receipt-chain
- **Current occupant:** [src/thinktank/agent.py](../src/thinktank/agent.py) (service-layer, confidence **0.7**)
- **Candidate alternatives:** [CMPLX-1T/SHOWROOM/SHOWCASES/case-04-thinktank/artifacts/CMPLXThinkTankEngine.py](../CMPLX-1T/SHOWROOM/SHOWCASES/case-04-thinktank/artifacts/CMPLXThinkTankEngine.py) — full reference impl
- **Prior-AI catalog:** THINKTANK-UNIFICATION-REPORT canonicalized 6 roles (PLANNER, IMPLEMENTER, CRITIC, RESEARCHER, VALIDATOR, SYNTHESIST) with weighted confidence per role.
- **Design refs:** agent framework session+novel ideas §CrewAI hierarchical micro-agent swarm; Aletheia Creative Permutations §17 Sealed Debate.
- **Status:** ◐ multi-candidate
- **Gap:** Reconcile service-layer thinktank with showcase ThinkTankEngine. Promote into `src/cmplx/thinktank/` or as a sub-port of diagnostic. Match the 6-role canonical from prior-AI report.

## Slot 24 — spectral-health

- **Canonical name:** Spectral Health Controller
- **Aliases:** spectral, graph laplacian, spectral gap, bridge-node detection, Cheeger-bound diagnostic
- **Port:** sub-port of `diagnostic`
- **INTERFACE:** *to be created*
- **Receipt grammar:** Mints `POST` per spectral fingerprint; `GATE` on health regression.
- **Depends on:** mmdb, morsr, receipt-chain
- **Current occupant:** none in cmplx tree
- **Candidate alternatives:** AGRE SpectralReasoner reference in Aletheia Full Stack §6.3
- **Prior-AI catalog:** Not in unification reports.
- **Design refs:** Aletheia Full Stack §6.3 Spectral Reasoning Controller (1 new ~100 lines following existing patterns); Aletheia Creative Permutations §16.
- **Status:** ○ not-built
- **Gap:** Entire build — ~100 lines per design ref. Reads MMDB lattice_nodes/edges, computes graph Laplacian, reports spectral gap ratio, connected components, bridge nodes, geometric gaps.

## Slot 25 — causal-dag

- **Canonical name:** Causal DAG (predict_delta + attribution_receipt)
- **Aliases:** causal, predict_delta, attribution_receipt, counterfactual analysis
- **Port:** sub-port of `diagnostic`
- **INTERFACE:** *to be created*
- **Receipt grammar:** Mints `POST` per prediction; `BOND` per attribution edge; `GATE` on causal-violation.
- **Depends on:** mmdb, receipt-chain
- **Current occupant:** none in cmplx tree
- **Candidate alternatives:** [src/expertise/expert_memory.py](../src/expertise/expert_memory.py) lineage tracking is conceptually adjacent
- **Prior-AI catalog:** Not in unification reports but referenced in CMPLXAgentEngine receipts as `CAUSED_BY` relationship.
- **Design refs:** Aletheia Creative Permutations §3 (Civilizational Causal Reverser), §7 (Receipt Chain as Causal DAG), §11.
- **Status:** ○ not-built
- **Gap:** Build per Creative Permutations §7 — translation is "receipt becomes node, prev_receipt_hash becomes edge, artifact hash becomes feature." ~30 lines per design ref.

---

# Layer 5 — Atlas & dispatch

## Slot 26 — atlas-mandelbrot

- **Canonical name:** Atlas Mandelbrot Deployment Boundary
- **Aliases:** atlas, Mandelbrot boundary, deployment selection, kissing number 196,560
- **Port:** *to be added* — proposed `atlas`
- **INTERFACE:** *to be created*
- **Receipt grammar:** Mints `GATE` on boundary check; `CROSSING` on deployment.
- **Depends on:** leech-lattice, morphon-controller, receipt-chain
- **Current occupant:** none
- **Candidate alternatives:** [src/identity/playbook.py](../src/identity/playbook.py) PlaybookEngine is conceptually adjacent (Playbook = global attractor per Atlas-6)
- **Prior-AI catalog:** Not in unification reports.
- **Design refs:** Atlas Microkernel Architecture pdf §Morphon-Mandelbrot Isomorphism (Atlas-1 through Atlas-6, 27 weeks); CMPLX Atlas Build Guide Atlas-1.
- **Status:** ○ not-built
- **Gap:** Entirely. The Atlas-3 build step from CMPLX Atlas Build Guide. Mandelbrot selection measures largest deployment not exceeding Leech kissing number.

## Slot 27 — julia-c-assignment

- **Canonical name:** Julia c-assignment per Morphon (Observer-Julia Correspondence)
- **Aliases:** julia, c-value, observer identity, fixed-c per agent
- **Port:** sub-port of `atlas`
- **INTERFACE:** *to be created*
- **Receipt grammar:** Mints `BIRTH` with `{c_value, role, tier, labels, e8_position}` payload.
- **Depends on:** atlas-mandelbrot, morphon, e8-lattice
- **Current occupant:** none
- **Candidate alternatives:** none
- **Prior-AI catalog:** Not in unification reports.
- **Design refs:** Atlas Microkernel §Observer-Julia Correspondence; Aletheia Creative Permutations §13 dual-rail inverse.
- **Status:** ○ not-built
- **Gap:** Entire build. Atlas-3 step.

## Slot 28 — dispatch-tree-ir

- **Canonical name:** Dispatch Tree IR — WorkflowSpec, StepSpec, RunEventLog
- **Aliases:** dispatch_tree, dispatch tree v21, workflow IR, hub specs
- **Port:** *to be added* — proposed `dispatch` or sub-port of `engine`
- **INTERFACE:** *to be created*
- **Receipt grammar:** Mints `POST` per step start/end; `BOND` per step → next; `GATE` per policy gate.
- **Depends on:** cqe-engine, aletheia-law-chain, receipt-chain
- **Current occupant:** [src/dtt/orchestrator.py](../src/dtt/orchestrator.py) — DTTOrchestrator, IdeaPacket, CompositionRound (skeleton, confidence **0.4**)
- **Candidate alternatives:** [CMPLX-1T/Wolfram study/dispatch_tree_v21_hier_workspace.json](../CMPLX-1T/Wolfram%20study/) reference (the V21 70-step manifest from Aletheia Full Stack §2.2)
- **Prior-AI catalog:** Not as IR per se. V21 dispatch tree referenced indirectly via FAMILY-UNIFICATION's lattice_runtime.
- **Design refs:** Aletheia_CQE_Operational_Package §Dispatch Tree Contract; cmplx_2_unified_build_plan §hub.specs.*/hub.run.*.
- **Status:** ⊙ stub-only
- **Gap:** Promote dtt orchestrator → real IR. Materialize WorkflowSpec/StepSpec/RunEventLog dataclasses. Wire V21 70-step manifest.

---

# Layer 6 — Transport

## Slot 29 — transport-carriers

- **Canonical name:** Transport carriers (chirp/DTMF/pixel/numbers_station/video)
- **Aliases:** transport, carrier, chirp, DTMF, pixel, numbers_station
- **Port:** `transport`
- **INTERFACE:** [src/cmplx/transport/](../src/cmplx/transport/)
- **Receipt grammar:** Mints `CROSSING` per encode/decode pair.
- **Depends on:** morphon, receipt-chain
- **Current occupant:** [src/cmplx/transport/](../src/cmplx/transport/) — 33 tests, carrier + chirp/DTMF + pixel + numbers_station + video stub (confidence **0.75**)
- **Candidate alternatives:** none
- **Prior-AI catalog:** Not in unification reports.
- **Design refs:** Aletheia Full Stack Ref §6.6 transport channels.
- **Status:** ◐ multi-candidate (chirp+pixel real, others stubs)
- **Gap:** Register on `transport` port. Complete numbers_station and video.

---

# Layer 7 — Services (the Tree 2 distributed layer)

These slots wrap the existing `src/*` service-layer scaffolds. Their job is to consume Layer 0–6 slots via `MorphonController` rather than reimplementing them.

## Slot 30 — governance-kernel

- **Canonical name:** Governance Kernel (CQE-laws enforcement, BoundaryEvent, AssemblyLine)
- **Aliases:** governance, GeometricGovernance, AssemblyLine, BoundaryEvent
- **Port:** consumes `constraints` + `receipt` + `conservation`; no own port
- **Current occupant:** [src/governance/engine.py](../src/governance/engine.py) + [src/governance/assembly.py](../src/governance/assembly.py) + [src/governance/dna.py](../src/governance/dna.py)
- **Status:** ◐ multi-candidate (parallel to aletheia-law-chain)
- **Gap:** Refactor to delegate admission to Slot 03 (aletheia), entropy to Slot 02 (nsl-phi), receipts to Slot 01.

## Slot 31 — mesh-orchestrator

- **Canonical name:** Mesh Service Orchestrator
- **Aliases:** mesh, MeshOrchestrator, ServiceDiscovery, IntentRouter
- **Port:** none in-process; bridges to morphon-controller via [src/mesh/morphon_bridge.py](../src/mesh/morphon_bridge.py) *to be created*
- **Current occupant:** [src/mesh/mesh.py](../src/mesh/mesh.py) + [src/mesh/service_discovery.py](../src/mesh/service_discovery.py) + [src/mesh/router.py](../src/mesh/router.py)
- **Status:** ✅ canonical (network layer)
- **Gap:** Build morphon_bridge.py — Wave 0 Gate A.

## Slot 32 — runtime-agent

- **Canonical name:** Runtime Persistent Agent Server (Workflow Hub)
- **Aliases:** runtime, RuntimeOrchestrator, AgentProcess, PartsFactoryIntake, L4 Workflow Hub
- **Port:** none; runs the FastAPI server that wires everything together
- **Current occupant:** [src/runtime/server.py](../src/runtime/server.py) + [src/runtime/persistent_agent.py](../src/runtime/persistent_agent.py) + [src/runtime/orchestrator.py](../src/runtime/orchestrator.py)
- **Status:** ✅ canonical
- **Gap:** Wire `MorphonController.register()` calls at startup for all in-process providers. Add mesh-bridge calls for remote-service ports.

## Slot 33 — daemon-crt

- **Canonical name:** Daemon CRT 24-Channel Scheduler
- **Aliases:** daemon, local_crt, global_crt, tmn2_daemon, coprime-period scheduler, heartbeat
- **Port:** none; cron-like coordinator
- **Current occupant:** [src/daemon/](../src/daemon/) — orchestrator.py + local_crt.py + global_crt.py + tmn2_daemon.py
- **Status:** ✅ canonical
- **Gap:** Publish E8 orientation (UP/DOWN/SIDE) into AGRM consumption buffer (Wave 2 step).

## Slot 34 — sidecar

- **Canonical name:** Red Hat Sidecar (per-agent SQLite)
- **Aliases:** sidecar, agent_sidecar, brain_states + knowledge + experiences DB
- **Port:** consumes `memory` per-agent-instance
- **Current occupant:** [src/sidecar/agent_sidecar.py](../src/sidecar/agent_sidecar.py)
- **Status:** ✅ canonical
- **Gap:** Route persistence calls through `MorphonController.get("memory")` instead of direct SQLite.

## Slot 35 — gateway-interface

- **Canonical name:** Unified HTTP Gateway (L5 Channels)
- **Aliases:** interface, APIGateway, gateway
- **Port:** none; external entrypoint
- **Current occupant:** [src/interface/gateway.py](../src/interface/gateway.py) + [auth.py](../src/interface/auth.py) + [config.py](../src/interface/config.py)
- **Status:** ✅ canonical
- **Gap:** Add MCP/SSE port-multiplexed routes for each `MorphonController` port.

## Slot 36 — identity-playbook

- **Canonical name:** Identity Service + Playbook Engine (global attractor)
- **Aliases:** identity, playbook, PlaybookEngine, Atlas-6 global attractor
- **Port:** none in-process; consumes `receipt` for run history
- **Current occupant:** [src/identity/](../src/identity/) — identity.py + playbook.py + service.py + contracts.py + instructions.py
- **Status:** ✅ canonical
- **Gap:** Wire to Slot 26 atlas-mandelbrot when built — Playbook IS the global attractor per Atlas-6.

## Slot 37 — wallet-economy

- **Canonical name:** Wallet + Token Economy
- **Aliases:** wallet, economy, mint, receipts (token)
- **Port:** consumes `receipt`
- **Current occupant:** [src/wallet/wallet.py](../src/wallet/wallet.py) + [economy.py](../src/wallet/economy.py) + [mint.py](../src/wallet/mint.py) + [receipts.py](../src/wallet/receipts.py)
- **Status:** ◐ multi-candidate (parallel receipts impl)
- **Gap:** Migrate receipts to Slot 01 — Wave 0 Gate B.

---

# Layer 8 — Canonical engines (prior-AI unified)

These five slots map to the prior-AI unification reports. They are aggregations/facades over Layer 0–6 primitives — the "official user-facing" engines from the SHOWROOM era.

## Slot 38 — agent-engine

- **Canonical name:** CMPLXAgentEngine
- **Aliases:** agent, AGENT, agent simulation, capability mgmt
- **Port:** *to be added* — proposed `agent`
- **Current occupant:** [src/runtime/persistent_agent.py](../src/runtime/persistent_agent.py) (closest)
- **Candidate alternatives:** [CMPLX-1T/Wolfram study/agent_controller.py](../CMPLX-1T/Wolfram%20study/agent_controller.py)
- **Prior-AI catalog:** AGENT-UNIFICATION-REPORT unified 10+ agent variants
- **Status:** ◐ multi-candidate
- **Gap:** Reconcile runtime persistent_agent with prior CMPLXAgentEngine. Decide whether `agent` is its own port or stays as a runtime concern.

## Slot 39 — atomic-engine

- **Canonical name:** CMPLXAtomicEngine (6-method atom combination)
- **Aliases:** atom, ATOM, atomic_unit, combination methods
- **Port:** consumes `morphon` + `geometry`; no own port
- **Current occupant:** Implicit in [src/cmplx/morphon/](../src/cmplx/morphon/) — atom IS morphon per user direction
- **Candidate alternatives:** [CMPLX-1T/Wolfram study/atomic_unit.py](../CMPLX-1T/Wolfram%20study/atomic_unit.py)
- **Prior-AI catalog:** ATOM-UNIFICATION-REPORT — 6 combination methods (Resonant Binding, Harmonic Coupling, Geometric Fusion, Fractal Nesting, Quantum Entanglement, Phase Coherence)
- **Status:** ◐ multi-candidate
- **Gap:** Add the 6 combination methods as composable operators on Morphon (per Slot 10 gap note).

## Slot 40 — document-engine

- **Canonical name:** CMPLXDocumentEngine
- **Aliases:** document, doc-decomposer, multi-format parser
- **Port:** *to be added* — proposed `document` or sub-port of `transport`
- **Current occupant:** [CMPLX-Manny/Working Prototyping/db/ai_memory/parse_compose_catalog.py](../CMPLX-Manny/Working%20Prototyping/db/ai_memory/parse_compose_catalog.py) (closest, for compose files only)
- **Candidate alternatives:** [src/runtime/persistent_agent.py](../src/runtime/persistent_agent.py) PartsFactoryIntake
- **Prior-AI catalog:** DOCUMENT-UNIFICATION-REPORT — 8 files unified, formats `.txt/.md/.json/.json5/.csv/.tsv`
- **Status:** ⊙ stub-only
- **Gap:** Build out as a real port. Use canonical 6 formats.

## Slot 41 — family-engine

- **Canonical name:** CMPLXFamilyEngine (22 controller families)
- **Aliases:** family, FAMILY, family_router, lattice_runtime
- **Port:** consumes `morphon-controller`; no own port (the 14 KNOWN_PORTS replace the family registry)
- **Current occupant:** [src/cmplx/morphon/controller.py](../src/cmplx/morphon/controller.py) — IS the family registry, just typed by port
- **Prior-AI catalog:** FAMILY-UNIFICATION-REPORT — 22 distinct families, base controller + registry + cross-family router
- **Status:** ✅ canonical (via Slot 11)
- **Gap:** Map the 22 prior-AI families onto the 14 KNOWN_PORTS to confirm coverage; add ports if any family doesn't fit.

## Slot 42 — training-engine

- **Canonical name:** CMPLXTrainingEngine
- **Aliases:** training, neural network, training_loop, layer-weighted loss
- **Port:** *to be added* — proposed `training` or sub-port of `engine`
- **Current occupant:** [src/expertise/pipeline.py](../src/expertise/pipeline.py) (closest)
- **Candidate alternatives:** [CMPLX-Manny/Working Prototyping/services/python-agent-runtime/](../CMPLX-Manny/Working%20Prototyping/services/python-agent-runtime/)
- **Prior-AI catalog:** TRAINING-UNIFICATION-REPORT — feedforward network, Xavier init, epoch training, layer-weighted loss (L3=1.5x, L4=1.2x, L6=1.3x, L8=1.1x)
- **Status:** ⊙ stub-only
- **Gap:** Build out training engine. Wire layer-weighted loss to crystal-fabric L0-L10 mapping.

---

# Layer 9 — Channels & portals

## Slot 43 — showroom

- **Canonical name:** CMPLX-1T SHOWROOM
- **Aliases:** showroom, ENTRANCE, exhibits, public-facing museum
- **Current occupant:** [CMPLX-1T/SHOWROOM/](../CMPLX-1T/SHOWROOM/) — already exists as the imported parts catalog
- **Status:** ✅ canonical (as parts catalog) / ⊙ stub-only (as live channel)
- **Gap:** Decide if SHOWROOM remains a static historical record or becomes a live channel that surfaces working slots as exhibits.

## Slot 44 — devkit

- **Canonical name:** CMPLXDevKit
- **Aliases:** devkit, research workspace, physics labs, test harness
- **Current occupant:** none in PartsFactory (CMPLXDevKit folder was empty)
- **Status:** ○ not-built
- **Gap:** Decide whether the Wolfram study / experiment files become DevKit content.

## Slot 45 — mcp-library

- **Canonical name:** CMPLXMCP — AI-callable tool library
- **Aliases:** mcp-library, MCP, tool capsules, doc-decomposer + e8-projector + thinktank-client + code-analyzer + training-loop
- **Current occupant:** none implemented (per [CMPLXMCP.md](../CMPLX-1T/SHOWROOM/PORTAL/CMPLXMCP.md) only)
- **Status:** ○ not-built
- **Gap:** Each MCP tool needs Docker capsule. Maps to MCP namespace contracts from cmplx_2_unified_build_plan §MCP.

## Slot 46 — mainline

- **Canonical name:** CMPLX-mainline
- **Aliases:** mainline, stable release channel, API suites
- **Current occupant:** none (per [CMPLX-mainline.md](../CMPLX-1T/SHOWROOM/PORTAL/CMPLX-mainline.md) — design phase only)
- **Status:** ○ not-built
- **Gap:** Pending substrate stabilization.

---

# Layer 10 — Applications & speculative

## Slot 47 — civsim

- **Canonical name:** CivSim — 5-resource economy with bounded-rational agents
- **Aliases:** civsim, agent simulation, society economy
- **Status:** ○ not-built
- **Design refs:** Aletheia Full Stack Ref §cqe_civ; Aletheia Creative Permutations §3, §6, §9, §19.

## Slot 48 — geometric-transformer

- **Canonical name:** Standalone Geometric Transformer (Λ⊗E₈ enforced)
- **Aliases:** geometric_transformer, E8-constrained transformer, ΔΦ-enforced attention
- **Status:** ● built (MVP)
- **Occupant:** [`src/cmplx/transform/`](../src/cmplx/transform/) — `GeometricTransformer`, `MorphonicTokenizer`, `MorphonicAttention` (MORSR), `MorphonicFFN` (TarPit), NSL-gated residual, SpeedLight whole-forward cache. PyTorch wrapper under [`src/cmplx/transform/torch/`](../src/cmplx/transform/torch/). See [`INTERFACE.md`](../src/cmplx/transform/INTERFACE.md) and [`BRIDGE.md`](../src/cmplx/transform/BRIDGE.md) for the contract.
- **Design refs:** Standalone_Geometric_Transformer.docx full spec.

## Slot 49 — forge

- **Canonical name:** Dependency Forge (in-house PEP 503/508/517/691/427/376/440)
- **Aliases:** forge, mcp_deps_*, in-house package builder, no PyPI dep
- **Status:** ○ not-built
- **Design refs:** gpt design idea §Forge spec.

## Slot 50 — zk-snark-proofs

- **Canonical name:** zk-SNARK Chamber Membership Proofs
- **Aliases:** zksnark, Groth16, chamber proofs
- **Status:** ○ not-built
- **Design refs:** CMPLX2 Implementation Extension §12.6.

## Slot 51 — k8s-crds

- **Canonical name:** Kubernetes Custom Resource Definitions
- **Aliases:** k8s, GeometricAgent, WeylChamber, CQERoute
- **Status:** ○ not-built
- **Design refs:** CMPLX2 Implementation Extension §12.5.2.

---

# Frame governance

## Adding a slot

A new slot is proposed via a `BIRTH` receipt on the frame Morphon itself with payload `{slot_id, canonical_name, port?, interface_path, depends_on[]}`. The proposal must justify why no existing slot covers the new piece (i.e., name + contract + receipt grammar are all distinct from any existing slot). If accepted, this document is updated and the version increments.

## Splitting a slot

If an existing slot turns out to cover two genuinely distinct things (the way "receipts" originally covered both token receipts and system receipts), it is split via a `GATE` deprecation of the original plus two `BIRTH` events for the successor slots. The original slot becomes a deprecation marker pointing at the successors. All existing merge receipts remain valid; their target slot is rewritten in the receipt index by adapter rules.

## Versioning

This document is versioned. Every accepted slot change increments minor version. Every restructuring (layer reordering, dependency-graph change) increments major version. The current version is encoded in the frame Morphon's `state` field and appears in every merge receipt's payload.

## Conflict resolution

When the four source priorities disagree:

1. If in-place code's contract is **stronger** (has tests, is consumed by other slots), it wins regardless of design or prior-AI preference.
2. If in-place code is a stub or absent, design refs decide.
3. If design refs are silent or inconsistent across formalization documents, prior-AI canonical_records decide.
4. If all three are silent, the slot is marked `○ not-built` and the contract is open.

Conflicts are recorded as notes on the slot, not silently resolved. Every conflict is an opportunity for the slot's contract to be sharpened.

## The frame is itself a Morphon

This document encodes a Morphon whose payload is `{slots: [...], version: "1.0", parent: null}`. Its `quad_encoding`, `parity_channels`, `sacred_frequency`, `digital_root`, `fractal_coordinate` are computed from the hash of the slot list. Every merge receipt's chain is rooted in this Morphon. The frame can be queried, replayed, and forked like any other Morphon. When the frame is forked (to try a different decomposition), both forks remain valid Morphons until one is gated-out by a `DEATH` receipt explaining why the other won.

That self-similarity is the point: the frame uses the system to organize the system, and any agent that understands the receipt grammar can read, propose against, and improve the frame using the same machinery they would use for any other Morphon operation.

---

**End of v1 frame. Merge proposals open.**
