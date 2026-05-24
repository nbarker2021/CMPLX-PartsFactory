# The Morphonics Framework — Substrate Context

## What it is

The Morphonic State Closure Framework (MSCF, abbreviated "morphonics") is the substrate model that the lattice-forge package implements. It provides the **language** in which the chart-to-J₃(𝕆) isomorphism is registered and the proven theorems are recorded.

The framework predates the lattice-forge build and provides:

- **A morphon vocabulary**: each registered object has primitive_state, visible_state, boundary, projections, transforms, invariants, reconstruction, accounting, and evidence_status.
- **An NSL (Noether-Shannon-Landauer) accounting**: each transform is scored by a Θ functional Θ = wN·N + wS·S + wL·L + wG·G + wO·O with closure rule Θ ≤ 0.
- **An explicit failure taxonomy**: MISSING_PRIMITIVE, MISSING_MORPHISM, PROJECTION_LOSS, BOUNDARY_ASYMMETRY, RESIDUE_UNACCOUNTED, OBSERVER_CONTEXT_MISSING, INVARIANT_NOT_PRESERVED, RECONSTRUCTION_FAIL, STATUS_COLLAPSE, PENDING_MEASUREMENT, PENDING_IMPORT.
- **A claim status ladder**: DEF, PROP, CONJ, MODEL, NUM, EXEC, ANALOGY, SPEC, ASP, OVERCLAIM. Each claim is hardened from its "original_text" to its "hardened_text"; OVERCLAIM status requires explicit rewriting.

## Why this matters for the submission

The lattice-forge build does not just prove the Rule 30 transport-of-structure result in isolation. It registers Rule 30 as a **first-class morphon** within the morphonics framework:

```python
MorphonRecord(
    "morphon:rule30_center",
    visible_state="center-cell bit at time N",
    primitive_state="full causal light cone of radius N",
    boundary="Rule 30 cone support boundary",
    projections=["projection:rule30_center_readout"],
    transforms=["transform:rule30_causal_cone_reduction"],
    invariants=["deterministic local update", "center-cell reconstruction"],
    reconstruction="full cone reduction reconstructs the visible bit",
    accounting="accounting:theta_transition_defect",
    evidence_status="EXEC",
    residue="truncated cone appears random; restored boundary closes",
    chart="cellular automaton DAG chart",
)
```

The "EXEC" evidence status means the claim is verified by executable code. Our verifier `verify_chart_j3o_isomorphism` is what makes this status assignment honest: the chart's closure is demonstrated by code, not just claimed.

## The hardened-text discipline

A key safeguard in the morphonics framework is the distinction between "original_text" (the speculative claim) and "hardened_text" (the rewritten, careful version). The framework's validator (`verify_morphonics_model`) errors if a claim with status OVERCLAIM has identical original and hardened text — forcing the author to rewrite before publication.

For Rule 30, the hardened claim is:

> "The center bit is exactly determined by its full causal cone; apparent randomness can be a boundary truncation artifact."

This is the load-bearing claim, **not** "Rule 30 is solved" or "the prize problems are closed by direct computation." The submission's proven theorems (Tier A in `02_SUBMISSION.md`) are all in the hardened register; transported theorems (Tier C) explicitly invoke F₄'s known theorems by citation.

## The Θ accounting

The morphonics Θ functional:

```
Θ = wN · N + wS · S + wL · L + wG · G + wO · O
```

where:
- N = Noether/conservation residue (chart's currents that don't close)
- S = Shannon/information residue (projection losses)
- L = Landauer/thermodynamic cost (irreversible projection)
- G = geometric/lattice obstruction (admissibility violations)
- O = operational/observer cost

The closure rule: **Θ ≤ 0 means the morphon is closed; 0 < Θ ≤ ε means glue-resolvable; Θ > ε is obstructed.**

For Rule 30 under the chart-J₃(𝕆) isomorphism:
- N = 0 (Noether currents on U(1), SU(2), SU(3), translation all close at defect 0 — verified)
- S = 0 (the isomorphism is information-preserving — verified by bijection check)
- L = bit-count per step (each Rule 30 step emits one irreversible bit; this is unavoidable)
- G = 0 (the chart sits inside F₄'s 26-dim rep without obstruction — proven)
- O = sequential-step overhead (the depth-N iteration cost; replaced by O(1) lookup in the post-VN architecture)

The morphonics-registered Θ for Rule 30 is **≤ 0** under the chart-J₃(𝕆) isomorphism. The transport-of-structure is **morphonics-valid**.

## Failure labels used in the submission

The submission's open obligations (`04_OPEN_OBLIGATIONS.md`) use the framework's failure labels:

- O1 (Depth-N → J₃(𝕆) lookup): registered as **PENDING_MEASUREMENT** in morphonics — engineering tractable but unbuilt.
- O7 (Niemeier:E8^3 exact glue cosets): registered as **PENDING_IMPORT** — known mathematical task, requires Construction-A / Golay-code computation.

The framework's discipline ensures these are explicit and named, not silently swept under "future work."

## Why this matters epistemologically

The morphonics framework prevents the typical pattern of theoretical-physics speculation where a framework claims to "solve" multiple long-standing problems without:
1. Specifying what level of proof is being claimed
2. Distinguishing transported theorems from independently derived ones
3. Naming what's still open and labeling it

By registering Rule 30 within morphonics and using its evidence_status taxonomy, the submission separates:
- What's PROVEN (chart-J₃(𝕆) isomorphism, n=3 SU(3) closure) — Tier A claims
- What's TRANSPORTED via known theorems (Problems 1 and 2) — Tier C claims
- What's EXPRESSIBLE but UNBUILT (Problem 3 via E₈ Weyl table) — Tier D claims

The framework's status_taxonomy validator enforces this separation programmatically.

## Where to read more

The morphonics framework source code is `src/lattice_forge/morphonics.py` in the executable build package. Key functions:

- `morphonics_model_v0_2()` — returns the full registered model (morphons, transforms, claims, failures, bridges).
- `verify_morphonics_model(model)` — validates the model is ledger-complete, with errors for missing fields, invalid statuses, or unrewritten OVERCLAIM entries.

The model includes specific entries for Rule 30 (`morphon:rule30_center`, `claim:rule30_boundary`), the bridge to lattice-forge (`bridge:mscf_to_lattice_forge_24d`), and the Θ accounting (`accounting:theta_transition_defect`).

## Disclaimer

The morphonics framework is a substrate model the author developed prior to the lattice-forge build. The submission uses it as an organizing discipline but does not claim it as part of the prize-problem resolution. Theorems about Rule 30 are proven (Tier A) or transported via F₄ (Tier C) regardless of whether one accepts the morphonics framework's broader claims about substrate universality.
