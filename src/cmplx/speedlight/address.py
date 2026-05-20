"""
SpeedLight-shaped MDHG address.

Adapted from `staging/by-family/mdhg/partsfactory/mdhg_speedlight.py`.
The 6-layer address `planet.city.building.floor.room.atom` lets you
turn neighbor queries into prefix matches and proximity queries into
E8 geometry.

This is the SpeedLight-flavored variant of the address scheme. The
existing `cmplx.crystal.fabric.assign_address` is the Crystal-flavored
variant; both produce comparable structures. The differences:

  - SpeedLight uses **planet names** (mercury..pluto) for the DR
    family; crystal.fabric uses (alpha..kappa). Same idea, different
    naming.
  - SpeedLight `floor` is the **SNAP label hash** (label neighborhood).
  - SpeedLight `building` is the **E8 sign pattern hash**.
  - SpeedLight `city` derives from content heuristics (forge / library
    / vault / nexus).

The 10 named cache aspects per address are listed in `ASPECTS`.
"""
from __future__ import annotations

import hashlib
from typing import Optional


# The 9 SpeedLight planets (digital-root family). Same DR class on
# the same planet → prefix match for DR-family queries.
PLANETS: tuple[str, ...] = (
    "mercury", "venus", "earth", "mars", "jupiter",
    "saturn", "uranus", "neptune", "pluto",
)

# The 10 canonical cache aspects per address.
ASPECTS: tuple[str, ...] = (
    "gate_w4",       # W4 legality result
    "gate_w80",      # W80 CRT result
    "kaprekar",      # convergence speed + path
    "sacred",        # DR class + triadic + frequency
    "phi",           # 4-component Phi metric
    "e8_nearest",    # nearest E8 lattice point
    "weyl_chamber",  # chamber signature
    "bonds",         # predicted + actual bond list
    "labels",        # full SNAP label set
    "metadata",      # arbitrary metadata
)


def _digital_root(n: int) -> int:
    n = abs(n)
    if n == 0:
        return 9
    return 1 + ((n - 1) % 9)


def _classify_city(content: str) -> str:
    """Entry-type heuristic for the city layer."""
    head = content[:100]
    head_short = content[:20]
    if any(tok in head for tok in ("def ", "class ", "import ", "function ")):
        return "forge"
    if head_short.startswith(("FILE REVIEW", "#", "---", "TITLE:", "## ")):
        return "library"
    if head_short.startswith(("{", "[", "<?", "<!DO", "<htm")):
        return "vault"
    return "nexus"


def compute_mdhg_address(
    content: str = "",
    content_hash: str = "",
    snap_labels: Optional[list[str]] = None,
    e8_coords: Optional[list[float]] = None,
    atom_id: str = "",
) -> dict:
    """Compute the 6-layer SpeedLight-shaped MDHG address.

    Returns a dict with `address` (the dotted full path) + each
    individual layer + `digital_root`. Symmetric to
    `cmplx.crystal.fabric.assign_address` but with the SpeedLight
    naming conventions.
    """
    labels = list(snap_labels or [])
    coords = list(e8_coords or [0.0] * 8)[:8]
    while len(coords) < 8:
        coords.append(0.0)
    ch = content_hash or hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    # Layer 1 — planet (DR family)
    dr = _digital_root(int(ch[:8], 16))
    planet = PLANETS[(dr - 1) % len(PLANETS)] if dr >= 1 else PLANETS[0]

    # Layer 2 — city (entry type)
    city = _classify_city(content)

    # Layer 3 — building (E8 quadrant via sign pattern)
    signs = "".join("+" if c >= 0 else "-" for c in coords)
    building = hashlib.md5(signs.encode()).hexdigest()[:4]

    # Layer 4 — floor (SNAP label neighborhood)
    label_key = ",".join(sorted(labels[:8]))
    floor = hashlib.md5(label_key.encode()).hexdigest()[:4]

    # Layer 5 — room (content hash prefix)
    room = ch[:4]

    # Layer 6 — atom (unique id)
    atom = (atom_id or ch[4:12])[:8]

    full = f"{planet}.{city}.{building}.{floor}.{room}.{atom}"
    return {
        "address": full,
        "planet": planet,
        "city": city,
        "building": building,
        "floor": floor,
        "room": room,
        "atom": atom,
        "digital_root": dr,
    }


_LEVELS = ("planet", "city", "building", "floor", "room", "atom")


def address_prefix(address: str, level: str) -> str:
    """Return the prefix of `address` up to and including `level`.

    Useful for neighborhood queries: an exact `planet` prefix gives
    all atoms in the same DR family; an exact `floor` prefix gives
    label neighbors; etc.
    """
    if level not in _LEVELS:
        raise ValueError(f"unknown level {level!r}; expected one of {_LEVELS}")
    parts = address.split(".")
    if len(parts) < 6:
        raise ValueError(f"malformed MDHG address {address!r}")
    n = _LEVELS.index(level) + 1
    return ".".join(parts[:n])


def aspect_key(address: str, aspect: str) -> str:
    """Build the `{address}:{aspect}` cache key."""
    if aspect not in ASPECTS:
        # Permit custom aspects but still emit them with the same shape
        pass
    return f"{address}:{aspect}"


def parse_address(address: str) -> dict:
    """Inverse of `compute_mdhg_address`: pull the 6 layers out of a
    dotted-path address. Does NOT recover digital_root (lossy)."""
    parts = address.split(".")
    if len(parts) != 6:
        raise ValueError(f"expected 6 levels, got {len(parts)}: {address!r}")
    return dict(zip(_LEVELS, parts))
