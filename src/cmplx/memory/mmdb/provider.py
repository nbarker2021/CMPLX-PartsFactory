"""
MMDBMemoryProvider — the `memory` port provider.

Wraps the SQLite-backed ``MMDB`` store and adds the extended-Protocol
methods: edge traversal, E8-coordinate query, and ETP encode/decode.

Sub-frame slot F-3. See docs/sub_frames/port_provider_facades.md.

The base MMDB stores morphons in a `morphons` table. This provider adds:
  - A `morphon_edges` table for typed weighted edges (relation, weight).
  - In-memory E8 index for `by_e8_coordinates(coords, radius)`.
  - ETP delegation through the `symbolic` port when registered.

The schema is added lazily on first edge or e8-query call so existing MMDB
consumers and tests are unaffected unless they use the extensions.
"""
from __future__ import annotations

import json
import math
from typing import Any, Iterator, Optional

from cmplx.morphon import Morphon

from .store import MMDB


# Extension schema — applied lazily by _ensure_extensions().
_EXT_SCHEMA = """
CREATE TABLE IF NOT EXISTS morphon_edges (
    from_id   TEXT NOT NULL,
    to_id     TEXT NOT NULL,
    relation  TEXT NOT NULL,
    weight    REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (from_id, to_id, relation)
);
CREATE INDEX IF NOT EXISTS idx_edges_from ON morphon_edges(from_id, relation);
CREATE INDEX IF NOT EXISTS idx_edges_to   ON morphon_edges(to_id, relation);
"""


