#!/usr/bin/env python3
"""
CMPLX-PartsFactory — Tool Discovery and Composition Harness

This module discovers, catalogs, and composes tools from the Manny Unification 2
ecosystem. It provides:
1. Discovery of code from Postgres/SQLite databases
2. Tool analysis and capability extraction
3. Composition API for wiring tools together
4. Catalog of tested combinations
5. Personal node companion that learns from usage

Usage:
    from src.discovery import PostgresDiscovery, SQLiteDiscovery
    discovery = PostgresDiscovery()
    tools = discovery.scan_unification_hub()
"""

import os
import sys
import json
import hashlib
import sqlite3
import psycopg2
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import importlib.util

# Database connection defaults
DEFAULT_POSTGRES = {
    "host": "localhost",
    "port": 5432,
    "user": "research",
    "password": os.environ.get("POSTGRES_PASSWORD", ""),
}

DEFAULT_SQLITE_PATHS = [
    "/mnt/d/Manny Unification 2/ai_memory/ai_memory/memory.db",
    # Field curator artifact index (optional — created on first run if absent)
    "/mnt/d/PartsFactory/CMPLX-PartsFactory/catalog/artifact_index.sqlite",
]


@dataclass
class DiscoveredTool:
    """A tool discovered from database or file system."""
    tool_id: str
    name: str
    source: str
    source_type: str  # postgres, sqlite, filesystem
    file_path: Optional[str] = None
    table_name: Optional[str] = None
    schema_name: Optional[str] = None
    code_content: Optional[str] = None
    description: Optional[str] = None
    families: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    e8_routing: Optional[Dict[str, Any]] = None
    input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    last_used: Optional[datetime] = None
    success_rate: float = 1.0
    compositions_tested: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "source": self.source,
            "source_type": self.source_type,
            "file_path": self.file_path,
            "table_name": self.table_name,
            "families": self.families,
            "capabilities": self.capabilities,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "compositions_tested": len(self.compositions_tested),
        }


class PostgresDiscovery:
    """Discover tools from PostgreSQL databases."""

    def __init__(self, host=None, port=None, user=None, password=None):
        self.host = host or DEFAULT_POSTGRES["host"]
        self.port = port or DEFAULT_POSTGRES["port"]
        self.user = user or DEFAULT_POSTGRES["user"]
        self.password = password or DEFAULT_POSTGRES["password"]
        self._conn = None
        self._tools: Dict[str, DiscoveredTool] = {}

    def connect(self, database="postgres") -> bool:
        """Connect to PostgreSQL database."""
        try:
            self._conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=database,
                user=self.user,
                password=self.password,
            )
            return True
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def list_databases(self) -> List[str]:
        """List all databases."""
        if not self._conn:
            return []
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT datname FROM pg_database
            WHERE datistemplate = false
            AND datname NOT IN ('postgres', 'template0', 'template1')
        """)
        return [row[0] for row in cursor.fetchall()]

    def list_schemas(self, database=None) -> List[str]:
        """List all schemas in database."""
        if not self._conn:
            return []
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """)
        return [row[0] for row in cursor.fetchall()]

    def list_tables(self, schema="public") -> List[str]:
        """List all tables in schema."""
        if not self._conn:
            return []
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (schema,))
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, table_name: str, schema="public") -> List[Dict[str, Any]]:
        """Get column schema for a table."""
        if not self._conn:
            return []
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table_name))
        return [
            {"name": row[0], "type": row[1], "nullable": row[2], "default": row[3]}
            for row in cursor.fetchall()
        ]

    def get_table_rows(self, table_name: str, schema="public", limit=100) -> List[Dict[str, Any]]:
        """Get sample rows from table."""
        if not self._conn:
            return []
        cursor = self._conn.cursor()
        cursor.execute(f'SELECT * FROM "{schema}".{table_name} LIMIT %s', (limit,))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_experts(self) -> List[DiscoveredTool]:
        """Get experts from unification_hub.manny_experts.expert."""
        if not self._connect_if_needed("unification_hub"):
            return []

        tools = []
        cursor = self._conn.cursor()
        cursor.execute("SELECT expert_id, domain, e8_position, snap_labels FROM manny_experts.expert LIMIT 500")
        for row in cursor.fetchall():
            expert_id, domain, e8_pos, snap_labels = row
            tool = DiscoveredTool(
                tool_id=f"expert_{expert_id}",
                name=domain or "unknown",
                source="unification_hub.manny_experts",
                source_type="postgres",
                table_name="expert",
                schema_name="manny_experts",
                families=[domain.split(".")[0] if domain else "unknown"],
                capabilities=snap_labels.split(",") if snap_labels else [],
            )
            tools.append(tool)
        return tools

    def _connect_if_needed(self, database) -> bool:
        """Connect to database if not already connected."""
        if self._conn is None:
            return self.connect(database)
        return True

    def scan_unification_hub(self) -> Dict[str, DiscoveredTool]:
        """Scan unification_hub for all expert tools."""
        if not self._connect_if_needed("unification_hub"):
            return {}

        tools = {}
        for expert in self.get_experts():
            tools[expert.tool_id] = expert

        self._tools.update(tools)
        return tools

    def scan_unification_aggregator(self) -> Dict[str, DiscoveredTool]:
        """Scan unification_aggregator schemas for artifacts."""
        if not self._connect_if_needed("unification_aggregator"):
            return {}

        tools = {}
        schemas = self.list_schemas()

        for schema in schemas:
            tables = self.list_tables(schema)
            for table in tables:
                if table in ("source", "artifact", "queue", "receipt"):
                    rows = self.get_table_rows(table, schema, limit=10)
                    for row in rows:
                        tool_id = f"{schema}.{table}.{row.get('id', 'unknown')}"
                        tool = DiscoveredTool(
                            tool_id=tool_id,
                            name=row.get("source_uri", table),
                            source=f"unification_aggregator.{schema}",
                            source_type="postgres",
                            table_name=table,
                            schema_name=schema,
                            description=row.get("artifact_kind", ""),
                        )
                        tools[tool_id] = tool

        self._tools.update(tools)
        return tools

    def get_all_tools(self) -> Dict[str, DiscoveredTool]:
        """Get all discovered tools."""
        return self._tools


