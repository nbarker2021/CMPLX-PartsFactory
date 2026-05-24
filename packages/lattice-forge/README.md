# Lattice Forge

Lattice Forge is an installable Python library for morphism-saturated lattice
admissibility queries. It ships a versioned seed ledger containing objects,
exact vectors, Gram forms, morphisms, admissibility edges, obstructions,
residue/NSL profiles, terminal 24D forms, and exactness labels.

The central use case is legal-future selection:

```text
low-rank morphism ecology -> admissibility paths -> terminal lattice futures
```

Terminal 24D forms are not treated as inert destinations. A categorical form
such as `A2^12` is resolved to its terminal record and generated as a canonical
component-action tree. Component embeddings and lifted involution/reflection
generators produce a residue trace; old glue rows remain compatibility evidence
rather than the thing the engine searches for at the end.

The bundled seed database is read-only. Project-local interaction state is
written to `.lattice_forge/overlay.sqlite`.

## Install

```bash
python -m pip install -e .
```

For the optional FastAPI server:

```bash
python -m pip install -e ".[server]"
```

## Python API

```python
from lattice_forge import Forge

forge = Forge.open()
result = forge.can_close("G2", "A2^12")
cone = forge.future_cone("G2")
dashboard = forge.exactness_dashboard("G2")
tree = forge.terminal_tree("A2^12")
all_trees = forge.terminal_trees()
verification = forge.verify_terminal_trees()
morphonics = forge.morphonics_model()
morphonics_check = forge.verify_morphonics()
rule30 = forge.rule30_morphon(max_depth=7)
rule30_check = forge.verify_rule30(max_depth=7)
vignettes = forge.rule30_vignettes(max_order=4)
vignette_check = forge.verify_rule30_vignettes(max_order=4)
moving = forge.rule30_moving_frame(max_depth=12, max_order=4)
moving_check = forge.verify_rule30_moving_frame(max_depth=12, max_order=4)
chiral = forge.rule30_color_chirality(max_depth=12, max_order=4)
chiral_check = forge.verify_rule30_color_chirality(max_depth=12, max_order=4)
action = forge.rule30_lagrangian(max_depth=12, max_order=4)
action_check = forge.verify_rule30_lagrangian(max_depth=12, max_order=4)
trace = forge.rule30_lagrangian_depth_trace(max_depth=256, max_order=4)
trace_check = forge.verify_rule30_lagrangian_depth_trace(max_depth=256, max_order=4)
scalar = forge.rule30_mandelbrot_scalar(max_depth=256, max_order=4)
scalar_check = forge.verify_rule30_mandelbrot_scalar(max_depth=256, max_order=4)
reduced = forge.rule30_reduced_alphabet(max_depth=1024, max_order=4)
reduced_check = forge.verify_rule30_reduced_alphabet(max_depth=1024, max_order=4)
symmetry = forge.rule30_symmetry_environment(max_depth=1024, max_period=128, max_order=4)
symmetry_check = forge.verify_rule30_symmetry_environment(max_depth=1024, max_period=128, max_order=4)
physics_stack = forge.rule30_physics_method_stack(max_depth=1024, max_period=128, max_order=4, max_block=8)
physics_stack_check = forge.verify_rule30_physics_method_stack(max_depth=1024, max_period=128, max_order=4, max_block=8)
n_coverage = forge.rule30_whole_integer_n_coverage(max_depth=4096, max_order=4)
n_coverage_check = forge.verify_rule30_whole_integer_n_coverage(max_depth=4096, max_order=4)
ribbon = forge.rule30_readout_ribbon_machine(max_depth=4096, max_order=4)
ribbon_check = forge.verify_rule30_readout_ribbon_machine(max_depth=4096, max_order=4)
hypervisor = forge.rule30_dihedral_block_hypervisor(max_depth=4096, block_size=8, max_order=4)
hypervisor_check = forge.verify_rule30_dihedral_block_hypervisor(max_depth=4096, block_size=8, max_order=4)
extension = forge.rule30_hypervisor_extension_tape(page_count=2, page_size=4096, block_size=8, max_order=4)
extension_check = forge.verify_rule30_hypervisor_extension_tape(page_count=2, page_size=4096, block_size=8, max_order=4)
sheet = forge.rule30_sheet_operator(page_count=2, page_size=4096, block_size=8, max_order=4)
sheet_check = forge.verify_rule30_sheet_operator(page_count=2, page_size=4096, block_size=8, max_order=4)
nth = forge.rule30_nth_bit_expression(4096)
nth_check = forge.verify_rule30_nth_bit_expression(4096)
proof = forge.rule30_proof_obligations(max_depth=4096, page_count=2, page_size=4096)
proof_check = forge.verify_rule30_proof_obligations(max_depth=4096, page_count=2, page_size=4096)
```

