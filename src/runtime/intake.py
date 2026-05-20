"""PartsFactoryIntake — File discovery + classification + atom creation pipeline.

Port of CMPLX-1T intake.py into CMPLX-PartsFactory runtime. Searches three-space
directories, classifies content types, extracts topics/entities, creates atoms
with provenance, and stores via MMDB + AgentMemory.

Integrations:
  - AgentMemory for atom persistence and task tracking
  - MMDB (service registry) for crystal storage
  - Manny for content classification
  - GeometricGovernance for boundary event provenance
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from governance.engine import GeometricGovernance, BoundaryEvent

from .memory import AgentMemory

logger = logging.getLogger("runtime.intake")


@dataclass
class IntakeConfig:
    search_locations: List[str] = field(default_factory=lambda: [
        "/mnt/d/PartsFactory",
        "/mnt/d/Manny Unification 2",
        "/mnt/d/OC build",
        "/mnt/d/Work Files",
    ])
    search_patterns: List[str] = field(default_factory=lambda: [
        "*session*", "*conversation*", "*chat*",
        "*transcript*", "*dialog*", "*output*",
        "*generated*", "*.log", "*report*.md",
        "*summary*.md", "*.txt", "*.json",
    ])
    skip_dirs: List[str] = field(default_factory=lambda: [
        ".git", "node_modules", ".cache", ".vscode",
        ".cursor", "__pycache__", "venv", ".venv",
        "*.corpus.zip",
    ])
    keywords: List[str] = field(default_factory=lambda: [
        "CMPLX", "E8", "Leech", "Morphon", "MDHG",
        "Docker", "Compose", "MCP", "Agent", "Physics",
        "Database", "PostgreSQL", "Vector", "Embedding",
        "SNAP", "MMDB", "Manny", "ThinkTank", "Governance",
        "Receipt", "Atom", "Crystal", "Pipeline", "Daemon",
    ])
    max_file_size: int = 100_000
    batch_limit: int = 100
    min_file_bytes: int = 100


@dataclass
class IntakeStats:
    files_scanned: int = 0
    files_parsed: int = 0
    atoms_created: int = 0
    embeddings_created: int = 0
    errors: int = 0


@dataclass
class ParsedFile:
    file_path: str
    file_size: int
    file_type: str
    content_hash: str
    content: str
    topics: List[str]
    entities: List[str]
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class IntakeAtom:
    atom_id: str
    receipt_id: str
    code_path: str
    content: str
    file_type: str
    topics: List[str]
    entities: List[str]
    file_hash: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    family: str = "intake"


class PartsFactoryIntake:
    """Port of CMPLX-1T Intake Engine into PartsFactory runtime.

    Discovers files across three-space directories, classifies content,
    extracts topics/entities, creates atoms with provenance tracking,
    stores via MMDB crystals and AgentMemory knowledge docs.
    """

    def __init__(
        self,
        memory: AgentMemory | None = None,
        governance: GeometricGovernance | None = None,
        services: Any = None,
        config: IntakeConfig | None = None,
    ):
        self.memory = memory
        self.governance = governance or GeometricGovernance()
        self.services = services
        self.config = config or IntakeConfig()
        self.stats = IntakeStats()
        self._intake_id = uuid4().hex[:12]

        logger.info(
            "PartsFactoryIntake initialized [%s] — %d locations, %d patterns",
            self._intake_id,
            len(self.config.search_locations),
            len(self.config.search_patterns),
        )

    # ── Discovery ──────────────────────────────────────────────

    async def discover_files(self) -> List[Path]:
        """Discover candidate files across all search locations."""
        logger.info("Starting file discovery across %d locations", len(self.config.search_locations))
        discovered: List[Path] = []

        for loc_str in self.config.search_locations:
            loc = Path(loc_str)
            if not loc.exists():
                logger.debug("Location not found: %s", loc)
                continue
            logger.info("Scanning: %s", loc)
            for pattern in self.config.search_patterns:
                try:
                    for f in loc.rglob(pattern):
                        if f.is_file() and self._should_process(f):
                            discovered.append(f)
                            self.stats.files_scanned += 1
                except Exception as e:
                    logger.warning("Error scanning %s in %s: %s", pattern, loc, e)

        logger.info("Discovered %d files for intake", len(discovered))
        return discovered

    def _should_process(self, file: Path) -> bool:
        for skip in self.config.skip_dirs:
            if skip in str(file):
                return False
        try:
            if file.stat().st_size < self.config.min_file_bytes:
                return False
        except Exception:
            return False
        return True

    # ── Classification ─────────────────────────────────────────

    async def classify_file(self, file: Path, content: str) -> str:
        """Classify file type by name and content. Uses Manny if available."""
        name = file.name.lower()

        if "session" in name or "conversation" in name or "chat" in name:
            return "conversation"
        elif "log" in name:
            return "log"
        elif "report" in name:
            return "report"
        elif "guide" in name or "readme" in name:
            return "guide"
        elif "transcript" in name or "dialog" in name:
            return "transcript"
        elif "Generated by" in content or "AI output" in content:
            return "ai_generated"

        if self.services and self.services.manny:
            try:
                result = self.services.manny.probe(
                    f"classify this content type: {content[:500]}",
                    domain="classification",
                )
                if isinstance(result, dict) and result.get("classification"):
                    return result["classification"]
            except Exception:
                pass

        return "unknown"

    # ── Parsing ────────────────────────────────────────────────

    async def parse_file(self, file: Path) -> Optional[ParsedFile]:
        """Parse a single file into structured data."""
        try:
            content = file.read_text(errors="ignore")
            content = content[:self.config.max_file_size]

            file_type = await self.classify_file(file, content)
            topics = self._extract_topics(content)
            entities = self._extract_entities(content)
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            self.stats.files_parsed += 1
            return ParsedFile(
                file_path=str(file),
                file_size=file.stat().st_size,
                file_type=file_type,
                content_hash=content_hash,
                content=content,
                topics=topics,
                entities=entities,
            )
        except Exception as e:
            logger.warning("Error parsing %s: %s", file, e)
            self.stats.errors += 1
            return None

    def _extract_topics(self, content: str) -> List[str]:
        topics = []
        for kw in self.config.keywords:
            if kw.lower() in content.lower():
                topics.append(kw)
        return topics[:10]

    def _extract_entities(self, content: str) -> List[str]:
        entities: List[str] = []
        paths = re.findall(r"/[\w/.-]+", content)
        entities.extend(p[:80] for p in paths[:20])
        urls = re.findall(r"https?://[\w/.-]+", content)
        entities.extend(urls[:20])
        hashes = re.findall(r"[a-f0-9]{40}", content)
        entities.extend(hashes[:10])
        return list(set(entities))[:50]

    # ── Atom Creation ──────────────────────────────────────────

    async def create_atom(self, parsed: ParsedFile) -> IntakeAtom:
        """Create an intake atom from parsed content."""
        atom_id = f"intake_{parsed.content_hash[:16]}"
        receipt_id = f"receipt_{uuid4().hex[:12]}_{int(time.time())}"

        atom = IntakeAtom(
            atom_id=atom_id,
            receipt_id=receipt_id,
            code_path=parsed.file_path,
            content=parsed.content,
            file_type=parsed.file_type,
            topics=parsed.topics,
            entities=parsed.entities,
            file_hash=parsed.content_hash,
        )

        self.stats.atoms_created += 1
        logger.debug("Created atom: %s [%s]", atom_id, parsed.file_type)
        return atom

    # ── Embedding Generation ───────────────────────────────────

    def _generate_embedding(self, text: str) -> Dict[str, Any]:
        import numpy as np
        words = text.lower().split()
        vec = np.zeros(64, dtype=np.float64)
        for i, word in enumerate(words[:512]):
            vec[i % 64] += hash(word) % 1000 / 1000.0
        norm = np.linalg.norm(vec)
        if norm > 1e-10:
            vec /= norm
        return {
            "vector": vec.tolist(),
            "dim": 64,
            "method": "intake_hash",
        }

    # ── Storage ────────────────────────────────────────────────

    async def store_atom(
        self, atom: IntakeAtom, embedding: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Store atom via AgentMemory and MMDB. Records provenance via governance."""
        result: Dict[str, Any] = {"atom_id": atom.atom_id}

        mem = self.memory
        if mem is not None:
            metadata = {
                "atom_id": atom.atom_id,
                "receipt_id": atom.receipt_id,
                "file_type": atom.file_type,
                "topics": atom.topics,
                "entities": atom.entities,
                "file_hash": atom.file_hash,
                "family": "intake",
                "source": atom.code_path,
            }
            doc_id = mem.add_document(atom.content[:5000], metadata=metadata)
            result["memory_doc_id"] = doc_id

            task_id = mem.store_task(
                task_type="intake_atom",
                input_data={"atom_id": atom.atom_id, "source": atom.code_path},
                output_data=metadata,
                status="done",
            )
            result["task_id"] = task_id

        svc = self.services
        if svc is not None and svc.mmdb is not None:
            try:
                crystal = svc.mmdb.store(
                    content=atom.content[:5000],
                    snap_labels=[
                        f"SNAPintake_{atom.file_type}",
                        *[f"SNAPintake_topic_{t}" for t in atom.topics[:3]],
                    ],
                    domain=f"intake.{atom.file_type}",
                    metadata={
                        "atom_id": atom.atom_id,
                        "receipt_id": atom.receipt_id,
                        "source": atom.code_path,
                        "entities": atom.entities[:10],
                    },
                )
                result["crystal_id"] = crystal.get("crystal_id", crystal.get("id"))
            except Exception as e:
                logger.warning("MMDB store failed: %s", e)
                result["crystal_error"] = str(e)[:120]

        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"intake_store_{atom.atom_id}",
            timestamp=time.time(),
            entropy_delta=0.0,
            receipt_data={
                "atom_id": atom.atom_id,
                "file_type": atom.file_type,
                "topics": atom.topics,
                "source": atom.code_path,
                "result": result,
            },
            boundary_type="intake.atom_stored",
        ))

        if embedding is not None:
            result["embedding"] = embedding
        return result

    # ── Full Intake Pipeline ───────────────────────────────────

    async def full_intake(
        self,
        locations: List[str] | None = None,
        limit: int | None = None,
    ) -> Dict[str, Any]:
        """Complete intake pipeline: discover → parse → create atoms → store."""
        logger.info("=" * 60)
        logger.info("PARTSFACTORY INTAKE STARTED [%s]", self._intake_id)
        logger.info("=" * 60)

        if locations is not None:
            self.config.search_locations = locations
        batch_limit = limit or self.config.batch_limit

        if self.memory is not None:
            self.memory.store_task(
                task_type="intake_full",
                input_data={"intake_id": self._intake_id, "locations": self.config.search_locations},
                status="running",
            )

        files = await self.discover_files()
        if not files:
            logger.warning("No files discovered for intake")
            return {"status": "empty", "intake_id": self._intake_id, "stats": self.stats}

        atoms_created: List[Dict[str, Any]] = []
        for i, file in enumerate(files):
            if i >= batch_limit:
                logger.info("Batch limit (%d) reached, stopping", batch_limit)
                break

            parsed = await self.parse_file(file)
            if parsed is None:
                continue

            atom = await self.create_atom(parsed)
            embedding = self._generate_embedding(parsed.content)
            store_result = await self.store_atom(atom, embedding)
            atoms_created.append(store_result)

        logger.info("=" * 60)
        logger.info("INTAKE COMPLETE [%s]", self._intake_id)
        logger.info("  Scanned:  %d", self.stats.files_scanned)
        logger.info("  Parsed:   %d", self.stats.files_parsed)
        logger.info("  Atoms:    %d", self.stats.atoms_created)
        logger.info("  Errors:   %d", self.stats.errors)
        logger.info("=" * 60)

        status = "complete" if self.stats.atoms_created > 0 else "empty"
        if self.memory is not None:
            self.memory.store_task(
                task_type="intake_full",
                input_data={"intake_id": self._intake_id},
                output_data={
                    "status": status,
                    "stats": {
                        "scanned": self.stats.files_scanned,
                        "parsed": self.stats.files_parsed,
                        "atoms": self.stats.atoms_created,
                        "errors": self.stats.errors,
                    },
                },
                status=status,
            )

        return {
            "status": status,
            "intake_id": self._intake_id,
            "stats": {
                "files_scanned": self.stats.files_scanned,
                "files_parsed": self.stats.files_parsed,
                "atoms_created": self.stats.atoms_created,
                "embeddings_created": self.stats.embeddings_created,
                "errors": self.stats.errors,
            },
            "atoms": atoms_created,
        }

    async def intake_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Intake a single file directly."""
        file = Path(filepath)
        if not file.exists():
            logger.warning("File not found: %s", filepath)
            return None

        parsed = await self.parse_file(file)
        if parsed is None:
            return None

        atom = await self.create_atom(parsed)
        embedding = self._generate_embedding(parsed.content)
        store_result = await self.store_atom(atom, embedding)
        return {
            "atom": atom,
            "embedding": embedding,
            "store": store_result,
        }

    def status(self) -> Dict[str, Any]:
        """Return intake status report."""
        return {
            "intake_id": self._intake_id,
            "stats": {
                "files_scanned": self.stats.files_scanned,
                "files_parsed": self.stats.files_parsed,
                "atoms_created": self.stats.atoms_created,
                "errors": self.stats.errors,
            },
            "config": {
                "locations": len(self.config.search_locations),
                "patterns": len(self.config.search_patterns),
                "batch_limit": self.config.batch_limit,
            },
        }