class SQLiteDiscovery:
    """Discover tools from SQLite databases."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self._conn = None
        self._tools: Dict[str, DiscoveredTool] = {}

    def connect(self, db_path: str = None) -> bool:
        """Connect to SQLite database."""
        path = db_path or self.db_path
        if not path:
            return False
        try:
            self._conn = sqlite3.connect(path)
            return True
        except Exception as e:
            print(f"SQLite connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def list_tables(self) -> List[str]:
        """List all tables in database."""
        if not self._conn:
            return []
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column schema for a table."""
        if not self._conn:
            return []
        cursor = self._conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        return [
            {"name": row[1], "type": row[2], "nullable": not row[3], "default": row[4]}
            for row in cursor.fetchall()
        ]

    def get_table_rows(self, table_name: str, limit=100) -> List[Dict[str, Any]]:
        """Get sample rows from table."""
        if not self._conn:
            return []
        cursor = self._conn.cursor()
        cursor.execute(f'SELECT * FROM "{table_name}" LIMIT ?', (limit,))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def scan_memory_db(self) -> Dict[str, DiscoveredTool]:
        """Scan memory.db for abilities and capabilities."""
        if not self.connect():
            return {}

        tools = {}
        tables = ["ability_map", "capabilities"]

        for table in tables:
            if table not in self.list_tables():
                continue

            rows = self.get_table_rows(table)
            for row in rows:
                if table == "ability_map":
                    tool = DiscoveredTool(
                        tool_id=f"ability_{row.get('id')}",
                        name=row.get("capability_name", ""),
                        source=row.get("source_name", ""),
                        source_type="sqlite",
                        table_name=table,
                        capabilities=[row.get("implementation", "")],
                        families=[row.get("source_name", "").split()[0] if row.get("source_name") else "unknown"],
                    )
                elif table == "capabilities":
                    tool = DiscoveredTool(
                        tool_id=f"cap_{row.get('id')}",
                        name=row.get("ability", ""),
                        source=row.get("family", ""),
                        source_type="sqlite",
                        table_name=table,
                        description=row.get("description", "")[:200],
                        families=[row.get("family", "")],
                    )
                tools[tool.tool_id] = tool

        self._tools.update(tools)
        return tools

    def scan_all(self, db_paths: List[str] = None) -> Dict[str, DiscoveredTool]:
        """Scan multiple SQLite databases."""
        paths = db_paths or [self.db_path]
        all_tools = {}

        for path in paths:
            if path and os.path.exists(path):
                self.db_path = path
                tools = self.scan_memory_db()
                all_tools.update(tools)

        return all_tools

    def get_all_tools(self) -> Dict[str, DiscoveredTool]:
        """Get all discovered tools."""
        return self._tools


