# aletheia — Bridge

## Port provided

`constraints` on `MorphonController`. Implements:

```python
class ConstraintsProvider(Protocol):
    def admit(self, morphon: Morphon) -> tuple[bool, str]: ...
```

## Provider class

`Aletheia` from `cmplx.constraints.aletheia`. Holds a tuple of
`ConservationLaw` objects; `admit()` walks them in order.

## Ports consumed

None in the first build. Stdlib only — `json`, `typing`.

Future extensions may consume:

- `geometry` — when Golay correction is lifted in, it needs the
  morphon's Leech projection to find the nearest valid codeword.
  Pattern: optional consumption (test for provider presence; degrade
  to "no correction available" if absent).

## How to wire up

```python
from cmplx.morphon import MorphonController
from cmplx.constraints.aletheia import Aletheia

MorphonController.get().register("constraints", Aletheia())
```

Custom laws:

```python
from cmplx.constraints.aletheia import (
    Aletheia, ConservationLaw, NoForbiddenKeysLaw,
)

aletheia = Aletheia()
aletheia.register_law(NoForbiddenKeysLaw("password", "secret"))
MorphonController.get().register("constraints", aletheia)
```

## Test fixtures

Tests register `Aletheia()` (with default laws) and verify:

- Well-formed morphons are admitted.
- Each built-in law refuses the morphons it should.
- Custom laws can be added and short-circuit correctly.
- Admission order is preserved.
- `admit_strict()` raises on rejection.
- End-to-end: `controller.admit_and_store()` with real Aletheia
  succeeds for valid morphons and raises for rejected ones.
