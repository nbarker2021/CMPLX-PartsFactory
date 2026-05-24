# The Weyl Lookup Architecture — Post-VN Substrate

## The architectural claim

Standard von Neumann (VN) architecture: a CPU fetches an instruction, decodes it, executes it, increments the program counter, repeats. State evolves sequentially; computation is one-instruction-at-a-time.

The substrate's alternative: **state evolves by lookup into a precomputed Weyl-group element table**. Each chart-state has a canonical-form fingerprint; the next state is determined by indexing into a table of Weyl-group elements keyed by the fingerprint. The "compute" step is O(1) — a constant-time hash into the table.

This is structurally identical to **content-addressable memory (CAM)**, but with the *specific* address-space being a Weyl group W(L) for some lattice L.

## Scale options

For Rule 30 specifically, the substrate offers a graded set of registrations, each with a different Weyl-table size:

| Lattice | |W| | Table size at 30-bit Weyl element | Use case |
|---|---:|---|---|
| F₄ | 1,152 | ~4 KB | Basic chart isomorphism + n=3 closure (PROVEN) |
| E₆ | 51,840 | ~190 KB | Adds spin-½ lift (the chirality doublet) |
| E₇ | 2,903,040 | ~11 MB | Adds dihedral-eversion structure |
| E₈ | 696,729,600 | ~2.6 GB | Universal substrate, full Magic Square reach |
| Niemeier | varies | various | Specific 24D terminal embeddings |

The submission's load-bearing claims need only **W(F₄) at ~4 KB** — smaller than a single CPU cache line full.

The universality claim (engineering follow-up, Open Obligation O1) targets **W(E₈) at ~2.6 GB** — tractable on consumer hardware.

## The lookup-table architecture in detail

Given any chart state at depth N, the substrate algorithm is:

```
1. Compute canonical Weyl-element fingerprint(N)        ~30 bits
2. table_lookup[fingerprint]                            O(1) memory access
3. Apply returned Weyl element to current chart state   O(rank)
4. Emit bit via diagonal readout                        O(1)
```

Step 1 is the **open problem** for full O(1) depth-from-N (Open Obligation O1). The candidates for computing the fingerprint from N:

- **McKay-Thompson series evaluation** at a CM point of the upper half plane parameterized by N (Monstrous Moonshine machinery; partially exposed by mmdb-unified service).
- **Conway-group orbit calculation** on the Leech lattice's minimal vectors indexed by N.
- **Magic Square direct lookup** if the encoder/decoder gives a closed-form path from N to a specific E₈ root system element.

The mathematical machinery for each candidate exists in the literature. The implementation is engineering.

## Why this matters beyond Rule 30

If the architecture is realized for E₈, the resulting **universal substrate** has:

- O(1) per-step operation for any system with a lossless encoder to E₈.
- ~2.6 GB pre-computed table, fits on consumer hardware.
- Substantially different from VN architecture: parallel-ready, content-addressable, no sequential fetch-decode-execute cycle.

The substrate's claim (Open Obligation O3, universality): **any deterministic dynamical system with a lossless E₈ encoder inherits this architecture**. Rule 30 is the first verified case; the framework supports arbitrary registration.

## Compared to existing post-VN architectures

The substrate's W(E₈) architecture sits among other proposed post-VN designs:

- **Reservoir computing** (Jaeger 2001, Maass 2002): dynamical-system substrates for computation. The substrate is a specific finite-state Weyl-group rather than a continuous reservoir.
- **Cellular automata as computational substrate** (Wolfram, Margolus): grid-based parallel update. The substrate generalizes to non-grid Weyl-group action.
- **Neuromorphic / spiking architectures** (IBM TrueNorth, Intel Loihi): asynchronous event-driven computation. The substrate is synchronous Weyl-element lookup, fundamentally different.
- **Content-addressable memory in databases**: hash tables for O(1) lookup. The substrate is structurally the same, with the specific table being W(E₈) and the hash being a McKay-Thompson canonical form.

The substrate is novel in that the **address space is a specific exceptional Lie group**, not an arbitrary key-value store.

## Caveats

The architectural claim is **structural**, not benchmarked. We do not provide a working prototype of the W(E₈) lookup table in this submission. The construction is an engineering task estimated at 2-4 weeks of focused development.

The benefit of O(1) lookup is realized only for problems whose lossless encoding into E₈ exists and is itself computable in O(1). For Rule 30 at the F₄ level, this is verified (T1-T8). For arbitrary systems, the encoder construction is per-system work.

## Why this is presented in the submission

This architecture is presented for context and to make the scope of the universality claim concrete. The submission does **not** claim the W(E₈) table is built or that the universality is verified.

The submission's proven claims (Tiers A, B, C in `02_SUBMISSION.md`) stand independently of whether the W(E₈) table is ever constructed. They depend only on the chart-to-J₃(𝕆) isomorphism + n=3 SU(3) Weyl closure + transport from F₄'s known theorems.

The architectural claim is included to:
1. Make the substrate framework's larger structural ambition clear.
2. Specify what would close Open Obligation O1 (Wolfram Problem 3 in its strongest form).
3. Provide a constructive path forward beyond the current submission.
