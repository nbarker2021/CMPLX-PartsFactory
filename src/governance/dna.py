"""DNA-based encoding/decoding system with geometric governance."""
from __future__ import annotations
import hashlib
import json
import time
import uuid
import logging
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    np = None
    HAVE_NUMPY = False

logger = logging.getLogger("dna")


class DNABase(Enum):
    A = 0
    T = 1
    G = 2
    C = 3


class DNAStrand:
    """Represents a DNA strand with embedded information and geometric governance."""

    def __init__(self, sequence: str = "", metadata: Dict[str, Any] = None):
        self.sequence = sequence
        self.metadata = metadata or {}
        self.embedding_vectors: list = []
        self._signature_value: float = 0.0

    @property
    def geometric_signature(self) -> float:
        return self._calculate_geometric_signature()

    def _calculate_geometric_signature(self) -> float:
        if not self.sequence:
            return 0.0
        base_values = [DNABase[base].value for base in self.sequence if base in "ATGC"]
        if not base_values:
            return 0.0
        return sum(x * x for x in base_values) / len(base_values)

    def encode_data(self, data: Any) -> str:
        json_str = json.dumps(data, sort_keys=True)
        binary_str = "".join(format(ord(c), "08b") for c in json_str)
        dna_sequence = ""
        for i in range(0, len(binary_str), 2):
            bits = binary_str[i:i+2].ljust(2, "0")
            base_value = int(bits, 2)
            dna_sequence += list(DNABase)[base_value].name
        self.sequence = dna_sequence
        self.metadata["encoded_data_type"] = type(data).__name__
        self.metadata["encoding_timestamp"] = time.time()
        return self.sequence

    def decode_data(self) -> Any:
        if not self.sequence:
            return None
        binary_str = ""
        for base in self.sequence:
            if base in "ATGC":
                base_value = DNABase[base].value
                binary_str += format(base_value, "02b")
        json_str = ""
        for i in range(0, len(binary_str), 8):
            byte = binary_str[i:i+8]
            if len(byte) == 8:
                json_str += chr(int(byte, 2))
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    def add_embedding(self, vector) -> None:
        self.embedding_vectors.append(vector)
        self.metadata["embedding_count"] = len(self.embedding_vectors)


class DNAEncoder:
    """Lossless DNA-based encoder/decoder with geometric governance."""

    def __init__(self, governance):
        self.governance = governance
        self.strands: Dict[str, DNAStrand] = {}

    def encode(self, data: Any, strand_id: str = None) -> str:
        if strand_id is None:
            strand_id = str(uuid.uuid4())
        strand = DNAStrand()
        sequence = strand.encode_data(data)
        from .engine import QuadraticInvariant
        self.governance.register_invariant(
            f"dna_strand_{strand_id}",
            QuadraticInvariant(strand._calculate_geometric_signature())
        )
        self.strands[strand_id] = strand
        from .engine import BoundaryEvent
        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"encode_{strand_id}",
            timestamp=time.time(),
            entropy_delta=0.0,
            receipt_data={"strand_id": strand_id, "sequence_length": len(sequence)},
            boundary_type="encoding",
        ))
        return strand_id

    def decode(self, strand_id: str) -> Any:
        if strand_id not in self.strands:
            raise ValueError(f"DNA strand {strand_id} not found")
        strand = self.strands[strand_id]
        data = strand.decode_data()
        current_sig = strand._calculate_geometric_signature()
        original = self.governance.invariants.get(f"dna_strand_{strand_id}")
        if original and not original.is_preserved(current_sig):
            from .engine import CQELawViolationError
            raise CQELawViolationError(
                f"DNA strand {strand_id} geometric signature corrupted"
            )
        from .engine import BoundaryEvent
        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"decode_{strand_id}",
            timestamp=time.time(),
            entropy_delta=0.0,
            receipt_data={"strand_id": strand_id, "decoded": data is not None},
            boundary_type="decoding",
        ))
        return data
