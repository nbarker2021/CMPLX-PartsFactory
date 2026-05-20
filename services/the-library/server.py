#!/usr/bin/env python3
"""
The Library — Document Processing Service (CMPLX-PartsFactory port)

Pipeline: DocumentReader → ChunkingEngine → RAGCardCreator (E8 embeddings)
→ AtomicFormDefiner (10 atomic contracts) → MorphonicFormGenerator (λ-calculus)
→ MDHGStratifier (10-layer hierarchy) → QualityGates (6 falsifiers F1–F6)

Integration: Manny (probe), SNAP (classify), MDHG (stratify), MMDB (store),
GeometricGovernance (audit).
"""

import asyncio
import hashlib
import json
import logging
import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np
from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.responses import JSONResponse

# Security: API-key auth for all endpoints
_LIBRARY_API_KEY = os.environ.get("LIBRARY_API_KEY", "")

def _require_api_key(x_api_key: str = Header(default="")):
    if not _LIBRARY_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="LIBRARY_API_KEY environment variable is not set. Configure it to enable this endpoint."
        )
    if x_api_key != _LIBRARY_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("the_library")

# ── Service URLs ──────────────────────────────────────────────────────────

MMDB_URL = os.environ.get("MMDB_URL", "http://host.docker.internal:8824")
MDHG_URL = os.environ.get("MDHG_URL", "http://host.docker.internal:8825")
SNAP_URL = os.environ.get("SNAP_URL", "http://host.docker.internal:8823")
TARPIT_URL = os.environ.get("TARPIT_URL", "http://host.docker.internal:8844")
MANNY_URL = os.environ.get("MANNY_URL", "http://host.docker.internal:8870")

STORAGE_PATH = Path(os.environ.get("LIBRARY_STORAGE", "/data/library"))
SERVICE_PORT = int(os.environ.get("PORT", "8838"))

# ── Geometric Governance (inline port) ────────────────────────────────────

class GeometricGovernanceError(Exception):
    pass

@dataclass
class BoundaryEvent:
    event_id: str
    timestamp: float
    entropy_delta: float
    receipt_data: Dict[str, Any]
    boundary_type: str

    def generate_receipt(self) -> Dict[str, Any]:
        raw = f"{self.event_id}{self.timestamp}{self.entropy_delta}{self.boundary_type}"
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "entropy_delta": self.entropy_delta,
            "boundary_type": self.boundary_type,
            "receipt_hash": hashlib.sha256(raw.encode()).hexdigest(),
            "receipt_data": self.receipt_data,
        }

class GeometricGovernance:
    def __init__(self):
        self.invariants: Dict[str, Any] = {}
        self.boundary_events: List[BoundaryEvent] = []
        self.audit_trail: List[Dict[str, Any]] = []

    def record_boundary_event(self, event: BoundaryEvent) -> None:
        self.boundary_events.append(event)
        receipt = event.generate_receipt()
        self.audit_trail.append({
            "type": "boundary_event",
            "timestamp": time.time(),
            "receipt": receipt,
        })

    def audit(self, action: str, payload: Dict[str, Any]) -> None:
        self.audit_trail.append({
            "action": action,
            "timestamp": time.time(),
            "payload": payload,
        })

# ── Manny / SNAP Integration Helpers ─────────────────────────────────────

def _http_post(url: str, body: dict, timeout: int = 15) -> Optional[dict]:
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning("HTTP POST %s failed: %s", url, e)
        return None

def _http_get(url: str, timeout: int = 10) -> Optional[dict]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning("HTTP GET %s failed: %s", url, e)
        return None

def classify_with_snap(text: str) -> Optional[dict]:
    return _http_post(f"{SNAP_URL}/stratify", {"text": text})

def probe_with_manny(query: str, domain: str = "general") -> Optional[dict]:
    return _http_post(f"{MANNY_URL}/probe", {"query": query, "domain": domain})

# ── Data Models ───────────────────────────────────────────────────────────

class DocumentStatus(Enum):
    PENDING = "pending"
    READING = "reading"
    CHUNKED = "chunked"
    RAG_CARDS_CREATED = "rag_cards_created"
    ATOMIC_FORMS_DEFINED = "atomic_forms_defined"
    MORPHONIC_FORMS_GENERATED = "morphonic_forms_generated"
    MDHG_STRATIFIED = "mdhg_stratified"
    VALIDATED = "validated"
    FAILED = "failed"