Every query records a receipt and event in `.lattice_forge/overlay.sqlite`.
Responses preserve status language such as `exact`, `computed_profile`,
`template`, `conceptual`, and `pending_import`.

## CLI

```bash
lattice-forge status
lattice-forge verify-seed
lattice-forge can-close G2 A2^12
lattice-forge terminal-tree A2^12
lattice-forge terminal-trees
lattice-forge verify-terminal-trees
lattice-forge morphonics-model
lattice-forge verify-morphonics
lattice-forge rule30-morphon --max-depth 7
lattice-forge verify-rule30 --max-depth 7
lattice-forge rule30-vignettes --max-order 4
lattice-forge verify-rule30-vignettes --max-order 4
lattice-forge rule30-moving-frame --max-depth 12
lattice-forge verify-rule30-moving-frame --max-depth 12
lattice-forge rule30-color-chirality --max-depth 12
lattice-forge verify-rule30-color-chirality --max-depth 12
lattice-forge rule30-lagrangian --max-depth 12
lattice-forge verify-rule30-lagrangian --max-depth 12
lattice-forge rule30-lagrangian-trace --max-depth 256
lattice-forge verify-rule30-lagrangian-trace --max-depth 256
lattice-forge rule30-mandelbrot-scalar --max-depth 256
lattice-forge verify-rule30-mandelbrot-scalar --max-depth 256
lattice-forge rule30-reduced-alphabet --max-depth 1024
lattice-forge verify-rule30-reduced-alphabet --max-depth 1024
lattice-forge rule30-symmetry-environment --max-depth 1024 --max-period 128
lattice-forge verify-rule30-symmetry-environment --max-depth 1024 --max-period 128
lattice-forge rule30-physics-stack --max-depth 1024 --max-period 128 --max-block 8
lattice-forge verify-rule30-physics-stack --max-depth 1024 --max-period 128 --max-block 8
lattice-forge rule30-n-coverage --max-depth 4096
lattice-forge verify-rule30-n-coverage --max-depth 4096
lattice-forge rule30-readout-ribbon --max-depth 4096
lattice-forge verify-rule30-readout-ribbon --max-depth 4096
lattice-forge rule30-dihedral-hypervisor --max-depth 4096 --block-size 8
lattice-forge verify-rule30-dihedral-hypervisor --max-depth 4096 --block-size 8
lattice-forge rule30-extension-tape --page-count 2 --page-size 4096 --block-size 8
lattice-forge verify-rule30-extension-tape --page-count 2 --page-size 4096 --block-size 8
lattice-forge rule30-sheet-operator --page-count 2 --page-size 4096 --block-size 8
lattice-forge verify-rule30-sheet-operator --page-count 2 --page-size 4096 --block-size 8
lattice-forge rule30-nth-bit 4096
lattice-forge verify-rule30-nth-bit 4096
lattice-forge rule30-proof-obligations --max-depth 4096 --page-count 2 --page-size 4096
lattice-forge verify-rule30-proof-obligations --max-depth 4096 --page-count 2 --page-size 4096
lattice-forge future-cone G2
lattice-forge exactness G2
lattice-forge witnesses --source-id G2 --target-id A2
lattice-forge obstructions --source-id G2
lattice-forge events
lattice-forge receipts
lattice-forge snapshot --out snapshot.json
```

## Server

```bash
lattice-forge serve --host 127.0.0.1 --port 8765
```

Supported v1 endpoints include:

- `GET /health`
- `GET /status`
- `GET /objects/{object_id}`
- `POST /can-close`
- `GET /future-cone/{object_id}`
- `GET /exactness/{object_id}`
- `GET /terminal-tree/{terminal_id_or_form}`
- `GET /terminal-trees`
- `GET /terminal-trees/verify`
- `GET /morphonics/model`
- `GET /morphonics/verify`
- `GET /rule30/morphon`
- `GET /rule30/verify`
- `GET /rule30/vignettes`
- `GET /rule30/vignettes/verify`
- `GET /rule30/moving-frame`
- `GET /rule30/moving-frame/verify`
- `GET /rule30/color-chirality`
- `GET /rule30/color-chirality/verify`
- `GET /rule30/lagrangian`
- `GET /rule30/lagrangian/verify`
- `GET /rule30/lagrangian-trace`
- `GET /rule30/lagrangian-trace/verify`
- `GET /rule30/mandelbrot-scalar`
- `GET /rule30/mandelbrot-scalar/verify`
- `GET /rule30/reduced-alphabet`
- `GET /rule30/reduced-alphabet/verify`
- `GET /rule30/symmetry-environment`
- `GET /rule30/symmetry-environment/verify`
- `GET /rule30/physics-stack`
- `GET /rule30/physics-stack/verify`
- `GET /rule30/n-coverage`
- `GET /rule30/n-coverage/verify`
- `GET /rule30/readout-ribbon`
- `GET /rule30/readout-ribbon/verify`
- `GET /rule30/dihedral-hypervisor`
- `GET /rule30/dihedral-hypervisor/verify`
- `GET /rule30/extension-tape`
- `GET /rule30/extension-tape/verify`
- `GET /rule30/sheet-operator`
- `GET /rule30/sheet-operator/verify`
- `GET /rule30/nth-bit/{n}`
- `GET /rule30/nth-bit/{n}/verify`
- `GET /rule30/proof-obligations`
- `GET /rule30/proof-obligations/verify`
- `GET /witnesses`
- `GET /obstructions`
- `GET /events`
- `GET /receipts`
- `GET /snapshot`

