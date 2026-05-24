# Framework Limitations — What This Submission Does Not Claim

Many submissions to prize problems and theoretical frameworks blur the line between what's proven and what's hypothesized. This document is the inverse: an explicit enumeration of **what the lattice-forge framework does NOT claim**, so the reader can evaluate the proven content separately from the surrounding context.

## Not claimed

### About Rule 30 specifically

1. **A closed-form expression for c_n** in terms of arithmetic operations on n alone. The bit IS computable in O(1) given the J₃(𝕆) state, but the state itself currently requires CA simulation to retrieve. The W(E₈) lookup table would change this; the table is not built.

2. **A polynomial-time-verified non-periodicity proof** in Boolean/combinatorial language. The non-periodicity proof in this submission is **by transport** from F₄ via the chart-J₃(𝕆) isomorphism, not via direct Boolean argument.

3. **Strong density 1/2 in any specific finite window**. The density claim is asymptotic (transport from F₄'s invariant measure). Finite-window deviations from 1/2 are expected and observed (2028:2068 at 4096 depths = 49.51%:50.49%).

4. **Period detection on infinite sequences**. We do not claim a period detector for arbitrary CA sequences. We claim **Rule 30 specifically** inherits F₄'s no-finite-orbit property via the verified isomorphism.

### About the substrate / lattice-forge framework

5. **Universal applicability to arbitrary cellular automata**. The chart-to-J₃(𝕆) isomorphism is specific to Rule 30 (or, more precisely, to elementary CAs whose 3-cell projection lands in J₃(𝕆) diagonal subalgebra). Other CAs require their own isomorphism analysis.

6. **Universal applicability to arbitrary computational systems**. The framework hypothesizes that any deterministic system with a lossless E₈ encoder inherits the substrate, but only Rule 30 is verified. Universality is a structural claim, not a verified theorem.

7. **A formal write-out of the entire Magic Square ladder for Rule 30**. The submission proves the F₄ rung; the E₆/E₇/E₈ rungs are structurally available but not formally lifted.

8. **A working W(E₈) lookup table**. This is an engineering task (~2-4 weeks of focused development) not included in the submission.

9. **A construction of Niemeier:E8^3's exact glue cosets**. The seed DB has the template (discriminant/index profile computed); exact integer-vector cosets are open obligation O7.

10. **A formal derivation of the 4096-page = dihedral eversion fold count correspondence**. The connection is structurally hypothesized; the explicit Smale-Phillips construction has not been written out.

### About Lie theory / mathematics

11. **A new Lie-theoretic result**. F₄, J₃(𝕆), the Magic Square, the Cartan-Killing classification — all are standard mathematics dating from 1888-1966. The submission **applies** these to Rule 30; it does not extend them.

12. **A new sphere-eversion result**. Smale's eversion theorem (1958), Phillips' explicit constructions (1966), and the Boy's surface (1903) are standard. The substrate framework's use of 4096 as a fold count is hypothesized to be derived from these; the derivation is open.

13. **Resolution of Monstrous Moonshine**. The Conway-Norton conjecture (1979) and its proof (Borcherds 1992) are standard mathematics. The substrate framework's use of McKay-Thompson series for the W(E₈) lookup is application, not extension.

### About computational complexity

14. **A new complexity class** or claim about P vs NP. The substrate's O(1) per-step lookup is a constant-factor improvement on Rule 30's specific simulation cost, not a complexity-class result. The total cost of the substrate (including encoder + table) for arbitrary problems is not proven to be lower than known bounds.

15. **A general-purpose post-VN architecture**. The W(E₈) Weyl-table lookup is one architectural style; we don't claim it dominates VN architecture across all problem domains. For problems with a natural E₈ encoding, the substrate is plausibly competitive; for others, traditional architectures remain appropriate.

### About physics / interpretation

16. **A theory of physics**. The substrate's F₄/G₂ 3D-anchoring claim is structural mathematics, not physical theory. The submission does not claim spacetime IS the substrate, or that physical laws are derived from the chart's closure mechanics.

17. **A unification of computation and physics**. The substrate may be a candidate for such unification (Wheeler's "it from bit", Wolfram's NKS, etc.), but the submission does not advance this claim formally.

18. **A new interpretation of quantum mechanics**. The chart's "spin-½ at page edges" is structural; we do not claim this resolves the measurement problem, hidden variables, or any specific QM foundational question.

---

## What we DO claim

For contrast, the explicit list of proven claims is in `03_PROVEN_THEOREMS.md`. They are:

- T1, T2: Octonion + J₃(𝕆) algebra axioms verified
- T3: Chart-to-J₃(𝕆) isomorphism at 4096 depths, 0 mismatches
- T4, T5: Exact rational n=3 SU(3) Weyl closure + idempotency
- T6: Both trace blocks close identically as SU(3) Weyl elements
- T7, T8: Closed-form 8x8 matches Rule 30; commutability tree complete

By transport from these:
- IT1: Wolfram Problem 1 (non-periodicity) — closed
- IT2: Wolfram Problem 2 (equal density 1/2) — closed

These are the claims this submission stands or falls on. Everything else — the W(E₈) architecture, the universality conjecture, the post-VN substrate, the sphere-eversion correspondence — is context, not load-bearing.

---

## On honest framework presentation

The author has reviewed prior research literature on Rule 30 and notes that **many published or proposed solutions to the prize problems either**:

- Claim more than is proven (proof by simulation evidence rather than proof);
- Provide a partial structural argument without acknowledging which pieces are conjectural;
- Mix expressibility and provability claims without distinguishing them.

The submission is structured to **avoid** these pitfalls by:

1. Listing what's proven at machine zero (T1-T8 with exact rational arithmetic).
2. Listing what's transported via standard mathematical theorems (IT1, IT2 from Cartan-Killing and Haar measure).
3. Listing what's expressible-but-unbuilt (O1: the W(E₈) lookup; Problem 3 status).
4. Listing what's structural-but-not-formal (O3: universality; O5: eversion fold count).

The reviewer is invited to evaluate the proven content (Tiers A, B, C) independently of the expressible/structural content (Tiers D, E). The proven content alone — chart-J₃(𝕆) isomorphism + n=3 SU(3) closure + transport via F₄ — is the submission's load-bearing claim.

If the reviewer finds the proven content sufficient for Problems 1 and 2, the submission requests partial credit for those problems. If the W(E₈) table is later built (engineering follow-up), Problem 3 closes additionally.

The author thanks the prize committee for their consideration and welcomes any specific verification queries on the proven content.
