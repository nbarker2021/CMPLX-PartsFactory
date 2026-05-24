# API

Primary import:

```python
from lattice_forge import Forge
```

`Forge.open(root=None)` creates or opens the project overlay and reads the
packaged seed.

Supported high-level methods:

- `status()`
- `verify_seed()`
- `object(object_id)`
- `can_close(source_id, target_id, max_depth=10)`
- `terminal_tree(terminal_id)`
- `terminal_trees()`
- `verify_terminal_trees()`
- `morphonics_model()`
- `verify_morphonics()`
- `rule30_morphon(max_depth=7, sample_count=512)`
- `verify_rule30(max_depth=7, sample_count=512)`
- `rule30_vignettes(max_order=4)`
- `verify_rule30_vignettes(max_order=4)`
- `rule30_moving_frame(max_depth=12, max_order=4)`
- `verify_rule30_moving_frame(max_depth=12, max_order=4)`
- `rule30_color_chirality(max_depth=12, max_order=4)`
- `verify_rule30_color_chirality(max_depth=12, max_order=4)`
- `rule30_lagrangian(max_depth=12, max_order=4)`
- `verify_rule30_lagrangian(max_depth=12, max_order=4)`
- `rule30_lagrangian_depth_trace(max_depth=256, max_order=4)`
- `verify_rule30_lagrangian_depth_trace(max_depth=256, max_order=4)`
- `rule30_mandelbrot_scalar(max_depth=256, max_order=4)`
- `verify_rule30_mandelbrot_scalar(max_depth=256, max_order=4)`
- `rule30_reduced_alphabet(max_depth=1024, max_order=4)`
- `verify_rule30_reduced_alphabet(max_depth=1024, max_order=4)`
- `rule30_symmetry_environment(max_depth=1024, max_period=128, max_order=4)`
- `verify_rule30_symmetry_environment(max_depth=1024, max_period=128, max_order=4)`
- `rule30_physics_method_stack(max_depth=1024, max_period=128, max_order=4, max_block=8)`
- `verify_rule30_physics_method_stack(max_depth=1024, max_period=128, max_order=4, max_block=8)`
- `rule30_whole_integer_n_coverage(max_depth=4096, max_order=4)`
- `verify_rule30_whole_integer_n_coverage(max_depth=4096, max_order=4)`
- `rule30_readout_ribbon_machine(max_depth=4096, max_order=4)`
- `verify_rule30_readout_ribbon_machine(max_depth=4096, max_order=4)`
- `rule30_dihedral_block_hypervisor(max_depth=4096, block_size=8, max_order=4)`
- `verify_rule30_dihedral_block_hypervisor(max_depth=4096, block_size=8, max_order=4)`
- `rule30_hypervisor_extension_tape(page_count=2, page_size=4096, block_size=8, max_order=4)`
- `verify_rule30_hypervisor_extension_tape(page_count=2, page_size=4096, block_size=8, max_order=4)`
- `rule30_sheet_operator(page_count=2, page_size=4096, block_size=8, max_order=4)`
- `verify_rule30_sheet_operator(page_count=2, page_size=4096, block_size=8, max_order=4)`
- `rule30_nth_bit_expression(n, page_size=4096, block_size=8, max_order=4)`
- `verify_rule30_nth_bit_expression(n, page_size=4096, block_size=8, max_order=4)`
- `rule30_proof_obligations(max_depth=4096, page_count=2, page_size=4096, block_size=8, max_order=4)`
- `verify_rule30_proof_obligations(max_depth=4096, page_count=2, page_size=4096, block_size=8, max_order=4)`
- `future_cone(object_id, max_depth=8)`
- `exactness_dashboard(object_id)`
- `witnesses(source_id=None, target_id=None, morphism_id=None)`
- `obstructions(source_id=None, target_id=None)`
- `export_object(object_id, vector_limit=12)`
- `latest_events(limit=20)`
- `latest_receipts(limit=20)`
- `snapshot(limit=100)`

Every high-level query records an overlay receipt, event, and query cache row.

## Terminal Trees

