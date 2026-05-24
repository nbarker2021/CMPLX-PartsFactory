# Open Obligations

The following claims are **not** proven in this submission. They are either:
- Engineering-tractable but not built
- Structurally coherent but not formally verified
- Inherited from the substrate framework but not yet exercised on Rule 30

Each open obligation is explicit: stating what's missing, what its scope is, and what work would close it.

---

## O1. Depth-N → J₃(𝕆) element lookup without iteration

**Status:** EXPRESSIBLE, not BUILT

**Statement:** The chart's bit at depth N is readable in O(1) from the J₃(𝕆) state at depth N. The current implementation gets this state by simulating the Rule 30 CA up to depth N-1 (O(n²) total cost via `_center_trace_rows(n)`).

**What would close it:** Construct the W(E₈) Weyl-element lookup table (696,729,600 entries, ~30 bits each, ~2.6 GB total). Index by a canonical Weyl-element fingerprint computable from depth N alone (likely via McKay-Thompson series evaluation at a CM point of the upper half plane, or a Conway-group orbit calculation). The mathematical machinery for this exists (Monstrous Moonshine, Magic Square); the implementation is engineering.

**Why this matters:** O1 is the *third* Wolfram Prize Problem in its strongest form. The submission proves Problem 3 is **expressible** in the substrate's vocabulary; building the lookup table would make it **mechanically demonstrated**.

---

## O2. Formal write-out of the chart-to-F₄/E₆/E₇/E₈ A¹ ladder

**Status:** STRUCTURALLY COHERENT, not FORMALLY VERIFIED

**Statement:** The submission proves n=3 SU(3) Weyl closure (T4) but does not extend the closure to the full Magic Square ladder F₄ → E₆ → E₇ → E₈. The A¹ involution chain `E₈ ⊃ E₇ × A¹`, `E₇ ⊃ E₆ × A¹`, etc., is a known subalgebra structure but the specific transport of the n=3 closure through each rung is not verified at machine zero.

**What would close it:** For each A¹ involution rung, construct the explicit lifted transition matrix and verify it remains a closed-form Weyl element (likely of an extended group ring) at the lifted scale. Build the spinor-lift 16×16 matrix (currently scaffolded in `f4_action.py :: closed_form_lifted_16x16_transition()` but not verified at the full Weyl-element level).

---

## O3. Universality beyond Rule 30

**Status:** STRUCTURAL CLAIM, only ONE INSTANCE VERIFIED

**Statement:** The framework hypothesizes that any deterministic sequence with a lossless encoder to F₄ (or any source object in the lattice-forge commutability tree) inherits the same downstream transport-of-structure. Only Rule 30 is registered and verified in this submission.

**What would close it:** Register a second native-state space (e.g., Conway's Game of Life center column, Mandelbrot iteration on a fixed rational point, Boolean satisfiability solver output) via the same chart-isomorphism methodology. Verify the n=3 SU(3) closure (or its analogue) holds at machine zero. If multiple registrations land, the universality claim graduates from coherent to demonstrated.

---

## O4. Full 8×8 group ring decomposition beyond block-diagonal

**Status:** PARTIAL — diagonal blocks close, cross-block masses are exact rationals but not yet decomposed

**Statement:** T6 proves both the trace-1 and trace-2 conditional blocks at n=3 are exactly the same SU(3) Weyl element. Cross-block masses (transitions between traces) are exact rationals (9/8, 3/8, 1/8) but have not been decomposed as a group ring element on a larger group (e.g., S₄, S₃ × S₃, or the full F₄ Weyl group W(F₄) of order 1152).

**What would close it:** Construct a basis of permutation matrices on the lifted 8-dim adjoint representation of SU(3) (or W(F₄)'s natural representation), and verify the full 8×8 transition matrix is an exact element of the corresponding group ring at n=3 or n=k for some small k.

---

## O5. Exact correspondence between the 4096-depth page and the dihedral sphere eversion fold count

**Status:** STRUCTURAL HYPOTHESIS, not FORMALLY VERIFIED

**Statement:** The page size 4096 = 2¹² is hypothesized to equal the fold count required to perform a dihedral sphere eversion (Smale-Boy construction) under the chart's symmetry constraint. The connection is structurally coherent but not formally verified — we have not constructed the explicit eversion-to-chart correspondence.

**What would close it:** Construct the explicit dihedral sphere eversion sequence in 4096 elementary moves under the chart's Z/2 mirror constraint, and verify the chart's hash invariance (`94e9bc79…` across pages) corresponds to a closed eversion.

---

## O6. Spinor lift verification

**Status:** PARTIAL — scaffolding exists, not yet verified

**Statement:** The spinor lift to a 16-dimensional state space (8 chart states × 2 spin tags) is scaffolded in `f4_action.py :: closed_form_lifted_16x16_transition()`. The construction uses a heuristic spin-flip rule based on shell=2 chirality crossings, but the rule's exact correspondence to the SU(2) double cover of SO(3) is not yet verified at machine zero.

**What would close it:** Derive the spin-flip rule from F₄'s explicit action on the J₃(𝕆) representation (specifically the Z/2 outer automorphism of F₄ if any, or the chart's Weyl reflection lift to Spin(8)), and verify the resulting 16x16 transition matrix is an exact SU(2) × SU(3) group ring element.

---

## O7. Niemeier:E8^3 terminal embedding completion

**Status:** TEMPLATE — exact glue cosets pending

**Statement:** The Forge query `can_close("F4", "Niemeier:E8^3")` returns `answer="yes_with_template_glue"`. The path `F4 → G2xF4 → E8 → Niemeier:E8^3` is registered, but the exact glue cosets at each edge are computed only as discriminant/index profiles, not as explicit integer-vector glue codes.

**What would close it:** Compute the explicit Construction A glue codes for the three E8 blocks composing Niemeier:E8^3, and verify these cosets close the terminal embedding morphism exactly.

This is the morphonics framework's `failure:leech_construction_pending` and `failure:expanded_involution_witnesses_pending` — explicitly registered as known gaps in the substrate.

---

## Summary

| Obligation | Severity | Engineering vs. Math | Estimated effort |
|---|---|---|---|
| O1: Depth-N→J₃(𝕆) lookup | High | Engineering | 2-4 weeks |
| O2: A¹ ladder write-out | Medium | Math + verification | 2-6 weeks |
| O3: Second native-state registration | High | Math + verification | 4-8 weeks per case |
| O4: Full 8x8 group ring decomp | Medium | Math | 1-2 weeks |
| O5: Eversion correspondence | Low (cosmetic) | Topology | 2-4 weeks |
| O6: Spinor lift derivation | Medium | Math | 2-4 weeks |
| O7: Glue cosets exact | Medium | Lattice computation | 1-3 weeks |

None of these block the **Tier A, B, C** proven theorems. They are forward work for strengthening the framework beyond what's required to close Wolfram Problems 1 and 2 via transport of structure.