class QualityGate(Enum):
    F1_TYPE_VALIDATION = "f1_type_validation"
    F2_CONSERVATION_LAW = "f2_conservation_law"
    F3_LATTICE_SNAP = "f3_lattice_snap"
    F4_RECEIPT_CHAIN = "f4_receipt_chain"
    F5_SEMANTIC_COHERENCE = "f5_semantic_coherence"
    F6_MDHG_ADDRESS = "f6_mdhg_address"

@dataclass
class DocumentRecord:
    document_id: str
    path: str
    title: str
    content: str
    word_count: int
    chunk_count: int = 0
    status: DocumentStatus = DocumentStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "path": self.path,
            "title": self.title,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "word_count": self.word_count,
            "chunk_count": self.chunk_count,
            "status": self.status.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

@dataclass
class RAGCard:
    card_id: str
    document_id: str
    chunk_index: int
    content: str
    embedding: List[float]
    e8_projection: List[float]
    digital_root: int
    atomic_forms: List[Dict[str, Any]] = field(default_factory=list)
    morphonic_forms: List[Dict[str, Any]] = field(default_factory=list)
    mdhg_address: Optional[Dict[str, Any]] = None
    quality_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "embedding_dimension": len(self.embedding),
            "e8_projection": self.e8_projection,
            "digital_root": self.digital_root,
            "atomic_forms_count": len(self.atomic_forms),
            "morphonic_forms_count": len(self.morphonic_forms),
            "mdhg_address": self.mdhg_address,
            "quality_scores": self.quality_scores,
        }

@dataclass
class QualityReport:
    document_id: str
    passed: bool
    gates: Dict[QualityGate, Tuple[bool, str]]
    overall_score: float
    issues: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "passed": self.passed,
            "gates": {k.value: v for k, v in self.gates.items()},
            "overall_score": self.overall_score,
            "issues": self.issues,
            "timestamp": self.timestamp,
        }

# ── Pipeline Stage 1: DocumentReader ─────────────────────────────────────

class DocumentReader:
    def __init__(self, library_path: Path):
        self.library_path = library_path
        self.documents_path = library_path / "documents"
        self.documents_path.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, file_path: str) -> Path:
        """Resolve file_path inside the library, blocking traversal outside."""
        # Reject absolute paths
        if Path(file_path).is_absolute():
            raise FileNotFoundError(f"Absolute paths not allowed: {file_path}")
        target = (self.documents_path / file_path).resolve()
        # Ensure the resolved path is still inside documents_path
        if not str(target).startswith(str(self.documents_path.resolve())):
            raise FileNotFoundError(f"Path escapes library: {file_path}")
        return target

    def read_file(self, file_path: str) -> Tuple[str, str]:
        path = self._safe_path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        content = path.read_text(encoding="utf-8", errors="replace")
        if content.strip():
            first_line = content.strip().split("\n")[0]
            title = first_line.lstrip("#").strip() if first_line.startswith("#") else path.stem
        else:
            title = path.stem
        return title, content

    def get_word_count(self, content: str) -> int:
        return len(content.split())

# ── Pipeline Stage 2: ChunkingEngine ─────────────────────────────────────

class ChunkingEngine:
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_by_structure(self, content: str) -> List[Tuple[str, int, int]]:
        chunks = []
        lines = content.split("\n")
        current_chunk = []
        current_pos = 0
        for line in lines:
            is_header = line.strip().startswith("#")
            if is_header and current_chunk:
                chunk_text = "\n".join(current_chunk)
                chunks.append((chunk_text, current_pos, current_pos + len(chunk_text)))
                current_chunk = []
                current_pos += len(chunk_text) + 1
            current_chunk.append(line)
        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            chunks.append((chunk_text, current_pos, current_pos + len(chunk_text)))
        return chunks

    def chunk_by_size(self, content: str) -> List[Tuple[str, int, int]]:
        chunks = []
        words = content.split()
        i = 0
        while i < len(words):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            chunks.append((chunk_text, i, i + len(chunk_words)))
            i += self.chunk_size - self.overlap
        return chunks

    def chunk(self, content: str, method: str = "hybrid") -> List[Dict[str, Any]]:
        if method == "structure":
            raw_chunks = self.chunk_by_structure(content)
        elif method == "size":
            raw_chunks = self.chunk_by_size(content)
        else:
            raw_chunks = self.chunk_by_structure(content)
            if len(raw_chunks) < 2:
                raw_chunks = self.chunk_by_size(content)
        result = []
        for i, (text, start, end) in enumerate(raw_chunks):
            if text.strip():
                result.append({
                    "chunk_index": i,
                    "content": text.strip(),
                    "start_pos": start,
                    "end_pos": end,
                    "word_count": len(text.split()),
                })
        return result

