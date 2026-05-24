# Module Index — full operational depth

Every `lattice_forge` module with its mathematical content, its API surface, and its honesty label. Use this as the searchable reference; use `ARCHITECTURE.md` for the layered map.

The index does NOT reduce the layers. Each entry preserves the module's actual algebraic/operational vocabulary.

---

## Ring 1 — proven foundation

### `octonion.py`
Cayley-Dickson construction of the octonion algebra `O = R + R·e_1 + ... + R·e_7`. Fano-plane triples `(1,2,3), (1,4,5), (1,7,6), (2,4,6), (2,5,7), (3,4,7), (3,6,5)` with the convention `e_i · e_j = e_k` for the listed cyclic order, `-e_k` reversed.

API:
- `Octonion(components)` — 8-tuple constructor
- `Octonion.real(x)`, `Octonion.basis(i)` — convenience constructors
- `__add__`, `__sub__`, `__neg__`, `__mul__` — algebra ops
- `conjugate()` — fix real part, negate imaginary
- `norm_squared()`, `norm()`, `inverse()`
- `real_part()`, `imag_part()`, `is_real()`
- Pre-built `O_ONE`, `O_E1`, ..., `O_E7`

Verifier: `verify_octonion_axioms()` — T1 PROVEN. Tests alternativity, the norm form `|xy| = |x||y|`, conjugate involutivity, and basis multiplication against the Fano table.

### `jordan_j3.py`
The exceptional Jordan algebra `J_3(O)` = 3×3 Hermitian octonionic matrices under the symmetrized product `A∘B = ½(AB + BA)`. 27-dimensional over R.

API:
- `J3` class with `+`, `-`, `*`, `jordan_product`, `trace`, `determinant`
- Diagonal idempotent construction
- Trace-stratum projections (shell=0, 1, 2, 3)

Verifier: `verify_j3o_axioms()` — T2 PROVEN.

### `f4_action.py`
The S_3 ⊂ W(F_4) action on the three trace-2 idempotents of J_3(O). Verifies n=3 SU(3) Weyl closure exactly over ℚ.

API:
- `n3_su3_closure_matrix_exact()` — M_3 = (1/3)(T_(1,2) + T_(1,3) + T_(2,3)) as exact Fraction matrix
- `verify_n3_su3_closure_exact()` — T4
- `search_for_su3_closure_scale(max_scale)` — T5
- `decompose_8x8_via_block_action_exact(n_steps)` — T6
- `closed_form_rule30_8x8_transition_exact()` — T7 (the chart-level transition matrix with row sums = 1)

The `closed_form_rule30_8x8_transition_exact` returns `{states, matrix}` where matrix is 8×8 of Fractions in `{0, 1/4, 1/2}`.

### `rule30.py`
Rule 30 CA evolution from a single-cell seed. Includes the chart trajectory, the chart-J_3(O) isomorphism verifier, and the chart local readout.

API:
- `canonical_rows(N)` — list of dicts mapping position → cell value, depth 0..N
- `rule30_bit(L, C, R)` — the local rule
- `verify_chart_j3o_isomorphism(max_depth)` — T3 PROVEN at 4096 depths × 6,272 checks, 0 mismatches
- `verify_rule30_chart_local_readout(max_depth)` — BONUS, 0 forward defects at depth 4096

### `substrate_map.py`
The 8-state Rule 30 routing table + 8×8 Weyl routing. Each chart state maps deterministically to a next-state direction; the Weyl routing assigns each chart state to a Weyl orbit class.

API:
- `RULE30_ROUTING_TABLE` (8×4 dict)
- `WEYL_13_TABLE` (8×8 dict)
- `EMISSION_TABLE` (8-element bit emission rule)
- `verify_substrate_map(max_depth)` — at depth 4096

### `forge.py`
Forge facade over the seed ledger. `Forge.open(path).can_close(src, tgt)` returns whether a commutability path exists between two algebraic objects.

