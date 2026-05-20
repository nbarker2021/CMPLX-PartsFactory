# tarpit — Bridge

## Port provided

`symbolic` — `TarPitSymbolicProvider` is the canonical port provider;
`TarpitEcology` is the in-process runtime for program execution.

**Canonical corpus forms** (witness only, not separate packages):
`evolving_tarpit`, `glyphic_tarpit`, `unified_tarpit` — see
`canonical_forms.py` and `identity_review/registers/tarpit-canonical-forms.md`.

## Ports consumed (optional)

- `geometry` — for proper E8 / Niemeier lattice inference when
  `infer_emergent_lattice()` runs. Currently uses statistical
  heuristics over bond demand; the geometry-port-driven form is
  planned.
- `addressing` — `Grain.compute_hash()` could route through MDHG for
  channel-aware bucketing. Currently uses raw SHA256.
- `crystal` — `CrystalRegistry.mount_triad` mounts `Triad.grains` as
  `E8Node`s with receipt `BOND` mint.

## Static imports

| Imports from | What | Why |
|---|---|---|
| `cmplx.geometry.alena` | `COUPLING`, `PHI` | Mass / golden-ratio constants shared across the build. |

The TarPit core is intentionally stdlib-only beyond ALENA constants
so it can be instantiated without the geometry / addressing ports
registered.

## What other components import FROM tarpit

| Importer (current + planned) | What |
|---|---|
| `cmplx.engine.cqe` (planned) | `Grain`, `OutputWall`, `ErrorWall`, `MirrorOperator` — TarPit IS the operational layer (layer 3 of CQE's 5-layer model). |
| `cmplx.snap` (planned wiring) | `Grain.tags + associations` — soft semantic overlay can attach SNAPLabel.all_labels. |
| `cmplx.crystal` (planned wiring) | `Triad` → `Crystal` minting via `CrystalRegistry.create(...)`. |
| `cmplx.worlds.forge` (planned) | `TarpitEcology.evolve()` for program-as-world evolution. |

## Cross-component semantics

TarPit is where **symbolic computation grounds into the geometric
substrate**. A program (string of `}<>+[]01`) reduces to:

```
program string
   │
   ▼
TarpitEcology.load_program(p) → instruction stream
   │
   ▼ (per step)
Grain operations (flip / move / loop / apply / nest)
   │                                                 │
   ▼                                                 │
Bond emergence (dim_2D test) → Dust → check closure ─┘
   │                                            │
   ▼ (success)                                  ▼ (fail)
OutputWall (X.d₁d₂…)              ErrorWall (mirror_candidate?)
   │                                            │
   │                                            ▼
   │                              MirrorOperator.apply_mirror()
   │                                            │
   │                              MirroredState (counter_grains, new_mediator)
   │                                            │
   ▼                                            ▼
Receipt chain                       (retry as overlay)
```

The two wall languages are the **boundary between symbolic and
geometric**: every step either produces a serialized closure code
(OutputWall) or a reproducible error signature (ErrorWall) that
mirroring can attempt to resolve.