The production server intentionally has no command-execution endpoint.

## Development

```bash
python -m pytest tests -q
python -S scripts/smoke.py
```

`verify-morphonics` is the first cross-domain hardening harness. It represents
the Morphonic State Closure Framework v0.2 as executable records: Morphons,
transforms, projections, accounting functionals, bridges, claims, and failure
labels. The check is expected to pass with open research gaps rather than
flatten speculative claims into proof-grade status.

`verify-rule30` is the first concrete Morphon case harness. It hardens the
forward-verifier lane-beam prototype by separating bounded ANF oracle
verification from construction, making canonical center-column closure the
primary target, and keeping arbitrary-row equivalence as a diagnostic.

`verify-rule30-vignettes` treats rotated/permuted Rule 30 cones as composable
vignettes. At order 4 the local composition algebra saturates the 128
zero-preserving Boolean functions on a 3-bit neighborhood, exposing a concrete
finite syndrome/locator search space while preserving the open gap that this is
not yet a global nth-bit decoder.

`verify-rule30-moving-frame` adds the co-moving bar/state interpretation. It
uses the triadic resolver law `LC^LR=CR`, `LC^CR=LR`, `LR^CR=LC` as an
admissibility filter over the static 128-function space. In the current bounded
test, the moving filter leaves 56 pair-basis candidates, 28 balanced locator
candidates, and splits schedules into 3 locked visible-pair orbits plus 3 full
triadic-cycle orbits.

`verify-rule30-color-chirality` promotes the three pair-codewords into a
six-token replacement cipher: `LC+`, `LC-`, `LR+`, `LR-`, `CR+`, `CR-`.
The color law is the same finite GF(2) pair algebra, while chirality is frame
handedness. The 24 primitive vignettes evenly cover all six tokens, the
composition/rotation/reflection tables close, and the moving-frame schedules
lift to chiral token schedules. This is the candidate alphabet for the
boundary-regeneration scalar; it is not yet the final nth-bit decoder.

`verify-rule30-lagrangian` makes the finite action explicit. Each local
plaquette has defect `d=x_i^{t+1}+f(L,C,R) mod 2`; the action is zero exactly
when the emitted bit is the legal Rule 30 update under its encoded frame. The
current harness enumerates 96 plaquettes, with 48 legal zero-action plaquettes
and 48 positive-action illegal plaquettes. It also records discrete Noether
currents for translation, color rotation, reflection/chirality, and neutral
annihilation, plus Shannon/Landauer accounting for the projection from a 3-bit
neighborhood to the six-token alphabet and then to the emitted center bit.

`verify-rule30-lagrangian-trace` carries that action ledger across the actual
canonical center-column depth trace. At `max_depth=256`, every depth has at
least one zero-action color/chirality token. The moving-schedule search finds
4 exact zero-action schedules out of 24, and all 4 are locked `CR` schedules,
matching the nonlinear `C*R` term in the Rule 30 ANF. This is the first real
global-depth signal from the Lagrangian layer; it narrows the remaining problem
to deriving the center-bit boundary scalar without replaying the local state.

`verify-rule30-mandelbrot-scalar` defines that scalar as a finite
Mandelbrot/Julia entry-exit map. The four perfect locked-`CR` schedules become
four signed light settings: each resolves the visible `CR`/`C*R` AST term with
one positive and one negative `LC`/`LR` side projection, plus aligned
forward/backward and left/right provisions. The scalar uses
`c=(R-L)/2+i*((L+C+R)/3-1/2)` and `z_exit=z0^2+c`. At `max_depth=256`, the
four light settings produce 1024/1024 correct representative predictions with
no ambiguous exit keys. A Fourier power summary is included for the resulting
interaction-state signal, but is not yet used as the selector.

