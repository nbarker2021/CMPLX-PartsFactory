"""MMDB PG Bridge — Polls PostgreSQL for new atoms, syncs to MMDB crystal store.

Port of TMN2 mmdb_pg_bridge. Operates as a bridge between PG atom tables
and the MMDB crystal storage service.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("services.mmdb_pg_bridge")

MORPHON_ID = os.getenv("WORK_MORPHON_ID", "mmdb-pg-bridge-001")
PG_URL = os.getenv("PG_URL", "postgresql://tmn2:tmn2_dev@host.docker.internal:5432/tmn2")
MMDB_URL = os.getenv("MMDB_URL", "http://host.docker.internal:8824")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
BLOCK = os.getenv("TMN2_BLOCK", "data")


class MMDBPGBridgeService:
    """MMDB to PostgreSQL bridge service.

    Polls PG atom tables and syncs new atoms to MMDB as crystals.
    Supports manual bridging, sync status tracking, and dedup by ID.
    """

    def __init__(self, mmdb_url: str = "", pg_url: str = "", governance=None):
        self.mmdb_url = (mmdb_url or MMDB_URL).rstrip("/")
        self.pg_url = pg_url or PG_URL
        self._governance = governance

        self._pending_atoms: list[dict] = []
        self._synced_ids: set[str] = set()
        self._sync_state: dict = {
            "last_sync": None,
            "items_synced": 0,
            "total_synced": 0,
            "errors": 0,
            "running": False,
            "last_error": None,
        }

    def _source_tag(self) -> dict:
        return {
            "morphon_id": MORPHON_ID,
            "snap_label": f"morphon.{MORPHON_ID}",
            "service": "mmdb_pg_bridge",
            "block": BLOCK,
        }

    def _poll_pg_atoms(self, batch_size: int) -> list[dict]:
        """Query PG atoms table for new entries not yet synced."""
        try:
            import psycopg2
            conn = psycopg2.connect(self.pg_url)
            cur = conn.cursor()
            cur.execute(
                "SELECT id, content, snap_labels, e8_coords, mdhg_address, domain, source_table "
                "FROM atoms WHERE id NOT IN (SELECT unnest(%s::text[])) ORDER BY created_at LIMIT %s",
                (list(self._synced_ids), batch_size),
            )
            cols = [d[0] for d in cur.description]
            atoms = [dict(zip(cols, row)) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return atoms
        except Exception:
            return []

    def _send_to_mmdb(self, atom: dict) -> bool:
        """Send atom to MMDB as crystal via HTTP."""
        import urllib.request
        import urllib.error

        payload = {
            "content": json.dumps(atom.get("content", atom)),
            "snap_labels": atom.get("snap_labels", []) + [f"morphon.{MORPHON_ID}"],
            "e8_coords": atom.get("e8_coords", [0.0] * 8),
            "mdhg_address": atom.get("mdhg_address", ""),
            "domain": atom.get("domain", "pg_bridge"),
            "metadata": {
                "bridged_at": datetime.now(timezone.utc).isoformat(),
                "source_table": atom.get("source_table", "atoms"),
                "source": self._source_tag(),
            },
        }
        try:
            req = urllib.request.Request(
                f"{self.mmdb_url}/store",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except (urllib.error.URLError, Exception):
            return False

    def sync(self, batch_size: Optional[int] = None, force: bool = False) -> dict:
        """Trigger a sync run: poll PG and bridge new atoms."""
        bs = batch_size or BATCH_SIZE
        atoms = self._poll_pg_atoms(bs)
        synced = 0
        errors = 0

        for atom in atoms:
            aid = atom.get("id", str(uuid.uuid4()))
            if aid in self._synced_ids and not force:
                continue
            ok = self._send_to_mmdb(atom)
            if ok:
                self._synced_ids.add(aid)
                synced += 1
            else:
                errors += 1

        self._sync_state["last_sync"] = datetime.now(timezone.utc).isoformat()
        self._sync_state["items_synced"] = synced
        self._sync_state["total_synced"] += synced
        self._sync_state["errors"] += errors

        if self._governance:
            from governance.engine import BoundaryEvent
            self._governance.record_boundary_event(BoundaryEvent(
                event_id=f"mmdb-sync-{int(time.time())}",
                timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"synced": synced, "errors": errors},
                boundary_type="mmdb_pg_sync",
            ))

        return {
            "synced": synced, "errors": errors, "batch_size": bs,
            "total_synced": self._sync_state["total_synced"],
            "source": self._source_tag(),
        }

    def bridge_atom(self, atom_id: str, content: str = "",
                    snap_labels: list[str] = None, e8_coords: list[float] = None,
                    mdhg_address: str = "", domain: str = "manual_bridge") -> dict:
        """Manually bridge a single atom to MMDB."""
        snap_labels = snap_labels or []
        e8_coords = e8_coords or [0.0] * 8

        atom = {
            "id": atom_id,
            "content": content,
            "snap_labels": snap_labels + [f"morphon.{MORPHON_ID}"],
            "e8_coords": e8_coords,
            "mdhg_address": mdhg_address,
            "domain": domain,
            "source_table": "manual",
        }

        if atom_id in self._synced_ids:
            return {"bridged": False, "reason": "already_synced",
                    "atom_id": atom_id, "source": self._source_tag()}

        ok = self._send_to_mmdb(atom)
        if ok:
            self._synced_ids.add(atom_id)
            self._sync_state["total_synced"] += 1
            return {"bridged": True, "atom_id": atom_id, "source": self._source_tag()}
        else:
            self._sync_state["errors"] += 1
            self._sync_state["last_error"] = f"Failed to bridge {atom_id}"
            return {"bridged": False, "reason": "mmdb_unreachable",
                    "atom_id": atom_id, "source": self._source_tag()}

    @property
    def status(self) -> dict:
        return {
            **self._sync_state,
            "pending": len(self._pending_atoms),
            "synced_ids_count": len(self._synced_ids),
            "poll_interval": POLL_INTERVAL,
            "source": self._source_tag(),
        }