API:
- `Forge.open(workdir)` — opens a Forge instance
- `Forge.can_close(src, tgt)` — yes/no + path
- T8 PROVEN: 8 paths F_4 → Niemeier:{E8^3, D16+E8, A17+E7, D10+E7², A11+D7+E6, E6⁴, A5⁴+D4, D4⁶}

### `ledger/`
SQLite-backed seed database. Immutable root of trust.

Tables:
- Root systems (A, B, C, D, E_6, E_7, E_8, F_4, G_2)
- Niemeier terminals (24 lattices)
- Admissibility edges (65)
- NSL boundary residues
- Involutions

### `core.py`
The universality probe primitive: single-tape chart construction, S_3 closure test.

---

## Ring 2 — companions

### `chart_codec.py` (Regime C — triadic)
Lossless S_3 word codec for the chart's shell=2 sub-trajectory. Each shell=2 transition encodes as the unique S_3 transposition mapping source to target.

API:
- `SHELL2_STATES` — `((1,1,0), (1,0,1), (0,1,1))`
- `S3` — six S_3 elements as 1-indexed permutations
- `apply_s3(perm_name, state)` — apply S_3 element to chart state
- `shell2_transition_element(src, dst)` — the unique mapping element
- `encode(shell2_traj)`, `decode(encoded)` — round-trip codec
- `verify_chart_codec(max_depth)` — 0 round-trip mismatches at depth 4096

### `chart_codec_d4.py` (Regime C' — quadratic)
Full-chart D_4 antipodal codec. Each of the 8 chart states maps uniquely to `(axis ∈ {0,1,2,3}, sheet ∈ {0,1})`.

API:
- `CHART_STATES` — all 8 chart triples
- `ANTIPODAL_LABEL[state]` — axis ∈ {0,1,2,3}
- `SHEET_SIGN[state]` — sheet ∈ {0,1}
- `chart_state(axis, sheet)` — inverse map
- `encode_d4(trajectory)`, `decode_d4(encoded)` — round-trip
- `axis_sheet_subsequence(encoded, axis)` — per-axis projection
- `verify_chart_codec_d4(max_depth)` — 0 round-trip mismatches at depth 4096

### `block_tower.py` (Regime A)
Hierarchical Rule 30 row checkpoint store. Stores row snapshots at every `base_page` boundary; replays at most `base_page` Rule 30 steps from the nearest stored row.

API:
- `Rule30Checkpoints(max_depth, base_page=64, max_level=3)` class
- `.row_at(depth)`, `.center_bit_at(depth)` — O(base_page) queries
- `verify_block_tower(max_depth)` — 0 mismatches at depth 4096

### `rule30_block_extractor.py`
Block-addressed nth-bit extractor on top of `Rule30Checkpoints`. Per-query time bounded by `base_page` row-steps.

API:
- `Rule30BlockExtractor(max_depth=4096)` class
- `.nth_bit(N)`, `.bit_range(start, end)` — query interface
- `verify_extractor(max_depth)`, `benchmark_extractor(depths)`

### `decomposition/` (Ring 2 paper subpackage)
Vendored Rule 30 decomposition paper modules. Sections 1–10 of the standalone paper.

- `rule30_decomposition.py` — Theorems 2.1, 3.1, 4.1, 5.1 (algebraic identities)
- `checkpoint_store.py` — Construction 7.1 (block-checkpoint extractor)
- `fast_rule30.py` — big-int Rule 30 evolution for large depth
- `empirical.py` — Section 6 (Lucas-sparsity), Section 8 (entropy, density, periodicity)

---

## Ring 3 — umbrella (forward research)

### `rule90_linearization.py`
The Rule 30 = Rule 90 ⊕ (C ∧ ¬R) decomposition. Lucas closed form. Duhamel reconstruction.

API:
- `correction(L, C, R) = C & (1 - R)` — the GF(2) correction term
- `linearization_identity_holds()` — truth-table verification
- `lucas_bit(d, x)` — Rule 90 cell from single-cell seed, O(log d)
- `rule30_center_via_decomposition(N)` — Theorem 2.3 reconstruction
- `correction_from_chart(state)` — chart projection
- `CORRECTION_FIRING_AXES_SHEETS` — `{(2,0), (3,1)}`
- `verify_rule90_linearization()` — verified at depths 1..1024

