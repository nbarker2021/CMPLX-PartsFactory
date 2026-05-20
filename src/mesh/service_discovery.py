import os
import time
import logging
from typing import Any

logger = logging.getLogger("mesh.discovery")

PG_HOST = os.environ.get("PG_HOST", "host.docker.internal")
PG_USER = os.environ.get("PG_USER", "research")
PG_PASS = os.environ.get("PG_PASS", "research_hub_dev")


class ServiceDiscovery:
    def __init__(self):
        self._discovered: dict[str, dict[str, Any]] = {}
        self._last_scan = 0.0
        self._pg_conn = None

    def _connect_pg(self, db: str = "unification_hub"):
        try:
            import psycopg2
            self._pg_conn = psycopg2.connect(
                host=PG_HOST, port=5432, dbname=db,
                user=PG_USER, password=PG_PASS,
            )
            return True
        except Exception as e:
            logger.warning("PG discovery connect failed: %s", e)
            return False

    def scan(self) -> dict[str, dict[str, Any]]:
        self._discovered = {}
        self._scan_postgres_hub()
        self._scan_postgres_aggregator()
        self._last_scan = time.time()
        return dict(self._discovered)

    def _scan_postgres_hub(self):
        if not self._connect_pg("unification_hub"):
            return
        try:
            cursor = self._pg_conn.cursor()
            cursor.execute("""
                SELECT table_schema, table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name, ordinal_position
            """)
            schemas: dict[str, dict] = {}
            for schema, table, col, dtype in cursor.fetchall():
                key = f"{schema}.{table}"
                schemas.setdefault(key, {
                    "source": "unification_hub",
                    "schema": schema,
                    "table": table,
                    "columns": [],
                })["columns"].append({"name": col, "type": dtype})

            for key, info in schemas.items():
                sid = f"pg_hub_{key.replace('.', '_')}"
                self._discovered[sid] = {
                    "service_id": sid,
                    "source": "unification_hub",
                    "type": "postgres_table",
                    "schema": info["schema"],
                    "table": info["table"],
                    "columns": info["columns"],
                    "discovered_at": time.time(),
                }

            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")
            count = cursor.fetchone()[0]
            logger.info("PostgreSQL unification_hub: %d tables discovered", count)
        except Exception as e:
            logger.warning("Hub scan error: %s", e)
        finally:
            try:
                self._pg_conn.close()
            except Exception:
                pass

    def _scan_postgres_aggregator(self):
        if not self._connect_pg("unification_aggregator"):
            return
        try:
            cursor = self._pg_conn.cursor()
            cursor.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                AND table_type = 'BASE TABLE'
            """)
            for schema, table in cursor.fetchall():
                tid = f"pg_agg_{schema}_{table}"
                self._discovered[tid] = {
                    "service_id": tid,
                    "source": "unification_aggregator",
                    "type": "postgres_table",
                    "schema": schema,
                    "table": table,
                    "discovered_at": time.time(),
                }
            logger.info("PostgreSQL unification_aggregator: tables discovered")
        except Exception as e:
            logger.warning("Aggregator scan error: %s", e)
        finally:
            try:
                self._pg_conn.close()
            except Exception:
                pass

    def get_all(self) -> dict[str, dict[str, Any]]:
        if not self._discovered:
            self.scan()
        return dict(self._discovered)

    def find_by_schema(self, schema: str) -> list[dict[str, Any]]:
        return [v for v in self._discovered.values() if v.get("schema") == schema]

    def last_scan_age(self) -> float:
        return time.time() - self._last_scan if self._last_scan else -1
