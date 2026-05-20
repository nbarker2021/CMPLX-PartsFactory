# Brain Interface

`cmplx.cognition.brain` is the composed-E8 brain image for the current
PartsFactory cognition lane.

The surface is library-first:

- `Expert` is one 8-D E8-positioned node with local weights and confidence.
- `LatticeSlice` composes three experts into a 24-D role slice.
- `Brain.manifold()` composes four role slices into the 96-D manifold view.
- `Brain.think(vector)` returns selected expert indexes, expert ids, scores,
  triad readings, tier, epoch, and freeze state.
- `Brain.learn(vector, reward, ...)` updates selected experts, triads, gating,
  contribution points, tier, and optional expert spawning.
- `Brain.to_state()` and `Brain.from_state()` round-trip the persistent brain
  image.
- `Brain.to_image()` and `Brain.from_image()` expose the product-level brain
  image, including capacity and conservation summaries.
- `Brain.expertise()` returns a routeable expert table for brain-routed
  classification and placement.
- `Brain.fork()` and `Brain.merge()` preserve the prior service behavior without
  requiring a service runtime.
- `Brain.compress()` preserves the prior brain-image compaction behavior.
- `Brain.think_manifold()` and `Brain.learn_manifold()` accept the 96-D
  SELF/MEMORY/BODY/ATTENTION shape used by the TMN/Claude brain hub.
- `Brain.contribute()` and `Brain.capacity_score()` carry forward the global
  brain-service contribution/capacity model.
- `Brain.record_observation()` stores personal-node label/address memory rows.
- `BrainProvider` manages brain instances and adapts morphons to vectors.
- `BrainImageStore` saves and loads local JSON brain images.

The provider does not reserve a MorphonController port. It can use existing
ports when the controller already has them:

- `geometry`: project a morphon to E8 before thinking.
- `memory`: store a snapshot morphon.
- `receipt`: mint a crossing receipt for a snapshot.

If geometry is not registered, morphon payloads are converted to stable 8-D
vectors by content hash. This keeps the product usable during assembly without
hardcoded URLs or invented port wiring.

Text routing is available through `BrainProvider.think_text()` and
`BrainProvider.learn_text()`. That carries forward MannyAI's in-process local
brain pattern without making live network services or Postgres a requirement.

## Provenance

This implementation is adapted from the prior local merge winner:

`D:\Manny Unification 2\proposals\manny-unified-build-2026-05-09\manny_runtime\brain.py`

The merge log that identified the winner is:

`D:\PartsFactory\Unification Prototypes\tools\brain\brain.py.merge.log.json`
