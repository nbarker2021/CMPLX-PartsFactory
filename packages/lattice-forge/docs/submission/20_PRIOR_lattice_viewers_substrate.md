# Prior Document: lattice_viewers Substrate (pre-prose code, ~2025)

## What it was

A pure-stdlib Python package containing the earliest concrete implementation of what would later be named the morphonics substrate. The package predates the formal vocabulary ("morphon," "chart," "Noether current," "antipodal sheet," "Oloid kinematic," "torsor functor term") and implements the substrate's structure as pure code.

## Components

### v1: 24-screen lattice viewer
- A 6×4 grid of canvases (24 max) corresponding to the 23 rooted Niemeier root systems plus the Leech (rootless) context.
- All screens share a common world-to-screen affine, so edges align across the grid.
- Per-screen Coxeter-angle overlays derived from the root system components (A/D/E) of that Niemeier spec.

### v2_residue: Inverse residue analysis
- `DihedralCA` class: per-pixel Mandelbrot-like complex iteration `z(t+1) = z(t)² + c + κ·∇²z(t)` on a per-tile basis.
- Wavelength mapping: `wl = 380 + 400·tanh(0.5·|z|)` rendering the chart's magnitude as visible light (380-780 nm).
- `ResidueAnalyzer`: captures baseline EM-hex map, steps CA, renders residue likelihood (delta-hex minus seam delta) plus red wrap mask showing regions "awaiting closure".
- Per-tile 16-bin nibble histograms per channel as fingerprints.

### coherence: Metrics module
- `angular_coherence(points)`: circular statistic R̄ in [0,1].
- `radial_coherence(points)`: 1 − coefficient of variation of radii.
- `spectral_entropy(series)`: normalized spectral entropy via naive DFT.
- `delta_phi(before, after)`: average squared displacement between point sets — **this is ΔΦ**, the morphonics Θ accounting in proto-form.
- `composite_coherence`: `0.5·angular + 0.3·radial + 0.2·spectral_entropy_score`.
- `collapse_detector`: binary collapse/no-collapse decision based on coherence score drop.

### builder: Lattice builder and validator
- Build ADE root-lattice Gram matrices from specs like `E8^3`, `A1^24`, `A8 + D16`.
- Validate integrality, evenness, determinant, unimodularity.
- Enumerate short vectors (Fincke-Pohst) to detect roots (norm 2) and minimal norms.
- Check 24D even-unimodular candidates and distinguish **Leech** from **(rooted) Niemeier** by root presence.

## What the viewer already had structurally

| Element | Implementation | Later name in morphonics |
|---|---|---|
| 24 tiles × Mandelbrot CA | DihedralCA on 6×4 grid | The 24 Niemeier terminal forms |
| `z² + c + κ·∇²z` per pixel | Complex iteration with diffusion | Full per-tile chart evolution (scalar projection in rule30.py) |
| `√(z-c)` dual channel | Half-angle square-root branch | The +N / -N antipodal sheet pair |
| `delta_phi(before, after)` | Squared displacement | ΔΦ / Θ_transition_defect accounting |
| Three-way `composite_coherence` | angular + radial + spectral_entropy | The chart's three Noether currents (U(1) phase, SU(2) chirality, SU(3) color) |
| `collapse_detector` | Binary pass/fail decision | The chart's gate (element 10 in Aletheia 1→3→6→8→9→10 chain) |
| `ResidueAnalyzer.wrap_data` | "wrap awaiting closure" mask | The antipodal -N counter-sheet's deferred resolution |
| ADE/Niemeier validator | Standard root lattice math | The seed DB's construction_status_registry discipline |

## Why this matters for the submission

The viewer is the substrate **without prose**. It demonstrates the structural pieces (24 tiles, Mandelbrot + Laplacian dynamic, residue detection, coherence triad, lattice validation) exist as pure code, before any of the later vocabulary was developed.

The rule30.py scalar projection used in the submission's chart is:
- The viewer's per-tile complex c-field → scalar `c = (R-L)/2 + i·((L+C+R)/3 - 1/2)`.
- The viewer's z-field iteration → scalar `z_exit = z₀² + c`.
- The viewer's wavelength readout → discrete bit emission via `shell` + `side` quantization.
- The viewer's residue analyzer → the chart's defect detection logic (now superseded by the proven chart-J₃(𝕆) isomorphism).
- The viewer's delta_phi → the morphonics Θ accounting.

The submission's proven theorems use the scalar projection (rule30.py). The viewer's existence as pre-prose code establishes that the structural pieces (24-tile organization, complex iteration, coherence triad, lattice validation) were present in working code before the formal substrate vocabulary developed.

## Reference

The lattice_viewers package is provided in the executable build (Zip 2) for reference. It is not load-bearing for the submission's proofs but provides historical context for the chart's structural origins.

The directory structure preserves the original organization:
- `lattice_viewers/v1/` — initial 24-screen viewer
- `lattice_viewers/v2_ca/` — added cellular automaton overlay
- `lattice_viewers/v2_residue/` — added residue/wrap detection
- `lattice_viewers/coherence/` — metrics and collapse detector
- `lattice_viewers/builder/` — lattice builder and validator