`terminal_tree("A2^12")` resolves the categorical form to
`Niemeier:A2^12` and generates the canonical component-action route from the
seed records. The generated tree includes:

- `composition_route`: the single canonical route after component ordering and
  orbit quotienting.
- `action_edges`: legal component-addition actions.
- `involution_tree`: compact lifted source involution/reflection generators for
  each component instance.
- `residue_trace`: the residue emitted by each component action.
- `closure_residue`: the terminal residue check, for example
  `729^2 = 531441` for `A2^12`.

`can_close("G2", "A2^12")` embeds this terminal tree in its result under
`result["terminal_tree"]` and marks the closure model as
`canonical_terminal_composition_tree`.

`terminal_trees()` returns normalized summaries for all 24 terminal forms,
including `ambient_dimension`, `root_rank`, `component_action_count`,
`compact_involution_count`, `residue_status`, and `evidence_level`.

`verify_terminal_trees()` checks all 24 generated terminal forms. The 23
rootful forms must end at root rank 24, close by index-square residue, and have
nonzero compact involution/action coverage. `Niemeier:Leech` is handled as the
rootless 24D terminal with root rank 0 and pending-import evidence for exact
code-construction data.

## Morphonics Harness

`morphonics_model()` returns the Morphonic State Closure Framework v0.2 as a
ledger-shaped model. It includes `MorphonRecord`, `TransformRecord`,
`ProjectionRecord`, `AccountingRecord`, `BridgeRecord`, `ClaimStatusRecord`,
and `FailureRecord` payloads.

`verify_morphonics()` validates that the model preserves the status taxonomy,
links claims to required definitions, keeps overclaims rewritten, checks each
Morphon for primitive reconstruction/accounting fields, and connects the MSCF
24D terminal layer to `verify_terminal_trees()`.

The expected status is `pass_with_open_gaps`: schema/accounting coherence is
passing, while research gaps such as expanded involution witnesses, Leech
Construction-A/Golay import, and TF1 measurement remain explicit failures.

## Rule 30 Morphon Harness

`rule30_morphon()` returns `rule30_morphon_hardened_v0_6`, a hardened version
of the forward-verifier directional lane-beam experiment. It preserves the Rule
30 algebraic normal form:

```text
f(L,C,R)=L+C+R+C*R over GF(2)
```

The bounded exact ANF ledger is used as an oracle for small-depth verification
only. The construction-facing path is the recursive ViewRecord projection:
lane records are composed without expanding the full ANF, then checked against
the exact oracle at bounded depth.

`verify_rule30()` checks:

- canonical single-seed center-column reconstruction,
- explicit `bounded_verification_only` status on the ANF oracle,
- smaller recursive ViewRecord growth than the full ANF ledger,
- preservation of arbitrary-row equivalence as a warning/diagnostic, not a
  claimed success.

The expected status is `pass_with_open_gaps`.

## Rule 30 Vignette Algebra

`rule30_vignettes()` treats each rotated/permuted local cone as a reusable
composition block. The primitive set contains 24 vignettes:

```text
4 orientations * 6 L/C/R port permutations
```

Those primitives quotient to three nonlinear-pair orbits: `LC`, `LR`, and
`CR`. The algebra then composes vignettes under GF(2) parity, interaction, and
serial port-substitution operations. By order 4 it saturates the 128 local
Boolean functions that preserve the all-zero input state.

This is interesting because it turns the center-column encoding question into a
finite syndrome/locator search surface. It is not yet a global decoder proof:
`verify_rule30_vignettes()` keeps `LOCAL_ALGEBRA_NOT_GLOBAL_DECODER`,
`ADMISSIBILITY_FILTER_PENDING`, and `ZERO_LOCATOR_NOT_PROVEN` as open gaps.

## Moving Beam Frame

`rule30_moving_frame()` tests the co-moving bar/state interpretation. The
static vignette algebra provides the 128 zero-preserving functions. The moving
frame then filters this space through the triadic pair-basis law:

```text
LC ^ LR = CR
LC ^ CR = LR
LR ^ CR = LC
```

