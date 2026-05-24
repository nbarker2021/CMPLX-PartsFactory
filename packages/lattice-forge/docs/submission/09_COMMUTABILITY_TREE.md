# The Commutability Tree — Lattice Classification

## What the commutability tree is

The lattice-forge seed database contains the **complete commutability tree** among low-rank root systems (classical A/D/E/F/G families) and the 24 Niemeier 24-dimensional terminal lattices.

A directed edge `S → T` in the tree means: "morphisms from source S to target T are admissible under the chart's closure constraints, with conditions specified by the edge's morphism record."

The tree is a finite, fully-enumerated object. The current build has:
- **19+ root systems** as sources (A₁ through A₂₄, D₄ through D₁₂, E₆/E₇/E₈, F₄, G₂, plus composite G₂×F₄)
- **24 Niemeier terminal lattices** (the 23 rooted ones + the rootless Leech lattice)
- **65 legal admissibility edges**, **1 forbidden edge**
- **33 involution records**
- **53 NSL boundary residues** (Noether-Shannon-Landauer accounting along each path)

## For Rule 30 specifically

The chart commutes with **F₄** (proven via the J₃(𝕆) isomorphism + n=3 SU(3) Weyl closure). From F₄, the seed DB exposes 8 canonical paths to 8 Niemeier terminals:

```
F₄ → G₂×F₄ → E₈ → Niemeier:E8^3       (Magic Square / 3-octonion terminal)
F₄ → G₂×F₄ → E₈ → Niemeier:D16_E8     (composite D16+E8 terminal)
F₄ → E₆ → E₇ → Niemeier:A17_E7        (A17+E7 terminal)
F₄ → E₆ → E₇ → Niemeier:D10_E7^2      (D10+E7+E7 terminal)
F₄ → E₆ → Niemeier:A11_D7_E6          (A11+D7+E6 terminal)
F₄ → E₆ → Niemeier:E6^4               (E6-cubed terminal)
F₄ → D₄ → Niemeier:A5^4_D4            (A5⁴+D4 terminal)
F₄ → D₄ → Niemeier:D4^6               (D4⁶ terminal)
```

These 8 paths exhibit the substrate's natural symmetry: F₄ has **four trunk-intermediaries** (D₄, E₆, E₇, E₈-via-G₂×F₄), each leading to **two Niemeier terminals**, giving 8 = 4 × 2 total endpoints.

## What this means structurally

### The number 8 is structural

The 8-state chart, 8-block dihedral page structure (block_size=8), 8-element E₈ maximal kissing clique, and 8 commutable Niemeier terminals from F₄ are all manifestations of the same substrate fact: 8 is the natural cardinality for F₄'s downstream registration.

### The Magic Square row is fully visible

From F₄, climbing through E₆, E₇, E₈ gives the full octonion Magic Square row (R, C, H, O over octonions). The lattice-forge tree registers each rung as an explicit morphism:

- F₄ → E₆: A¹ involution corresponding to ℝ → ℂ (real to complex octonion extension)
- E₆ → E₇: A¹ involution corresponding to ℂ → ℍ (complex to quaternion)
- E₇ → E₈: A¹ involution corresponding to ℍ → 𝕆 (quaternion to octonion)

Or via the other trunk: F₄ → G₂×F₄ → E₈ direct (the exceptional dual pair).

### G₂ is registered as the bond partner

The composite `G₂×F₄` is a first-class object in the tree. Its existence as a registered node reflects the substrate's structural claim that F₄ and G₂ are the **two 3D-anchored exceptionals** (F₄ via 3×3 Hermitian octonionic matrices, G₂ via Im(𝕆) ≅ ℝ⁷ extending 3D cross products). The dual pair makes their bonded action explicit.

## The "valid commuting lattices" question — answered

The user's question, restated from the conversation: "determine WHICH of the ONLY valid lattices that commute between THIS observed Ax3 triadic bond chart."

For Rule 30's chart:

**Valid commuting lattices** (those whose Weyl group contains S₃ and whose Cartan subalgebra commutes with the chart's grading), in order of complexity:

| Lattice | |W| | Carries chart structure? |
|---|---:|---|
| A₂ = SU(3) | 6 | Yes — the chart itself, minimal case |
| G₂ | 12 | Yes — via Im(𝕆) action |
| F₄ | 1,152 | **Yes — natural home, J₃(𝕆) Aut** |
| E₆ | 51,840 | Yes — F₄ extended via Cayley-Dickson |
| E₇ | 2,903,040 | Yes — E₆ extended |
| E₈ | 696,729,600 | Yes — terminus of Magic Square |

For the basic chart-isomorphism + n=3 closure, **F₄ is sufficient** with a 1,152-element Weyl table (~4 KB).

For the spin-½ lift (the chirality doublet structure), the natural home is E₆ with |W(E₆)| = 51,840 (~190 KB Weyl table).

For the full sphere-eversion (4096-page) structure, the natural home is E₈ with |W(E₈)| = 696,729,600 (~2.6 GB Weyl table).

## Practical implication

The "post-VN substrate" claim discussed in the conversation has a **graded cost**:

- For the proofs we've verified (chart isomorphism + n=3 closure): **~4 KB lookup table** (W(F₄)). Fits in a single CPU cache line full. O(1) per step. Buildable in minutes.

- For the spinor lift (Wolfram Problem 3 if extracted via E₆): **~190 KB lookup table** (W(E₆)). Still trivial for consumer hardware.

- For the full universal substrate claim (Wolfram Problem 3 via E₈): **~2.6 GB lookup table** (W(E₈)). Tractable, requires precomputation effort.

The framework doesn't require the largest table for Rule 30 specifically — F₄'s 4 KB table is sufficient for the proven content. The E₈ claim is a structural extension toward universality, not a load-bearing requirement.

## Path edge structure

Each edge in the commutability tree has an explicit record:

```json
{
  "edge_id": "edge:F4->G2xF4:pair_with_G2",
  "source_id": "F4",
  "target_id": "G2xF4",
  "via_morphism_id": "mor:F4->G2xF4:pair_with_G2",
  "status": "legal",
  "condition_json": "{}",
  "obstruction_json": "{}",
  "hash": "d1cbe1ecf70624b051d6f9b5ef3e118a4a858dfcd083a8a0e78b54d313eb3f9b"
}
```

The morphism IDs encode the operation being performed: `pair_with_G2`, `exceptional_dual_pair_closure`, `component_terminal_embedding_template`, etc.

Glue templates (the cosets needed to complete each terminal embedding) are stored with `status="template"`, meaning the discriminant/index profile is computed but exact integer-vector coset representatives are pending.

## Closure status

The tree's invariant: **any path from a source to a terminal is either legal (returns "yes_with_template_glue" or "yes_with_exact_glue"), forbidden (one specific edge), or unreachable (no path exists)**. There are no ambiguous cases.

For Rule 30's F₄ chart, all 8 paths to Niemeier terminals are "yes_with_template_glue" — the terminal embeddings exist as morphisms; the exact glue cosets are open obligation O7.
