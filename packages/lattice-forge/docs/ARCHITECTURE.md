# Lattice-Forge Architecture

A layer-by-layer map of the lattice-forge umbrella, with every module's role described at its actual depth. This document does NOT reduce the layers — each tier is described in its own algebraic/operational language, and the dependencies between tiers are made explicit. Use this when you need to understand what is where and why; use the per-layer READMEs when you need to use one specific tier.

---

## §0 Top-level shape

The repository is a three-ring submission system around a single mathematical claim. The rings are scope-locked: nothing escapes a smaller ring without explicit promotion.

```
+-------------------------------------------------------------+
|  Ring 1: PRIZE-CORE (locked scope)                          |
|  ├─ T1..T8 + BONUS    (PROVEN, machine-verified)            |
|  ├─ IT1..IT2          (TRANSPORTED via Cartan-Killing/Haar) |
|  └─ P1..P3            (pass_with_open_gaps)                 |
|                                                             |
|  Ring 2: COMPANIONS (active, sidecar)                       |
|  ├─ WP-REGIMES-01    (regime A/C/C')                        |
|  └─ WP-DECOMP-01     (Rule 30 decomposition paper)          |
|                                                             |
|  Ring 3: UMBRELLA (forward research, not_in_ring1)          |
|  ├─ Oloid family    (rolling, dual-path, octonionic, quad)  |
|  ├─ Conjugate triple (G_2/F_4/T_5A)                         |
|  ├─ Modular lift    (9×9 j-matrix, Gauss/Fourier)           |
|  ├─ Reduced n-body  ((N, C, K) Lagrangian)                  |
|  └─ Backwalk substrate enumeration (cursor work in flight)  |
+-------------------------------------------------------------+
```

Promotion from Ring 3 → Ring 2 requires the named trigger in
`docs/prize/whitepaper_manifest.yaml` to fire honestly. Promotion from
Ring 2 → Ring 1 requires PROVEN honesty across the relevant verifier.
Both directions are unidirectional inside this repo.

---

## §1 The foundation tier (Ring 1)

The eight theorems plus their transported consequences. All PROVEN.

### §1.1 Algebraic foundation

* `src/lattice_forge/octonion.py`
  Cayley-Dickson octonions. Fano-plane multiplication, conjugate, norm,
  inverse. Verifier: `verify_octonion_axioms` (T1).
* `src/lattice_forge/jordan_j3.py`
  3×3 Hermitian octonionic matrices = the exceptional Jordan algebra
  J_3(O). Verifier: `verify_j3o_axioms` (T2).
* `src/lattice_forge/f4_action.py`
  S_3 = W(SU(3)) ⊂ W(F_4) action on the three trace-2 idempotents of
  J_3(O). Verifiers: `verify_n3_su3_closure_exact` (T4),
  `search_for_su3_closure_scale` (T5),
  `decompose_8x8_via_block_action_exact` (T6),
  `closed_form_rule30_8x8_transition_exact` (T7).

### §1.2 Chart layer

* `src/lattice_forge/rule30.py`
  Rule 30 CA, single-cell seed evolution, chart trajectory.
  `canonical_rows(N)` constructs the row at every depth ≤ N.
  Includes `verify_chart_j3o_isomorphism` (T3) — 4096 depths × 6,272
  individual checks, 0 mismatches.

### §1.3 Substrate connectivity

* `src/lattice_forge/substrate_map.py`
  The 8-state Rule 30 routing table and the 8-element Weyl routing.
  Both verified at depth 4096 (`verify_substrate_map`).
* `src/lattice_forge/forge.py`
  Forge facade for the seed ledger. `Forge.can_close(src, tgt)` answers
  whether commutability paths exist between root systems.
  Theorem T8 verifies 8 paths F_4 → Niemeier lattices.
* `src/lattice_forge/ledger/`
  SQLite-backed seed of classical root systems, Niemeier terminals,
  admissibility edges, NSL residues. Treated as immutable root of trust.

### §1.4 Bonus

