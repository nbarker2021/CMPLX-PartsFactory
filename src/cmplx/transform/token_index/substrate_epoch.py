"""
Substrate epoch — SpeedLight whole-forward cache namespace segment.

Derived from ``token_bonds`` row count and max ``id`` so any ingest,
refine, or index upsert invalidates cached forwards without scanning rows.
"""
from __future__ import annotations

import hashlib
import sqlite3


def _epoch_from_conn(conn: sqlite3.Connection) -> str:
    cur = conn.execute(
        "SELECT COUNT(*), COALESCE(MAX(id), 0) FROM token_bonds"
    )
    count, max_id = cur.fetchone()
    payload = f"{int(count)}:{int(max_id)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def compute_substrate_epoch(db_or_conn: str | sqlite3.Connection) -> str:
    """Stable 16-char digest of substrate mutation generation."""
    if isinstance(db_or_conn, sqlite3.Connection):
        return _epoch_from_conn(db_or_conn)
    conn = sqlite3.connect(str(db_or_conn))
    try:
        return _epoch_from_conn(conn)
    finally:
        conn.close()


def notify_substrate_mutation(_conn: sqlite3.Connection) -> None:
    """Hook after substrate writes (epoch is derived on read)."""


__all__ = ["compute_substrate_epoch", "notify_substrate_mutation"]