### `f2_majorana.py`
F_2 quadratic forms, Arf invariant, edge-glue criterion.

API:
- `F2Quadratic(A)` class — upper-triangular matrix over F_2
- `.evaluate(v)`, `.bilinear(v, w)`, `.radical()`, `.arf_invariant()`
- `rule30_correction_quadratic()` — Q(L,C,R) = C + CR with Arf = 0
- `can_glue_edges(q_left, q_right)` — Arf-matching criterion
- `verify_f2_majorana()` — known Arf values verified

### `contributions_registry.py`
SQLite registry of validated additions to the umbrella's exact-data backbone.

Schema:
- `contributions(id, kind, key_json, value_json, provenance, validated_by, validation_rationale, validated_at, content_hash)`
- `proposals(id, kind, key_json, value_json, provenance, proposed_at, status, rejection_reason, decided_at)`

API:
- `Registry(path)` class with `.propose(...)`, `.lookup(...)`, `.all_entries(...)`, `.stats()`
- `.register_validator(name, callable)` — install a validator

### `contribution_validators.py`
Four F_2-deterministic validators:
- `f2_arf_validator` — recomputes Arf from the matrix
- `lucas_recurrence_validator` — Pascal recurrence check
- `rule30_decomposition_validator` — Theorem 2.3 check
- `f2_edge_glue_validator` — Arf-matching criterion

`install_default_validators(registry)` registers all four.

### `actuation.py`
±1 spectral actuation primitives. The bijection-forcing layer.

API:
- `Actuation(sign)` class with `Actuation.POSITIVE`, `Actuation.NEGATIVE`
- `.compose(other)`, `.spectrality` (F_2 bit form)
- `actuate_octonionic(state, actuation)` — multiplies octonion by ±1
- `actuate_kinematic(state, actuation)` — θ → θ + π for -1
- `actuate_quad(quad, actuation)` — all 4 Oloids
- `paired_actuation_read_octonionic(N, enum)` — read-with-bijection
- `verify_actuation_module()` — paired_read_consistency = 1.000

### `oloid_rolling.py`
Single Oloid, combinatorial state.

API:
- `OloidState(sheet, phase, parity)` class
- `.roll(bit)`, `.as_dyad()` (returns (head, tail))
- `roll_chart_landing(bits)`, `roll_chart_trace(bits)`
- `cyclic_rotate`, `antipodal_swap`, `weyl_mirror` — symmetries
- `enumerate_landings(K)` — K-bit landing table
- `verify_oloid_rolling()` — 4-period structural checks

### `oloid_dual_path.py`
Three-dyad parallel Oloid with cyclic involution superscript. Read-then-verify flow.

API:
- `DualPathOloid(podal, antipodal, shared, level)` class
- `.roll(bit)`, `.involute()`, `.involute_k(k)`, `.head_tail_triad()`
- `roll_dual_path(bits)`, `roll_dual_path_trace(bits)`
- `dyad_index_at_depth(N, level) = (N + level) mod 3`
- `read_tape_with_enumeration(N, enum)` — read-then-verify (100% match)
- `gauge_inverted_initial()` — 180° gauge twist

### `oloid_octonionic.py`
Octonion-grounded Oloid. The actual algebra.

API:
- `OctonionicOloidState(octonion)` class
- `.roll(bit)` — right-multiplies by e_4 (bit=0) or e_5 (bit=1)
- `.head_bit()`, `.orient_bit()`, `.dominant_basis_index()`
- `.gauge_inverted()` — multiply by `O_ONE * (-1)`
- `roll_octonion(bits)`, `roll_octonion_trace(bits)`
- `orient_bit_information_content(sequences)` — measures non-trivial 1 bit
- `verify_octonionic_oloid()` — e_4² = -1, e_4⁴ = +1 verified algebraically

