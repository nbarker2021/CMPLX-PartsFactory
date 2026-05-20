from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("services.pg")

PG_URL = os.environ.get(
    "PG_URL",
    "postgresql://...:@host.docker.internal:5432/unification_hub"  # configure via PG_URL env var,
)

_pg_conn = None


def get_pg():
    global _pg_conn
    if not PG_URL:
        return None
    try:
        import psycopg2
        if _pg_conn is None or _pg_conn.closed:
            _pg_conn = psycopg2.connect(PG_URL)
            _pg_conn.autocommit = True
        return _pg_conn
    except Exception:
        return None


def ensure_table(conn, name: str, schema: str) -> None:
    try:
        cur = conn.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS {name} ({schema})")
    except Exception as e:
        logger.warning("ensure_table(%s): %s", name, e)


def upsert(conn, table: str, data: dict, pk: str = "id") -> None:
    try:
        cur = conn.cursor()
        columns = list(data.keys())
        values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in data.values()]
        placeholders = ", ".join(["%s"] * len(columns))
        cols = ", ".join(columns)
        updates = ", ".join(f"{c}=EXCLUDED.{c}" for c in columns if c != pk)
        sql = (
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) "
            f"ON CONFLICT ({pk}) DO UPDATE SET {updates}"
        )
        cur.execute(sql, values)
    except Exception as e:
        logger.warning("upsert(%s): %s", table, e)
