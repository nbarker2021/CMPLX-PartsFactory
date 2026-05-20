# tarpit — Interface

The **Morphonic Ribbon Ecology** — TarPit synthesizes BitChanger,
Brainfuck, and Jot into a unified symbolic-computation substrate
where every primitive is a `Grain` (a 1D ribbon in representation
space), grains bond into `Dust` and `Triad`s, and every step emits
either an `OutputWall` or an `ErrorWall`.

Promoted from `evolving_tarpit/` + `glyph_tarpit/` + `unified_tarpit.py`
canonicals (the three exemplars). Converted to pure-stdlib (no numpy)
so it lives alongside the rest of `cmplx`.

## Surface

### Grain primitives

- `GrainType` — BIT / COMBINATOR / MEDIATOR / DUST / TRIAD
- `DimensionalExtent` — extent vector + L_max/A_max/V_max capacity
  bounds. Methods: `norm`, `mass_1d`, `parallelogram_area(other)`,
  `is_materially_2d(other, epsilon)`, `mass_2d(other)`.
- `Grain` — irreducible unit: `id, grain_type, value (bit), extent,
  position, certificates, tags, associations`. Methods: `flip()`,
  `observe()`, `can_bond_with(other)`, `compute_hash()`, `to_ribbon()`.
- `Ribbon` — explicit `start, end, value`. `vector` / `length` /
  `intersects(other)`.
- `GrainField` — the tape. Holds grains per position, evolves through
  time, computes digital root + entropy. `create_grain`, `set_grain`,
  `flip_current`, `move_pointer`.

### Bond chemistry

- `Dust` — minimal composite: `(a, b, mediator, certificates)`.
- `Triad` — stabilized higher form built from a closure-checked Dust.
- `BondEngine` — `attempt_bond(a, b)`, `check_closure(dust)`,
  `promote_to_triad(dust)`, `get_bond_statistics()`.

### Wall languages

- `WallType` — OUTPUT / ERROR.
- `ErrorClass` — CAPACITY_EXCEEDED / INVARIANT_VIOLATION /
  BOND_FAILURE / MIRROR_REQUIRED / TIMEOUT / INVALID_STATE.
- `OutputWall` — `(closure_count, residual_digits, residual_set,
  grains, dusts, certificates)`. `serialize()` returns `X.d₁d₂…`.
- `ErrorWall` — `(error_class, stack_signature, reproducer_grains,
  violated_invariants, suggested_actions, mirror_candidate)`.
- `MirroredState` — result of mirror operator: `counter_grains +
  new_mediator + certificates`. `is_valid_bridge()`.
- `MirrorOperator` — `pole_inversion`, `constraint_dualization`,
  `chamber_reflection`, `apply_mirror`.
- `WallEmitter` — `emit_output(...)`, `emit_error(...)`,
  `get_wall_statistics()`.

### Jot encoding

- `SKCombinator` — S / K / I combinator representation.
- `JotGrainEncoder` — `interpret_bits(bits, field)`, `_execute_apply`
  (Jot `0` = bond), `_execute_nest` (Jot `1` = extend extent).

### Ecology (the provider)

- `ComputationPhase` — OBSERVE / REFLECT / SYNTHESIZE / RECURSE
  (MORSR cycle).
- `ComputationResult` — `program, grain_field, output_walls,
  error_walls, dusts, triads, steps_executed, bonds_formed,
  mirrors_applied, success, final_digital_root, final_mass`.
- `TarpitEcology` — `load_program(p, language)`, `step()`, `run()`,
  `evolve(iterations, mutation_rate)`, `infer_emergent_lattice()`,
  `get_statistics()`.

### Instruction set

| Char | Language | Op |
|---|---|---|
| `}` | BitChanger | Flip current bit, then move right |
| `<` | BitChanger / BF | Move pointer left |
| `>` | Brainfuck | Move pointer right |
| `+` | Brainfuck | Flip current bit |
| `[` | both | Loop start (jump past `]` if bit=0) |
| `]` | both | Loop end (jump back to `[` if bit=1) |
| `0` | Jot | Apply: bond with neighbor grain |
| `1` | Jot | Nest: extend extent vector |

### Provider

`TarpitEcology` registers on the `symbolic` port of
`MorphonController`. The single registered ecology hosts a single
program at a time; multi-program use means multi-instance.

## What's NOT in this layer

- True E6 token codec — `e6_tarpit_bridge` variants exist in the
  corpus but stand alone; planned as `cmplx.symbolic.e6` (or merged
  with `cmplx.geometry`).
- True intersect-test geometry — `Ribbon.intersects` is the simple
  parallel/non-parallel form; full polytope intersection is a TBD.
- The full GVS toroidal-flow / world-spawning hookup — that's
  `cmplx.worlds.forge` (planned).
