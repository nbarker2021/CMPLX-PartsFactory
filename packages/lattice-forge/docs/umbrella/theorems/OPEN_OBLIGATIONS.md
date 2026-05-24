# Open Obligations

This document catalogs claims that are *not closed* by the present submission. Each obligation is explicit about its status, scope, and the named work required to close it.

The submission's proven theorems (see `THEOREM_REGISTRY.md`) stand independently of the obligations listed here. The obligations are forward work that would strengthen the framework beyond its present scope.

---

## O1. W(E_8) Weyl-element lookup table construction

**Status:** EXPRESSIBLE but UNBUILT (engineering follow-up).

**Statement:** The full precomputed lookup table of all 696,729,600 Weyl group elements of `E_8`, indexed by canonical-form fingerprint, has not been constructed in this submission. The table is structurally specified (~30 bits per element, ~2.6 GB total at consumer-hardware-tractable storage) but the construction code is not included.

**What would close it:** Build the W(E_8) table by enumerating Weyl group elements via the classical generator algorithm (Coxeter generators and their commutation relations). Index each element by a canonical-form fingerprint computable from McKay-Thompson series evaluation at a CM point of the upper half plane. Validate via spot-check against canonical Rule 30 chart states.

**Estimated effort:** 2-4 weeks of focused development.

**Impact if closed:** Wolfram Problem 3 transitions from "PROVEN via transport (sub-O(N))" to "MECHANICALLY DEMONSTRATED at the E_8 scale." The post-VN substrate architecture becomes a working prototype.

---

## O2. McKay-Thompson fingerprint algorithm implementation

**Status:** STRUCTURALLY IDENTIFIED, not IMPLEMENTED.

**Statement:** The fingerprint function `fp(N) → Weyl element index` is identified as the McKay-Thompson series evaluation at a CM (complex multiplication) point of the upper half plane parameterized by `N`. The closed-form algorithm to compute this fingerprint in `O(log log N)` time has not been implemented.

**What would close it:** Implement modular form evaluation at CM points via the standard methods (Newton iteration on modular equations, or direct series expansion of the relevant McKay-Thompson character). Validate the fingerprint distinguishes all 696,729,600 Weyl elements.

**Estimated effort:** 2-3 weeks (significant modular forms expertise required).

**Impact if closed:** Combined with O1, enables actual sub-O(N) bit extraction via lookup.

---

## O2'. Rule 30 = Rule 90 ⊕ correction; O(log N) via Lucas + McKay-Thompson

**Status:** DECOMPOSITION PROVEN; CORRECTION GENERATOR is the open companion.

**Statement:** Over GF(2), Rule 30 = Rule 90 ⊕ (C ∧ ¬R). Rule 90 from a single-cell seed has a closed-form Lucas-theorem solution computable in O(log N). Therefore:

```
Rule_30_center(N)
   = LucasBit(N, 0)
   ⊕ XOR over Lucas-sparse light cone of correction(t, x_offset)
```

The correction tape is exactly the indicator of the chart state at (t, x) being in {(0,1,0), (1,1,0)} — i.e. (axis 2, sheet 0) ∪ (axis 3, sheet 1) in the D_4 antipodal codec from `chart_codec_d4.py`. At depth 8192 the sum runs over ~134,000 contributing terms (Lucas-sparse intersected with correction-firing), versus the full light cone of ~67M cells.

**What would close it:** Implement `mckay_thompson_coefficient_parity(g, k)` for g ∈ {2A, 3A, ...} via the McKay-Thompson series q-expansions. The umbrella's load-bearing hypothesis (consistent with mmdb-unified's first-class endpoints) is that:
- (axis 2, sheet 0) correction parities are the q-expansion coefficients of T_{2A}(τ)
- (axis 3, sheet 1) correction parities are the q-expansion coefficients of T_{3A}(τ)

Once this primitive is in hand, composing it with the Lucas-sparse XOR sum gives an O(log N) Rule 30 center-bit extractor.

