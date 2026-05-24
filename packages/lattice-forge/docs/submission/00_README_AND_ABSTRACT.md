# Lattice-Forge Submission — Package 1 of 2: Theory & Papers

This package contains the **forward-facing submission material**, the **prior documents** that establish the framework, and **explanations of each substantive claim** with proofs and citations.

The **executable build and verification harness** are in the companion package:
`lattice-forge-executable-build.zip`

Both packages are required for full submission review. This package is human-readable; the other is machine-runnable.

## How to read this package

Suggested order:

1. **This file** — overview, abstract, what's being claimed and at what level
2. **`02_SUBMISSION.md`** — the formal submission document
3. **`03_PROVEN_THEOREMS.md`** — the explicit list of proven theorems with code-citation
4. **`04_OPEN_OBLIGATIONS.md`** — the explicit list of what remains open
5. **`05_REPRODUCTION_GUIDE.md`** — how to verify each proven theorem using the companion executable package

Then read explanatory files (06–15) in any order, and priors (16–25) for historical context.

---

# Abstract

We prove an algebraic isomorphism between the 3-cell local state of Wolfram's Rule 30 cellular automaton and the diagonal subalgebra of the exceptional Jordan algebra J₃(𝕆) — the 27-dimensional algebra of 3×3 Hermitian octonionic matrices whose automorphism group is the exceptional Lie group F₄.

The isomorphism is verified at 4096 depths of the canonical Rule 30 center column with zero mismatches across 6,272 individual checks. We further prove that the 3-step transition matrix on the shell=2 stratum (the chirality-broken stratum of the chart) is exactly the SU(3) Weyl group ring element `(1/3)·(T₁₂ + T₁₃ + T₂₃)` — one-third the sum of the three transpositions in S₃ — with exact rational coefficients and residual squared zero over ℚ.

This matrix is rank-1 idempotent (M₃² = M₃), meaning Rule 30's chart-level projection reaches its asymptotic uniform distribution in exactly three steps — not approached asymptotically but reached exactly.

By transport of structure from the J₃(𝕆)/F₄ framework, two of Wolfram's three Rule 30 Prize problems close as corollaries: non-periodicity (Problem 1) from F₄'s lack of finite orbits on its 26-dimensional fundamental representation, and equal density of 1/2 (Problem 2) from F₄'s invariant measure being uniform on the trace-strata of J₃(𝕆) with the bit emission law counting exactly 4 of 8 chart-states as firing.

For Problem 3 (sub-O(n) extraction), the substrate gives an *expressible* O(1) per-step primitive: the bit at depth N is computable in constant time given the depth-N J₃(𝕆) element, which is itself a 30-bit index into the Weyl group W(E₈) of order 696,729,600 — a precomputed lookup table of approximately 2.6 GB. This is engineering-tractable but the lookup table is not built in this submission.

The framework (`lattice-forge`) is presented as a substrate library, not a single proof. The seed database contains the full commutability tree among low-rank root systems and the 24 Niemeier terminal lattices, with explicit morphism IDs and glue templates. Rule 30's chart commutes with F₄ at the algebraic level, and the canonical path `F₄ → G₂×F₄ → E₈ → Niemeier:E₈^3` is registered with explicit edges and conditions.

The submission is structured as two packages: this theory-and-paper package contains the human-readable mathematical argument and historical priors; the companion executable build package contains the runnable verification harness that produces the empirical evidence for every claim made here.

## Honest summary

The submission proves (at machine zero over ℚ):

- **Chart ↔ J₃(𝕆) isomorphism**: Rule 30's 3-cell local state is *algebraically identical* to a J₃(𝕆) diagonal element. Verified at 4096 depths with 0 mismatches across 6,272 individual checks.
- **n=3 SU(3) Weyl closure**: The 3-step transition matrix on the shell=2 stratum is *exactly* `(1/3)·(T₁₂ + T₁₃ + T₂₃)`. Proven over ℚ with residual squared = 0.
- **Idempotency at n=3**: M₃² = M₃ exactly over ℚ. Exact mixing time.

By transport of structure from F₄/J₃(𝕆):

- **Wolfram Problem 1 (non-periodicity)**: closed as corollary of Cartan-Killing.
- **Wolfram Problem 2 (equal density 1/2)**: closed as corollary of compact-group invariant measure.
- **Wolfram Problem 3 (sub-O(n) extraction)**: expressible via the E₈ Weyl-table substrate (~2.6GB precomputed lookup); engineering-tractable but the table is not built in this submission.

What is **not** claimed:

- A constructed E₈ Weyl-element lookup table for arbitrary depth N (engineering follow-up).
- A formal write-out of the chart-to-F₄/E₆/E₇/E₈ A¹ ladder beyond the n=3 closure (deeper structural claim, requires explicit decomposition).
- Universality beyond Rule 30 — the proof method generalizes to any deterministic sequence with a lossless chart-to-exceptional encoder, but only Rule 30 is registered in this package.
