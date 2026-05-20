# Sub-Frame: Reality Calibration (v1)

**Status:** v1 frozen — G5 gate defined, calibration infrastructure to follow.
**Parent frame:** [ATTRACTOR_FRAME.md](../ATTRACTOR_FRAME.md)
**Companion sub-frame:** [deep_review_catalog.md §8](deep_review_catalog.md)
**User direction (2026-05-17):** the existing repos contain real working examples of the system; our substrate has to reproduce their behavior, not just be internally coherent.

---

## 0. Why this sub-frame exists

The merge protocol's four gates (G1 contract, G2 admission, G3 properties, G4 determinism) verify that the substrate is **internally consistent**. They don't verify it produces the same **observable behavior** as the prior repos that are operational evidence the system works. Without a fifth gate, the substrate can be a coherent abstraction that has drifted from the thing it's supposed to represent.

This sub-frame adds **G5 — Reality calibration**: a slot is fully canonical only when its behavioral contribution to the calibration suite passes — meaning a known working example from a prior repo, when its inputs are routed through the substrate, produces outputs that match (within tolerance) the prior repo's claimed values.

## 1. What G5 is

**Statement:** for a slot's implementation to pass G5, at least one calibration target whose execution touches that slot must run on the substrate and produce observed values that fall within tolerance of the target's expected values.

**Mechanics:**

- A **calibration target** is a tuple `(target_name, claim_set, harness)`.
- A **claim** is `(claim_name, expected_value, tolerance, observed_fn)` where `observed_fn` is a callable that runs through the substrate and returns the observed value.
- A **harness** is the orchestration code that invokes the substrate paths.
- A **calibration receipt** records the outcome of one claim's evaluation.
- A target **passes** when every claim in its claim_set passes (each `|observed - expected| ≤ tolerance`).

**G5 acceptance flow:**

```
target.run() → for each claim:
    observed = claim.observed_fn(substrate)
    delta = |observed - expected|
    pass = delta ≤ tolerance
    mint CalibrationReceipt(...)
target.passed = all(claim.pass for claim in claims)
```

## 2. Where calibration lives

**Code:** `src/calibration/` (NOT inside `cmplx/` — calibration is meta-work *about* the substrate, not work the substrate does).

**Ledger:** `src/calibration/ledger.py` — a separate `CalibrationLedger` storing JSONL records under `data/calibration/<target_name>/<run_id>.jsonl`. Each record is a `CalibrationReceipt`.

**Cross-reference to cmplx.receipt:** every calibration receipt carries `operational_chain_range = (chain_head_before, chain_head_after)`. When a calibration harness invokes substrate paths that mint cmplx receipts (e.g., `admit_and_store`), the calibration receipt links to the operational receipt range it produced. Two ledgers, one stitched audit trail.

## 3. CalibrationReceipt grammar

```python
@dataclass
class CalibrationReceipt:
    calibration_id: str        # uuid4
    timestamp: str             # ISO format UTC
    target_name: str           # e.g., "wolfram_poc"
    claim_name: str            # e.g., "rule30_center_entropy"
    expected: Any              # claimed value from prior repo (number, dict, list)
    tolerance: float | dict    # acceptable delta (or per-field for dict expecteds)
    observed: Any              # what the substrate produced
    delta: float | dict        # |observed - expected| per field
    passed: bool               # delta within tolerance
    operational_chain_range: tuple[str, str]  # (head_before, head_after) on cmplx.receipt
    harness_version: str       # version of the calibration harness (semver)
    notes: str                 # human-readable context
```

## 4. Initial calibration targets

Five targets from [deep_review_catalog.md §8.2](deep_review_catalog.md), in priority order:

### 4.1 `wolfram_poc` — Rule 30 / E8 equivalence

**Source:** [CMPLX-1T/Wolfram study/cmplx_wolfram_poc.py](../../CMPLX-1T/Wolfram%20study/cmplx_wolfram_poc.py)

**Claims (first batch):**

| Claim | Expected | Tolerance | Substrate path |
|---|---|---|---|
| `e8_root_count` | 240 | 0 (exact) | `cmplx.geometry.e8._history_reference.composed_E8Lattice` produces N roots |
| `e8_root_norms_squared` | all == 2.0 | 1e-6 | every root has norm² == 2 |
| `rule30_center_entropy` | ≈ 0.865 bits | ±0.05 | standard Rule 30 over 100 steps; entropy of center column |
| `geometric_center_entropy_vs_rule30` | matches Rule 30 entropy | ±0.10 | digital-root sequence from E8 rotations; entropy comparable |
| `digital_root_in_range` | always 1..9 | exact | every digital-root output stays in [1, 9] |