class FileSystemDiscovery:
    """Discover tools from file system."""

    def __init__(self, root_path: str = None):
        self.root_path = root_path or "/mnt/d/Manny Unification 2"
        self._tools: Dict[str, DiscoveredTool] = {}

    def scan_brain_files(self) -> Dict[str, DiscoveredTool]:
        """Scan for brain/personal_node implementations."""
        tools = {}

        # Key files identified by agents
        brain_files = [
            ("/mnt/d/Manny Unification 2/proposals/manny-unified-build-2026-05-09/manny_runtime/brain.py", "unified_brain", "Manny Unified Brain"),
            ("/mnt/d/Manny Unification 2/Working Prototyping/services/brain-unified/brain.py", "brain_service", "OpenCMPLX Brain Service"),
            ("/mnt/d/Manny Unification 2/historical builds/mannyunification_staging/systems/TMN4/prototypes/tmn4_unified_brain_frame_2026_04_21/src/tmn4_unified_frame/personal_node.py", "tmn4_personal_node", "TMN4 Personal Node"),
            ("/mnt/d/Manny Unification 2/output/archive-staging/6833b24d-9ff1-447e-b87c-9e3ba44cb290/cqe_clean/applications/cqe_personal_node.py", "cqe_personal_node", "CQE Personal Node"),
            ("/mnt/d/Manny Unification 2/historical builds/MannyAI/brain/brain.py", "mannyai_brain", "MannyAI Production Brain"),
            ("/mnt/d/Manny Unification 2/historical builds/CMPLX-TMN3/src/claude_brain_hub.py", "tmn3_brain_hub", "TMN3 Claude Brain Hub"),
        ]

        for path, tool_id, name in brain_files:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    content = f.read()
                tool = DiscoveredTool(
                    tool_id=tool_id,
                    name=name,
                    source="filesystem",
                    source_type="filesystem",
                    file_path=path,
                    code_content=content[:1000],  # First 1000 chars
                    families=["brain", "personal_node"],
                    capabilities=["e8_expert", "hebbian_learning", "triad_system"] if "brain" in tool_id else ["evaluation", "label_signature"],
                )
                tools[tool_id] = tool

        self._tools.update(tools)
        return tools

    def scan_key_systems(self) -> Dict[str, DiscoveredTool]:
        """Scan for key system implementations."""
        tools = {}

        # Key system files
        system_files = [
            ("/mnt/d/Manny Unification 2/historical builds/MannyAI/tools/full_tarpit_tokens.py", "mannyai_tarpit", "MannyAI TarPit"),
            ("/mnt/d/Manny Unification 2/historical builds/MannyAI/data/speedlight.py", "mannyai_speedlight", "MannyAI SpeedLight"),
            ("/mnt/d/Manny Unification 2/historical builds/CMPLX-TMN2/src/tarpit/tarpit.py", "cmplx_tarpit", "CMPLX-TMN2 TarPit"),
            ("/mnt/d/Manny Unification 2/historical builds/CMPLX-TMN2/src/token_ir/token_ir.py", "cmplx_token_ir", "CMPLX-TMN2 Token IR"),
            ("/mnt/d/Manny Unification 2/historical builds/CMPLX-TMN3/morphos/core/brain/brain.py", "morphos_brain", "MorphOS Brain"),
        ]

        for path, tool_id, name in system_files:
            if os.path.exists(path):
                size = os.path.getsize(path)
                tool = DiscoveredTool(
                    tool_id=tool_id,
                    name=name,
                    source="filesystem",
                    source_type="filesystem",
                    file_path=path,
                    description=f"{size} bytes",
                    capabilities=[path.split("/")[-2]],
                )
                tools[tool_id] = tool

        self._tools.update(tools)
        return tools

    def scan_all(self) -> Dict[str, DiscoveredTool]:
        """Scan all file system sources."""
        tools = {}
        tools.update(self.scan_brain_files())
        tools.update(self.scan_key_systems())
        return tools

    def get_all_tools(self) -> Dict[str, DiscoveredTool]:
        """Get all discovered tools."""
        return self._tools


def create_discovery_harness() -> Dict[str, Any]:
    """Create complete discovery harness with all sources."""
    harness = {
        "postgres": PostgresDiscovery(),
        "sqlite": SQLiteDiscovery(),
        "filesystem": FileSystemDiscovery(),
        "tools": {},
    }

    # Scan all sources
    print("Scanning PostgreSQL databases...")
    try:
        harness["postgres"].scan_unification_hub()
        harness["postgres"].scan_unification_aggregator()
    except Exception as e:
        print(f"PostgreSQL scan failed: {e}")

    print("Scanning SQLite databases...")
    harness["sqlite"].scan_all(DEFAULT_SQLITE_PATHS)

    print("Scanning file system...")
    harness["filesystem"].scan_all()

    # Merge all tools
    all_tools = {}
    all_tools.update(harness["postgres"].get_all_tools())
    all_tools.update(harness["sqlite"].get_all_tools())
    all_tools.update(harness["filesystem"].get_all_tools())
    harness["tools"] = all_tools

    print(f"Total tools discovered: {len(all_tools)}")
    return harness


if __name__ == "__main__":
    print("=== CMPLX PartsFactory Discovery Harness ===\n")
    harness = create_discovery_harness()

    print(f"\nTools by source:")
    by_source = {}
    for tool in harness["tools"].values():
        by_source.setdefault(tool.source_type, []).append(tool.name)

    for source, names in by_source.items():
        print(f"  {source}: {len(names)} tools")

    print(f"\nTool IDs:")
    for tool_id in list(harness["tools"].keys())[:20]:
        print(f"  - {tool_id}")