This models the claim that after two rotations the missing/complementary pair
resolves the local state. The bounded test currently finds:

- 56 pair-basis moving-frame candidates,
- 28 balanced locator candidates,
- 24 two-seed schedules,
- 6 schedule orbits,
- 3 locked visible-pair orbits,
- 3 full triadic-cycle orbits.

This is still not a global nth-bit decoder. The open gap is now narrower:
derive the boundary-regeneration scalar that chooses the zero/one class at each
co-moving boundary.

## Color/Chirality Cipher

`rule30_color_chirality()` promotes the moving-frame pair basis into an
explicit six-token codeword alphabet:

```text
LC+, LC-, LR+, LR-, CR+, CR-
```

The three colors are the nonlinear pair masks `LC`, `LR`, and `CR`. Chirality
is the handedness of the local frame. The finite laws are:

- distinct colors compose to the third color by the GF(2) pair resolver,
- same-color composition annihilates to the zero pair,
- chirality composes as a binary sign,
- rotation cycles the color basis while preserving chirality,
- L/R reflection swaps `LC` and `CR`, fixes `LR`, and flips chirality.

The bounded result currently shows that the 24 primitive vignettes evenly cover
all six chiral tokens, the composition/rotation/reflection tables close, and
the 24 moving schedules lift to chiral token schedules. This supplies the
candidate replacement-cipher alphabet for Rule 30 boundary regeneration. It is
still not the final global `n -> center bit` selector.

## Discrete Lagrangian / NSL Action

`rule30_lagrangian()` defines a finite discrete action over Rule 30 local
plaquettes:

```text
x_i^{t+1} = L + C + R + C*R mod 2
d_i^t = x_i^{t+1} + f(L,C,R) mod 2
L_i^t = d_i^t + token_charge_defect + chirality_defect + noether_defect
S = sum L_i^t
```

In the enumerated local system, `S=0` is exactly the legal-update condition.
The harness enumerates all six color/chirality tokens, all eight local
neighborhood states, and both emitted bits: 96 plaquettes total. It currently
finds 48 zero-action legal plaquettes and 48 positive-action illegal
plaquettes.

The same payload includes Noether, Shannon, and Landauer accounting:

- translation currents for the uniform local CA action,
- C3 color-rotation current for `LC/LR/CR`,
- L/R reflection current with chirality flip,
- neutral annihilation current for same-color composition,
- `log2(6)` token bits versus 3 full neighborhood bits,
- named boundary scalar for the unresolved projection residue.

This is still local action closure, not the final global center-column selector.

## Lagrangian Depth Trace

`rule30_lagrangian_depth_trace()` applies the action/accounting layer to the
canonical single-seed center-column trace. For each depth it records the local
center neighborhood, emitted center bit, compatible zero-action chiral tokens,
and selector-bit accounting. It also scores every moving chiral schedule by
action defect over the full tested window.

At `max_depth=256`, the current result is:

- every depth has at least one zero-action compatible token,
- compatible-token counts are `{2: 36, 4: 64, 6: 156}`,
- center bits are `{0: 121, 1: 135}`,
- 4 of 24 moving schedules have zero action at every tested depth,
- all perfect schedules are locked `CR` schedules,
- the best action defect is 0 and the worst is 70.

This is the first global-depth test of the Lagrangian layer. It does not yet
derive the nth-bit boundary scalar, but it identifies the stable zero-action
frame as `CR`, the nonlinear term of the Rule 30 ANF.

## Mandelbrot/Julia Boundary Scalar

`rule30_mandelbrot_scalar()` turns the four perfect locked-`CR` schedules into
typed light settings. Each light setting is one signed resolution of the two
side terms:

- visible AST term: `CR` / `C*R`,
- one positive projection term from `LC` or `LR`,
- one negative projection term from the other side term,
- aligned forward/backward provision,
- aligned left/right provision,
- chirality arrow,
- Julia seed `z0`.

The scalar functor is:

```text
locked_CR_light_setting x local_3_cell_state
  -> Mandelbrot c x Julia z0
  -> z_exit = z0^2 + c
  -> finite exit key
  -> emitted bit
```

with:

```text
c = (R-L)/2 + i*((L+C+R)/3 - 1/2)
```

At `max_depth=256`, the finite map has 4 light settings, 32 exit rows, 0
ambiguous exits, and 1024/1024 correct representative predictions. It also
reports Fourier power bins over the center-column signal for later
interaction-state selector work.

## Reduced Alphabet Rule Catalog

`rule30_reduced_alphabet()` tests whether the reduced vocabulary can serve as
the entire construction catalog. The allowed rule sources are:

- six chiral tokens,
- `ZERO` neutral token,
- four signed `CR` light settings,
- Mandelbrot scalar entry `c`,
- reduced scalar readout law.

The excluded construction sources are:

- the 128-function vignette catalog,
- ANF monomial expansion,
- full arbitrary Boolean rule search.

The reduced scalar readout law is:

```text
singleton_shell OR (doublet_shell AND positive_side_axis)
```

At `max_depth=1024`, the reduced catalog reproduces all 32 local
light-setting rows and all 4096 center-trace representative predictions. The
audit also shows that pair-product charges alone are insufficient because they
collapse `000` and singleton states into the same pair-product class; the
scalar shell resolves that ambiguity while staying inside the reduced catalog.

## Rule 30 Symmetry Environment

`rule30_symmetry_environment()` wraps the reduced Rule 30 catalog in a finite
representation model:

- S1/U1 phase representatives for the four signed light settings,
- an SU2-style chirality doublet over `+` and `-`,
- an SU3-style color triplet over `LC`, `LR`, and `CR`,
- a finite action functional with Noether/Shannon/Landauer accounting,
- bounded nonperiodicity diagnostics over the center-bit and reduced-signature
  traces.

The harness is intentionally status-aware: it treats the physics language as a
finite symmetry environment over exact cellular-automaton codewords, not as a
claim that Rule 30 has been proven to be a continuum gauge field.

## Rule 30 Physics Method Stack

`rule30_physics_method_stack()` runs six methods that are forced by the finite
Rule 30/codeword setup rather than imported decoratively:

- gauge normalization: removes redundant light-setting representatives,
- de Bruijn transfer operator: builds the symbolic-dynamics graph for a
  radius-1 cellular automaton,
- holonomy loop test: checks phase, color, and chirality closed-loop residue,
- correlation functions: reports autocorrelation and cross-correlation probes,
- ECC syndrome decoder: tests pair products plus scalar shell/side sign as
  parity checks,
- renormalization/coarse-graining: groups depths into blocks and checks that
  local reduced readout stays exact at block scale.

The response includes `solo_tests` for each method and
`cumulative_stack_tests` that add the methods one by one. The final
`all_methods_unified` row is the all-six-in-unison check.

## Whole-Integer N Scalar Coverage

`rule30_whole_integer_n_coverage()` tests whether every whole integer depth in
the bounded window has a scalar assignment. It distinguishes:

- unassigned `N` values,
- scalar readout defects,
- pair-product-only ambiguity,
- cases repaired by the existing scalar `c` shell/side-axis variable.

The expected current result is that no tested whole integer `N` is unassigned
and no new Boolean rule is needed. The remaining non-fitting term is the known
pair-product-only ambiguity `000 -> [0, 1]`, which the scalar shell resolves.

## Readout Ribbon Machine

`rule30_readout_ribbon_machine()` treats the center bar as a finite machine
ribbon:

```text
center context at n -> scalar readout -> emitted bit -> center input at n+1
```

The harness checks:

- feedback defects from output to next input,
- finite scalar transition conflicts,
- strong face bond `CR` and weak counterface `LC/LR/ZERO`,
- forward/backward/neutral time-polarity labels from scalar side axis,
- a dimensionless mass/action proxy derived from the scalar and Lagrangian
  terms.

This proves machine form for the bounded reduced system. It does not by itself
claim formal Turing universality without a simulation theorem.

## Dihedral Block Hypervisor

