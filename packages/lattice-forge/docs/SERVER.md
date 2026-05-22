# Server

Install server extras:

```bash
python -m pip install -e ".[server]"
```

Run:

```bash
lattice-forge serve --host 127.0.0.1 --port 8765
```

The server is a local FastAPI wrapper around the same `Forge` service layer used
by the Python API and CLI.

Useful endpoints:

- `GET /health`
- `GET /status`
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
- `GET /events`
- `GET /receipts`
- `GET /snapshot`

`/terminal-tree/A2^12` generates the canonical terminal component-action tree
and residue trace for the `Niemeier:A2^12` form.

`/terminal-trees` returns normalized summaries for all 24 terminal forms.
`/terminal-trees/verify` returns pass/fail diagnostics for the all-terminal
composition-tree checks.

`/morphonics/model` returns the Morphonic State Closure Framework v0.2 as
ledger-shaped records. `/morphonics/verify` validates those records and should
return `pass_with_open_gaps` while preserving pending research failures.

`/rule30/morphon` runs the hardened Rule 30 Morphon harness. `/rule30/verify`
validates canonical single-seed closure and reports arbitrary-row compression
limits as warnings/open gaps.

`/rule30/vignettes` generates the rotated-cone vignette composition algebra.
`/rule30/vignettes/verify` checks that the order-4 algebra saturates the local
zero-preserving Boolean function space while preserving global-decoder gaps.

`/rule30/moving-frame` applies the triadic co-moving bar/state filter over the
vignette algebra. `/rule30/moving-frame/verify` checks the resolver law and
reports the reduced moving-frame candidate space.

`/rule30/color-chirality` exposes the six-token color/chirality cipher over
the Rule 30 pair-codewords. `/rule30/color-chirality/verify` checks token
coverage and closure under composition, rotation, and L/R reflection.

`/rule30/lagrangian` exposes the finite Rule 30 discrete action ledger with
Noether/Shannon/Landauer accounting. `/rule30/lagrangian/verify` checks that
zero action is equivalent to legal local Rule 30 updates and that the finite
Noether currents close.

`/rule30/lagrangian-trace` applies the action ledger to the canonical
center-column depth trace and scores all moving chiral schedules. The verify
endpoint checks that every tested depth has a zero-action token and that at
least one moving schedule remains zero-action across the window.

`/rule30/mandelbrot-scalar` exposes the finite Mandelbrot/Julia boundary scalar
over the four signed locked-`CR` light settings. The verify endpoint checks
that the light settings are well-formed, exit keys are unambiguous, and the
tested representative predictions are exact.

`/rule30/reduced-alphabet` tests the stricter construction catalog that uses
only the six chiral tokens, `ZERO`, four signed light settings, the scalar
entry map, and invariant exchange laws. The verify endpoint checks local and
depth-trace equivalence while preserving the pair-product-only negative
control.

`/rule30/symmetry-environment` exposes the finite S1/U1, SU2-style, and
SU3-style representation layer for the reduced catalog. The verify endpoint
checks phase count, 3 x 2 token-space closure, Noether defect, reduced catalog
accuracy, and bounded nonperiodicity diagnostics.

`/rule30/physics-stack` runs the six-method hardening suite: gauge
normalization, de Bruijn transfer, holonomy, correlations, ECC syndrome
decoding, and renormalization/coarse-graining. The verify endpoint checks that
each solo method passes and that the cumulative all-six stack has zero defect.

`/rule30/n-coverage` tests whole-integer depth coverage for the reduced scalar
layer. The verify endpoint checks that no tested `N` is unassigned, no scalar
readout defects appear, and the only pair-product-only ambiguity remains the
expected `000 -> [0, 1]` class.

`/rule30/readout-ribbon` treats the center bar as a finite readout-ribbon
machine. The verify endpoint checks output-to-next-input feedback, transition
conflicts, strong/weak polarity bond assignment, scalar coverage, and the
finite mass/action proxy.

`/rule30/dihedral-hypervisor` groups the readout ribbon into 8-depth
dihedral/spinor transport blocks. The verify endpoint checks complete block
coverage, zero tail, zero block conflicts, and preserved lower ribbon closure.

`/rule30/extension-tape` appends hypervisor pages and checks that each 4096
setting can continue the same lower scalar/ribbon/block math. The verify
endpoint checks page-boundary feedback, stable relative tables, and preserved
lower closure.

`/rule30/sheet-operator` exposes the finite relative sheet operator that maps
reduced scalar state keys to emitted center bits. The verify endpoint checks
stable page hashes and zero transition conflicts.

`/rule30/nth-bit/{n}` returns the formulaic nth-bit expression: page, block,
phase, local state, scalar, Julia exit, and sheet-table witness. The verify
endpoint checks that every reported bit witness agrees.

`/rule30/proof-obligations` returns the submission ledger for bounded execution,
formulaic expression, and theorem obligations. The verify endpoint checks the
ledger shape and preserves named open proof work instead of hiding it.

There is no `/run` endpoint in v1.
