# Prior Document: Six-Stage Substrate Pipeline (Reference)

## What it is

The substrate's running pipeline implements a six-stage information-flow architecture that pre-dates and frames the lattice-forge build:

```
SUBMIT → EVALUATE (TarPit) → MEASURE (MORSR 240-pulse)
       → GOVERN (SAP Triad) → PLACE (MDHG/AGRM → 24D Leech)
       → RECEIPT (SpeedLight, 7/8 closure)
```

## The stages

### 1. SUBMIT
Raw data enters the pipeline. For Rule 30: the canonical center column from a single-seed initial condition.

### 2. EVALUATE — TarPit
The TarPit (Encoded Tarpit Program, ETP) is the substrate's evaluator. It atomizes content into universal-IR atoms using the canonical encoding rules. For Rule 30: the chart's local state at each depth becomes an atom.

The TarPit service runs at `tarpit-api:8844` in the substrate's docker deployment.

### 3. MEASURE — MORSR (240-pulse)
MORSR (Mutual Orbital Resonance State Reconstruction) is the substrate's measurement engine. It performs 240 diagnostic ripple/sub-ripple pulses to characterize the atom's behavior in the chart.

The 240 is not arbitrary: it matches the number of minimal vectors in the E₈ root system (240 roots at norm² = 2). Each pulse probes one E₈ root direction.

The MORSR service runs at `mmdb-unified:8824` and exposes Klein j-invariant + McKay-Thompson series endpoints (Monstrous Moonshine machinery).

### 4. GOVERN — SAP Triad
SAP = Substrate Admissibility Profile. The triad checks:
- (a) Internal closure (Θ ≤ 0 per NSL accounting)
- (b) Lattice admissibility (commutability with seed DB edges)
- (c) Information preservation (no Shannon residue)

If all three pass, the measured state is admissible. If any fail, the state is flagged for review (e.g., PROJECTION_LOSS or RESIDUE_UNACCOUNTED).

### 5. PLACE — MDHG / AGRM
MDHG (Multi-Dimensional Hierarchical Graph) places the atom into the substrate's hierarchical structure:

```
grain → dust → triad → block → cluster → domain → region → planet → universe
```

AGRM (Adaptive Geometric Routing Map) routes the placement to the appropriate 24D terminal lattice (one of the 24 Niemeier forms, including Leech as rootless).

The MDHG service runs at `mdhg-unified:8825`.

### 6. RECEIPT — SpeedLight (7/8 closure)
SpeedLight issues a signed receipt for the placement, with full lineage. The "7/8 closure" refers to the receipt's coverage of 7 of 8 substrate-grade closure properties (the 8th being external verification / human audit).

The SpeedLight service runs at `speedlight-api:8843`.

## How this relates to the submission

The submission's chart-J₃(𝕆) isomorphism is registered through this pipeline:

1. **SUBMIT**: Rule 30's chart (8 local states + 4096-depth trace).
2. **EVALUATE**: TarPit atomization (each depth's chart state is an atom).
3. **MEASURE**: MORSR pulse against E₈ root directions (the 240-pulse diagnostic).
4. **GOVERN**: SAP triad — internal closure (Θ = 0), lattice admissibility (F₄ commutes), information preservation (bijection verified).
5. **PLACE**: MDHG places at the F₄ chart-level node, with routing to Niemeier:E8^3 via the canonical path F₄ → G₂×F₄ → E₈ → Niemeier:E8^3.
6. **RECEIPT**: SpeedLight issues a signed receipt for the registered morphon (Move 2 in the conversation: speedlight receipt `bcb4c0d7ad96faae`).

The pipeline produces a substrate-grade record that the chart was registered, the closure validated, and the lineage signed.

## Why this matters for the submission

The submission's proof content (T1-T8) is independent of the pipeline. The pipeline provides:
1. **A way to register Rule 30 as a first-class morphon** with substrate-grade receipts.
2. **A bridge to the 24D terminal lattices** (the Niemeier classification).
3. **A coordinate for further work** — once registered, Rule 30 can be queried, evolved, and composed with other registered morphons via the pipeline.

For the prize submission, the pipeline registration is **infrastructure**, not proof. The proofs stand on T1-T8.

## Reference for substrate operators

The substrate pipeline operates as docker services in the author's running deployment. For an external reviewer, the pipeline is documented as a reference architecture but is not required to run the submission's proofs.

To exercise the pipeline:
- Install Docker with sufficient memory.
- Pull the substrate's containers (tarpit-api, mmdb-unified, mdhg-unified, speedlight-api).
- Register a chart via tarpit `/process` endpoint with `use_mmdb=true, use_mdhg=true, write_receipts=true`.
- Retrieve the receipt's lineage via speedlight `/lineage/{subject}` endpoint.

These steps are documented in the author's working notes and are not required for the prize submission. The submission's proofs run on the standalone executable build (Zip 2).

## Honest scope

The six-stage pipeline is part of the author's substrate framework, in production-grade development. For the prize submission, it serves as:
1. Context for where Rule 30 sits in the substrate.
2. Evidence that the framework has running infrastructure beyond Rule 30.
3. A path forward for registering additional native-state spaces (per Open Obligation O3 universality).

It is not load-bearing for the submission's proofs and is mentioned for completeness only.