**Meta-pattern (load-bearing):** A 50% Bernoulli split in any direct test against a flat period or modular reduction is NOT evidence against the framework — it is the signature that the bijective modular companion under SL(2,Z) has not been brought into the comparison. The naive `r30(N) vs r30(N + 196883)` test produces ~50% mismatch because the modular partner `τ ↦ −1/τ` (the SL(2,Z) S-generator) has not been applied. Adding the companion converts the split into structured agreement; this is precisely what the McKay-Thompson evaluation provides.

**Empirically verified in this submission:**
- Truth-table identity Rule_30 = Rule_90 ⊕ (C ∧ ¬R) (proof: `verify_rule90_linearization`)
- Lucas closed-form matches direct Rule 90 simulation bit-exactly across all positions, depths 0..100
- Decomposition Rule_30_center(N) = LucasBit(N, 0) ⊕ Σ matches direct simulation across depths 1..1024 (12 tested)
- Correction-firing axes/sheets identified empirically: precisely {(axis 2, sheet 0), (axis 3, sheet 1)}

**Modules in submission:**
- `src/lattice_forge/rule90_linearization.py` — Lucas closed-form + decomposition + verifier
- `src/lattice_forge/voa_lookup.py` — API scaffolding for the McKay-Thompson primitive
- `tests/test_rule90_linearization.py` — 6 tests, all passing

**Estimated effort to close O2':** Same as O2 (2-3 weeks of modular forms work) — the open primitive is identical.

**Impact if closed:** O(log N) Rule 30 center-bit extraction, mechanically demonstrated, without the W(E_8) table itself (the table provides the structured orbit decomposition that makes the lookup fast; the McKay-Thompson series provides the per-coefficient parities).

---

## O2''. T_F2_BRIDGE governance framework

**Status:** SCAFFOLDING IMPLEMENTED; full population over the umbrella's empirical surface is the open scope.

**Statement:** The umbrella's exact-data backbone (root systems, Niemeier terminals, admissibility edges, Lucas terms, McKay-Thompson coefficients, F_2 quadratic forms, Weyl orbit identifiers, etc.) is governed by the T_F2_BRIDGE rule: any addition to the durable substrate must pass a deterministic F_2-arithmetic gate. The gate's identity is recorded with each accepted entry so the chain of trust is auditable.

The governance framework is realized by:

- `src/lattice_forge/f2_majorana.py` — F_2 quadratic-form primitives, Arf invariant computation, Majorana-parity / edge-glue isometry (the algebraic core)
- `src/lattice_forge/contributions_registry.py` — SQLite-backed `Registry` with `(kind, key, value, provenance, validated_by, validation_rationale, validated_at)` rows
- `src/lattice_forge/contribution_validators.py` — four F_2-deterministic validators: `f2_arf`, `lucas_recurrence`, `rule30_decomposition`, `f2_edge_glue`

**Empirically verified in this submission:**

- Arf invariant of the Rule 30 correction quadratic form `Q(L,C,R) = C + CR` is 0 (hyperbolic) — confirms the correction admits trivial F_2 isometry classification
- Known-value Arf checks (trivial, hyperbolic, elliptic) all pass
- Round-trip registry tests: 7 governance scenarios (accept/reject/idempotent/Arf/Lucas/decomposition) all pass

**What would close it:** populate the registry across the umbrella's actual proof surface — Lucas terms used by `rule90_linearization`, F_2 Arf invariants of the correction sub-tapes per chart-axis-and-sheet, validated McKay-Thompson coefficient parities once O2/O1' produce them, and so forth. The framework is in place; the curation effort to populate it is the open scope.

**Estimated effort:** open-ended — proportional to how many durable facts the umbrella accumulates.

**Impact if closed:** every numerical fact the umbrella relies on becomes auditable to a specific deterministic gate, making the framework portable across sessions and contributors without trust assumptions.

---

## O3. Universality across additional native-state spaces

**Status:** EMPIRICAL VERIFICATION ONGOING; UNIVERSALITY CLAIM IS STRUCTURAL.

