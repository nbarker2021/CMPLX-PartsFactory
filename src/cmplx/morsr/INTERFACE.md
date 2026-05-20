# morsr — Interface

**MORSR** (Middle-Out, Ripple, SubRipple — later renamed to many
things; the original intent is the canonical anchor) is a recursive
diagnostic-pulse engine. Take a centroid, pulse outward to anything
that touches it (ripple), pulse again to anything that touched that
(subripple), evaluate what was hit and what interfered, re-center,
repeat until you've traced everything.

Promoted from the canonical sources:
- `CQE_MORSR_NewBest_v1/cqe_plus/morsr.py` — the cleanest expression
  of the pulse / shell / handshake cycle.
- `morsr_complete.py` (CompleteMORSRExplorer) — the 240-node lattice
  traversal mode.
- `morsr_service.py` — the 240-direction sonar service form.
- User clarification: the diagnostic core is the centroid-pulse-
  ripple-subripple-recenter loop; everything else is accretion.

Acceptance gate runs through `cmplx.nsl` — every candidate is scored
as an `NSLSectors` triple and gated by the chosen `GateMode`
(GOVERN / AMORTIZE / SIGNAL).

## Surface

### `Overlay` — the pulse state

A position vector + optional 240-bit activation mask + arbitrary
metadata. Pulses mutate Overlays. Operators take Overlay → Overlay.

- `position: tuple[float, ...]` — the centroid coordinate (default 8-D)
- `activations: tuple[int, ...]` — bitmask of active E8 roots (default 240 zeros)
- `metadata: dict`
- `clone() -> Overlay`
- `hash_id() -> str` — content hash
- `to_dict()` / `from_dict()`

### Operators (the pulse generators)

Four canonical operators from `CQE_MORSR_NewBest`:
- `op_rtheta(overlay, theta=0.1) -> Overlay` — rotation in a 2-plane
- `op_weyl_reflect(overlay, root_index) -> Overlay` — reflect across a Weyl wall
- `op_midpoint(overlay, other) -> Overlay` — average two overlays
- `op_parity_mirror(overlay) -> Overlay` — flip the activation parity

All operators are pure (no in-place mutation). All return a new
Overlay. The set is pluggable — register custom operators via
`MORSREngine.add_operator(name, fn)`.

### Shells (the reach bounds)

A shell defines which indices a pulse is allowed to touch from the
current state. Two modes:

- **Radial**: indices within fractional radius `R = base × factor^stage`
- **BFS-hop**: indices reachable within `hops = base × factor^stage`
  via a neighbor relation

API:
- `Shell.radial(mask_len, base, factor, stage) -> (allowed_set, meta)`
- `Shell.bfs(mask_len, base, factor, stage, active_idxs) -> (allowed_set, meta)`
- `build_shell(mode, base, factor, stage, ...) -> (allowed_set, meta)`

### Handshake (the per-pulse audit trail)

Every candidate emits a `Handshake` — the diagnostic Reader half.

- `op: str`, `overlay_id: str`
- `phi_before: float`, `phi_after: float`, `delta: float`
- `sectors: NSLSectors`
- `reason: str` — `"strict_decrease"`, `"plateau"`, `"out_of_shell"`,
  `"rejected_govern"`, `"amortized"`, `"signaled_violation"`, etc.
- `accepted: bool`
- `signature: str` — content hash

`HandshakeLog` aggregates them with reason counts and per-op breakdown.

### Pulse cycle (the diagnostic ripple engine)

`MORSREngine.pulse(seed, max_stages=None)` runs the core cycle:

```
for stage in 0..N:
    shell = build_shell(mode, base, factors[stage], stage, current_actives)
    ring_0 = identity (the current overlay)
    ring_1 = [apply(op, current) for op in operators]
    for candidate in ring_1:
        if not candidate.in(shell): reject "out_of_shell"
        sectors = nsl.compute_sectors(current, candidate)
        decision = nsl.gate(sectors, mode=gate_mode, budget=stage_budget)
        emit Handshake(...)
    if any accepted: current = best_accepted
    update return-metric EMA
    if return_ema < stop_threshold: STOP
```

Outputs:
- `Region` — all overlays accepted, indexed by `overlay_id`
- `HandshakeLog` — the audit trail
- `StageMetrics` per stage (accepts / attempts / Δφ / return)

### `CompleteTraversal` mode

For the 240-node lattice variant (`CompleteMORSRExplorer`): visit
every E8 root exactly once per task, blending the current position
toward each root and scoring via NSL. Three traversal strategies:

- `"systematic"` — sequential 0..239
- `"distance_ordered"` — closest first
- `"chamber_guided"` — Weyl-chamber-sorted

Returns a comprehensive analysis with score statistics, chamber
distribution, parity variations, and top-k performing nodes.

### `SonarScan` mode

The diagnostic-by-pinging form (`morsr_service.py`): from a starting
coordinate, send 240 directional pings (one per E8 root), record
hit/no-hit per direction, classify coverage into shells:

- `shell_0` ≥ 50% directions hit
- `shell_1` ≥ 25%
- `shell_2` ≥ 10%
- `shell_3` < 10%

Emit **shadow actions** — gap-filling suggestions for unhit
directions, categorized into 8 dimensions: `geometry, computation,
agent, economy, governance, physics, observation, structure`.

### Provider

- `MORSREngine` — the pulse-cycle executor. Bundles operator set +
  shell mode + NSL provider + handshake log.
- `MORSRProvider` — registers on the `diagnostic` port of
  `MorphonController`. Exposes `pulse(seed)`, `traverse(seed, strategy)`,
  `scan(centroid, atoms, radius)`.

## What's NOT in this layer

- HTTP service skin (the `/ping`, `/scan`, `/atom`, `/intersection`
  endpoints from `morsr_service.py`). Lives in
  `services/morsr_service.py`, planned.
- The full triadic-parity-repair iteration from `MORSRExplorer` —
  the simple form is included; the full Bregman-distance Fejér-
  monotone version is downstream work.
- Cross-domain "complexity separation" insights (P/NP analysis)
  from `CompleteMORSRExplorer._make_overlay_determinations` —
  those are application-layer concerns, not engine concerns.
