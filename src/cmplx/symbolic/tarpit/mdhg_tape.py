"""
MDHG-backed TarPit tape (glyphic_tarpit preview → spine).

Planet/slot hash-graph storage for tape cells. Stdlib-only; uses in-memory
or filesystem SQLite. Full CMPLX MDHG routing is a future bridge target.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TapePosition:
    planet_id: str
    slot: int


class MDHGTapeBackend:
    """Simplified MDHG backend — one SQLite DB per planet."""

    def __init__(self, base_path: str = ":memory:") -> None:
        self.in_memory = base_path == ":memory:"
        if self.in_memory:
            self.base_path = Path(".")
        else:
            self.base_path = Path(base_path)
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.registry_path = self.base_path / "planets.db"
            self._init_registry()
        self.planets: Dict[str, sqlite3.Connection] = {}

    def _init_registry(self) -> None:
        conn = sqlite3.connect(self.registry_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS planets (
                planet_id TEXT PRIMARY KEY,
                created_at REAL,
                access_count INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()
        conn.close()

    def get_or_create_planet(self, planet_id: str) -> sqlite3.Connection:
        if planet_id in self.planets:
            return self.planets[planet_id]
        if self.in_memory:
            conn = sqlite3.connect(
                f"file:{planet_id}?mode=memory&cache=shared", uri=True
            )
        else:
            conn = sqlite3.connect(self.base_path / f"{planet_id}.db")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS slots (
                slot_id TEXT PRIMARY KEY,
                slot_num INTEGER,
                payload TEXT,
                glyph_logic TEXT,
                created_at REAL,
                access_count INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()
        if not self.in_memory:
            reg = sqlite3.connect(self.registry_path)
            reg.execute(
                "INSERT OR IGNORE INTO planets (planet_id, created_at) VALUES (?, ?)",
                (planet_id, 0.0),
            )
            reg.commit()
            reg.close()
        self.planets[planet_id] = conn
        return conn

    def put(
        self,
        planet_id: str,
        slot: int,
        payload: Dict[str, Any],
        glyph_logic: Optional[str] = None,
    ) -> Dict[str, Any]:
        conn = self.get_or_create_planet(planet_id)
        slot_id = f"{planet_id}_{slot}"
        conn.execute(
            """
            INSERT OR REPLACE INTO slots
            (slot_id, slot_num, payload, glyph_logic, created_at, access_count)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (slot_id, slot, json.dumps(payload), glyph_logic, 0.0),
        )
        conn.commit()
        return {"slot_id": slot_id, "planet": planet_id, "slot": slot}

    def get(self, planet_id: str, slot: int) -> Optional[Dict[str, Any]]:
        if planet_id not in self.planets:
            if self.in_memory:
                return None
            planet_path = self.base_path / f"{planet_id}.db"
            if not planet_path.exists():
                return None
            self.planets[planet_id] = sqlite3.connect(planet_path)
        conn = self.planets[planet_id]
        slot_id = f"{planet_id}_{slot}"
        row = conn.execute(
            "SELECT payload, glyph_logic FROM slots WHERE slot_id = ?",
            (slot_id,),
        ).fetchone()
        if row:
            return {
                "payload": json.loads(row[0]) if row[0] else None,
                "glyph_logic": row[1],
            }
        return None

    def list_planets(self) -> List[str]:
        if self.in_memory:
            return list(self.planets.keys())
        conn = sqlite3.connect(self.registry_path)
        rows = conn.execute("SELECT planet_id FROM planets").fetchall()
        conn.close()
        return [r[0] for r in rows]


PLANET_CAPACITY = 1000


@dataclass
class TarpitMDHGTape:
    """TarPit tape with MDHG planet/slot addressing."""

    backend: MDHGTapeBackend = field(default_factory=MDHGTapeBackend)
    _pointer: TapePosition = field(
        default_factory=lambda: TapePosition("planet_0", 0)
    )
    _cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def pointer(self) -> Tuple[str, int]:
        return (self._pointer.planet_id, self._pointer.slot)

    @pointer.setter
    def pointer(self, value: Tuple[str, int]) -> None:
        planet_id, slot = value
        self._pointer = TapePosition(planet_id, slot)

    def read_cell(self, position: Optional[Tuple[str, int]] = None) -> Dict[str, Any]:
        if position is None:
            position = self.pointer
        planet_id, slot = position
        cache_key = f"{planet_id}:{slot}"
        if cache_key in self._cache:
            return dict(self._cache[cache_key])
        data = self.backend.get(planet_id, slot)
        if data and data.get("payload"):
            cell = dict(data["payload"])
        else:
            cell = {"glyph": "∅", "glyph_id": "empty", "position": position}
        cell["position"] = position
        self._cache[cache_key] = cell
        return cell

    def write_cell(
        self,
        payload: Dict[str, Any],
        *,
        position: Optional[Tuple[str, int]] = None,
        glyph_logic: Optional[str] = None,
    ) -> Dict[str, Any]:
        if position is None:
            position = self.pointer
        planet_id, slot = position
        payload = dict(payload)
        payload["position"] = position
        result = self.backend.put(
            planet_id, slot, payload, glyph_logic=glyph_logic or payload.get("glyph")
        )
        cache_key = f"{planet_id}:{slot}"
        self._cache[cache_key] = payload
        return result

    def move_pointer(self, delta: int) -> Tuple[str, int]:
        planet_id, slot = self.pointer
        new_slot = slot + delta
        if new_slot < 0:
            planet_num = int(planet_id.split("_")[1]) if "_" in planet_id else 0
            self._pointer = TapePosition(f"planet_{planet_num - 1}", PLANET_CAPACITY - 1)
        elif new_slot >= PLANET_CAPACITY:
            planet_num = int(planet_id.split("_")[1]) if "_" in planet_id else 0
            self._pointer = TapePosition(f"planet_{planet_num + 1}", 0)
        else:
            self._pointer = TapePosition(planet_id, new_slot)
        return self.pointer
