# engine.cqe — Interface

**CQE — Cartan-Quadratic Equivalence executor.** The pre-CMPLX
identity tag of every system in this build; in the unified form,
`engine.cqe` is the orchestrator that wires everything together.

Two main entry points, blending the canonical "Unified Runtime" and
"Modular Orchestrator" forms found in the corpus:

- `process_text(text, mode)` — 8-stage unified pipeline
- `solve_problem(problem, domain_type, mode)` — 5-phase modular pipeline

Both share governance, NSL conservation, receipt minting, and CQE
atom population.

## Surface

### CQEAtom (the Morphon-with-CQE-fields view)

- `CQEAtom(morphon, source_text=None)` — wrap an existing Morphon;
  populate any missing CQE fields (quad_encoding, parity_channels,
  sacred_frequency, digital_root, fractal_coordinate).
- `CQEAtom.forge(payload, ...)` — construct a fresh Morphon with all
  CQE fields pre-populated.
- Helpers: `quad_from_text`, `quad_from_payload`, `parity_from_quad`,
  `digital_root_of_quad`.

### Pure-function primitives

**Mandelbrot** (`mandelbrot.py`):
- `mandelbrot_iterate(c_real, c_imag, max_iter)` → `{escaped, iterations, z_norm, c}`
- `hash_to_complex(text)` → `(c_real, c_imag)`
- `classify_behavior(result)` → `"BOUNDED" / "FAST_ESCAPE" / "MEDIUM_ESCAPE" / "SLOW_ESCAPE"`
- `analyze_string(text)` — end-to-end string → Mandelbrot report
- `is_in_set(c_real, c_imag)` — boolean membership

**Toroidal** (`toroidal.py`):
- `torus_point(u, v, R, r)` → `(x, y, z)`
- `generate_toroidal_shell(n_points, seed)` → list of points with
  `{u, v, position, pattern, radius_ratio}`
- 4 rotation patterns: `poloidal / toroidal / meridional / helical`
- `pattern_distribution(shell)`, `pattern_balance(shell)`
- `sacred_frequency(text)` → `[174, 963]` Hz from SHA256

**Banding** (`banding.py`):
- `compute_v_total(scores, weights)` — weighted mean
- `band_for(v)` → `"BREAKTHROUGH" / "PEER_READY" / "EXPLORATORY"`
  (thresholds: 0.80 / 0.60)
- `ValidationBand` enum

### DomainAdapter (problem → E8 vector)

- `embed_p_problem(size, complexity_hint)` — small norm, regular
- `embed_np_problem(size, nondeterminism)` — larger norm, scattered
- `embed_optimization_problem(variables, constraints, objective_type)`
- `embed_scene_problem(scene_complexity, narrative_depth, character_count)`
- `embed_text(text)` — SHA256 → unit sphere → E8 root norm √2
- `hash_to_features(payload)` — generic JSON-payload fallback
- `adapt(problem, domain_type)` — dispatcher

### CQEObjectiveFunction (multi-component scoring)

- `evaluate(vector, reference_channels, domain_context, v_before)`
  → `ObjectiveScores` with:
  - `phi_total` (weighted combination)
  - `parity_consistency`, `chamber_stability`,
    `geometric_separation`, `kissing_alignment`
  - `nsl_sectors` (the NSL ΔN/ΔI/ΔL triple)

### CQEGovernance (policy layer)

- 6 `GovernanceLevel`s: `PERMISSIVE → STANDARD → STRICT → TQF_LAWFUL → UVIBS_COMPLIANT → ULTIMATE`
- 9 `ConstraintType`s: quad / e8 / parity / governance / temporal /
  spatial / logical / semantic / nsl
- `CQEConstraint(validator, repair, severity)` — register custom
- `CQEPolicy(constraint_ids, auto_repair, strict_enforcement, violation_threshold)`
- `validate(item, ctx) -> {valid, violations, constraint_count, policy}`
- `repair(item, ctx) -> (item, applied_repair_names)`
- 5 built-in constraints: quad range, E8 bounds, parity consistency,
  NSL conserved, timestamp validity
- 6 built-in policies matching the levels

### OperationMode (stage activation)

- `BASIC` — e8 + phi + governance + validation
- `ENHANCED` — adds semantics + atom population
- `SACRED_GEOMETRY` — adds toroidal shell
- `MANDELBROT_FRACTAL` — adds fractal analysis
- `ULTIMATE_UNIFIED` — everything including MORSR exploration

### CQERunner (the orchestrator)

- `process_text(text, mode)` — 8-stage pipeline; returns `TextResult`
  with e8, fractal, toroidal_patterns, phi_scores, nsl_sectors,
  governance_valid, v_total, band, receipt_ids
- `solve_problem(problem, domain_type, mode)` — 5-phase pipeline;
  returns `ProblemSolution` with initial/optimal vectors, channels,
  objective_score, phi_scores, recommendations, receipt_ids
- `forge_atom(payload, parent, source_text)` — mint a CQEAtom +
  MINT receipt

### CQEProvider (the port)

- `process_text` / `solve_problem` / `forge_atom` pass-throughs
- `set_mode(mode)`, `set_governance_policy(name)`
- `attach_morsr(morsr_provider)` — wire MORSR for Phase 3

Registers on the `engine` port of `MorphonController`.

## What's NOT in this layer (yet)

- `LambdaTerm` reducer — λ-calculus primitive (separate from TarPit
  Jot). Planned `cmplx.symbolic.lambda` follow-up.
- `CQERAG` — retrieval-augmented generation with CQE provenance.
- Slice tools (Legendre, Galois, etc.) — domain-specific analyzers.
- `TransformRequest`/`CQERunner.run(request)` typed shape — current
  form takes plain dicts.
- Full TQF Orbit-4 and UVIBS 80D constraint sets — placeholders for
  now; policies exist but use the starter constraints.
- HTTP service skin (`/process`, `/solve`, `/health`) — lives in
  `services/cqe_service.py`, planned.