### `quad_oloid.py`
Four-Oloid D_4 ring with role-specific generators.

API:
- `QuadOloid(o1, o2, o3, o4)` class with `.roll(bit)`, `.quad_orient_signature()`, `.ring_closure_check()`
- Generators: `(e_4, e_5)` for O_1, `(e_5, e_6)` for O_2, `(e_6, e_7)` for O_3, `(e_7, e_4)` for O_4
- `roll_quad(bits)`, `quad_orient_information_content(sequences)`
- Empirically traps in quaternion sub-algebras (2/16 distinct signatures)
- `verify_quad_oloid()`

### `oloid_kinematic.py`
Continuous Oloid rolling with gauge bijection forced.

API:
- `KinematicOloidState(theta, parity)` class
- `.roll(bit)` — θ → θ ± π/2
- `.quarter_index()`, `.sheet()`, `.phase()`, `.as_tuple()`
- `gauge_inverted_kinematic_initial()`, `gauge_inverted_quad_initial()`
- `correspondence_test(bits, force_bijection=True)`
- `quad_oloid_inferred_sheet_phase(q, step, ...)`
- 4 structural identities pass; joint correspondence at chance (sub-algebra trap)

### `j_modular_matrix.py`
9×9 j-modular matrix at level 9 for T_g convolution.

API:
- `T_2A_COEFFICIENTS`, `T_3A_COEFFICIENTS` (and indirectly via voa_harness: T_1A, T_5A, T_7A)
- `J_MATRIX_2A`, `J_MATRIX_3A` — 9×9 integer matrices
- `get_j_matrix(g)` — lookup by class name
- `lift_octonion_to_v9(o)` — 8 octonion components + L_2 norm squared
- `apply_j_matrix(v, J)` — 9-dim convolution
- `modular_parity_signature(v)`, `modular_parity_per_coordinate(v)`
- `verify_j_modular_matrix()`

### `gauss_fourier_lift.py`
9-DFT, level-9 Gauss sum, spectrograph readout.

API:
- `octonion_gauss_reduce(o)` — F_2 reduction with DC parity
- `octonion_l2_reduce(o)` — antisymmetric L_1-sum lift
- `dft_9_complex(v)`, `dft_9_real_cosine(v)`, `inverse_dft_9_complex(F)`
- `gauss_sum_9_principal()` — Ramanujan c_9(1) = 0
- `gauss_sum_9_against(v)` — inner product against Gauss kernel
- `spectrograph_readout(o)` — full readout dict including DC "middle bar"
- `paired_spectrograph(o_pos, o_neg)` — ±1 actuation bijection check
- `verify_gauss_fourier_lift()`

### `three_move_closure.py`
The actual O(1) computation. Rank-1 idempotent paired-actuation closure.

API:
- `paired_state_sum(pos, neg)`, `paired_state_max_abs(pos, neg)`
- `three_move_closure_demo(move_count=3, bit=0)`
- `closure_depth_at(initial_pos, initial_neg, bit, max_moves)` — returns the depth at which the bijection completes (0 for canonical ±O_ONE pair)
- `verify_three_move_closure()`

### `voa_lookup.py`
Scaffolding for the McKay-Thompson primitive (O2).

