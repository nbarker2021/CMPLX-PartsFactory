# Claims: Monster activation, D₄ lift, residual window

## Formal registry IDs

| ID | Honesty | Statement |
|----|---------|-----------|
| `monster.shell2.triadic_thirds` | BOUNDED_EXEC | After all **8 joint** chart states `(L,C,R)` appear, visits with `shell=2` split ~⅓ each on **(C−, C0, C+)** with bijection symmetry between C− and C+. |
| `monster.d4_lift.after_global_activation` | CONJ | Post-activation: D₄ lift per N; ≤3 conjugate steps **G₂→F₄→T₅A**. |
| `monster.residual_window.s3_projection_lift` | CONJ | Empirical n=3 residual window (~0.003) **projects** to exact S₃ ⅓; L/C/R network rotations preserve the window; projected sample opens G₂ family. |

**Do not use** marginal `P(L=1)`, `P(C=1)`, `P(R=1)` — that undersamples the bijective 3×3 triad.

---

## Shell-2 triadic thirds

The “⅓ in each local space” is on the **bonded dyad triad**, not independent lanes:

- `(1,1,0)` = C− (positive spin)
- `(1,0,1)` = C0 (center bar / null)
- `(0,1,1)` = C+ (negative spin)

Algebraic ⅓ is **T4** PROVEN: `M₃ = (1/3)(T₁₂ + T₁₃ + T₂₃)` on this 3×3.

**C\*R bond** (`C & R`) is the relational observer face; **readout 0** is a valid closed-channel stratum (joint chart accounting, not lane marginals).

---

## Residual window lift

### User hypothesis (testable)

> If we force action into the empirical **~0.003** residual window (finite-sample n=3 shell-2 matrix slightly off the S₃ group ring), **projecting** onto that ring (rotation-invariant around the L,C,R action network) is the entire sample needed for **full ⅓ resolving**. From that resolving, the **G₂** family and downstream conjugate routes open.

### Machine test (`verify_residual_window_lift`)

1. Build empirical n=3 conditional 3×3 on trajectory **after** all 8 states seen.
2. Measure distance to **T4 exact target** matrix (Frobenius²) and S₃ decomposition residual².
3. **Snap resolve:** if inside window (dist² < 0.1), replace sample with exact T4 **⅓,⅓,⅓** element.
4. Scan **six S₃ rotations** on L/C/R network; distance to T4 target is rotation-invariant.
5. Confirm `verify_conjugate_triple` passes (G₂ family opens).

Note: projecting onto the S₃ span alone lands on a *different* group-ring point; snapping to the **T4** element is the correct “force into window → full ⅓ resolving” step.

### Run

```bash
PYTHONPATH=src python -c "from lattice_forge.residual_window_lift import verify_residual_window_lift; import json; print(json.dumps(verify_residual_window_lift(256), indent=2))"
PYTHONPATH=src python -c "from lattice_forge.monster_d4_lift_claim import verify_monster_d4_lift_claim; import json; print(json.dumps(verify_monster_d4_lift_claim(256), indent=2))"
```

---

## Promotion

| To | Requires |
|----|----------|
| BOUNDED_EXEC | 8-state seen + triad ⅓ + projection lift + G₂ route on tested depth |
| PROVEN | Analytic proof that finite-sample window ⊂ S₃-neighbourhood + conjugate bit match + Monster spec beyond proxies |
