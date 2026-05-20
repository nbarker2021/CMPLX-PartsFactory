"""Crystal Service — Crystal + MDHG + CPL projection system.

Port of TMN2 crystal.py. Crystals are custom hash tables shaped to
their data's geometry. MDHG provides hash-derived addressing per
level. CPL provides Leech lattice, Golay, and Julia projection.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("services.crystal")

PORT = int(os.environ.get("PORT", "8000"))
PG_URL = os.environ.get("PG_URL", "")
COUPLING = float(os.environ.get("COUPLING", "0.030076"))
PHI = (1 + math.sqrt(5)) / 2


class HashAlgo(str, Enum):
    SHA3_512 = "sha3_512"
    SHA3_256 = "sha3_256"
    BLAKE2B = "blake2b"
    SHA256 = "sha256"


@dataclass
class LevelConfig:
    name: str
    algorithm: HashAlgo
    output_bytes: int
    description: str = ""


DEFAULT_FABRIC = [
    LevelConfig("universe",       HashAlgo.SHA3_512, 64, "Global attractor"),
    LevelConfig("galaxies",       HashAlgo.BLAKE2B,  32, "Domain cluster"),
    LevelConfig("systems",        HashAlgo.SHA3_256, 32, "Functional group"),
    LevelConfig("planets",        HashAlgo.SHA3_256, 32, "Module observer"),
    LevelConfig("cities",         HashAlgo.BLAKE2B,  32, "Route observer / AGRM"),
    LevelConfig("locals",         HashAlgo.SHA256,   32, "District hash"),
    LevelConfig("neighborhoods",  HashAlgo.SHA256,   32, "Semantic cluster"),
    LevelConfig("buildings",      HashAlgo.SHA256,   16, "Structure hash"),
    LevelConfig("rooms",          HashAlgo.SHA256,   16, "Interior space"),
    LevelConfig("atoms",          HashAlgo.SHA256,    8, "Semantic atom"),
]

ATOM_LEVELS = [
    LevelConfig("planet",   HashAlgo.SHA3_256, 32, "Digital root family"),
    LevelConfig("city",     HashAlgo.BLAKE2B,  32, "Content type"),
    LevelConfig("building", HashAlgo.SHA256,   16, "E8 quadrant"),
    LevelConfig("floor",    HashAlgo.SHA256,   16, "Content hash slice"),
    LevelConfig("room",     HashAlgo.SHA256,   16, "Label hash"),
    LevelConfig("atom",     HashAlgo.SHA256,    8, "Content identity"),
]

PLANET_NAMES = ["alpha", "beta", "gamma", "delta", "epsilon",
                "zeta", "eta", "theta", "kappa"]

CITY_MAP = {
    "atom": "code", "code": "forge", "doc": "library", "data": "vault",
    "config": "tower", "mixed": "nexus", "tool": "tool", "agent": "agent",
    "document": "doc", "compose": "compose", "image": "image",
    "contract": "contract", "schema": "schema", "test": "test",
    "system": "system", "module": "module",
}

MEANING_LEVELS = ["surface", "semantic", "latent", "archetypal", "transcendent"]
_GOLAY_GENERATOR = [
    0b110111000101, 0b101110001011, 0b011100010111,
    0b111000101101, 0b110001011011, 0b100010110111,
]


@dataclass
class Crystal:
    crystal_id: str = ""
    name: str = ""
    crystal_type: str = "knowledge"
    state: str = "growing"
    e8_root: list[float] = field(default_factory=lambda: [0.0] * 8)
    meaning_levels: list[str] = field(default_factory=lambda: MEANING_LEVELS[:3])
    level_config: list[dict] = field(default_factory=list)
    owner: str = ""
    snap_address: str = ""
    receipt_chain: str = ""
    created_at: float = 0.0
    node_count: int = 0
    total_mass: float = 0.0

    def __post_init__(self):
        if not self.crystal_id:
            self.crystal_id = str(uuid.uuid4())[:12]
        if not self.receipt_chain:
            self.receipt_chain = hashlib.sha256(
                f"crystal:{self.crystal_id}".encode()
            ).hexdigest()[:32]
        if not self.created_at:
            self.created_at = time.time()
        if not self.snap_address:
            self.snap_address = f"crystal://{self.name or self.crystal_id}"


@dataclass
class E8Node:
    node_id: str = ""
    crystal_id: str = ""
    content: str = ""
    content_type: str = "atom"
    e8_coords: list[float] = field(default_factory=lambda: [0.0] * 8)
    snap_labels: list[str] = field(default_factory=list)
    mdhg_address: dict = field(default_factory=dict)
    importance: float = 0.5
    meaning_level: int = 0
    mass: float = 0.0

    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"node-{uuid.uuid4().hex[:8]}"
        if not self.mass:
            self.mass = len(self.snap_labels) * COUPLING


# ── Pure functions (no state) ───────────────────────────────

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


def digital_root(values: list[float]) -> int:
    total = int(sum(abs(v) * 1000 for v in values))
    while total >= 10:
        total = sum(int(d) for d in str(total))
    return total if total > 0 else 9


def assign_address(content: str = "", e8_coords: list[float] = None,
                   entry_type: str = "atom", labels: list[str] = None,
                   content_hash: str = "",
                   levels: list[LevelConfig] = None) -> dict:
    e8 = list(e8_coords or [0.0] * 8)[:8]
    while len(e8) < 8:
        e8.append(0.0)
    ch = content_hash or hashlib.sha256(content.encode()).hexdigest()[:16]
    lvls = levels or ATOM_LEVELS

    address = {}
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
    parity = 0
    for i, row in enumerate(_GOLAY_GENERATOR):
        if data_12 & (1 << i):
            parity ^= row
    return (data_12 << 12) | parity


def project_to_leech(e8_coords: list[float]) -> list[float]:
    leech = []
    for phase in range(3):
        shift = phase * 2.0944
        for i, c in enumerate(e8_coords[:8]):
            leech.append(c * math.cos(shift + i * 0.7854))
    return leech


def julia_iterate(c_real: float, c_imag: float, max_iter: int = 50) -> dict:
    z_r, z_i = 0.0, 0.0
    for n in range(max_iter):
        z_r2, z_i2 = z_r * z_r, z_i * z_i
        if z_r2 + z_i2 > 4.0:
            return {"escaped": True, "iterations": n,
                    "z_norm": math.sqrt(z_r2 + z_i2)}
        z_i = 2 * z_r * z_i + c_imag
        z_r = z_r2 - z_i2 + c_real
    return {"escaped": False, "iterations": max_iter,
            "z_norm": math.sqrt(z_r * z_r + z_i * z_i)}


class CrystalService:
    """Crystal + MDHG + CPL universe factory.

    Creates and manages crystals (custom hash tables shaped to data geometry),
    with MDHG hierarchical addressing and CPL projection (Golay, Leech, Julia).
    """

    def __init__(self, pg_url: str = "", governance=None):
        self._governance = governance
        self._pg_url = pg_url or PG_URL
        self._pg_conn = None
        self._crystals: dict[str, Crystal] = {}
        self._init_tables()
        self._load_crystals_from_pg()

    def _get_pg(self):
        if not self._pg_url:
            return None
        try:
            import psycopg2
            if self._pg_conn is None or self._pg_conn.closed:
                self._pg_conn = psycopg2.connect(self._pg_url)
                self._pg_conn.autocommit = True
            return self._pg_conn
        except Exception:
            return None

    def _init_tables(self):
        conn = self._get_pg()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS crystals (
                crystal_id TEXT PRIMARY KEY, name TEXT,
                crystal_type TEXT DEFAULT 'knowledge',
                state TEXT DEFAULT 'growing', e8_root JSONB DEFAULT '[]',
                meaning_levels JSONB DEFAULT '[]',
                level_config JSONB DEFAULT '[]',
                owner TEXT DEFAULT '', snap_address TEXT DEFAULT '',
                receipt_chain TEXT DEFAULT '', node_count INT DEFAULT 0,
                total_mass DOUBLE PRECISION DEFAULT 0,
                created_at DOUBLE PRECISION,
                committed_at DOUBLE PRECISION,
                activated_at DOUBLE PRECISION)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS e8_nodes (
                node_id TEXT PRIMARY KEY, crystal_id TEXT,
                content TEXT DEFAULT '',
                content_type TEXT DEFAULT 'atom',
                e8_coords JSONB DEFAULT '[]',
                snap_labels JSONB DEFAULT '[]',
                mdhg_address JSONB DEFAULT '{}',
                importance DOUBLE PRECISION DEFAULT 0.5,
                meaning_level INT DEFAULT 0,
                mass DOUBLE PRECISION DEFAULT 0,
                created_at DOUBLE PRECISION)""")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_e8n_crystal ON e8_nodes(crystal_id)")
        except Exception as e:
            logger.warning("PG init: %s", e)

    def _save_crystal(self, c: Crystal):
        conn = self._get_pg()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("""INSERT INTO crystals
                (crystal_id, name, crystal_type, state, e8_root,
                 meaning_levels, level_config, owner, snap_address,
                 receipt_chain, node_count, total_mass, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (crystal_id) DO UPDATE SET
                state=EXCLUDED.state, node_count=EXCLUDED.node_count,
                total_mass=EXCLUDED.total_mass,
                receipt_chain=EXCLUDED.receipt_chain""",
                        (c.crystal_id, c.name, c.crystal_type, c.state,
                         json.dumps(c.e8_root), json.dumps(c.meaning_levels),
                         json.dumps(c.level_config), c.owner, c.snap_address,
                         c.receipt_chain, c.node_count, c.total_mass, c.created_at))
        except Exception as e:
            logger.warning("PG save: %s", e)

    def _save_node(self, n: E8Node):
        conn = self._get_pg()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("""INSERT INTO e8_nodes
                (node_id, crystal_id, content, content_type,
                 e8_coords, snap_labels, mdhg_address, importance,
                 meaning_level, mass, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (node_id) DO NOTHING""",
                        (n.node_id, n.crystal_id, n.content[:2000], n.content_type,
                         json.dumps(n.e8_coords), json.dumps(n.snap_labels),
                         json.dumps(n.mdhg_address), n.importance,
                         n.meaning_level, n.mass, time.time()))
        except Exception as e:
            logger.warning("PG node: %s", e)

    def _load_crystals_from_pg(self):
        conn = self._get_pg()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM crystals"
            )
            cols = [d[0] for d in cur.description]
            for row in cur.fetchall():
                data = dict(zip(cols, row))
                c = Crystal(
                    crystal_id=data.get("crystal_id", ""),
                    name=data.get("name", ""),
                    state=data.get("state", "growing"),
                    e8_root=json.loads(data["e8_root"]) if isinstance(data.get("e8_root"), str) else (data.get("e8_root") or [0.0] * 8),
                    meaning_levels=json.loads(data["meaning_levels"]) if isinstance(data.get("meaning_levels"), str) else (data.get("meaning_levels") or []),
                    level_config=json.loads(data["level_config"]) if isinstance(data.get("level_config"), str) else (data.get("level_config") or []),
                    owner=data.get("owner", ""),
                    snap_address=data.get("snap_address", ""),
                    receipt_chain=data.get("receipt_chain", ""),
                    node_count=data.get("node_count", 0),
                    total_mass=data.get("total_mass", 0),
                    created_at=data.get("created_at", 0) or 0,
                )
                self._crystals[c.crystal_id] = c
            logger.info("Loaded %d crystals from PG", len(self._crystals))
        except Exception as e:
            logger.warning("PG load: %s", e)

    # ── Public API ───────────────────────────────────────────

    def create_crystal(self, name: str, crystal_type: str = "knowledge",
                       e8_seed: list[float] = None,
                       meaning_depth: int = 3, level_count: int = 6,
                       owner: str = "") -> Crystal:
        if not e8_seed:
            sb = hashlib.sha256(name.encode()).digest()[:8]
            e8_seed = [(b / 127.5 - 1.0) for b in sb]
            n = math.sqrt(sum(c * c for c in e8_seed)) or 1.0
            e8_seed = [c / n * PHI for c in e8_seed]
        levels = DEFAULT_FABRIC[:level_count] if level_count <= 10 else DEFAULT_FABRIC
        crystal = Crystal(
            name=name, crystal_type=crystal_type, e8_root=e8_seed,
            meaning_levels=MEANING_LEVELS[:meaning_depth],
            level_config=[asdict(l) for l in levels], owner=owner,
        )
        self._crystals[crystal.crystal_id] = crystal
        self._save_crystal(crystal)

        if self._governance:
            from governance.engine import BoundaryEvent
            self._governance.record_boundary_event(BoundaryEvent(
                event_id=f"crystal-{crystal.crystal_id}",
                timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"crystal_id": crystal.crystal_id, "name": name},
                boundary_type="crystal_create",
            ))

        return crystal

    def add_node(self, crystal_id: str, content: str,
                 content_type: str = "atom",
                 e8_coords: list[float] = None,
                 labels: list[str] = None) -> E8Node:
        crystal = self._crystals.get(crystal_id)
        if not crystal:
            raise ValueError(f"Crystal {crystal_id} not found")
        levels = [LevelConfig(**l) for l in crystal.level_config] if crystal.level_config else ATOM_LEVELS
        mdhg = assign_address(
            content=content, e8_coords=e8_coords or crystal.e8_root,
            entry_type=content_type, labels=labels, levels=levels,
        )
        node = E8Node(
            crystal_id=crystal_id, content=content,
            content_type=content_type, e8_coords=e8_coords or crystal.e8_root,
            snap_labels=labels or [], mdhg_address=mdhg,
            mass=len(labels or []) * COUPLING,
        )
        crystal.node_count += 1
        crystal.total_mass += node.mass
        crystal.receipt_chain = hashlib.sha256(
            f"{crystal.receipt_chain}:node:{node.node_id}:{time.time()}".encode()
        ).hexdigest()[:32]
        self._save_node(node)
        self._save_crystal(crystal)
        return node

    def get_crystal(self, crystal_id: str) -> Optional[Crystal]:
        return self._crystals.get(crystal_id)

    def list_crystals(self, state: str = "") -> list[dict]:
        return [
            asdict(c) for c in self._crystals.values()
            if not state or c.state == state
        ]

    def commit_crystal(self, crystal_id: str) -> dict:
        c = self._crystals.get(crystal_id)
        if not c:
            raise ValueError("Crystal not found")
        c.state = "committed"
        self._save_crystal(c)
        return {"crystal_id": crystal_id, "state": "committed", "nodes": c.node_count}

    def activate_crystal(self, crystal_id: str) -> dict:
        c = self._crystals.get(crystal_id)
        if not c:
            raise ValueError("Crystal not found")
        c.state = "active"
        self._save_crystal(c)
        return {"crystal_id": crystal_id, "state": "active"}

    @property
    def hash_fabric(self) -> dict:
        return {
            "full_10": [asdict(l) for l in DEFAULT_FABRIC],
            "atom_6": [asdict(l) for l in ATOM_LEVELS],
            "algorithms": [a.value for a in HashAlgo],
        }

    @property
    def health(self) -> dict:
        return {
            "ok": True, "service": "crystal-mdhg-cpl",
            "crystals": len(self._crystals),
            "total_nodes": sum(c.node_count for c in self._crystals.values()),
        }
