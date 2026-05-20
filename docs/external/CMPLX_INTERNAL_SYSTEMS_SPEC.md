# CMPLX Internal Systems Specification

**Version:** 2.1.0 — Companion to Morphonic System Spec 2.0.0
**Date:** March 14, 2026
**Scope:** Every subsystem, its precise role, its data structures, its contracts, and its Docker deployment

---

## 0. The Three Pillars

Every datum in CMPLX touches exactly three persistence systems. They are not interchangeable. Each holds a different aspect of the datum's identity.

```
MMDB  = WHERE the datum IS        (storage — the body)
MDHG  = WHERE the datum FITS      (memory  — the address)
SpeedLight = WHAT the datum DID   (receipts — the history)
```

A datum without an MMDB record doesn't exist. A datum without an MDHG address can't be found. A datum without a SpeedLight receipt can't be trusted. All three must be present for a datum to be fully alive in the system.

---

## 1. MMDB — The Storage Layer (Body)

### 1.1 What MMDB Is

MMDB (Morphonic Memory DataBase) is content-addressed persistent storage. It holds the actual bytes — the raw data, the embeddings, the computed results. It does NOT hold addresses, labels, or history. Those belong to MDHG and SpeedLight respectively.

### 1.2 Data Model

```
MMDB Record:
  content_hash: SHA-256(canonical_bytes)     ← primary key
  corpus_id:    which corpus this belongs to
  source_id:    which source within the corpus
  chunk_id:     which chunk within the source
  content:      the actual bytes
  embedding:    768D vector (from CMPLXEmbedder)
  e8_projection: 8D vector (E8 snap of embedding)
  digital_root: DR(e8_projection) ∈ {1..9}
  terms:        extracted tokens [{term, position}]
  metadata:     arbitrary JSON
  created_at:   timestamp
```

### 1.3 The Base-4 Encoding

All MMDB content is internally representable in Base-4 (Z₄). This is the "lingua franca" from the formalizations:

```
Base-4 value   Binary pair   DNA base   E8 half-integer
    0            00            A           +½,+½
    1            01            C           +½,-½
    2            11            G           -½,-½
    3            10            T           -½,+½
```

The Gray map (0→00, 1→01, 2→11, 3→10) preserves Hamming distance — adjacent Z₄ values map to binary pairs that differ in exactly one bit. This means MMDB content, DNA sequences, and E8 half-integer roots all live in the same algebraic structure. The quadratic invariant is preserved under the Gray map:

```
L_CL(E_B4(D)) ≡ D  and  I(Q(D)) = I(Q(L_CL(E_B4(D))))
```

Encode to Base-4, decode from Base-4, get the exact original, with the same quadratic form.

### 1.4 Storage Backend

```
SQLite:  metadata, corpus/source/chunk tables, term index
Filesystem: actual content blobs (content-addressed by hash)
LatticeBank: pre-allocated R⁸ vectors for hot projections (capacity 4096)
```

### 1.5 MMDB Operations

```
import_chunks(source_id, chunks)  → stores chunks, generates content_hashes
import_terms(mappings)            → indexes terms with positions
search(term, limit)               → returns matching chunks by term overlap
embed(content)                    → 768D embedding + 8D E8 projection + DR
lattice_place_hash(hash, "E8")    → content-addressed E8 coordinate
lattice_place_hash(hash, "LEECH24") → content-addressed Leech coordinate
```

### 1.6 Docker Deployment

MMDB runs as a single NanoClaw with role `StorageClaw`:
```yaml
mmdb-storage:
  image: cmplx/morphon:latest
  command: ["--role", "StorageClaw", "--db-path", "/data/mmdb.sqlite"]
  volumes:
    - mmdb-data:/data
  deploy:
    resources:
      limits: { cpus: '1.0', memory: 1G }
```

---

## 2. MDHG — The Memory Layer (Address)

### 2.1 What MDHG Is

