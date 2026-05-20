# geometry — Bridge

## Port provided

`geometry` on `MorphonController`. Implements:

```python
class GeometryProvider(Protocol):
    def e8_coordinates(self, morphon: Morphon) -> tuple[float, ...]: ...
    def leech_point(self, morphon: Morphon) -> str: ...
```

## Provider class

`Geometry` from `cmplx.geometry`. Stateless. Instantiate once at boot
and register.

## Ports consumed

None. The geometry port is stdlib-only — `hashlib`, `math`. Extended
operations on sub-packages may use `numpy` for nearest-root and Weyl-
chamber math, but the port itself does not.

## How to wire up

```python
from cmplx.morphon import MorphonController
from cmplx.geometry import Geometry

MorphonController.get().register("geometry", Geometry())
```

## Test fixtures

Tests register `Geometry()` and verify:

- E8 coordinates are 8-tuples of floats in [-1, 1].
- L2 norm is approximately 1 (on the unit sphere).
- Same payload → same coordinates across calls.
- Different payloads → different coordinates (high probability).
- Leech point is a 50-char base-16 string with the `leech::` prefix.
