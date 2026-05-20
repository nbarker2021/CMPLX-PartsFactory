# nsl — Interface

**NSL = Noether-Shannon-Landauer.** The 3-sector conservation scalar
the entire system uses as ΔΦ / dphi / phi_total / "the acceptance
metric". Every operation in the unified system that changes state
must report its NSL delta; cumulative ΔΦ must stay ≤ 0.

Promoted from the canonical sources:
- `CMPLX-TMN-main/src/conservation/conservation.py` — the cumulative
  ledger service (`ΔΦ = ΔN + ΔI + ΔL`).
- `CMPLX-1T/docker/unified/aletheia_mvp/conservation_law.py` — the
  scalar computations (`Φ(v) = ||v||²/2`, Landauer cost, Shannon
  bound, adjustment).
- `CMPLX-TMN-main/src/personal_node/personal_node.py` — the
  3-triad / 24-D Leech structure of the sector vectors.
- `cmplx_pending/.../SNAPNslReceipts2025Q4.json` — the canonical
  receipt shape.

## The structural insight

The three sector triads (`triad_noether`, `triad_shannon`,
`triad_landauer`) are each **8-D**. Together they form a **24-D
Leech-lattice vector**. NSL isn't just terminology — the
three-sector decomposition IS the Leech embedding of the conservation
law.

## Surface

### Constants
- `COUPLING = 0.030076` — universal coupling, matches `geometry.alena.COUPLING`
- `TOLERANCE = 1e-10` — numerical tolerance for ΔΦ ≤ 0 comparison
- `BOLTZMANN_K = 1.380649e-23` — Boltzmann constant (J/K)
- `DEFAULT_TEMPERATURE = 300.0` — Kelvin

### Pure functions (the Phi primitives)
- `potential(vector) -> float` — `Φ(v) = ||v||² / 2`
- `delta_phi(v_before, v_after) -> float`
- `shannon_bound(vector) -> float` — `log₂(||v||² + 1)` bits
- `landauer_cost(delta_phi, temperature=300) -> float` — `k_B × T × |ΔΦ|` joules
- `enforce_conservation(v_before, v_after) -> (v_adjusted, was_adjusted)` —
  if ΔΦ > 0, scale `v_after` to preserve `||v_before||²`

### `NSLSectors` dataclass — the 3-sector scalar
- `dN: float`, `dI: float`, `dL: float`
- `total -> float` — sum of all three
- `is_conserved(tolerance=TOLERANCE) -> bool` — `total ≤ tolerance`
- `to_dict() -> {"dNoether", "dShannon", "dLandauer"}` — canonical receipt shape
- `from_dict(d) -> NSLSectors` — inverse

### `NSLTriads` dataclass — the 24-D Leech embedding
- `noether: list[float]` (8-D), `shannon: list[float]` (8-D), `landauer: list[float]` (8-D)
- `as_leech_vector -> tuple[float, ...]` — concatenated 24-D vector
- `score(x8) -> NSLSectors` — compute (dN, dI, dL) as inner products with each triad
- `hebbian_update(x8, reward, lr=COUPLING)` — learn the triads from rewarded experience
- `from_leech_vector(v24) -> NSLTriads`

### Gate modes
- `GateMode.GOVERN` (ΠG) — reject if ΔΦ > 0
- `GateMode.AMORTIZE` (ΠE) — allow with amortization against a budget
- `GateMode.SIGNAL` (ΠB) — signal but don't reject
- `gate(sectors, mode, budget=0.0) -> (accepted: bool, reason: str)`

### `NSLReceipt` dataclass
- `delta_phi: float`, `sectors: NSLSectors`, `timestamp: float`,
  `agent_id, service, atom_id, operation, epoch` — matches the
  canonical SNAP NSL receipt JSON

### `NSLLedger` — cumulative conservation ledger
- `append(receipt) -> dict` — adds entry; updates cumulative; flags violation if dΦ > 0
- `cumulative -> float`
- `violations -> int`
- `is_valid -> bool`
- `audit() -> dict` — recompute cumulative chain, return drift / errors
- `by_agent(agent_id) -> dict` / `by_service(service)` / `by_operation(op)`
- `stats() -> dict`

### `NSLProvider` (the port)
Registers on the `conservation` port of `MorphonController`. Bundles
`NSLLedger` with default gate mode and helper methods that any
component can call.

## What's NOT in this layer

- HTTP service skin (the FastAPI `/check`, `/ledger`, `/audit`
  endpoints from `conservation.py`). Lives in
  `services/conservation_service.py`, planned.
- Postgres persistence — the in-process ledger is the default; the
  MMDB-backed variant uses the `memory` port when available.
- Aletheia integration (adding an `NSLConservationLaw` to the
  default law set) — separate follow-up.