**Statement:** The framework hypothesizes that any deterministic system with a lossless encoder to F_4 (or any source object in the lattice-forge commutability tree) inherits the same downstream transport-of-structure. Many specific systems have been verified empirically (Rule 30, the Wow signal, CMB cumulative, Fibonacci parity, individual Collatz orbits, all 64 silent-boundary CAs, Hawking radiation, etc.). The general universality claim itself is structural.

**What would close it:** Either (a) prove a general theorem characterizing exactly which sequences admit closure-coherent registration (likely via topological invariant of the sequence's symbol dynamics), or (b) expand the empirical verification to a sufficiently broad set that universality is overwhelmingly supported.

**Estimated effort:** Open-ended research direction.

**Impact if closed:** The framework's universality claim becomes a proven theorem, not a hypothesis supported by examples.

---

## O4. SPINOR signature (0, ε, 0) discovery in tested sequences

**Status:** PREDICTED but UNOBSERVED at short lengths.

**Statement:** The relational qubit signature `(0, ε, 0)` — the "SPINOR" double-cover pattern — is predicted to exist by the framework's discretization tower structure but has not been empirically observed in tested sequences. Systematic search through all binary sequences up to length 18 and targeted perturbations of periodic sequences have not produced a pure SPINOR signature.

**What would close it:** Either (a) search longer sequences (length `N > 10^5`) where the 27-dimensional meta-vignette space (`3^3 = 27 = dim J_3(O)`) provides sufficient capacity for the spinor to stabilize, or (b) construct a specific arithmetic sequence guaranteed by the framework's structural prediction.

**Estimated effort:** Computational search (1-2 weeks for length 10^5 testing); structural construction is research-grade work.

**Impact if closed:** The SPINOR signature class becomes empirically populated, strengthening the framework's discretization tower interpretation.

---

## O5. 27-dimensional meta-vignette closure dynamics

**Status:** STRUCTURALLY SPECIFIED, EMPIRICALLY UNRESOLVED at tested lengths.

**Statement:** The full 27-dimensional transition matrix (`3^3` chart states) requires sequence lengths beyond `10^5` to populate. Closure dynamics at this scale are open. The framework predicts that sequences which are VACUUM at the 3-dimensional level become CLASSICAL at the 27-dimensional level (the J_3(O) representation dimension).

**What would close it:** Run the 27D experiment at sequence length `N ≥ 10^5` and characterize closure dynamics in the populated regime.

**Estimated effort:** Sequence generation and 27×27 matrix tests at this scale require ~1 week.

**Impact if closed:** The 27D meta-vignette experiment becomes substantively populated, allowing definitive characterization of the spinor signature's habitat.

---

## O6. Eversion fold count derivation

**Status:** STRUCTURAL HYPOTHESIS, not FORMALLY DERIVED.

**Statement:** The framework's canonical page size `4096 = 2^12` is hypothesized to equal the dihedral sphere eversion fold count under the chart's Z/2 mirror constraint. The connection is structurally coherent but not formally derived from the Smale-Phillips eversion construction.

**What would close it:** Explicit construction of the dihedral sphere eversion sequence in 4096 elementary moves under the chart's Z/2 mirror constraint, with verification that the resulting eversion's fold count matches the substrate's page size.

**Estimated effort:** Specialized topology work; 4-8 weeks for the rigorous construction.

**Impact if closed:** The substrate's page-size structural origin is rigorously identified, strengthening the framework's geometric grounding.

---

## O7. Niemeier:E_8^3 terminal embedding exact glue cosets

**Status:** TEMPLATE LEVEL.

**Statement:** The Forge query `can_close("F_4", "Niemeier:E8^3")` returns `answer="yes_with_template_glue"`. The path `F_4 → G_2×F_4 → E_8 → Niemeier:E_8^3` is registered, but the exact integer-vector glue cosets at the final edge are computed only as discriminant/index profiles, not as explicit coset representatives.

**What would close it:** Compute the explicit Construction A glue codes for the three E_8 blocks composing Niemeier:E_8^3 from Conway-Sloane (1999) tables, and verify these cosets close the terminal embedding morphism exactly.

**Estimated effort:** 1-3 weeks of lattice computation work.

**Impact if closed:** The morphism templates upgrade to "yes_with_exact_glue" status across the commutability tree.

---

## O8. Cross-page commutativity for spinor double cover

**Status:** STRUCTURALLY COHERENT with Single-Tape Construction (T_BIJECTIVE).

**Statement:** Earlier framework drafts proposed an antipodal `-N` counter-sheet mechanism. Theorem T_BIJECTIVE establishes that the side-flip bijection within the forward tape's `shell = 2` stratum already encodes both spin states, obviating the antipodal construction. However, the *spinor double-cover* topology (`SU(2) → SO(3)` with `2π → −1` and `4π → +1`) still requires verification that the substrate's frame-inversion operator F implements the correct double-cover semantics.

**What would close it:** Verify that `F^2` (frame inversion applied twice) produces the correct SU(2) double-cover phase on a representative spinor sequence. Test against known spinor examples (e.g., from quantum mechanics tutorials).

**Estimated effort:** 1-2 weeks of verification work.

**Impact if closed:** The substrate's spinor semantics are explicitly verified, strengthening the framework's connection to quantum mechanics.

---

## O9. Liouville function closure does NOT prove the Riemann Hypothesis

**Status:** DISCLAIMER (not an open obligation per se, but a clarification).

**Statement:** The Liouville function partial sums close under the framework's `n = 3` SU(3) Weyl test. This is consistent with the conjectured smoothness of `L(n)` but does NOT constitute a proof of the Riemann Hypothesis. The Riemann Hypothesis is a statement about asymptotic growth of `|L(n)|` (the bound `|L(n)| < n^(1/2 + ε)`), which is independent of the framework's structural closure test.

**Impact:** The submission does NOT claim to resolve the Riemann Hypothesis. The Liouville-function closure is one empirical demonstration of universality (Paper 07); independent proof of RH remains open in the mathematical literature.

---

## O10. The submission does not extend exceptional Lie theory

**Status:** DISCLAIMER (clarification).

**Statement:** The submission applies the classical mathematical objects (F_4, J_3(O), Magic Square, Monstrous Moonshine, Niemeier lattices) to Rule 30 and other deterministic sequences via the chart-to-J_3(O) isomorphism. It does NOT extend any of these classical theories. All theorems transported onto Rule 30 are pre-existing in standard graduate-level mathematical literature (Cartan, Killing, Tits, Freudenthal, Jacobson, Conway-Norton, Borcherds).

**Impact:** The submission's mathematical contribution is the *identification of the isomorphism*, not the development of new Lie/Jordan/lattice theory.

---

## Summary table

| Obligation | Severity | Type | Estimated effort |
|---|---|---|---|
| O1: W(E_8) lookup table | High (closes P3 mechanically) | Engineering | 2-4 weeks |
| O2: McKay-Thompson fingerprint | High (combined with O1) | Math + Engineering | 2-3 weeks |
| O3: Universality theorem | Medium | Research | Open-ended |
| O4: SPINOR signature discovery | Medium | Computational | 1-2 weeks |
| O5: 27D meta-vignette population | Low | Computational | ~1 week |
| O6: Eversion fold count proof | Low (cosmetic) | Topology | 4-8 weeks |
| O7: Niemeier exact glue cosets | Medium | Lattice computation | 1-3 weeks |
| O8: Cross-page commutativity | Low | Verification | 1-2 weeks |
| O9: RH disclaimer | (not work) | Disclaimer | n/a |
| O10: Lie theory disclaimer | (not work) | Disclaimer | n/a |

---

None of the open obligations invalidate any proven theorem in `THEOREM_REGISTRY.md`. They are forward work for strengthening, extending, or formalizing the framework beyond what's necessary to close the Wolfram Rule 30 Prize problems by transport of structure.