API:
- `CORRECTION_CLASS_HYPOTHESIS` — `{(2,0): "2A", (3,1): "3A"}`
- `MONSTER_SCALAR = 47 * 59 * 71 = 196883`
- `correction_class_for(axis, sheet)` — class lookup
- `mckay_thompson_coefficient_parity(g, k)` — NOT IMPLEMENTED (O1')
- `architecture_summary()` — structured architecture record

### `voa_harness.py`
Empirical McKay-Thompson parity test with bijection forced. 5-lane L/C/R chirality.

API:
- `T_1A_COEFFICIENTS`, `T_2A_COEFFICIENTS`, `T_3A_COEFFICIENTS`, `T_5A_COEFFICIENTS`, `T_7A_COEFFICIENTS`
- `LANE_PARTITION` — `{1A: C, 2A: C, 3A: C, 5A: L, 7A: R}`
- `mckay_thompson_coefficient_parity(g, k)` — table lookup
- `INDEX_HYPOTHESES` — 4 candidate index functions (k=N, k=firing_count, k=N-1, k=N+firing)
- `run_hypothesis(max_depth, index_fn, table_size)` — single-hypothesis run
- `verify_voa_harness(max_depth)` — full sweep with bijective rates
- `five_lane_router(max_depth, table_size)` — L/C/R partition test
- T_3A bijective rate ~89% at depth 256

### `g2_f4_t5_conjugate.py`
The conjugate triple routing. Three-max-zero bijection coverage.

API:
- `G2_REPRESENTATIVE_PERMUTATION = (0, 2, 3, 1, 4, 6, 7, 5)` — Fano triality
- `F4_REPRESENTATIVE_AXIS_CYCLE = {0: 0, 1: 2, 2: 3, 3: 1}`
- `g2_representative_permutation(state)` — apply G_2 element
- `f4_representative_chart_cycle(axis)` — apply F_4 cyclic
- `t5_modular_conjugate(k)` — T_5A parity at index k
- `conjugate_triple_route(N, enum)` — routing function
- `verify_conjugate_triple(max_depth=256)` — 100% match, ≤3 moves

### `forced_involution_cache.py`
Failure-orbit cache with O(1) sub-log lookup.

API:
- `DEFAULT_INVOLUTIONS` — 8 named involutions (identity, 3 swaps, antipode, 3 swap+antipode)
- `axis_preserves_under(involution)` — chart-axis invariance test
- `run_forced_involution_sweep(involutions)` — full sweep
- `ForcedInvolutionCache` class with `.populate()`, `.will_fail(name, state)`, `.failure_bit_pattern(name)`, `.stats()`
- Reveals S_3 sum-zero relation `60 ⊕ 90 ⊕ 102 = 0` among swap failure bit patterns
- `verify_forced_involution_cache()` — ~100 ns/lookup

### `formulaic_instantiation.py`
Single-request (head, tail) extractor.

API:
- `formulaic_query(N, chart_axis_oracle=None)` — returns head + tail + path
- `_build_chart_axis_oracle_table(max_n)`, `make_table_oracle(max_n)`
- `verify_formulaic_instantiation(max_depth)` — measures oracle speedup
- Oracle speedup: ~3942× over enumeration fallback

### `reduced_nbody.py`
(N, C, K) Lagrangian formulation.

API:
- `ReducedNBodyState(N, C, K, chart_axis, chart_sheet)` class with 5 coords
- `lagrangian_value(state)` — M_3 Weyl-average evaluation
- `reduced_state_at_depth(N, base_page=64)`
- `reduced_trajectory(start_N, end_N)`
- `conserved_quantities(state)` — chart_axis, Arf = 0, F_4 Weyl orbit class
- `evolve_one_step(state)`, `evolve_many_steps(initial, n_steps)`
- `verify_reduced_nbody(max_depth)` — chart_match_rate = 1.0, reduction ~51× at depth 256

---

## Substrate enumeration tier (backwalk)

### `backwalk/`
The substrate enumeration engine. Materializes the W(E_8) Weyl-element pod for the O1 lookup.

| Module | Role | Honesty |
|---|---|---|
| `schema.py` | JSONL schema for backwalk records | structural |
| `lattice_catalog.py` | Root system / Niemeier lattice catalog | inherited from Ring 1 ledger |
| `exceptional_spine.py` | F_4 → E_6 → E_7 → E_8 ascending spine | structural |
| `e8_weyl_pod.py` | W(E_8) Weyl-element pod construction | EXPRESSIBLE (O1) |
| `glue_weyl.py` | Weyl-equivariant glue tables | structural |
| `weyl_bond_dual.py` | Dual Weyl bond enumeration | BOUNDED_EXEC at tested range |
| `weyl_bond_quadrant.py` | Quadrant-restricted Weyl bond | BOUNDED_EXEC |
| `lattice_space_job.py` | Full lattice-space exhaustion driver | BOUNDED_EXEC at tested range |
| `generator.py` | Orchestration generator | structural |
| `hydrate.py` | Materialization / hydration | structural |
| `proof_capture.py` | Per-record proof capture | structural |

### `algebra/o1_registry.py`
The O1 (W(E_8) lookup) registry. Receives validated Weyl-element entries from the backwalk and exposes O(1) lookups.

### `empirical/`
Empirical platform exhaust runner (CPU/GPU class targets).

- `manifest.py` — platform manifest schema
- `resolver.py` — platform → environment resolver
- `runner.py` — per-platform run driver
- `exhaust.py` — multi-platform exhaustion runner

### `honesty_harness.py`
Honesty-label aware harness for open claims. Routes each claim's verifier and reports per the umbrella's honesty taxonomy.

### `monster_d4_lift_claim.py`
Monster D_4 lift claim — bridges the chart's D_4 antipodal codec to the Monster's representation theory.

### `residual_window_lift.py`
Residual S_3 projection lift — quantifies the residual after the 3-step Weyl closure (T4).

---

## Auxiliary modules

### `cli.py`
Lattice-forge CLI surface. `lattice-forge falsify --tier-a`, etc.

### `server.py`
Optional FastAPI server for commutability tree queries. Not required for the proofs.

### `overlay.py`
Project-local interaction state.

### `terminal_tree.py`
24D terminal composition trees.

### `morphonics.py`
Morphonic State Closure Framework model + verifier.

### `seed.py`
Read-only seed database access.

### `tools/`
Pipeline tools (six-stage flow):
- `tarpit.py` — TarPit evaluation
- `morsr.py` — MORSR 240-pulse measurement
- `nsl.py` — NSL (Noether-Shannon-Landauer) accounting
- `mdhg.py` — MDHG addressing
- `speedlight.py` — SpeedLight receipt
- `transport.py` — transport tower
- `geometry.py` — geometric primitives
- `receipt.py` — receipt management
- `base.py` — base types

### `witness/`
Witness HTTP API for the claim system:
- `api.py`, `engine.py`, `formal.py`, `model.py`, `readout.py`, `spec.py`, `state_keys.py`

### `falsify/`
Machine-falsifiable Tier A / B harnesses:
- `tier_a.py` — Tier A breaks (Ring 1)
- `tier_b.py` — Tier B (companions)

### `witness_state_store.py`
In-memory witnessed-state table (per Forge instance).

---

## Test surface (per module)

```
Ring 1:
  test_octonion.py, test_jordan_j3.py, test_chart_isomorphism.py,
  test_f4_action.py, test_substrate_map.py
  test_rule30_proof_obligation_ledger.py

Ring 2:
  test_chart_codec.py, test_chart_codec_d4.py, test_block_tower.py

Ring 3:
  test_rule90_linearization.py, test_f2_majorana.py,
  test_oloid_rolling.py, test_oloid_dual_path.py,
  test_oloid_octonionic.py, test_quad_oloid.py, test_oloid_kinematic.py,
  test_actuation.py, test_j_modular_matrix.py,
  test_gauss_fourier_lift.py, test_three_move_closure.py,
  test_g2_f4_t5_conjugate.py, test_voa_harness.py,
  test_five_lane_router.py, test_forced_involution_cache.py,
  test_reduced_nbody.py

Backwalk:
  test_algebra_o1.py, test_backwalk_pilot.py,
  test_empirical_platforms.py, test_honesty_harness.py,
  test_weyl_bond_dual.py, test_monster_d4_lift_claim.py

Infrastructure:
  test_witness_http.py, test_falsify_tier_a.py
```

285+ passing tests. Run via:
```
PYTHONPATH=src python -m pytest tests -q
```

---

*The index does not reduce the layers. If a module appears here in a stub form, it is because the upstream module documents the algebra at greater depth — see the module's own docstring and the FORMALIZATION document section for that module.*