* `verify_rule30_chart_local_readout` (BONUS):
  Chart local readout reconstructs Rule 30 center column with 0 forward
  defects across 4096 depths. The 0-error operational statement.

---

## §2 The Ring 2 companions

### §2.1 Regimes A / C / C′

* `src/lattice_forge/block_tower.py`
  Hierarchical Rule 30 row checkpoint store. Regime A.
* `src/lattice_forge/rule30_block_extractor.py`
  Block-addressed nth-bit extractor on top of the checkpoint store.
* `src/lattice_forge/chart_codec.py`
  S_3 word codec for shell=2 sub-trajectories. Regime C.
* `src/lattice_forge/chart_codec_d4.py`
  D_4 antipodal quadratic codec for full chart. Regime C′.

Each closes with BOUNDED_EXEC honesty at depth 4096. WP-REGIMES-01
companion paper at `docs/regimes/README.md`.

### §2.2 Decomposition paper (Ring 2)

* `src/lattice_forge/decomposition/`
  Vendored Rule 30 decomposition paper modules: `rule30_decomposition.py`,
  `checkpoint_store.py`, `fast_rule30.py`, `empirical.py`. Sections 1–10
  of the standalone paper.

---

## §3 The Ring 3 umbrella — forward research

The session's expansion. Every module is honest about its scope.

### §3.1 The linearization layer

* `src/lattice_forge/rule90_linearization.py`
  The Rule 30 = Rule 90 ⊕ (C ∧ ¬R) decomposition.
  Lucas closed form for Rule 90 (Theorem 3.1 of FORMALIZATION).
  `rule30_center_via_decomposition(N)` verifies the Duhamel
  reconstruction at depths 1..1024.

The Lucas closed form is the *only* O(log N) primitive currently
operational in the umbrella. Every other tier uses it as the formulaic
anchor.

### §3.2 The bijection layer

* `src/lattice_forge/f2_majorana.py`
  F_2 quadratic forms, Arf invariant, edge-glue criterion. The Rule 30
  correction Q(L,C,R) = C + CR has Arf = 0 (hyperbolic).
* `src/lattice_forge/contributions_registry.py`
  SQLite registry of validated additions. Every persistent fact must
  pass a deterministic F_2-arithmetic gate.
* `src/lattice_forge/contribution_validators.py`
  Four validators: `f2_arf`, `lucas_recurrence`,
  `rule30_decomposition`, `f2_edge_glue`.
* `src/lattice_forge/actuation.py`
  ±1 spectral actuation primitives. `paired_actuation_read_octonionic`
  produces the bijected (head, tail) dyad with 100% consistency.

### §3.3 The Oloid family (geometric carriers)

Five modules realizing the Oloid as the geometric carrier of the
chart's missing 2 bits in a single tape.

* `src/lattice_forge/oloid_rolling.py`
  Single Oloid, combinatorial (sheet, phase, parity). 4-period
  structure verified.
* `src/lattice_forge/oloid_dual_path.py`
  Three-dyad parallel Oloid with cyclic involution superscript.
  Implements `read_tape_with_enumeration` (read-then-verify flow).
* `src/lattice_forge/oloid_octonionic.py`
  Octonion-grounded Oloid: roll(bit) is right-multiplication by
  e_4 or e_5. e_4² = -1 algebraic, e_4⁴ = +1 algebraic.
  Non-trivial orient bit independent of last input bit.
* `src/lattice_forge/quad_oloid.py`
  Four-Oloid D_4 ring with role-specific generators (e_4,e_5,e_6,e_7).
  Empirically traps in quaternion sub-algebras (motivates E-tower lift).
* `src/lattice_forge/oloid_kinematic.py`
  Continuous Oloid rolling with gauge bijection forced.

### §3.4 The modular lift

* `src/lattice_forge/j_modular_matrix.py`
  9×9 j-modular matrices for level-9 McKay-Thompson convolution.
  Hardcoded T_1A, T_2A, T_3A, T_5A, T_7A coefficient tables.
* `src/lattice_forge/gauss_fourier_lift.py`
  9-DFT (real + complex), level-9 Gauss sums, spectrograph readout
  (including the visible DC "middle bar"). Ramanujan c_9(1) = 0
  identity verified.