class MMDBMemoryProvider:
    """The `memory` port — SQLite-backed morphon persistence with edges + E8 query.

    Conforms to ``cmplx.morphon.MemoryProvider`` Protocol. Registration:

        MorphonController.get().register("memory", MMDBMemoryProvider(":memory:"))

    or with a file path:

        MorphonController.get().register("memory", MMDBMemoryProvider("data.db"))
    """

    name: str = "mmdb_memory_provider"

    def __init__(self, path: str = ":memory:") -> None:
        self._db = MMDB(path)
        self._extensions_initialized = False

    # ── Core MemoryProvider methods ─────────────────────────────────

    def store(self, morphon: Morphon) -> None:
        """Persist the morphon."""
        self._db.store(morphon)

    def fetch(self, morphon_id: str) -> Optional[Morphon]:
        """Retrieve a morphon by ID, or None if not present."""
        return self._db.fetch(morphon_id)

    # ── Edge traversal extensions ───────────────────────────────────

    def store_edge(
        self,
        from_id: str,
        to_id: str,
        relation: str,
        weight: float = 1.0,
    ) -> None:
        """Record a typed weighted edge between two stored morphons.

        Edges are stored independently of the morphons themselves — calling
        store_edge on IDs whose morphons aren't yet stored is permitted
        (the edge will resolve when the morphons are later stored).
        """
        self._ensure_extensions()
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        with self._db._lock:
            self._db._conn.execute(
                "INSERT OR REPLACE INTO morphon_edges "
                "(from_id, to_id, relation, weight, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (from_id, to_id, relation, weight, now),
            )

    def neighbors(
        self,
        morphon_id: str,
        relation: str | None = None,
    ) -> list[str]:
        """Return morphon IDs reachable from morphon_id via outgoing edges.

        If relation is None, return neighbors across all relation types.
        """
        self._ensure_extensions()
        with self._db._lock:
            if relation is None:
                rows = self._db._conn.execute(
                    "SELECT to_id FROM morphon_edges WHERE from_id = ? "
                    "ORDER BY weight DESC, to_id ASC",
                    (morphon_id,),
                ).fetchall()
            else:
                rows = self._db._conn.execute(
                    "SELECT to_id FROM morphon_edges WHERE from_id = ? AND relation = ? "
                    "ORDER BY weight DESC, to_id ASC",
                    (morphon_id, relation),
                ).fetchall()
        return [r[0] for r in rows]

    # ── E8-coordinate query ───────────────────────────────────────

    def by_e8_coordinates(
        self,
        coords: tuple[float, ...],
        radius: float = 0.0,
    ) -> list[Morphon]:
        """Return stored morphons whose E8 coordinates fall within radius of coords.

        Radius is Euclidean distance in 8D. radius=0 means exact match.
        Morphons whose ``e8_coordinates`` field is None are skipped.

        This scans the full table. For large stores, an index over E8
        coordinates is a Wave-1 follow-up — the cmplx tree's MMDB doesn't
        yet have one, and adding it requires deciding on a multidim
        index strategy.
        """
        self._ensure_extensions()
        with self._db._lock:
            rows = self._db._conn.execute(
                "SELECT serialized_json FROM morphons WHERE serialized_json LIKE ?",
                ('%"e8_coordinates"%',),
            ).fetchall()

        results = []
        for (sj,) in rows:
            data = json.loads(sj)
            e8 = data.get("e8_coordinates")
            if e8 is None:
                continue
            if not isinstance(e8, (list, tuple)) or len(e8) != len(coords):
                continue
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(e8, coords)))
            if dist <= radius + 1e-12:
                results.append(Morphon.deserialize(data))
        return results

    # ── ETP integration ─────────────────────────────────────────────

    def encode_to_etp(self, morphon: Morphon) -> str:
        """Encode the morphon as an ETP program.

        Delegates to the registered ``symbolic`` provider when present.
        Falls back to a local SHA256 → loopless-alphabet encoding when
        symbolic is not registered.
        """
        symbolic = self._maybe_get_symbolic()
        if symbolic is not None:
            return symbolic.encode_to_etp(morphon)
        return self._fallback_encode_to_etp(morphon)

    def decode_from_etp(self, ledger: list[dict]) -> Morphon:
        """Reconstruct a morphon from an ETP ledger.

        Delegates to the registered ``symbolic`` provider when present.
        Falls back to materializing the ledger's final row as a morphon
        payload.
        """
        symbolic = self._maybe_get_symbolic()
        if symbolic is not None:
            return symbolic.decode_from_etp(ledger)
        return self._fallback_decode_from_etp(ledger)

    # ── Convenience surface ────────────────────────────────────────

    def count(self) -> int:
        """Return the number of morphons in the store."""
        return self._db.count()

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": self.name,
            "path": self._db.path,
            "morphon_count": self._db.count(),
            "extensions_initialized": self._extensions_initialized,
        }

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "MMDBMemoryProvider":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"<MMDBMemoryProvider path={self._db.path!r}>"

    # ── Internals ──────────────────────────────────────────────────

    def _ensure_extensions(self) -> None:
        """Apply the extension schema (edges table) lazily on first use."""
        if self._extensions_initialized:
            return
        with self._db._lock:
            self._db._conn.executescript(_EXT_SCHEMA)
        self._extensions_initialized = True

    def _maybe_get_symbolic(self) -> Any:
        try:
            from cmplx.morphon import MorphonController
            return MorphonController.get().get_provider("symbolic")
        except (LookupError, ImportError):
            return None

    def _fallback_encode_to_etp(self, morphon: Morphon) -> str:
        """Local encoding used when no symbolic provider is registered.

        Matches TarPitSymbolicProvider's encoding scheme byte-for-byte.
        """
        import hashlib
        alphabet = "}<>+01"
        serialized = json.dumps(
            {
                "id": morphon.id,
                "payload": morphon.payload,
                "parent": morphon.parent,
            },
            sort_keys=True,
            default=str,
        ).encode("utf-8")
        digest = hashlib.sha256(serialized).digest()
        return "".join(alphabet[b % len(alphabet)] for b in digest)

    def _fallback_decode_from_etp(self, ledger: list[dict]) -> Morphon:
        if not ledger:
            return Morphon.forge(payload={"etp_decode": "empty_ledger"})
        final = ledger[-1]
        return Morphon.forge(payload={
            "etp_decode": True,
            "torus8": list(final.get("torus8", [])),
            "torus8_mirror": list(final.get("torus8_mirror", [])),
            "wall10": final.get("wall10", "0.000"),
            "digital_root": final.get("digital_root", 0),
            "halted": final.get("halted_now", False),
            "n_grains": final.get("n_grains", 0),
            "dusts": final.get("dusts", 0),
            "triads": final.get("triads", 0),
            "steps": final.get("step", 0),
        })
