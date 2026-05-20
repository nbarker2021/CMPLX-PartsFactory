"""
Fabric constants + pure functions for crystal addressing.

Adapted directly from the working `services/crystal_service.py`
implementation. The 10-level fabric is the canonical scaling hierarchy
that aligns with MDHG's grain→dust→...→universe ladder.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import Enum

from cmplx.geometry.alena import COUPLING, PHI


class HashAlgo(str, Enum):
    SHA3_512 = "sha3_512"
    SHA3_256 = "sha3_256"
    BLAKE2B = "blake2b"
    SHA256 = "sha256"


@dataclass(frozen=True)
class LevelConfig:
    name: str
    algorithm: HashAlgo
    output_bytes: int
    description: str = ""


DEFAULT_FABRIC: tuple[LevelConfig, ...] = (
    LevelConfig("universe",      HashAlgo.SHA3_512, 64, "Global attractor"),
    LevelConfig("galaxies",      HashAlgo.BLAKE2B,  32, "Domain cluster"),
    LevelConfig("systems",       HashAlgo.SHA3_256, 32, "Functional group"),
    LevelConfig("planets",       HashAlgo.SHA3_256, 32, "Module observer"),
    LevelConfig("cities",        HashAlgo.BLAKE2B,  32, "Route observer / AGRM"),
    LevelConfig("locals",        HashAlgo.SHA256,   32, "District hash"),
    LevelConfig("neighborhoods", HashAlgo.SHA256,   32, "Semantic cluster"),
    LevelConfig("buildings",     HashAlgo.SHA256,   16, "Structure hash"),
    LevelConfig("rooms",         HashAlgo.SHA256,   16, "Interior space"),
    LevelConfig("atoms",         HashAlgo.SHA256,    8, "Semantic atom"),
)


ATOM_LEVELS: tuple[LevelConfig, ...] = (
    LevelConfig("planet",   HashAlgo.SHA3_256, 32, "Digital root family"),
    LevelConfig("city",     HashAlgo.BLAKE2B,  32, "Content type"),
    LevelConfig("building", HashAlgo.SHA256,   16, "E8 quadrant"),
    LevelConfig("floor",    HashAlgo.SHA256,   16, "Content hash slice"),
    LevelConfig("room",     HashAlgo.SHA256,   16, "Label hash"),
    LevelConfig("atom",     HashAlgo.SHA256,    8, "Content identity"),
)


PLANET_NAMES: tuple[str, ...] = (
    "alpha", "beta", "gamma", "delta", "epsilon",
    "zeta", "eta", "theta", "kappa",
)


CITY_MAP: dict[str, str] = {
    "atom": "code", "code": "forge", "doc": "library", "data": "vault",
    "config": "tower", "mixed": "nexus", "tool": "tool", "agent": "agent",
    "document": "doc", "compose": "compose", "image": "image",
    "contract": "contract", "schema": "schema", "test": "test",
    "system": "system", "module": "module",
}


MEANING_LEVELS: tuple[str, ...] = (
    "surface", "semantic", "latent", "archetypal", "transcendent",
)


# Golay(24,12) generator matrix rows (12 bits each)
_GOLAY_GENERATOR: tuple[int, ...] = (
    0b110111000101, 0b101110001011, 0b011100010111,
    0b111000101101, 0b110001011011, 0b100010110111,
)


def _hash(data: bytes, algo: HashAlgo, size: int) -> str:
    if algo == HashAlgo.SHA3_512:
        h = hashlib.sha3_512(data).digest()
    elif algo == HashAlgo.SHA3_256:
        h = hashlib.sha3_256(data).digest()
    elif algo == HashAlgo.BLAKE2B:
        h = hashlib.blake2b(data, digest_size=min(size, 64)).digest()
    else:
        h = hashlib.sha256(data).digest()
    return h[:size].hex()


def digital_root(values) -> int:
    """1..9 digital root of |sum(values)|*1000. Zero maps to 9."""
    total = int(sum(abs(v) * 1000 for v in values))
    while total >= 10:
        total = sum(int(d) for d in str(total))
    return total if total > 0 else 9


def assign_address(
    content: str = "",
    e8_coords=None,
    entry_type: str = "atom",
    labels=None,
    content_hash: str = "",
    levels=None,
) -> dict:
    """Hierarchical address keyed across the fabric levels.

    Returns a dict with one entry per level + `full` (dotted path) +
    `digital_root`. Adapted from `services/crystal_service.py`.
    """
    e8 = list(e8_coords or [0.0] * 8)[:8]
    while len(e8) < 8:
        e8.append(0.0)
    ch = content_hash or hashlib.sha256(content.encode()).hexdigest()[:16]
    lvls = levels or ATOM_LEVELS

    address: dict = {}
    for i, lv in enumerate(lvls):
        nm = lv.name.lower()
        if nm in ("planet", "universe"):
            dr = digital_root(e8)
            address[lv.name] = PLANET_NAMES[dr - 1] if 1 <= dr <= 9 else "alpha"
        elif nm in ("city", "galaxies"):
            address[lv.name] = CITY_MAP.get(entry_type, "nexus")
        elif nm in ("building", "systems"):
            address[lv.name] = "".join("+" if c >= 0 else "-" for c in e8[:4])
        elif nm in ("floor", "locals", "neighborhoods"):
            seg = ch[i * 2:(i * 2) + 4] if len(ch) > i * 2 + 3 else ch[:4]
            address[lv.name] = f"F{int(seg, 16) % 64:02d}"
        elif nm in ("room", "cities"):
            lbl = "|".join(sorted(labels or []))
            address[lv.name] = f"R{int(hashlib.sha256(lbl.encode()).hexdigest()[:4], 16) % 128:03d}"
        elif nm in ("atom", "atoms"):
            address[lv.name] = ch[:8]
        else:
            address[lv.name] = _hash(
                f"{lv.name}:{ch}".encode(), lv.algorithm, lv.output_bytes
            )[:8]

    address["full"] = ".".join(address[l.name] for l in lvls)
    address["digital_root"] = digital_root(e8)
    return address


def golay_encode(data_12: int) -> int:
    """Golay(24,12) encoder. Input is 12 bits, output is 24."""
    if not 0 <= data_12 < (1 << 12):
        raise ValueError(f"data_12 must be 12 bits, got {data_12}")
    parity = 0
    for i, row in enumerate(_GOLAY_GENERATOR):
        if data_12 & (1 << i):
            parity ^= row
    return (data_12 << 12) | parity


def project_to_leech(e8_coords) -> list[float]:
    """8D → 24D triadic phase replication (rough Leech projection).

    Three E8 copies rotated by 2π/3 and 4π/3 phase offsets. The actual
    Leech lattice embedding is more involved (Niemeier, Conway); this
    captures the triadic structure usable for distance/cluster work.
    """
    leech: list[float] = []
    for phase in range(3):
        shift = phase * 2.0944  # ≈ 2π/3
        for i, c in enumerate(e8_coords[:8]):
            leech.append(c * math.cos(shift + i * 0.7854))
    return leech


def julia_iterate(c_real: float, c_imag: float, max_iter: int = 50) -> dict:
    """Julia-set iterator. Returns escape status + iteration count."""
    z_r, z_i = 0.0, 0.0
    for n in range(max_iter):
        z_r2, z_i2 = z_r * z_r, z_i * z_i
        if z_r2 + z_i2 > 4.0:
            return {
                "escaped": True,
                "iterations": n,
                "z_norm": math.sqrt(z_r2 + z_i2),
            }
        z_i = 2 * z_r * z_i + c_imag
        z_r = z_r2 - z_i2 + c_real
    return {
        "escaped": False,
        "iterations": max_iter,
        "z_norm": math.sqrt(z_r * z_r + z_i * z_i),
    }


def e8_seed_from_name(name: str) -> list[float]:
    """Deterministic E8 seed from a string name: SHA256 → unit sphere → φ scale."""
    sb = hashlib.sha256(name.encode()).digest()[:8]
    seed = [(b / 127.5 - 1.0) for b in sb]
    n = math.sqrt(sum(c * c for c in seed)) or 1.0
    return [c / n * PHI for c in seed]