**Substrate touches:** `geometry` port (E8 roots), morphon/snap path (digital-root computation via existing CQE atom flow). Atlas isn't strictly needed for these claims — c-values are not exercised.

### 4.2 `quorum_consensus` — Multi-agent E8 convergence

**Source:** [CMPLX-1T/Wolfram study/experiment_03_quorum_cmply.py](../../CMPLX-1T/Wolfram%20study/experiment_03_quorum_cmply.py)

**Claims (sketch — to be detailed when implemented):**

- N agents (e.g., 50) initialized at random E8 roots converge to a single root within K rounds
- Vote-distribution entropy decreases monotonically (within noise)
- Final consensus root is reproducible given fixed seed

**Substrate touches:** `geometry`, `snap`, `addressing`, `memory` (per-agent state).

### 4.3 `triadic_morphon` — Collision → ordered triple

**Source:** [experiment_04_triadic_morphon.py](../../CMPLX-1T/Wolfram study/experiment_04_triadic_morphon.py)

**Claims (sketch):**

- Two-form collisions produce a third form with specific Cartan-matrix relationships
- Pairwise inner products of the three forms fall in `{-2, -1, 0, 1, 2}` (E8 inner-product set)
- Fourth-element search is deterministic per (form_a, form_b) input

**Substrate touches:** `morphon`, `geometry`, `engine` (CQE collision), `atlas` (if c-values matter for the triple).

### 4.4 `100form_transition` — Representational space discontinuity

**Source:** [experiment_100form.py](../../CMPLX-1T/Wolfram study/experiment_100form.py)

**Claims (sketch):**

- Representational space size at level N is monotone non-decreasing in N
- The slope `Δspace / Δlevel` shows a measurable discontinuity at N=100 (not just smooth growth)

**Substrate touches:** `geometry`, `addressing` (multi-scale slots), `engine` (form generation).

### 4.5 `economic_phase_boundary` — Cross-domain E8 generalization

**Source:** [case-06/tool03/economic_phase_boundary.py](../../CMPLX-1T/SHOWROOM/SHOWCASES/case-06-layer-toolkit/artifacts/CMPLX_Tool_Suite/tool03_economic/economic_phase_boundary.py)

**Claims (sketch):**

- PBPS curve from synthetic recession-shaped 8D time-series peaks before the synthetic "recession" event
- Peak magnitude correlates with magnitude of pre-event signal

**Substrate touches:** `geometry`, `snap`, diagnostic (rolling entropy). Cross-domain — verifies E8 isn't physics-specific.

## 5. Build order

1. **Calibration infrastructure** — `src/calibration/`:
   - `ledger.py` — `CalibrationLedger` with JSONL persistence + cross-reference to cmplx.receipt
   - `harness.py` — base `CalibrationTarget` class + `CalibrationClaim` dataclass + `run()` orchestration
2. **First target: `wolfram_poc`** — `src/calibration/targets/wolfram_poc.py`. Cover the 5 claims above. First reality-check on whether our substrate matches the prior POC.
3. **Calibration receipts written, reviewed** — surface what passes vs fails. Failures are the work surface.
4. **Targets 4.2–4.5** — one per work session, in priority order. Each new target may reveal substrate gaps that route back to parent-frame slot work.

## 6. What G5 changes about prior slots

Every parent-frame slot currently marked `✅ canonical` is provisionally canonical — fully canonical only when at least one calibration target whose harness touches the slot passes. The first wolfram_poc run will retroactively confirm or surface gaps in:

- Slot 5 (e8-lattice)
- Slot 10 (morphon)
- Slot 11 (morphon-controller)
- Slot 17 (snap) — only if claim 4.1's "digital_root" path goes through snap

Other slots stay provisional until a calibration target exercises them. Calibration coverage IS the substrate's evidence of fidelity.

## 7. Edge cases + design notes

**Tolerance per claim.** Some claims (e8_root_count) are exact (tolerance 0). Some (entropy) need numerical slack (±0.05). For dict-valued expecteds (e.g., `{"e8_inner_products": [...]}`), tolerance can be per-field.

**Receipt chain cross-reference.** A calibration run that invokes `admit_and_store` produces cmplx receipts; the calibration receipt links to those by chain head. If a calibration test is purely geometric (no admit cycle), the chain range is `(head, head)` (empty).

**Re-running calibration.** Targets are re-runnable. A calibration that previously passed but newly fails is a substrate regression — same severity as a failing G4 test, but visible at the behavioral layer rather than the local layer.

**What G5 does NOT do.** It does not require the substrate to be a byte-identical clone of the prior repo. The substrate may be cleaner, faster, more modular — calibration only requires the observable behavior to match. Two substrates that produce the same Rule 30 entropy via different paths both pass.

---

**End of reality_calibration v1. First target build: wolfram_poc.**