`rule30_dihedral_block_hypervisor()` groups the ribbon into 8-depth
dihedral/spinor transport blocks. At depth 4096, this yields:

```text
4096 / 8 = 512 complete blocks
```

Each block is represented as:

- a compression object over its 8 emitted bits, polarity word, and phase class,
- a generation object that feeds the next block entry context.

The verification checks that there is no partial tail, no block conflict, no
underlying ribbon feedback defect, and no underlying transition conflict.

## Hypervisor Extension Tape

`rule30_hypervisor_extension_tape()` treats one 4096-depth hypervisor setting as
an extension page. Appending another page continues the same lower math:

```text
4096-page -> next 4096-page -> ...
```

The harness checks:

- page-boundary feedback,
- per-page block completeness,
- stable scalar relative table across pages,
- underlying ribbon feedback and transition closure.

This models the center row as a wraparound self-feeding result tape that
updates the relative table while preserving the center bar being generated.

## Rule 30 Sheet Operator And Nth-Bit Expression

`rule30_sheet_operator()` extracts the stable page-relative transition table as
`T_rule30_relative_sheet`. The operator maps a reduced scalar state key
`LCR|shell|side` to the emitted center bit. Verification checks that the table
has no conflicts, remains hash-stable across tested pages, and preserves page
boundary closure.

`rule30_mandelbrot_field_address(n)` treats the Rule 30 CA itself as the
already-defined Mandelbrot field. It resolves `n` into page, block, phase,
scalar shell, side bucket, address word, and hash, without adding a framework
field above the CA.

`rule30_exit_trajectory(n)` applies the CA-induced field address to the Julia
entry/exit map. The reported `extra_field_search` is zero: the trajectory is
read from the field address for `n`, then verified against the center bit.

`rule30_sheet_lift(n)` models the two Julia sheets as primitive resolution
sheets, not the full address space. Arbitrary `n` is lifted to sheet `k=n` and
`k+1`, so distant depths can live many lifted sheets beyond the primitive pair.

`rule30_julia_resolution(n)` combines the field address, exit trajectory, and
lifted sheet into a single grid-square resolution record. It reports the
resolved bit and verifies that it matches the canonical center bit.

`rule30_torsor_functor_term(n)` adds the missing origin-free displacement
term. The primitive fiber is still only `J_closed_0/J_open_1`; the torsor
coordinate records how the CA base action, scalar exit, and sheet functor place
that fiber at lifted sheet `k=N`. Its bitorsor witness checks that the left CA
action and right scalar/functor action target the same lifted sheet, and its
2-functor witness records naturality, monad unit/multiplication, and spin state
coherence.

`rule30_oloid_winding_from_n(n)` emits a forward +N Oloid rolling witness from
depth alone. `rule30_oloid_antipodal_winding(n)` evaluates the same chart with
the hidden `-N` antipode present as a counter-sheet. The paired verifier reports
both the best static selector and the best adaptive selector; the latter answers
whether the residual defect was caused by dropping the non-viewed antipodal
state from the accounting.

`rule30_winding_number_proof()` is intentionally a bounded winding witness. It
preserves the trace-backed topological/spinor evidence and labels the remaining
shortcut obligation as a pending depth-only extractor instead of claiming a
finished arbitrary-N proof.

`rule30_nth_bit_expression(n)` returns the formulaic nth-bit record. It
decomposes `n` into page, block, and dihedral phase coordinates, constructs the
local reduced scalar `c_n`, applies the CA-field Julia resolution, and checks
the same bit against the sheet lookup. This is an executable expression surface
over the legal state language; a depth-only shortcut theorem is tracked
separately.

`rule30_proof_obligations()` is the submission-facing ledger. It prevents
status collapse by separating `EXPRESSIBLE`, `BOUNDED_EXEC`, `CONJ`, and
`PAPER_PROOF` obligations. Current bounded execution covers scalar coverage,
ribbon feedback, dihedral block closure, and page-table stability; remaining
public-proof obligations include depth-only extraction, all-page induction, and
external nonperiodicity/density evidence.