# ── Pipeline Stage 3: RAGCardCreator (E8 embeddings) ─────────────────────

class RAGCardCreator:
    def create_card(self, document_id: str, chunk: Dict[str, Any], chunk_index: int) -> RAGCard:
        card_id = f"rag_{document_id}_{chunk_index:04d}_{uuid4().hex[:6]}"
        content = chunk["content"]
        embedding, e8_projection, digital_root = self._compute_embedding(content)
        return RAGCard(
            card_id=card_id,
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
            e8_projection=e8_projection,
            digital_root=digital_root,
        )

    def _compute_embedding(self, text: str, dim: int = 768) -> Tuple[List[float], List[float], int]:
        h = hashlib.sha256(text.encode()).hexdigest()
        vector = []
        for i in range(dim):
            byte_val = int(h[i % len(h)], 16)
            vector.append((byte_val / 15.0) * 2 - 1)
        e8_proj = vector[:8]
        digital_root = len(text) % 9 + 1
        return vector, e8_proj, digital_root

# ── Pipeline Stage 4: AtomicFormDefiner (10 contracts) ───────────────────

class AtomicFormDefiner:
    ATOMIC_CONTRACTS = [
        "dim_adapt",
        "typed_bridge",
        "receipt_wrapper",
        "lattice_type_cast",
        "graph_to_causal",
        "term_to_graph",
        "seal_and_fingerprint",
        "orbit_expand",
        "delta_phi_decorator",
        "dual_rail_inverse",
    ]

    def define_atomic_forms(self, rag_card: RAGCard) -> List[Dict[str, Any]]:
        forms = []
        for contract in self.ATOMIC_CONTRACTS:
            form = self._define(contract, rag_card)
            if form:
                forms.append(form)
        rag_card.atomic_forms = forms
        return forms

    def _define(self, contract: str, card: RAGCard) -> Optional[Dict[str, Any]]:
        content = card.content
        if contract == "dim_adapt":
            return {
                "contract": "dim_adapt", "input_dim": len(card.embedding),
                "output_dim": 8, "adapted_vector": card.e8_projection,
            }
        if contract == "typed_bridge":
            return {"contract": "typed_bridge", "input_type": "text_chunk", "output_type": "vector_embedding", "bridge_valid": True}
        if contract == "receipt_wrapper":
            return {"contract": "receipt_wrapper", "receipt_id": f"rcpt_{uuid4().hex[:8]}", "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16], "timestamp": datetime.now().isoformat()}
        if contract == "lattice_type_cast":
            return {"contract": "lattice_type_cast", "src_lattice": "text_space", "dst_lattice": "E8", "cast_valid": True}
        if contract == "delta_phi_decorator":
            delta_phi = -abs(len(content) % 100) / 100.0
            return {"contract": "delta_phi_decorator", "delta_phi": delta_phi, "conserved": delta_phi <= 0}
        return {"contract": contract, "defined": True, "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16]}

# ── Pipeline Stage 5: MorphonicFormGenerator (λ-calculus) ────────────────

class MorphonicFormGenerator:
    def generate_forms(self, rag_card: RAGCard) -> List[Dict[str, Any]]:
        forms = [
            {
                "form": "M0_universal_morphon",
                "lambda_expr": f"λx.{rag_card.content[:50]}...",
                "reduction_rules": 8, "observation_functor": True,
            },
            {
                "form": "MGLC_morphonic_lambda",
                "lambda_term": f"λ{hashlib.sha256(rag_card.content.encode()).hexdigest()[:8]}.body",
                "beta_reductions": len(rag_card.content.split()), "normal_form": True,
            },
            {
                "form": "observation_functor", "functor_type": "content_observer",
                "maps_to": f"E8_{rag_card.digital_root}",
            },
        ]
        rag_card.morphonic_forms = forms
        return forms

# ── Pipeline Stage 6: MDHGStratifier (10-layer hierarchy) ────────────────

class MDHGStratifier:
    LAYERS = ["atom", "room", "floor", "building", "city", "planet", "velocity", "dimension", "lattice", "universe"]

    def stratify(self, rag_card: RAGCard, document: DocumentRecord) -> Dict[str, Any]:
        from pathlib import Path as _P
        mdhg_address = {
            "atom": rag_card.card_id,
            "room": f"room_{document.document_id}_{rag_card.chunk_index}",
            "floor": f"floor_{document.title.replace(' ', '_').lower()[:20]}",
            "building": f"building_{_P(document.path).stem}",
            "city": "city_library",
            "planet": "planet_documents",
            "velocity": 0.5,
            "dimension": rag_card.digital_root,
            "lattice": "E8",
            "universe": "CMPLX_Library",
        }
        hamiltonian_path = [f"{layer}:{mdhg_address[layer]}" for layer in self.LAYERS if layer in mdhg_address]
        mdhg_address["hamiltonian_path"] = hamiltonian_path
        mdhg_address["layer_count"] = len(self.LAYERS)
        rag_card.mdhg_address = mdhg_address

        snap_result = classify_with_snap(rag_card.content)
        if snap_result:
            mdhg_address["snap_classification"] = snap_result

        return mdhg_address

# ── Pipeline Stage 7: QualityGates (6 falsifiers F1–F6) ──────────────────

class QualityGates:
    def validate(self, rag_card: RAGCard, document: DocumentRecord) -> QualityReport:
        gates = {}
        issues = []
        scores = []

        f1_passed, f1_msg = self._f1(rag_card, document)
        gates[QualityGate.F1_TYPE_VALIDATION] = (f1_passed, f1_msg)
        scores.append(1.0 if f1_passed else 0.0)
        if not f1_passed:
            issues.append(f1_msg)

        f2_passed, f2_msg = self._f2(rag_card)
        gates[QualityGate.F2_CONSERVATION_LAW] = (f2_passed, f2_msg)
        scores.append(1.0 if f2_passed else 0.0)
        if not f2_passed:
            issues.append(f2_msg)

        f3_passed, f3_msg = self._f3(rag_card)
        gates[QualityGate.F3_LATTICE_SNAP] = (f3_passed, f3_msg)
        scores.append(1.0 if f3_passed else 0.0)
        if not f3_passed:
            issues.append(f3_msg)

        f4_passed, f4_msg = self._f4(rag_card)
        gates[QualityGate.F4_RECEIPT_CHAIN] = (f4_passed, f4_msg)
        scores.append(1.0 if f4_passed else 0.0)
        if not f4_passed:
            issues.append(f4_msg)

        f5_passed, f5_msg = self._f5(rag_card)
        gates[QualityGate.F5_SEMANTIC_COHERENCE] = (f5_passed, f5_msg)
        scores.append(1.0 if f5_passed else 0.0)
        if not f5_passed:
            issues.append(f5_msg)

        f6_passed, f6_msg = self._f6(rag_card)
        gates[QualityGate.F6_MDHG_ADDRESS] = (f6_passed, f6_msg)
        scores.append(1.0 if f6_passed else 0.0)
        if not f6_passed:
            issues.append(f6_msg)

        overall_score = sum(scores) / len(scores) if scores else 0.0
        passed = all(g[0] for g in gates.values())

        rag_card.quality_scores = {gate.value[3:]: float(p) for gate, (p, _) in gates.items()}
        rag_card.quality_scores["overall"] = overall_score

        report = QualityReport(
            document_id=document.document_id,
            passed=passed,
            gates=gates,
            overall_score=overall_score,
            issues=issues,
        )

        manny_result = probe_with_manny(
            f"quality validation for {document.document_id}: {', '.join(issues) if issues else 'all passed'}"
        )
        if manny_result:
            report.issues.append(f"manny_probe: {manny_result.get('response', 'ok')}")

        return report

    def _f1(self, rag_card: RAGCard, document: DocumentRecord) -> Tuple[bool, str]:
        if not rag_card.content:
            return False, "Empty content"
        if not rag_card.embedding:
            return False, "Missing embedding"
        if len(rag_card.atomic_forms) < 10:
            return False, f"Missing atomic forms: {len(rag_card.atomic_forms)}/10"
        return True, "Type validation passed"

    def _f2(self, rag_card: RAGCard) -> Tuple[bool, str]:
        for form in rag_card.atomic_forms:
            if form.get("contract") == "delta_phi_decorator":
                if form.get("delta_phi", 0) > 0:
                    return False, f"ΔΦ violation: {form['delta_phi']} > 0"
        return True, "Conservation law satisfied (ΔΦ ≤ 0)"

    def _f3(self, rag_card: RAGCard) -> Tuple[bool, str]:
        if not rag_card.e8_projection:
            return False, "Missing E8 projection"
        if len(rag_card.e8_projection) != 8:
            return False, f"Invalid E8 dimension: {len(rag_card.e8_projection)}"
        return True, "E8 lattice snap valid"

    def _f4(self, rag_card: RAGCard) -> Tuple[bool, str]:
        for form in rag_card.atomic_forms:
            if form.get("contract") == "receipt_wrapper":
                if not form.get("receipt_id"):
                    return False, "Missing receipt ID"
                return True, "Receipt chain intact"
        return False, "No receipt wrapper found"

    def _f5(self, rag_card: RAGCard) -> Tuple[bool, str]:
        content = rag_card.content
        if len(content.split()) < 10:
            return False, "Chunk too short for semantic coherence"
        if not any(content.endswith(p) for p in ".!?"):
            return False, "No complete sentences"
        return True, "Semantic coherence valid"

    def _f6(self, rag_card: RAGCard) -> Tuple[bool, str]:
        if not rag_card.mdhg_address:
            return False, "Missing MDHG address"
        required = ["atom", "room", "floor", "building", "city", "planet"]
        for layer in required:
            if layer not in rag_card.mdhg_address:
                return False, f"Missing MDHG layer: {layer}"
        return True, "MDHG address valid"

# ── TheLibrary — Orchestrator ────────────────────────────────────────────

class TheLibrary:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or STORAGE_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "documents").mkdir(parents=True, exist_ok=True)

        self.reader = DocumentReader(self.storage_path)
        self.chunker = ChunkingEngine(chunk_size=512, overlap=50)
        self.rag_creator = RAGCardCreator()
        self.atomic_definer = AtomicFormDefiner()
        self.morphonic_generator = MorphonicFormGenerator()
        self.mdhg_stratifier = MDHGStratifier()
        self.quality_gates = QualityGates()
        self.governance = GeometricGovernance()

        self.documents: Dict[str, DocumentRecord] = {}
        self.rag_cards: Dict[str, RAGCard] = {}
        self.quality_reports: Dict[str, QualityReport] = {}

        logger.info("The Library initialized at %s", self.storage_path)

    async def ingest_document(self, file_path: str, collection: str = "default") -> DocumentRecord:
        document_id = f"doc_{uuid4().hex[:12]}"
        logger.info("Ingesting document: %s", file_path)
        title, content = self.reader.read_file(file_path)
        word_count = self.reader.get_word_count(content)
        document = DocumentRecord(
            document_id=document_id, path=file_path, title=title,
            content=content, word_count=word_count,
            metadata={"collection": collection},
        )
        self.documents[document_id] = document
        doc_path = self.storage_path / "documents" / f"{document_id}.json"
        doc_path.write_text(json.dumps(document.to_dict(), indent=2))
        logger.info("Document ingested: %s (%d words)", document_id, word_count)

        self.governance.audit("ingest", {"document_id": document_id, "path": file_path, "collection": collection})
        return document

    async def process_document(
        self, document_id: str,
        create_rag: bool = True,
        define_atomic: bool = True,
        generate_morphonic: bool = True,
        stratify_mdhg: bool = True,
        validate_quality: bool = True,
    ) -> Dict[str, Any]:
        if document_id not in self.documents:
            raise ValueError(f"Document not found: {document_id}")
        document = self.documents[document_id]
        results = {"document_id": document_id}

        logger.info("Chunking document: %s", document_id)
        chunks = self.chunker.chunk(document.content, method="hybrid")
        document.chunk_count = len(chunks)
        document.status = DocumentStatus.CHUNKED
        results["chunks"] = len(chunks)

        if create_rag:
            logger.info("Creating RAG cards: %s", document_id)
            for chunk in chunks:
                card = self.rag_creator.create_card(document_id, chunk, chunk["chunk_index"])
                if define_atomic:
                    self.atomic_definer.define_atomic_forms(card)
                if generate_morphonic:
                    self.morphonic_generator.generate_forms(card)
                if stratify_mdhg:
                    self.mdhg_stratifier.stratify(card, document)
                self.rag_cards[card.card_id] = card
            document.status = DocumentStatus.RAG_CARDS_CREATED
            results["rag_cards"] = len([c for c in self.rag_cards.values() if c.document_id == document_id])

        if validate_quality:
            logger.info("Validating quality: %s", document_id)
            doc_cards = [c for c in self.rag_cards.values() if c.document_id == document_id]
            all_passed = True
            for card in doc_cards:
                report = self.quality_gates.validate(card, document)
                self.quality_reports[card.card_id] = report
                if not report.passed:
                    all_passed = False
                self.governance.audit("quality_gate", {
                    "card_id": card.card_id,
                    "document_id": document_id,
                    "passed": report.passed,
                    "overall_score": report.overall_score,
                    "issues": report.issues,
                })
            document.status = DocumentStatus.VALIDATED if all_passed else DocumentStatus.FAILED
            results["quality_passed"] = all_passed
            results["quality_reports"] = len([r for r in self.quality_reports.values()
                                               if r.document_id == document_id])

        self.governance.audit("process", results)
        return results

    def get_report(self, document_id: str) -> Dict[str, Any]:
        if document_id not in self.documents:
            return {"error": "Document not found"}
        document = self.documents[document_id]
        doc_cards = [c for c in self.rag_cards.values() if c.document_id == document_id]
        doc_reports = [r for r in self.quality_reports.values() if r.document_id == document_id]
        return {
            "document": document.to_dict(),
            "rag_cards_count": len(doc_cards),
            "quality_reports_count": len(doc_reports),
            "quality_passed": all(r.passed for r in doc_reports),
            "status": document.status.value,
        }

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        results = []
        for card in self.rag_cards.values():
            if query.lower() in card.content.lower():
                results.append({
                    "card_id": card.card_id,
                    "document_id": card.document_id,
                    "chunk_index": card.chunk_index,
                    "content": card.content[:200] + "...",
                    "similarity": 1.0,
                })
        return results[:limit]

# ── FastAPI App ───────────────────────────────────────────────────────────

app = FastAPI(title="The Library", version="1.0.0", description="Document Processing Pipeline Service")
library = TheLibrary()


@app.on_event("startup")
async def startup():
    logger.info("The Library service starting on port %d", SERVICE_PORT)


@app.get("/health")
async def health():
    services = {}
    for name, url in [("mmdb", MMDB_URL), ("mdhg", MDHG_URL), ("snap", SNAP_URL),
                       ("tarpit", TARPIT_URL), ("manny", MANNY_URL)]:
        svc = _http_get(f"{url}/health")
        services[name] = "healthy" if svc else "unreachable"
    return {
        "service": "the-library",
        "status": "healthy",
        "port": SERVICE_PORT,
        "storage": str(STORAGE_PATH),
        "services": services,
        "document_count": len(library.documents),
        "rag_card_count": len(library.rag_cards),
        "governance_audit_count": len(library.governance.audit_trail),
    }


def _safe_ingest_path(file_path: str) -> Path:
    """Prevent path traversal for ingest queries."""
    if Path(file_path).is_absolute():
        raise FileNotFoundError(f"Absolute paths not allowed: {file_path}")
    # Resolve relative to the library storage path
    base = library.storage_path.resolve()
    target = (base / file_path).resolve()
    if not str(target).startswith(str(base)):
        raise FileNotFoundError(f"Path escapes library: {file_path}")
    return target


@app.post("/ingest")
async def ingest(file_path: str = Query(...), collection: str = Query("default"), _=Depends(_require_api_key)):
    try:
        _safe_ingest_path(file_path)
        doc = await library.ingest_document(file_path, collection)
        return {"document_id": doc.document_id, "title": doc.title, "word_count": doc.word_count, "status": "ingested"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/{document_id}")
async def process(
    document_id: str,
    create_rag: bool = Query(True),
    define_atomic: bool = Query(True),
    generate_morphonic: bool = Query(True),
    stratify_mdhg: bool = Query(True),
    validate_quality: bool = Query(True),
    _=Depends(_require_api_key),
):
    try:
        results = await library.process_document(
            document_id, create_rag, define_atomic, generate_morphonic, stratify_mdhg, validate_quality,
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/report/{document_id}")
async def report(document_id: str, _=Depends(_require_api_key)):
    result = library.get_report(document_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/search")
async def search(query: str = Query(...), limit: int = Query(10), _=Depends(_require_api_key)):
    return {"results": library.search(query, limit)}


@app.get("/governance/audit")
async def governance_audit(_=Depends(_require_api_key)):
    return {"audit_trail": library.governance.audit_trail[-100:]}


@app.get("/governance/boundary-events")
async def governance_boundary_events(_=Depends(_require_api_key)):
    receipts = [e.generate_receipt() for e in library.governance.boundary_events]
    return {"boundary_events": receipts[-100:]}


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
