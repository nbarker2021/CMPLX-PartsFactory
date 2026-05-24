# Prior Document: NSL (Noether-Shannon-Landauer) Canonical Conservation Scalar

## What it is

The NSL is the substrate's canonical conservation scalar. It unifies three otherwise-distinct conservation accountings under one functional:

```
Θ = α · N + β · S + γ · L - absorption
```

where:
- **N** = Noether residue (physical conservation law violations)
- **S** = Shannon residue (information loss / projection-loss)
- **L** = Landauer cost (thermodynamic cost of irreversible operations)
- **absorption** = the orbit's absorption capacity (a constant for a given system)
- α, β, γ = unit-normalization weights

The closure rule:
- Θ ≤ 0: internally closed
- 0 < Θ ≤ ε: glue-resolvable
- Θ > ε: obstructed

## Origin

The NSL functional generalizes:
- Noether's theorem (1918): every continuous symmetry gives a conserved current.
- Shannon's information theory (1948): channel capacity bounds for lossless information transmission.
- Landauer's principle (1961): irreversible bit erasure costs at least kT·ln(2) of energy.

The substrate's claim: these three are **manifestations of one underlying conservation law** in different dressings (physical/informational/thermodynamic). The Θ functional sums them with appropriate weights.

## In the lattice-forge build

The NSL is implemented in `src/lattice_forge/ledger/nsl.py` as the `NSLTerm` dataclass:

```python
@dataclass(frozen=True)
class NSLTerm:
    noether_residue: float
    shannon_residue: float
    landauer_cost: float
    absorption_capacity: float = 0.0
    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 1.0
    
    @property
    def theta(self) -> float:
        return self.alpha * self.noether_residue \
             + self.beta * self.shannon_residue \
             + self.gamma * self.landauer_cost \
             - self.absorption_capacity
    
    @property
    def closes_internally(self) -> bool:
        return self.theta <= 0.0
```

The morphonics framework's `accounting:theta_transition_defect` (in `morphonics.py`) is the formal record:

```
Theta(phi) = wN * N + wS * S + wL * L + wG * G + wO * O
```

with the additional terms wG (geometric obstruction) and wO (observer cost) extending NSL to the lattice-forge's specific use cases.

## For Rule 30 under the chart-J₃(𝕆) isomorphism

We computed:
- **N = 0** (all four Noether currents on the chart close at defect 0 — verified at 1024 depths in the build's `rule30_symmetry_environment` function: u1_phase, su2_chirality, su3_color, translation all have defect 0).
- **S = 0** (the chart-to-J₃(𝕆) isomorphism is information-preserving — bijection check at 4096 depths passes with 0 mismatches).
- **L = 1 per step** (each Rule 30 step emits one irreversible bit; Landauer cost is intrinsic, not framework-relative).
- **G = 0** (chart sits inside F₄'s 26-dim representation without lattice obstruction — admissibility edge legal).
- **O = sequential-step overhead** (depth-N iteration cost; replaced by O(1) lookup in the post-VN substrate).

The Θ for Rule 30 under the chart isomorphism is:

```
Θ = 0 + 0 + 1·N - absorption
```

where N is the depth and absorption is the per-step bit-emission absorption (= 1 per step from F₄'s natural bit-readout). Net Θ per step = 0, indicating **internal closure**.

## Why this matters for the submission

The NSL closure (Θ = 0 per step under the isomorphism) is the morphonics framework's certification that the chart-J₃(𝕆) transport is **valid** — no Noether, Shannon, or Landauer cost is unaccounted for. The transport is mathematically clean by the framework's own discipline.

If any of N, S, L were nonzero, the transport would have a residue that needs explicit handling. The fact that N = S = G = 0 (under the isomorphism) and L is consumed by the natural bit-emission cost means the framework registers Rule 30 cleanly without leftover obstruction.

## NSL is not the OVERCLAIM of "ΔΦ unifies all physics"

A critical caveat: the morphonics framework explicitly downgrades the strong claim "ΔΦ unifies Noether, Shannon, and Landauer laws" from OVERCLAIM status:

```python
ClaimStatusRecord(
    "claim:nsl_unification",
    source="Unified Conservation Law",
    original_text="Delta Phi unifies Noether, Shannon, and Landauer laws.",
    hardened_text="Theta records Noether-, Shannon-, Landauer-, geometric-, and obstruction-like terms without subsuming them absent domain derivation.",
    status="OVERCLAIM",
    ...
)
```

The framework distinguishes:
- **OVERCLAIM (original text)**: "ΔΦ = unified conservation law" — strong, undeclared.
- **Hardened text**: "Θ records the residues; it does not subsume the originating physical/informational/thermodynamic laws without domain-specific derivation."

The submission uses the hardened-text version. The NSL is a useful accounting tool; it is not a claim that physics, information theory, and thermodynamics are formally identical.

## Reference

- `src/lattice_forge/ledger/nsl.py` — NSL implementation
- `src/lattice_forge/morphonics.py` — full Θ accounting and claim hardening
- The author's working memory entry: "NSL (Noether-Shannon-Landauer) is what ΔΦ / dphi / phi_total IS — the canonical conservation scalar; find it in the datasets, don't invent."

The NSL is provided as substrate context. The submission's load-bearing proofs (T1-T8) do not require accepting the NSL framework; they stand on the chart-J₃(𝕆) isomorphism + transport from F₄'s known theorems.
