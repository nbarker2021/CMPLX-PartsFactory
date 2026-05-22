# lattice-forge Production Manifest

## Identity

`lattice-forge` is a standalone lattice and morphism admissibility engine.
It is packaged as distribution `lattice-forge`, imported as `lattice_forge`,
stores project overlays in `.lattice_forge/`, and exposes one console command:
`lattice-forge`.

The package is not a public PyPP or main-CMPLX runtime. Prototype material was
preserved only where it forms the seed ledger and receipt model needed by the
new product.

## Implemented Layers

- `src/lattice_forge/seed.py` - read-only bundled seed database access.
- `src/lattice_forge/overlay.py` - project-local writable overlay database.
- `src/lattice_forge/ledger/` - preserved seed ledger query kernel and data.
- `src/lattice_forge/forge.py` - high-level service facade.
- `src/lattice_forge/terminal_tree.py` - generated terminal composition trees
  with residue-as-action-trace.
- `src/lattice_forge/cli.py` - production command line entry point.
- `src/lattice_forge/server.py` - optional FastAPI app factory.
- `docs/DATA_STATE.md` - seed and overlay state model.
- `docs/API.md` - Python API quick reference.
- `docs/SERVER.md` - optional server API notes.

## Data Surfaces

- Bundled seed database: immutable package data.
- Project overlay: `.lattice_forge/overlay.sqlite`.
- Overlay tables: `meta`, `receipts`, `events`, `query_cache`, `handoffs`,
  `imports`.
- Query responses preserve evidence/status labels such as `exact`,
  `computed_profile`, `template`, `conceptual`, and `pending_import`.

## Public Surfaces

- Python:
  - `from lattice_forge import Forge`
  - `Forge.open().can_close("G2", "A2^12")`
  - `Forge.open().terminal_tree("A2^12")`
  - `Forge.open().terminal_trees()`
  - `Forge.open().verify_terminal_trees()`
  - `Forge.open().future_cone("G2")`
  - `Forge.open().exactness_dashboard("G2")`
- CLI:
  - `lattice-forge status`
  - `lattice-forge can-close G2 A2^12`
  - `lattice-forge terminal-tree A2^12`
  - `lattice-forge terminal-trees`
  - `lattice-forge verify-terminal-trees`
  - `lattice-forge serve --host 127.0.0.1 --port 8765`
- Server:
  - `/health`
  - `/status`
  - `/objects/{id}`
  - `/can-close`
  - `/future-cone/{id}`
  - `/exactness/{id}`
  - `/terminal-tree/{id}`
  - `/terminal-trees`
  - `/terminal-trees/verify`
  - `/witnesses`
  - `/obstructions`
  - `/events`
  - `/receipts`
  - `/snapshot`

## Production Boundary

The v1 server is query-only. Command execution is intentionally absent, and
there is no `/run` endpoint.
