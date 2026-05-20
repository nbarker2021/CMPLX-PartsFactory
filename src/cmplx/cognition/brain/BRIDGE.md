# Brain Bridge

The brain product currently bridges through existing CMPLX surfaces instead of
adding a new controller port.

## Current Wiring

`BrainProvider.vector_for_morphon(morphon)` tries this route:

1. `morphon.project_to_e8()` if the `geometry` port is registered.
2. Stable payload hashing when geometry is unavailable.

`BrainProvider.store_snapshot(agent_id)` tries this route:

1. Build a brain-state `Morphon` with `Brain.to_state()`.
2. Store it through the `memory` port if registered.
3. Mint a crossing receipt through the `receipt` port if registered.

All three integrations are optional and fail closed to the library behavior.

`BrainImageStore` is the local-first persistence bridge. It saves the same
product image produced by `Brain.to_image()` as JSON and can restore it without
Postgres, a service mesh, or Docker. This carries forward the MannyAI
local-brain sync pattern while matching the current PartsFactory rule that
service endpoints are not authority until wired.

Text/content routing enters through `think_text()` and `learn_text()`. These
methods use stable content hashing, so SNAP-style labelers and local tools can
ask the brain for an expert route without requiring geometry to be registered.

The 96-D manifold bridge enters through `think_manifold()` and
`learn_manifold()`. This mirrors the TMN brain hub's four 24-D lattices:
SELF, MEMORY, BODY, and ATTENTION. The current implementation trains each
24-D role as three 8-D expert-facing slices so it does not require a separate
96-D service runtime.

`contribute()`, `capacity_score()`, and `record_observation()` preserve the
global brain service and TMN4 personal-node memory behavior as local brain image
metadata. These are intentionally metadata/library operations for now; PG tables
and HTTP routes are deferred to a later service-wrapper pass.

## HTTP Wrapper

`cmplx.cognition.brain.service.create_app()` builds the current FastAPI wrapper
around `BrainProvider`. The wrapper exposes current library behavior plus
compatibility route names from prior brain services:

- `/think`, `/learn`, `/think_text`, `/learn_text`
- `/think_manifold`, `/learn_manifold`
- `/contribute`, `/capacity`, `/expertise`, `/fork`, `/merge`, `/compress`
- `/snapshot/{agent_id}` and local image save/load routes
- `/run`, `/probe`, `/experts`, `/verbalize` for Manny-runtime client shape

Known future integrations are explicit bridge stubs under `/bridges`:

- `controller_port`
- `conservation_gate`
- `pg_persistence`
- `docker_lattice_seed`
- `cqe_personal_step`

Bridge plans report what would be needed and perform no external mutation.

## Deferred Port Decision

The current controller has a fixed `KNOWN_PORTS` set. A future `cognition` or
`brain` port should be added only after a protocol pass decides the contract:
whether the port owns agent lifecycle, brain image persistence, inference,
learning, or all of those. This merge therefore restores the product code and
wiring adapters without expanding controller authority prematurely.