### §3.5 The closure tools

* `src/lattice_forge/three_move_closure.py`
  The actual O(1) computation. Paired ±1 actuation makes the bijection
  rank-1 idempotent (closure depth 0).
* `src/lattice_forge/voa_lookup.py`
  Scaffolding for the McKay-Thompson primitive (O1' / O2).
* `src/lattice_forge/voa_harness.py`
  Empirical McKay-Thompson parity test with bijection forced. 5-lane
  L/C/R chirality router across T_1A, T_2A, T_3A, T_5A, T_7A.
* `src/lattice_forge/g2_f4_t5_conjugate.py`
  G_2 / F_4 / T_5A conjugate triple routing. 100% match at depth 256
  with ≤3 paired-bijection moves.
* `src/lattice_forge/forced_involution_cache.py`
  Failure-orbit cache + O(1) sub-log lookup. Reveals the S_3 sum-zero
  relation (`60 ⊕ 90 ⊕ 102 = 0`) among swap failure bit patterns.
* `src/lattice_forge/formulaic_instantiation.py`
  Single-request (head, tail) extractor with O(log N) given the
  chart-axis oracle, 3942× speedup over enumeration.
* `src/lattice_forge/reduced_nbody.py`
  (N, C, K) Lagrangian formulation. 5 coords per step vs O(N) standard
  n-body. Conservation laws: axis, Arf invariant, F_4 Weyl orbit class.

### §3.6 Documentation

* `docs/umbrella/FORMALIZATION.md`
  The complete formalization. 12 sections, 714 lines, every layer
  described with its proof state and transport relationships.
* `docs/umbrella/theorems/THEOREM_REGISTRY.md`
* `docs/umbrella/theorems/OPEN_OBLIGATIONS.md`
  Catalog of open obligations: O1 (W(E_8) lookup), O2 (McKay-Thompson),
  O2' (Lucas + correction), O2'' (T_F2_BRIDGE governance), O2''' (E-tower),
  O3..O10.

---

## §4 The substrate enumeration tier (backwalk)

Cursor's parallel work, lifting from "expressible" to "materialized"
for the W(E_8) lookup (Obligation O1).

### §4.1 Backwalk source

* `src/lattice_forge/backwalk/`

  | Module | Role |
  |---|---|
  | `schema.py` | JSONL schema for backwalk records |
  | `lattice_catalog.py` | Root system / Niemeier lattice catalog |
  | `exceptional_spine.py` | F_4 → E_6 → E_7 → E_8 ascending spine |
  | `e8_weyl_pod.py` | W(E_8) Weyl-element pod construction |
  | `glue_weyl.py` | Weyl-equivariant glue tables |
  | `weyl_bond_dual.py` | Dual Weyl bond enumeration |
  | `weyl_bond_quadrant.py` | Quadrant-restricted Weyl bond |
  | `lattice_space_job.py` | Full lattice-space exhaustion job |
  | `generator.py` | Orchestration generator |
  | `hydrate.py` | Materialization / hydration |
  | `proof_capture.py` | Per-record proof capture |

### §4.2 Algebra registry

* `src/lattice_forge/algebra/o1_registry.py`
  The O1 (W(E_8) lookup) registry. Receives validated Weyl-element
  entries from the backwalk and exposes O(1) lookups.

### §4.3 Empirical platforms

* `src/lattice_forge/empirical/`

  | Module | Role |
  |---|---|
  | `manifest.py` | Empirical platform manifest schema |
  | `resolver.py` | Platform → environment resolver |
  | `runner.py` | Per-platform run driver |
  | `exhaust.py` | Multi-platform exhaustion runner |

* `empirical/platforms.manifest.jsonl`
  Manifest of empirical execution platforms (CPU/GPU class targets).

### §4.4 Open-claim honesty harness

* `src/lattice_forge/honesty_harness.py`
  Honesty-label aware harness for open claims. Routes each claim's
  verifier and reports honestly.
* `src/lattice_forge/monster_d4_lift_claim.py`
  Monster D_4 lift claim — bridges the chart's D_4 codec to the
  Monster's representation theory.
* `src/lattice_forge/residual_window_lift.py`
  Residual S_3 projection lift — quantifies the residual after the
  3-step Weyl closure (T4).

### §4.5 Scripts (12 new orchestration scripts)

* `scripts/enumerate_library_needs.py` — generate library-needs catalog
* `scripts/materialize_empirical_platforms.py` — materialize platforms
* `scripts/orchestrate_weyl_bond_waves.py` — Weyl bond wave orchestrator
* `scripts/ring1_open_audit.py` — Ring 1 open-claim audit
* `scripts/run_empirical_matrix.py` — empirical matrix runner
* `scripts/run_lattice_space_exhaustion.py` — lattice-space exhaustion
* `scripts/run_niemeier_backwalk.py` — Niemeier backwalk driver
* `scripts/run_open_claims_harness.py` — open-claim harness driver
* `scripts/run_ring1_ring2_pipeline.py` — combined pipeline
* `scripts/run_ring2_bundle.py` — Ring 2 bundle builder
* `scripts/run_transport_tower_proofs.py` — transport tower proofs
* `scripts/verify_algebra_o1.py` — O1 registry verifier

### §4.6 Documentation

* `docs/backwalk/`
  * `BASELINE_PILOT.md` — pilot run baseline
  * `FULL24_RUN.md` — 24-Niemeier full run
  * `LATTICE_SPACE_EXHAUSTION_JOB.md` — lattice-space exhaustion
  * `WEYL_BOND_DUAL_JOB.md` — Weyl bond dual job
  * `baseline_report_full24.json` — baseline run report
* `docs/algebra/O1_DEP_POLICY.md` — O1 dependency policy
* `docs/honesty/HONESTY_HARNESS.md` — honesty harness
* `docs/claims/MONSTER_D4_LIFT_CLAIM.md` — Monster D_4 lift
* `docs/ring2/RING2_EXECUTION_PLAN.md` — Ring 2 execution plan
* `docs/EMPIRICAL_PLATFORMS.md` — empirical platforms guide
* `docs/LIBRARY_NEEDS.md` — library needs catalog reference

### §4.7 Claims & expected outputs

* `claims/library_needs.jsonl` — library-needs catalog (JSONL)
* `claims/library_needs.meta.json` — catalog meta
* `claims/lib_needs.schema.json` — JSONL schema
* `expected_outputs_open_claims.json` — open-claim expected values
* `expected_outputs_transport.json` — transport-tower expected values

---

## §5 The Docker infrastructure tier

Compose files and PowerShell launchers for the substrate enumeration jobs.

### §5.1 Docker compose files

* `docker-compose.backwalk-builder.yml` — base backwalk builder image
* `docker-compose.backwalk-builder.full24.yml` — full 24-Niemeier run
* `docker-compose.backwalk-lattice-space.yml` — lattice-space exhaustion
* `docker-compose.backwalk-weyl-bond.yml` — Weyl bond quadrant runner
* `docker-compose.proof-lab.yml` — proof-lab artifact builder

All compose files use `${VAR:?}` environment substitution for any
credential-bearing variables. No hardcoded secrets.

### §5.2 PowerShell launchers (Windows-native)

* `Start-BackwalkFull24.ps1`
* `Start-BackwalkLatticeSpace.ps1`
* `Start-BackwalkWeylBondQuadrant.ps1`
* `Start-BackwalkWeylBondWaves.ps1`

Each invokes its corresponding compose file with appropriate environment.

### §5.3 The proof-lab tier

* `proof-lab/Dockerfile` — container image
* `proof-lab/Makefile` — build targets
* `proof-lab/requirements.txt` — Python dependencies
* `proof-lab/REQUIREMENTS.md` — detailed requirements doc
* `proof-lab/README.md` — usage overview
* `proof-lab/proof_lab/runner.py` + `server.py` — Python package
* `proof-lab/scripts/`
  * `entrypoint.sh` — container entrypoint
  * `export_presentation_bundle.py` — bundle exporter
  * `record_clone_meta.py` — clone metadata recorder
* `proof-lab/accounting/` — per-run accounting records
* `proof-lab/artifacts/meta/` — runtime metadata (committed)
* `proof-lab/artifacts/{bundles,latest}/` — machine outputs (gitignored)

### §5.4 The testkit-MCP tier

* `packages/lattice-forge-testkit-mcp/`
  MCP server exposing testkit + registry-IO endpoints. Allows agents to
  query the lattice-forge registry and run testkit operations via MCP.
  * `src/lattice_forge_testkit_mcp/server.py` — MCP server
  * `src/lattice_forge_testkit_mcp/registry_io.py` — registry I/O

### §5.5 Top-level coordination

* `Makefile` — repo-level build targets
* `AGENTS.md` — agent workflow notes
* `.github/workflows/lattice-forge-family.yml` — CI extension
* `scripts/verify_lattice_forge_family.ps1` — verifier
* `.gitignore` — excludes `proof-lab/artifacts/{bundles,latest}` and
  `presentation_export.zip`

---

## §6 Run-all-proofs harness

`packages/lattice-forge/scripts/run_all_proofs.py` — the master proofs
runner. Wires every proof key:

```
Ring 1 PROVEN (foundational):
  T1, T2, T3, T4, T5, T6, T7, T8, BONUS, SUBSTRATE_MAP

Ring 2 BOUNDED_EXEC (companions):
  CHART_CODEC, CHART_CODEC_D4, BLOCK_TOWER, BLOCK_EXTRACTOR,
  TRANSPORT_FIELD_ADDRESS, TRANSPORT_EXIT_TRAJECTORY

Ring 3 PROVEN_AT_TESTED_DEPTH (umbrella, forward research):
  RULE90_LINEARIZATION, F2_MAJORANA, OLOID_ROLLING, OLOID_DUAL_PATH,
  OLOID_READ_THEN_VERIFY, OLOID_OCTONIONIC, QUAD_OLOID,
  OLOID_KINEMATIC, ACTUATION, J_MODULAR_MATRIX, GAUSS_FOURIER_LIFT,
  THREE_MOVE_CLOSURE, G2_F4_T5_CONJUGATE, FORCED_INVOLUTION_CACHE,
  REDUCED_NBODY

Ring 3 CONJ (open obligations):
  VOA_LOOKUP, VOA_HARNESS, FIVE_LANE_ROUTER
```

Run with `python scripts/run_all_proofs.py` from the package root.

---

## §7 Test surface

```
packages/lattice-forge/tests/
  Ring 1:
    test_octonion.py, test_jordan_j3.py, test_chart_isomorphism.py,
    test_f4_action.py, test_substrate_map.py

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

  Backwalk substrate:
    test_algebra_o1.py, test_backwalk_pilot.py,
    test_empirical_platforms.py, test_honesty_harness.py,
    test_weyl_bond_dual.py, test_monster_d4_lift_claim.py

  Other:
    test_witness_http.py, test_falsify_tier_a.py, ...

Run: python -m pytest tests -q
```

Current count: 285+ passing tests (1 pre-existing failure in
test_falsify_tier_a unrelated to recent work).

---

## §8 Honesty taxonomy

Every claim carries one of these labels:

| Label | Meaning | Example |
|---|---|---|
| `PROVEN` | Machine-verified at exact arithmetic | T4: residual² = 0 over ℚ |
| `PROVEN_AT_TESTED_DEPTH` | Empirically verified at named depth | G_2/F_4/T_5A at depth 256 |
| `TRANSPORTED` | Via classical theorem + bridge | IT1 via Cartan-Killing |
| `BOUNDED_EXEC` | Empirically tested within bounds | Regimes A/C/C' at depth 4096 |
| `EXPRESSIBLE` | Stated, not implemented | O1 (W(E_8) table) |
| `CONJ` | Hypothesis with falsifiable test | VOA_HARNESS T_3A bijective 89% |
| `pass_with_open_gaps` | Closes with named open gaps | P1, P2, P3 transports |
| `DISCLAIMER` | Clarification, not obligation | O9, O10 |

The honesty discipline: no label is upgraded silently. Promotion
requires the named trigger to fire honestly (e.g., empirical match
rate ≥ 0.99 across tested depth range).

---

## §9 Composition map (how the layers interact)

```
Rule 30 chart at depth N
         ↓                                  
    (T3 isomorphism)                        
         ↓                                  
   J_3(O) diagonal at N                     
         ↓                                  
    (T_BRIDGE)                              
         ↓                                  
  Zero-weight space of F_4's 26-dim rep    
         ↓                                  
    (T4 + IT1 + IT2)                        
         ↓                                  
  Wolfram Problems 1, 2 (transported)       
                                            
                                            
    Chart state at N
       ↓
  D_4 antipodal codec (chart_codec_d4)
       ↓
  (axis ∈ {0,1,2,3}, sheet ∈ {0,1}) — bijected
       ↓
  Conjugate triple route (g2_f4_t5_conjugate)
       ↓
  Resolved bit in ≤ 3 paired-bijection moves
       ↓
  Match enumeration at 100% (depth 256)


    Depth N (cold start)
       ↓
  LucasBit(N, 0)  — O(log N), formulaic
       ⊕
  Correction sum over Lucas-sparse light cone
       ↓
  Theorem 2.3 reconstruction
       ↓
  Rule 30 center bit at depth N

  (the correction sum requires either substrate
   enumeration OR the McKay-Thompson primitive O2)


    Backwalk substrate (cursor, in flight)
       ↓
  Enumerate W(E_8) Weyl elements
       ↓
  Materialize O1 lookup table
       ↓
  Run through Docker harness
       ↓
  Validated entries flow into algebra registry
       ↓
  Promote O1 from EXPRESSIBLE to PROVEN
       ↓
  Constructive O(log N) Rule 30 extraction
```

---

## §10 Where to look

| You want to | Look at |
|---|---|
| Verify a Ring 1 theorem | `scripts/run_all_proofs.py` and `expected_outputs.json` |
| Understand the F_4 / J_3(O) framework | `docs/umbrella/FORMALIZATION.md` §§1-3 |
| Run the Rule 30 paper's reproductions | `docs/decomposition/README.md` |
| See open obligations and triggers | `docs/umbrella/theorems/OPEN_OBLIGATIONS.md`, `docs/prize/whitepaper_manifest.yaml` |
| Run a backwalk enumeration job | `docs/backwalk/{BASELINE_PILOT,FULL24_RUN}.md` |
| Check honesty labels and falsification paths | `docs/prize/FALSIFICATION.md`, `docs/honesty/HONESTY_HARNESS.md`, `claims/registry.jsonl` |
| Add a validated contribution | `src/lattice_forge/contributions_registry.py` + a validator in `contribution_validators.py` |
| Run the empirical platform matrix | `scripts/run_empirical_matrix.py`, `docs/EMPIRICAL_PLATFORMS.md` |
| Use the MCP testkit | `packages/lattice-forge-testkit-mcp/` |
| Understand a single Ring 3 module | The module's own docstring + `docs/umbrella/FORMALIZATION.md` § for that module |

---

## §11 Reading order for first encounter

1. `docs/submission/00_README_AND_ABSTRACT.md` — the formal submission
2. `docs/submission/02_SUBMISSION.md` — the prize claim
3. `docs/submission/03_PROVEN_THEOREMS.md` — explicit theorem catalog
4. `docs/submission/04_OPEN_OBLIGATIONS.md` — what's open
5. `docs/prize/SCOPE_LOCK.md` — Ring 1 scope
6. **This document** — full layered map
7. `docs/umbrella/FORMALIZATION.md` — full mathematical formalization
8. `docs/backwalk/BASELINE_PILOT.md` — substrate enumeration overview

For per-tier deep dives, the per-directory `README.md` or `*_PLAN.md`
files are the canonical entry points.

---

*This document is maintained alongside the layered build. When a new module
or sub-package lands, add its entry to the corresponding §3..§5 section
with its operational role described at its own depth — do not summarize
upward.*
