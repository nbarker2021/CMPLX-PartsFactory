# crystal — Interface

The composite primitive that binds SNAP-decomposition, MDHG-addressing,
and E8-position into one auditable record. Two surfaces:

1. **Data crystals** (`Crystal`, `E8Node`) — knowledge units mounted on
   the 10-level fabric (universe → galaxies → ... → atoms). A crystal
   holds N E8 nodes; each node carries `snap_labels + mdhg_address +
   e8_coords + content`.

2. **Tool crystals** (`ToolCrystal`, `ToolAtom`) — n=4 bonded atoms
   (INPUT, TRANSFORM, BOUNDARY, OUTPUT) that express a tool as a
   crystal. Composition rules let tool crystals bond into pipelines
   (SEQUENTIAL / PARALLEL / CONDITIONAL / RECURSIVE).

## Surface

### Fabric constants
- `DEFAULT_FABRIC` — 10 levels (universe..atoms)
- `ATOM_LEVELS` — 6-tier E8 quadrant (planet/city/building/floor/room/atom)
- `MEANING_LEVELS` — surface/semantic/latent/archetypal/transcendent
- `PLANET_NAMES` — alpha..kappa (9 digital-root families)

### Pure functions
- `digital_root(values) -> int` — 1..9 partition of a numeric vector
- `assign_address(content, e8_coords, entry_type, labels, content_hash, levels) -> dict` —
  builds a hierarchical MDHG-style address with `full` and `digital_root` fields
- `golay_encode(data_12) -> int` — Golay(24,12) parity
- `project_to_leech(e8_coords) -> list[float]` — 8D → 24D triadic phase replication

### `Crystal` (data)
Identity + `e8_root`, `meaning_levels`, `level_config`, `snap_address`,
`receipt_chain`, `node_count`, `total_mass`. Auto-generates id +
receipt on construction.

### `E8Node`
A single mounted point inside a crystal. Carries
`content + content_type + e8_coords + snap_labels + mdhg_address +
importance + meaning_level + mass`.

### `BlockType`, `CompositionRule`
String enums: INPUT/TRANSFORM/BOUNDARY/OUTPUT and
SEQUENTIAL/PARALLEL/CONDITIONAL/RECURSIVE.

### `ToolAtom`
A block of a tool crystal: `atom_id, block_type, tool_name, handler,
param_schema, output_desc, laws, snap_labels, e8_coords, description`.
Default `laws = ["delta_phi_le_0", "receipt_required"]`.

### `ToolCrystal`
`name, description, category, input_atom, transform_atom,
boundary_atom, output_atom, bonds, resonance, e8_coords`. `configure()`
sets the TRANSFORM handler + schema + laws. `add_bond()` links to
another crystal. `_compute_resonance()` is `sha256(name+category+desc)`.

### `CrystalRegistry` (the port provider)
- `create(name, ...) -> Crystal` — mints a data crystal
- `add_node(crystal_id, content, content_type, e8_coords, labels) -> E8Node`
- `get(crystal_id) -> Crystal | None`
- `list(state=None) -> list[Crystal]`
- `commit(crystal_id) -> dict` / `activate(crystal_id) -> dict`
- `register_tool(tool_crystal) -> None` / `get_tool(name) -> ToolCrystal`
- `vibrate(crystal_id, frequency) -> list[E8Node]` — resonance-based query

Registers on the `crystal` port of `MorphonController`.

## What's NOT in this layer

- Postgres persistence — `crystal_service.py` in `services/` handles
  that. This in-process registry uses MMDB through the `memory` port
  when persistence is needed.
- Tool execution — `CompositionExecutor` belongs in a future
  `cmplx.engine.cqe` (boundary enforcement, receipt chain).
- SNAP rule application — `SNAPLabeler` lives in `cmplx.snap`; the
  crystal just stores its output as `snap_labels`.