MDHG (Multi-Dimensional Hierarchical Geometry) is a geometric cache that assigns addresses to data based on where the data naturally fits in lattice space. It does NOT store the data itself (that's MMDB) or the data's history (that's SpeedLight). It stores the data's position.

### 2.2 The Address Space

An MDHG address is a 10-level hierarchical path derived from the datum's receipt chain:

```
atom / room / floor / building / city / planet / velocity / dimension / lattice / universe
```

Levels 1-6 are spatial (where in the hierarchy). Level 7 is temporal (how fast it changes). Levels 8-10 are structural (which lattice, which coordinates, which universe).

### 2.3 Three Timescales

```
FAST:  Working set. High eviction rate. LRU within Voronoi cells.
       Size: ~1000 items. Access: <1ms. Eviction: seconds.

MED:   Recent history. Moderate eviction.
       Size: ~10,000 items. Access: <10ms. Eviction: minutes.

SLOW:  Accumulated identity. Minimal eviction.
       Size: ~1,000,000 items. Access: <100ms. Eviction: overnight audit only.
```

Promotion: FAST → MED when access count exceeds threshold. MED → SLOW when item persists through 3 audit cycles.
Demotion: SLOW → MED when staleness exceeds threshold. MED → FAST eviction when pressure is high.

### 2.4 The Golden Ratio Hash Table (AGRMMDHG)

The internal structure of each MDHG level is the MDHGHashTable from `agrmmdhg.py` (2,557 lines):

```
Building count = ⌊log_φ(capacity)⌋
Each building contains:
  velocity_region:  size = base / φ²     (FAST tier)
  dimensional_core: size = velocity × φ   (MED/SLOW tier)
  conflict_structures: Hamiltonian path collision resolution

Collision resolution:
  When two items hash to the same slot, find the optimal
  Hamiltonian path through the conflict graph — the same
  algorithm as superpermutation search applied to hash collisions.

Co-access tracking:
  Maintains co-access matrix tracking which keys are accessed together.
  Periodic optimization relocates frequently co-accessed items to
  adjacent slots, improving cache locality.
```

### 2.5 24D Quantization

For the Leech-scale MDHG:
```
24D Leech vector → quantize to grid (grid_size × grid_size)
→ hash to 2D slot → per-slot eviction cache
```

### 2.6 MDHG Operations

```
put(level, chunk_id, embedding_24d, payload)  → quantize + hash + place
get(level, chunk_id)                          → retrieve by ID
query_nearest(level, coords_24d, k)           → k-nearest in Leech space
admit_crystal(crystal_id, vector_24d, meta)   → Planet-level admission
promote(item, from_level, to_level)           → tier promotion
evict(level, count)                           → LRU eviction
coverage_report()                             → density per Voronoi cell
```

### 2.7 Docker Deployment

MDHG runs inside each manifold as the geometric cache. The StorageClaw holds SLOW tier. Each manifold holds its own FAST and MED tiers:
```yaml
# Inside each manifold container:
environment:
  MDHG_FAST_CAPACITY: "1000"
  MDHG_MED_CAPACITY: "10000"
  MDHG_DIMENSIONS: "24"
  MDHG_GRID_SIZE: "12"
```

---

## 3. SpeedLight — The Receipt Layer (History)

### 3.1 What SpeedLight Is

SpeedLight is two things: an idempotent computation cache AND a receipt chain. The cache prevents redundant work. The chain proves what work was done. They share a key: the content hash of the computation.

### 3.2 The Three-Tier Cache

```
Tier 1 (Memory): Dict[content_hash → result]. O(1) lookup.
                  LRU eviction. Volatile — lost on restart.

Tier 2 (Disk):   JSONL ledger of all operations.
                  Persistent — survives restart.
                  Append-only — never modified.

Tier 3 (Compute): The actual computation function.
                   Called only when tiers 1 and 2 miss.
```

The SpeedLight sidecar envelope for each computation:
```
{
  task_hash:   SHA-256(canonical_input),
  geo_state: {
    embedding: [768D vector],
    e8_snap:   [8D vector],
  },
  emergence: {
    flags:      [list of detected patterns],
    confidence: float,
    delta_phi:  float (conservation residual),
  },
  receipt: {
    prev_hash:  SHA-256(previous receipt),
    hmac:       HMAC-SHA256(key, receipt_body),
    type:       one of {event, observation, shadow_beam, shadow_regret,
                        debt_repay, drift, instruments, sidecar_receipt},
    timestamp:  ISO-8601,
  }
}
```

### 3.3 The SpeedLight Pipeline

Every computation passes through:
```
GeoTokenize → GeoTransform → Emergence Detection → Chained Audit
```

GeoTokenize: convert input to geometric tokens (E8 coordinates).
GeoTransform: apply the computation in geometric space.
Emergence Detection: check for novel patterns (flags).
Chained Audit: append hash-chained receipt with delta_phi.

### 3.4 Receipt Types

```
event:           Primary execution receipt. The standard type.
observation:     Measurement receipt from CA observation.
shadow_beam:     Counterfactual: what WOULD have happened under different governance.
shadow_regret:   Rejected alternative: what was considered and explicitly declined.
debt_repay:      Resource reconciliation receipt.
drift:           State correction receipt (detected deviation from expected).
instruments:     Monitoring measurement (critical slowing, volatility, risk).
sidecar_receipt: Cached computation reuse receipt.
```

### 3.5 Receipt Chain Integrity

```
Each receipt includes:
  receipt_id:      UUID
  timestamp:       float (time.time())
  controller_id:   which controller emitted it
  controller_name: human-readable name
  tier:            which controller tier (ATOM..MASTER)
  operation:       what was done
  inputs_hash:     SHA-256(inputs)
  outputs_hash:    SHA-256(outputs)
  prev_hash:       SHA-256(previous receipt)
  delta_phi:       conservation residual for this operation
  metadata:        arbitrary JSON

Chain verification: walk from first to last, verify each prev_hash.
Conservation audit: sum all delta_phi, verify ≤ 0.
HMAC verification: recompute HMAC for each receipt, verify match.
```

### 3.6 The Receipt Causal DAG

The receipt chain is also a causal DAG. `receipt_causal_dag.py` converts the linear chain into a graph where:
- Nodes = receipts
- Edges = causal dependencies (one receipt caused another)
- Weights = delta_phi contribution

MORSR applied to the meta-DAG optimizes future controller ordering by analyzing which paths through the DAG produced the best outcomes. The system studies its own execution history to improve.

### 3.7 Docker Deployment

SpeedLight runs as a sidecar in every manifold AND as a dedicated ReceiptClaw:
```yaml
# Sidecar inside each manifold:
environment:
  SPEEDLIGHT_LANGUAGE: "base100"
  SPEEDLIGHT_CACHE_SIZE: "10000"

# Dedicated chain manager:
nanoclaw-receipt:
  image: cmplx/morphon:latest
  command: ["--role", "ReceiptClaw", "--chain", "/data/receipts"]
  volumes:
    - receipt-chain:/data/receipts
```

---

## 4. The Contract Layer

### 4.1 What a Contract Is

A contract in CMPLX is a function decorated with `@receipt_wrapper` that:
1. Takes inputs
2. Hashes them (inputs_hash)
3. Executes a computation
4. Hashes the outputs (outputs_hash)
5. Computes delta_phi (conservation residual)
6. Emits a receipt with both hashes and delta_phi
7. Returns the outputs

The receipt is the proof that the contract executed. The delta_phi is the proof that conservation held. The hash chain links this contract to every contract before it.

### 4.2 The Six Quality Gates (Falsifiers F1-F6)

Every submission must pass all six. No override. No exception.

```
F1  Type Validation:      Structural integrity of the submission.
                          Is the data well-formed? Are required fields present?
                          Contract: type_check(datum) → bool

F2  Conservation Law:     ΔΦ ≤ 0 across the operation.
                          The delta_phi_decorator enforces:
                            GateResult(ok = (newJ ≤ prevJ + 1e-12))
                          Contract: delta_phi_check(pre_state, post_state) → GateResult

F3  Lattice Snap:         Valid E8 projection exists.
                          snap(v) = argmin_{α ∈ Λ_E8} ||v - α||²
                          Deviation from nearest lattice point < threshold.
                          Contract: e8_snap_verify(vector) → (snapped, deviation)

F4  Receipt Chain:        Provenance is intact and signed.
                          prev_hash matches, HMAC verifies, no gaps.
                          Contract: chain_verify(receipt, chain) → bool

F5  Semantic Coherence:   Content is internally consistent.
                          Embedding similarity between chunks > threshold.
                          Contract: coherence_check(datum, neighbors) → float

F6  MDHG Address:         Valid placement exists in the hierarchy.
                          The datum can be quantized to a Leech cell.
                          At least one Voronoi cell accepts it.
                          Contract: mdhg_place_verify(coords, level) → bool
```

### 4.3 The delta_phi_decorator

The atomic conservation gate:
```python
@delta_phi_decorator
def any_operation(inputs):
    # Compute pre-state energy J_pre
    # Execute operation
    # Compute post-state energy J_post
    # If J_post > J_pre + 1e-12: ESCROW (don't commit, but receipt it)
    # If J_post ≤ J_pre + 1e-12: COMMIT
    return outputs
```

Escrowed items are NOT destroyed. They remain in the receipt chain as failed attempts (receipt type: shadow_regret). Conservation is maintained because the information that the attempt was made is preserved.

### 4.4 The BRM Step Contract

The master routing contract from the formalizations:
```python
def brm_step(state):
    candidates = intersect_4tuple_lanes_E8(state)   # 4-calculi intersection
    scored = []
    for r in candidates:
        s2, s5 = sigma_p_primary(awb, r, p_list=[2,5])  # Hex+Quin alignment
        synd16, synd5 = code_syndromes(r)                 # Golay/Hamming check
        if synd16 or synd5: continue                       # Reject off-lattice
        cost = deltaS_need(r) - (I_struct(r) + bmin*B_saved(r)) + l2*s2 + l5*s5
        scored.append((cost, r))
    r_hat = tie_break_by_QML(min(scored))                  # φ-probe tiebreak
    emit_with_CRT8(r_hat)                                  # CRT receipt emission
```

### 4.5 The BRS Check Contract

The 7-condition system health exam:
```python
def brs_check(awb_log, hodge_log, crt_log, udms_log, alena_log):
    D_needed = rank_J + d_CRT + d_duplex + d_anchors - d_redundant(awb_log)
    return all([
        D_embed == D_needed,                      # Dimensional match
        D_audit == audit_mult * D_embed,          # Audit proportional
        is_pointwise_min_NF(awb_log),             # AWB at normal form
        is_min_coexact(hodge_log),                # Hodge minimally coexact
        escrow_equal(udms_log),                   # Duplex escrow balanced
        crt_log.defects == 0,                     # CRT zero errors
        all_zero_syndrome(alena_log),             # ALENA zero syndrome
    ])
```

---

## 5. The TarPit — Evaluation Engine

### 5.1 What the TarPit Is

The TarPit is a Turing-complete evaluator. It accepts any computable function and determines what it does, without judgment. Judgment is deferred to GOVERN.

### 5.2 Sandbox Types

```
MDHG:       Sandboxed with geometric addressing constraints.
MMDB:       Sandboxed with storage access constraints.
THINKTANK:  Sandboxed with multi-agent deliberation constraints.
```

### 5.3 TarPit Operations

```
evaluate(submission) → {output, trace, intermediate_states}
```

The trace records every intermediate state. This is the raw material for the CA measurement — the CA observes the trace, not the output.

### 5.4 In the Morphonic Architecture

The TarPit is Pipeline Stage 2 (EVALUATE). In the eversion network, it is the self-intersection detection — the TarPit determines WHERE the Morphon surface crosses itself during eversion. Those crossings are the computation.

---

## 6. GNLC — The Geometry-Native Lambda Calculus

### 6.1 The Four Lambda Calculi

```
λ₁ (Structure):  Defines relationships between atoms via tensors and braids.
                  This is the geometric rail — determines topology.
                  β-reduction = lossless geometric transformation preserving
                  the Bregman distance defined by the 0.03 metric.

λ₂ (State):      Manages temporal dynamics and transitions.
                  Governed by the 0.03 metric and toroidal closure.
                  This is the temporal rail — tracks eversion phase.

λ₃ (Composition): Handles interaction of complex objects.
                   This is the interaction rail — determines self-intersections.

λ_θ (Meta):       Self-modification, schema evolution, meta-governance.
                   Operates on the Leech lattice itself (not within a single E8 rail).
                   This is the manifold graph layer — λ_θ operates on the graph,
                   not within any single manifold.
```

### 6.2 GNLC β-Reduction

β-reduction in GNLC is a geometric operation on the E8 lattice:
```
(λx.M) N → M[x := N]

In E8 terms:
  λx is a direction in root space
  M is a surface in that direction
  N is a specific point
  M[x := N] is the surface evaluated at that point
  The operation preserves the Bregman distance defined by 0.03
```

This is proven lossless: the quadratic invariant before and after β-reduction is identical.

### 6.3 The Morphon Layer (SNAP Layer 8)

The Morphon layer in the 10-layer SNAP composition holds:
```
lambda_form:              the GNLC expression
reduction_rules:          which of the 8 E8 rules apply to this Morphon's topology
normal_form_convergence:  whether the expression has a normal form (halts)
```

Layer 10 (ALL LAMBDA FORMS) holds M₀, the Universal Morphon — the master lambda expression that contains all possible Morphon shapes.

---

## 7. The 24 CA Panels — Observation System

### 7.1 What the 24 Panels Are

Each of the 24 Niemeier lattice classifications provides a different projection of the same underlying state. The 24 CA panels display the CA's cell state projected through each of the 24 even unimodular lattices in 24D:

```
Panel 1:  D24        — single large root system, maximal symmetry
Panel 2:  D16⊕E8     — two-component, asymmetric
Panel 3:  E8³        — three independent E8s (the Leech construction)
...
Panel 23: A1²⁴       — 24 independent rank-1 components, minimal symmetry
Panel 24: Leech       — no roots, unique, maximum kissing number
```

### 7.2 The Observation Function

The CA observation function is a nonlinear wavelength-to-RGB-to-hex mapping:
```
state → wavelength (370-780nm based on cell value)
      → RGB (physical wavelength to RGB conversion)
      → hex (6-character string)
```

This amplifies small state deviations that would be invisible in raw numerical comparison. A contract that slightly violates conservation produces a color shift detectable before the numerical violation reaches threshold.

### 7.3 Wolfram Rule Assignment

Each CA cell gets a Wolfram class based on:
```
role × operation × ideology × emergency → (class, kernel, parameters)

Classes:
  I  (relax):    dampens deviations. Stabilizing.
  II (oscillate): cycles deviations. Periodic.
  III (amplify):  grows deviations. Signal propagation.
  IV (complex):   emergent behavior. Edge of chaos.

Kernels: relax, oscillate, amplify, complex
Parameters: diffuse, noise, inertia, amp, nonlin (per ideology)
```

### 7.4 In the Morphonic Architecture

The 24 panels are the 24 CRT channels. Each panel is one channel of the CRT 24-Ring Cycle. The CRT guarantees that the 24 independent projections can reconstruct the full state exactly. The panels are not for visualization — they are the measurement apparatus.

---

## 8. The Glyph System — Symbolic Compression

### 8.1 What a Glyph Is

A glyph is a triad|inverse compression of text:
```
Input:  "the quick brown fox jumps over the lazy dog"
Triad:  "the quick brown"        (first 3 words)
Inverse: "dog lazy the"           (last 3 words, reversed)
Glyph:  "the quick brown|dog lazy the"
```

### 8.2 The Glyph as Morphon Skin

The triad is the outer face of the Morphon — what it presents to the world. The inverse is the inner face — what the eversion reveals. The `|` separator is the equator — the Morin surface. The glyph IS the Morphon in its most compressed form.

### 8.3 Glyph Operations

```
compress_to_glyph(text, level) → glyph_string
  level 1-10: compression depth (higher = more aggressive)
  Stores in self.glyphs[text[:10]] for lookup and audit

text_to_vector(glyph) → 128D vector
  Hash-based embedding normalized to unit ball
  Used for MMDB storage and MDHG placement
```

### 8.4 The ShellingCompressor

Extends glyphs with Cartan path representation — the glyph encodes not just the content but the path through E8 root space that produced it. The shelling is the order in which E8 roots are visited during compression.

---

## 9. HyperPermutations and HyperTowers

### 9.1 What a HyperTower Is

An NHyperTower is a hierarchical structure where each level contains all permutations of the previous level, connected by de Bruijn-like sequences:

```
Level 0: base tokens (e.g., 5 symbols: a,b,c,d,e)
Level 1: all permutations of 5 symbols (120 permutations)
Level 2: superpermutation of level 1 (minimal string containing all)
Level N: superpermutation of level N-1
```

### 9.2 The Connection to MDHG

Each HyperTower level IS one MDHG scale:
```
Level 0 = atom      (individual tokens)
Level 1 = room      (all arrangements of tokens)
Level 2 = floor     (minimal traversal of all arrangements)
Level 3 = building  (traversal of traversals)
...
```

The HyperTower is the MDHG hierarchy expressed as a superpermutation stack.

### 9.3 Lambda Operator Honor

Each token in the tower is validated by digital root parity:
```python
def lambda_operator_honor(self, token: str) -> bool:
    dr = sum(ord(c) for c in token) % 9 or 9
    return dr in self.projection_channels  # [3, 6, 9]
```

Only tokens with DR in {3, 6, 9} are "honored" — they participate in the tower structure. Other tokens are transformative (processing) but don't define the tower's skeleton.

### 9.4 Tower Journals

Each HyperTower has a journal (SNAP Layer 5) that records:
```
events:              what happened at each tower level
state_changes:       transitions between levels
observation_history: CA measurements at each level
```

The journal IS the temporal dimension of the tower. The tower is the spatial structure. The journal is how it evolved over time.

---

## 10. Atlas — Canonicalization Engine

### 10.1 What Atlas Does

Atlas takes any expression and reduces it to canonical form:
```
Expression → alpha_rename → flatten(associative) → sort(commutative)
           → const_fold → SNAP key (SHA-256 of canonical tuple)
```

Two expressions with the same SNAP key are structurally equivalent.

### 10.2 Atlas in the Morphonic Architecture

Atlas finds the Morin surface. The SNAP key IS the Morin surface identifier — the halfway state of eversion where inside and outside are maximally entangled. Two computations with the same SNAP key have the same Morin surface and therefore the same eversion path.

### 10.3 The N→L→A→E→CNF Operator Chain

The complete canonicalization from the formalizations:
```
N = partition Normalization  (flatten to standard form)
L = modular Legalization     (validate against base constraints)
A = Aperture                 (Taxicab/Cabtaxi witness check — 1729 redundancy)
E = Embedding                (E8 projection)
CNF = Canonical Normal Form  (SNAP key)

Property: After the full chain, the equivalence descriptor ℰ recovers
the initial state. The chain is reversible. N→L→A→E→CNF is lossless.
```

### 10.4 Family Bucketing

Beyond exact SNAP matching, Atlas groups expressions into families by replacing small constants with wildcards. Family hit rate (38.4%) is 5.1× raw hit rate (7.5%).

### 10.5 AOP32 Encoding

Transformation rules are encoded as 32-bit opcodes:
```
bits 0-7:   lane assignment
bits 8-15:  winding number
bits 16-23: mode (strict/relaxed)
bits 24-31: energy level
```

---

## 11. How All Systems Refine the Neural Network

The Morphonic Eversion Network from Spec 2.0.0 is refined by each subsystem:

```
Subsystem          NN Component It Refines           How
─────────────────────────────────────────────────────────────────
MMDB               Input embedding layer             Content-addressed lookup
                                                     before embedding
MDHG               Output placement head             Geometric address
                                                     prediction, not random
SpeedLight         Training data source              Receipt chain IS the
                                                     training corpus
F1-F6 Gates        Conservation constraint layer     Six hard gates, not one
                                                     soft loss term
TarPit             Evaluation stage in pipeline      NN doesn't evaluate —
                                                     TarPit does, NN learns
                                                     from TarPit traces
GNLC               Morphon topology classifier       Lambda normal form
                                                     determines genus
24 CA Panels       Measurement vocabulary            24 projections per item,
                                                     not one flat vector
Glyph System       Token embedding                   Triad|inverse as
                                                     bidirectional encoding
HyperTower         Scale-recursive training          Each tower level is
                                                     one training scale
Atlas              SNAP key as canonical target       NN predicts SNAP key,
                                                     not raw output
BRM Step           Routing decision model            NN learns the cost
                                                     function, not just labels
BRS Check          Validation head                   7 binary outputs
                                                     matching 7 BRS conditions
```

## 12. How All Systems Refine the Manifold Deployment

```
Subsystem          Manifold Component It Refines     How
─────────────────────────────────────────────────────────────────
MMDB               Per-hinge LatticeBank             Each hinge holds 4096
                                                     pre-projected vectors
MDHG               Per-manifold geometric cache      FAST/MED/SLOW tiers
                                                     inside each manifold
SpeedLight         Per-manifold sidecar              Idempotent cache +
                                                     receipt chain per node
Contracts          Inter-manifold edge protocol      Each edge traversal
                                                     is a contract execution
TarPit             Full-eval path computation        When gating fails,
                                                     TarPit evaluates
GNLC               Hinge activation language         Hinge deployment IS
                                                     lambda reduction
24 CA Panels       Manifold health monitoring        24 views of each
                                                     manifold's state
Glyph System       Manifold-to-manifold messaging    Glyphs compress inter-
                                                     manifold data transfer
Atlas              Edge braid word canonicalization   Atlas reduces braid
                                                     words to canonical form
BRS Check          NanoClaw validator fleet           7 NanoClaws, one per
                                                     BRS condition
```

## 13. How All Systems Refine SNAP

```
Subsystem          SNAP Component It Refines         How
─────────────────────────────────────────────────────────────────
MMDB               SNAP Layer 1 (Lattice)            E8 coords from content hash
                   SNAP Layer 2 (Vector)             768D embedding
MDHG               SNAP Layer 6 (Atlas location)     MDHG address
SpeedLight         SNAP Layer 9 (SpeedLight)         Causality chain + receipt
Contracts          All layers                        Every layer validated by
                                                     F1-F6 before SNAP creation
TarPit             SNAP Layer 7 (TarPit)             Sticky state + decay rate
GNLC               SNAP Layer 8 (Morphon)            Lambda form + reduction rules
                   SNAP Layer 10 (All Lambda Forms)  M₀ + MGLC + functors
24 CA Panels       SNAP Layer 3 (RAG)                Context links from CA
                                                     observation neighbors
Glyph System       SNAP Layer 4 (Glyph)              Visual hash + symbol encoding
HyperTower         SNAP Layer 5 (Journal)            Event log + state changes
Atlas              SNAP naming convention            SNAPXXX-family.morphon.atom.variant-[hash]
                                                     derived from Atlas canonicalization
```

---

## 14. The Complete Data Flow

A single submission flowing through the entire system:

```
1. USER SUBMITS raw data to gateway manifold

2. DOMAIN ADAPTER converts raw → 3-rail E8 features
   (α=primary, β=secondary, γ=temporal)

3. ATLAS CANONICALIZATION reduces input to canonical form
   N→L→A→E→CNF produces SNAP key

4. SPEEDLIGHT checks cache (content_hash lookup)
   HIT → return cached result + sidecar_receipt
   MISS → continue

5. MMDB stores the raw content
   content_hash, embedding, e8_projection, terms

6. GLYPH COMPRESSOR produces triad|inverse symbolic encoding
   Stores in SNAP Layer 4

7. DR ROUTER classifies: DR=3 (creative), DR=6 (expansion),
   DR=9 (consolidation), other (transformative)

8. SNAP LABELER assigns 5-dimensional labels
   (structural, semantic, quality, risk, domain)

9. PERCOLATION INDEX checks label density in Leech neighborhood

10. CA GATE checks Wolfram class of the MDHG cell
    Class I (relax) → gate aggressively
    Class IV (complex) → full eval always

11. IF GATED:
    Neighbor consensus from SNAP-labeled items
    MDHG placement from quick Leech projection
    Receipt: type=event, path=gated
    Register in percolation index (densifies coverage)

12. IF NOT GATED:
    a. MORSR explores sparse neighborhood
       Pattern selected by DR lane (spiral/cascade/ripple/chaos)

    b. TARPIT evaluates the submission
       Sandbox type determined by domain
       Trace recorded for all intermediate states

    c. CA MEASURES the residue
       24 panels project through 24 Niemeier lattices
       Wolfram rules propagate disturbances
       Observation function amplifies small deviations

    d. GOVERNANCE runs competing strategies
       4 ideologies (utopia/socdem/libcon/weird) evaluate
       PolicyOrchestrator runs 4 strategies (conservative/aggressive/balanced/exploratory)
       F1-F6 quality gates enforce (all must pass)
       delta_phi_decorator checks conservation
       BRS check verifies 7 conditions

    e. HYPERTOWER builds the scale hierarchy
       Current submission placed in tower at appropriate level
       Journal records the event

    f. MDHG PLACES the submission
       24D Leech quantization → slot → cache tier
       Hamiltonian path navigation for collision resolution
       Golden ratio building partitioning

    g. SNAP COMPOSITION creates complete 10-layer record
       All 10 layers populated from pipeline results

    h. SPEEDLIGHT records the computation
       GeoTokenize → GeoTransform → Emergence → Receipt
       Content hash → cache entry for future reuse

    i. RECEIPT CAUSAL DAG learns from the path taken
       Records quality score for this pipeline path
       Updates routing weights for future submissions

13. RESULT returned to user with:
    item_key, path taken, SNAP depth, Leech coordinates,
    gate info (if gated), manifold status (if full eval),
    observables, repairs applied, receipt hash

14. PERIODICALLY:
    Conservation auditor walks full chain
    Verifies cumulative ΔΦ ≤ 0
    Flags any violation with specific receipt index
```

---

*Every subsystem is an instance of the six-stage pipeline. Every data structure is a projection of the same geometric object through different lattice bases. Every contract enforces the same conservation law. Every receipt chain grows the same coverage that makes the next operation faster.*

*This is one machine. These are its organs.*
