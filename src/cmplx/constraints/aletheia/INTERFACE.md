# aletheia — Interface

**Aletheia** is the system's conservation-law layer. Every morphon that
asks to be admitted runs through a chain of laws. Each law evaluates
the morphon against an invariant the system commits to preserving. If
any law refuses, the morphon is rejected with the law's reason.

Aletheia does not produce morphons; it admits or denies them. The
historical Aletheia2 / Aletheia3 designs framed this as ΔΦ ≤ 0
(operations may only decrease or preserve potential), with the Golay
code providing error-correction so borderline morphons can be
corrected before rejection. This first build implements the law-chain
admission shape; Golay correction is reference material, lifted in
when needed.

## What this package exposes

| Symbol | Purpose |
|---|---|
| `Aletheia(laws=None)` | Provider class. Takes an optional initial set of laws. |
| `Aletheia.admit(morphon)` | The primary operation. Returns `(admitted: bool, reason: str)`. |
| `Aletheia.register_law(law)` | Add a law to the chain. |
| `Aletheia.laws` | Read-only tuple of registered laws. |
| `ConservationLaw` | Abstract base. Subclass to define a law. |
| `LawResult` | The `(admitted, reason)` tuple. |
| `RejectionError` | Raised by `admit_strict()` on rejection. |
| Built-in laws (in `laws.py`): | |
| `PayloadIsMappingLaw` | Payload must be a Mapping. |
| `PayloadNotEmptyLaw` | Payload must have at least one key. |
| `PayloadSizeLimitLaw(max_bytes)` | Serialized payload under N bytes. |
| `StateTransitionWellFormedLaw` | Morphon must be in a state that can be admitted (not terminal). |
| `NoForbiddenKeysLaw(*keys)` | Reject morphons whose payload has any of the named keys. |

## How admission works

1. `admit(morphon)` walks the registered laws in order.
2. Each law's `evaluate(morphon)` is called.
3. The first law that returns `(False, reason)` short-circuits and
   that result is returned.
4. If all laws return `(True, "")`, the morphon is admitted.

Order matters — laws should be ordered cheapest-first so quick
rejections happen first.

## Writing a law

```python
from cmplx.constraints.aletheia import ConservationLaw, LawResult

class NoTimestampInFutureLaw(ConservationLaw):
    name = "no_timestamp_in_future"

    def evaluate(self, morphon) -> LawResult:
        ts = morphon.payload.get("timestamp")
        if ts and ts > current_time():
            return False, f"future timestamp not allowed: {ts}"
        return True, ""
```

Then:

```python
aletheia = Aletheia()
aletheia.register_law(NoTimestampInFutureLaw())
```

## Strict mode

For callers that want exceptions instead of `(False, reason)`:

```python
aletheia.admit_strict(morphon)  # raises RejectionError if denied
```

This is what the morphon controller's `admit_and_store` could be
upgraded to use; current behaviour wraps the result.

## Invariants

1. **Pure**: a law's `evaluate()` doesn't mutate the morphon.
2. **Ordered**: the registration order is the evaluation order.
3. **Short-circuit**: first rejection wins; later laws aren't called.
4. **Default laws**: `Aletheia()` with no args registers a sensible
   default set (the built-ins above). Pass `laws=[]` to start empty.

## What this package does NOT do

- Doesn't store the rejection — that's the caller's concern (the
  morphon controller records it on the morphon's receipt chain).
- Doesn't correct the morphon — Golay-correction is a separate
  operation (`golay_correct()`, not yet implemented in this build;
  reference at `_history_reference/Aletheia3Golay.py`).
- Doesn't decide policy — the laws are policy; this layer just
  evaluates them.

## How morphon talks to this

Through the `constraints` port:

```python
from cmplx.morphon import MorphonController
from cmplx.constraints.aletheia import Aletheia

MorphonController.get().register("constraints", Aletheia())
controller.admit_and_store(morphon)  # now uses real laws
```
