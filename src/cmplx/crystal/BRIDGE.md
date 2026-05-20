# crystal — Bridge

## Port provided

`crystal` — `CrystalRegistry` is the canonical provider. Once
registered, components can `mc.get_provider("crystal").add_node(...)`
to mount a fact / asset / tool at a specific lattice position.

## Ports consumed (optional)

- `memory` — for durable persistence (delegates Crystal + E8Node rows
  to MMDB). Optional: in-process registry works without it.
- `addressing` — when constructing addresses, can defer to MDHG for
  richer `mdhg_address` fields. Currently uses the lightweight
  `assign_address` pure function inline.
- `geometry` — when computing `e8_root` from a name seed, can defer
  to `Geometry` for canonical embedding. Currently uses a SHA256 →
  unit-sphere fallback.

## Static imports

| Imports from | What | Why |
|---|---|---|
| `cmplx.geometry.e8` | `DIMENSION` | E8 vector length constraint. |
| `cmplx.geometry.alena` | `COUPLING`, `PHI` | Mass weighting and golden-ratio scaling. |

## What other components import FROM crystal

| Importer (current + planned) | What |
|---|---|
| `cmplx.snap` | `SNAPEngine.label` via `CrystalRegistry.add_node` / `mount_ennead`. |
| `cmplx.engine.cqe` (planned) | `ToolCrystal`, `CompositionRule` for the executor + boundary enforcement. |
| `cmplx.worlds.forge` (planned) | `Crystal` as world-state representation; `assign_address` for spatial routing. |
| `cmplx.transport.pixel` (future) | `E8Node.snap_labels` + `e8_coords` to render shape pixels (SNAP-driven render). |

## Cross-component semantics

A `Crystal` is the **bind record** that closes the loop:

```
SNAP.stratify(content) → labels
                  │
                  ▼
ALENA.project_to_channels(e8_coords) → channel-snapped vector
                  │
                  ▼
MDHG.assign_address(...) → mdhg_address
                  │
                  ▼
Crystal.add_node(content, e8_coords, labels) → E8Node
        with snap_labels + mdhg_address + e8_coords stored together
                  │
                  ▼
Crystal.receipt_chain extended (sha256 chain over inserts)
```

The receipt_chain is the auditable provenance: every node added
re-hashes the chain. This is the structural backbone for
`delta_phi ≤ 0` conservation enforcement (planned, in `cqe`).