`verify-rule30-reduced-alphabet` tests the stricter reduction claim: use the
six chiral tokens, `ZERO`, the four signed `CR` light settings, the scalar
entry map, and invariant exchange laws as the entire rule catalog. It excludes
the 128-function Boolean catalog and ANF expansion as construction tools. At
`max_depth=1024`, it reproduces 32/32 local light-setting rows and 4096/4096
center-trace representative predictions. The negative control is important:
pair-product charges alone collapse `000` and singleton states; the scalar
shell is the reduced primitive that resolves that ambiguity.

`verify-rule30-symmetry-environment` promotes the reduced catalog into a finite
representation environment. The four signed light settings act as S1/U1 phase
representatives, the chirality sign is an SU2-style doublet, and `LC`, `LR`,
`CR` form an SU3-style color triplet under finite exchange, rotation, and
reflection. The harness reports Noether/Shannon/Landauer accounting and bounded
nonperiodicity diagnostics for the canonical center signal.

`verify-rule30-physics-stack` tests six non-arbitrary methods that naturally
follow from the existing finite CA/codeword structure: gauge normalization,
de Bruijn transfer operator, holonomy loops, correlation functions, ECC
syndrome decoding, and renormalization/coarse-graining. Each method is tested
solo, then the stack is applied cumulatively until all six run in one
framework.

`verify-rule30-n-coverage` tests whether every whole integer depth in a bounded
window is assigned by the reduced scalar coverage layer. It reports unassigned
`N` values, readout defects, pair-product-only ambiguities, and whether one
scalar `c` adjustment per `N` suffices without adding a new Boolean rule.

`verify-rule30-readout-ribbon` treats the center bar as a finite readout ribbon:
the emitted center bit becomes the next center input component. It checks
feedback defects, finite transition conflicts, strong/weak polarity bonds, and
a dimensionless mass/action proxy derived from the scalar/Lagrangian terms.
It keeps formal Turing universality as an open proof obligation.

`verify-rule30-dihedral-hypervisor` groups the readout ribbon into 8-depth
dihedral/spinor transport blocks. At depth 4096 this is exactly 512 complete
blocks with no tail. Each block is represented both as a compression object and
as a generation object for the next ribbon context.

`verify-rule30-extension-tape` treats each 4096-depth hypervisor setting as an
extension page. It checks that page exits feed the next page entry context, the
relative scalar transition table remains stable across pages, and each page can
continue the same lower scalar/ribbon/block math.

`verify-rule30-sheet-operator` extracts that stable relative table as
`T_rule30_relative_sheet`, a finite operator that maps reduced scalar state keys
to emitted center bits. This is the code object behind the page-power picture.

`verify-rule30-field-address`, `verify-rule30-exit-trajectory`,
`verify-rule30-sheet-lift`, and `verify-rule30-julia-resolution` implement the
corrected field view: the Rule 30 CA already defines the Mandelbrot field for
`N`; the two Julia sheets are primitive resolution sheets; arbitrary `N` lands
on lifted sheet `k` with continuation `k+1`; and the grid-square record must
resolve to the canonical center bit without an extra field search.

`verify-rule30-torsor-functor` adds the torsor term needed to calculate from
the two primitive sheets without choosing a fake origin. The CA base action is
the left action, the scalar/sheet functor is the right action, and the witness
checks that both land on the same lifted sheet. It also records the induced
spin/chirality state and a finite 2-functor/monad coherence witness.

`verify-rule30-oloid-winding` and `verify-rule30-oloid-antipode` expose the
spinor/Oloid kinematic bridge. The first checks a one-sided +N rolling chart;
the second carries the hidden `-N` counter-sheet beside it and reports whether
the adaptive +N/-N selector removes the residual center-bar defect. A zero
adaptive defect is recorded as a bounded witness, while a static depth-only
selector remains a separate proof obligation.

`verify-rule30-winding-number` records the bounded winding trace as a witness,
not as a finished arbitrary-N proof. It deliberately labels the result
`BOUNDED_TRACE_WITNESS` until a depth-only modular or continuous kinematic
extractor is derived.

`verify-rule30-nth-bit` emits the nth-bit expression in the reduced scalar
language: page/block/phase coordinates, local state, scalar `c_n`, CA-field
Julia resolution, and the sheet lookup all have to agree with the canonical
center bit.

`verify-rule30-proof-obligations` names the submission-facing ledger: bounded
execution evidence, formulaic expression evidence, and the theorem obligations
that remain before a public shortcut claim should be made.

Build checks:

```bash
python -m build
```

## Boundaries

Lattice Forge is a new product, not a direct main-CMPLX package. It preserves
the prototype's key idea: the database is the build system, and template or
conceptual rows must never be flattened into proof-grade exact morphisms.
