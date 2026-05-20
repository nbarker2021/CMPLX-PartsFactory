"""Global Aggregation Daemon — aggregates all agent data to PostgreSQL using LocalCRT."""
from __future__ import annotations
import json
import os
import time
import logging
from typing import Any, Optional
from dataclasses import dataclass

from daemon.local_crt import LocalCRT

logger = logging.getLogger("global-crt")

PG_HOST = os.environ.get("POSTGRES_HOST", "host.docker.internal")
PG_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
PG_USER = os.environ.get("POSTGRES_USER", "research")
PG_PASS = os.environ["POSTGRES_PASSWORD"]
PG_DB = os.environ.get("POSTGRES_DB", "unification_hub")
CACHE_HOST = os.environ.get("CACHE_PG_HOST", "host.docker.internal")
CACHE_PORT = int(os.environ.get("CACHE_PG_PORT", "55432"))
CACHE_DB = os.environ.get("CACHE_PG_DB", "unification_aggregator")


class PgConnector:
    """Manages two PostgreSQL connections for primary and cache databases."""

    def __init__(self):
        self._primary: Any = None
        self._cache: Any = None
        self._init_tables()

    def _connect(self, host, port, db):
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=host, port=port, user=PG_USER, password=PG_PASS, dbname=db,
                connect_timeout=5,
            )
            conn.autocommit = True
            return conn
        except Exception as e:
            logger.warning("PG connection failed (%s:%s/%s): %s", host, port, db, e)
            return None

    @property
    def primary(self):
        if self._primary is None:
            self._primary = self._connect(PG_HOST, PG_PORT, PG_DB)
        return self._primary

    @property
    def cache(self):
        if self._cache is None:
            self._cache = self._connect(CACHE_HOST, CACHE_PORT, CACHE_DB)
        return self._cache

    def _init_tables(self):
        for conn, name in [(self.primary, "primary"), (self.cache, "cache")]:
            if conn is None:
                continue
            try:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS agent_registry (
                        agent_id TEXT PRIMARY KEY,
                        identity_tag TEXT,
                        archetype TEXT,
                        domain TEXT,
                        capabilities TEXT,
                        status TEXT DEFAULT 'initialized',
                        last_seen REAL,
                        wallet_balance REAL DEFAULT 0.0,
                        created_at REAL DEFAULT EXTRACT(EPOCH FROM NOW())
                    );
                    CREATE TABLE IF NOT EXISTS agent_experiences (
                        id BIGSERIAL PRIMARY KEY,
                        agent_id TEXT REFERENCES agent_registry(agent_id),
                        entry_type TEXT,
                        content TEXT,
                        embedding TEXT,
                        created_at REAL
                    );
                    CREATE TABLE IF NOT EXISTS domain_reports (
                        id BIGSERIAL PRIMARY KEY,
                        domain TEXT NOT NULL,
                        report_data TEXT,
                        expert_count INTEGER DEFAULT 0,
                        generated_at REAL
                    );
                    CREATE TABLE IF NOT EXISTS expert_derivations (
                        id BIGSERIAL PRIMARY KEY,
                        expert_id TEXT,
                        parent_ids TEXT,
                        composition_rounds INTEGER,
                        convergence_score REAL,
                        created_at REAL
                    );
                """)
                if name == "cache":
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS system_ticks (
                            id BIGSERIAL PRIMARY KEY,
                            tick_id INTEGER,
                            channel_firings TEXT,
                            buffer_flushes TEXT,
                            recorded_at REAL
                        );
                    """)
                conn.commit()
                logger.info("PG tables initialized on %s", name)
            except Exception as e:
                logger.warning("PG init on %s: %s", name, e)


class GlobalAggregationDaemon:
    """Global CRT daemon that aggregates agent data to PostgreSQL."""

    def __init__(self, tick_interval: float = 15.0):
        self.pg = PgConnector()
        self.crt = LocalCRT(service_name="global-crt", tick_interval=tick_interval)
        self._register_channels()
        self._ingest_buffer: list[dict] = []

    def _register_channels(self):
        self.crt.register("agent_sweep", 2, self._sweep_agents, "Discover active agents")
        self.crt.register("experience_aggregate", 3, self._aggregate_experiences, "Batch experiences")
        self.crt.register("domain_report", 7, self._generate_reports, "Generate domain reports")
        self.crt.register("cache_maintenance", 13, self._maintain_cache, "Cache maintenance")
        self.crt.register_buffer("ingest_buffer", self._flush_ingest, flush_period=2)

    def ingest_agent_data(self, payload: dict):
        """HTTP endpoint: accept identity, wallet, experience payloads from sidecars."""
        self._ingest_buffer.append(payload)

    def _flush_ingest(self, items: list[dict]):
        conn = self.pg.primary
        if conn is None:
            return
        cur = conn.cursor()
        for item in items:
            agent_id = item.get("agent_id", "unknown")
            identity = item.get("identity")
            if identity:
                cur.execute("""
                    INSERT INTO agent_registry (agent_id, identity_tag, archetype, domain, capabilities, last_seen)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (agent_id) DO UPDATE SET
                        last_seen = EXCLUDED.last_seen,
                        status = 'active'
                """, (agent_id, identity.get("identity_tag"), identity.get("archetype"),
                      identity.get("domain"), identity.get("capabilities"), time.time()))

    def _sweep_agents(self):
        logger.info("Agent sweep complete")

    def _aggregate_experiences(self):
        logger.info("Experience aggregation cycle")

    def _generate_reports(self):
        conn = self.pg.primary
        if conn is None:
            return
        cur = conn.cursor()
        cur.execute("""
            SELECT domain, COUNT(*) as cnt FROM agent_registry
            WHERE status = 'active' GROUP BY domain
        """)
        for row in cur.fetchall():
            cur.execute("""
                INSERT INTO domain_reports (domain, report_data, expert_count, generated_at)
                VALUES (%s, %s, %s, %s)
            """, (row[0], json.dumps({"status": "ok"}), row[1], time.time()))
        conn.commit()

    def _maintain_cache(self):
        conn = self.pg.cache
        if conn is None:
            return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM system_ticks WHERE recorded_at < %s", (time.time() - 86400,))
            conn.commit()
        except Exception:
            pass

    def start(self):
        self.crt.start_background()

    def stop(self):
        self.crt.stop()
