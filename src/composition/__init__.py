#!/usr/bin/env python3
"""
CMPLX-PartsFactory — Tool Composition Harness

This module provides a composition API for wiring discovered tools together.
It allows testing of tool combinations and catalogs the results.

Usage:
    from src.composition import CompositionHarness, CompositionResult

    harness = CompositionHarness()
    result = harness.compose(["e8_lattice", "bond_check"], "A → B → C")
    harness.record_result(result)
"""

import os
import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Tool family definitions
TOOL_FAMILIES = [
    "mmdb", "mdhg", "speedlight", "daemon", "brain",
    "economy", "tarpit", "snap", "thinktank", "agent",
    "cooperative", "sap", "karpathy", "staging"
]

FAMILY_CAPABILITIES = {
    "mmdb": ["e8_lattice", "leech_lattice", "crystal_storage", "conservation", "ingest"],
    "mdhg": ["hash_fabric", "bond_chemistry", "e6_tokens", "morphon", "grains"],
    "speedlight": ["geo_tokenizer", "receipt_chain", "base100", "compute"],
    "daemon": ["24_ring", "channel_ticks", "economy", "orchestration"],
    "brain": ["e8_expert", "hebbian", "triad", "gating", "tier_system"],
    "tarpit": ["e6_encoding", "bond_check", "navigation", "atoms"],
    "snap": ["14_pass", "labeler", "enricher", "fleet", "cluster"],
    "thinktank": ["5_phase", "futures", "dtt", "moe"],
}


class CompositionType(Enum):
    """Types of tool compositions."""
    SEQUENTIAL = "sequential"      # A → B → C
    PARALLEL = "parallel"        # A || B
    CONDITIONAL = "conditional"   # A ? B : C
    LOOP = "loop"               # A → A → ... → done
    PIPELINE = "pipeline"        # Multi-stage pipeline


@dataclass
class CompositionResult:
    """Result of a tool composition test."""
    composition_id: str
    tool_ids: List[str]
    composition_type: str
    description: str
    inputs: Any
    outputs: Any
    success: bool
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    output_quality: float = 0.0  # 0-1 quality score
    delta_phi: float = 0.0      # Conservation check
    bonds_formed: int = 0
    receipts_generated: int = 0
    tested_at: datetime = field(default_factory=datetime.now)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "composition_id": self.composition_id,
            "tool_ids": self.tool_ids,
            "composition_type": self.composition_type,
            "description": self.description,
            "success": self.success,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "output_quality": round(self.output_quality, 3),
            "delta_phi": round(self.delta_phi, 4),
            "bonds_formed": self.bonds_formed,
            "receipts_generated": self.receipts_generated,
            "tested_at": self.tested_at.isoformat(),
            "notes": self.notes[:100] if self.notes else "",
        }


class CompositionHarness:
    """Harness for composing and testing tool combinations."""

    def __init__(self, catalog_path: str = None):
        self.catalog_path = catalog_path or "/mnt/d/PartsFactory/CMPLX-PartsFactory/catalog"
        self._tools: Dict[str, Any] = {}
        self._compositions: List[CompositionResult] = []
        self._composition_cache: Dict[str, List[str]] = {}  # tool_id -> tested_with
        os.makedirs(self.catalog_path, exist_ok=True)

    def register_tool(self, tool_id: str, tool: Any):
        """Register a tool for composition."""
        self._tools[tool_id] = tool

    def register_tools(self, tools: Dict[str, Any]):
        """Register multiple tools."""
        self._tools.update(tools)

    def compose(
        self,
        tool_ids: List[str],
        description: str,
        composition_type: str = "sequential",
        test_input: Any = None,
    ) -> CompositionResult:
        """Compose tools and execute the composition."""
        start_time = time.time()
        composition_id = hashlib.sha256(
            f"{'-'.join(tool_ids)}{description}{time.time()}".encode()
        ).hexdigest()[:16]

        result = CompositionResult(
            composition_id=composition_id,
            tool_ids=tool_ids,
            composition_type=composition_type,
            description=description,
            inputs=test_input,
            outputs=None,
            success=False,
            execution_time_ms=0,
        )

        try:
            # Get tool implementations
            tool_impls = []
            for tid in tool_ids:
                if tid in self._tools:
                    tool_impls.append(self._tools[tid])
                else:
                    result.error = f"Tool not found: {tid}"
                    result.execution_time_ms = (time.time() - start_time) * 1000
                    return result

            # Execute composition based on type
            if composition_type == "sequential":
                result.outputs = self._execute_sequential(tool_impls, test_input)
            elif composition_type == "parallel":
                result.outputs = self._execute_parallel(tool_impls, test_input)
            elif composition_type == "pipeline":
                result.outputs = self._execute_pipeline(tool_impls, test_input)
            else:
                result.outputs = self._execute_sequential(tool_impls, test_input)

            result.success = True
            result.execution_time_ms = (time.time() - start_time) * 1000

            # Update cache
            for tid in tool_ids:
                self._composition_cache.setdefault(tid, []).extend(
                    [t for t in tool_ids if t != tid]
                )

        except Exception as e:
            result.error = str(e)
            result.execution_time_ms = (time.time() - start_time) * 1000

        return result

    def _execute_sequential(self, tools: List[Any], input_data: Any) -> Any:
        """Execute tools sequentially."""
        data = input_data
        for tool in tools:
            if callable(tool):
                data = tool(data)
            elif hasattr(tool, 'process'):
                data = tool.process(data)
        return data

    def _execute_parallel(self, tools: List[Any], input_data: Any) -> List[Any]:
        """Execute tools in parallel."""
        results = []
        for tool in tools:
            if callable(tool):
                results.append(tool(input_data))
            elif hasattr(tool, 'process'):
                results.append(tool.process(input_data))
        return results

    def _execute_pipeline(self, tools: List[Any], input_data: Any) -> Any:
        """Execute as multi-stage pipeline."""
        return self._execute_sequential(tools, input_data)

    def test_pair(self, tool_a: str, tool_b: str, test_input: Any = None) -> CompositionResult:
        """Test composition of a tool pair."""
        return self.compose([tool_a, tool_b], f"{tool_a} → {tool_b}", "sequential", test_input)

    def test_family_composition(self, family: str, test_input: Any = None) -> List[CompositionResult]:
        """Test all compositions within a family."""
        results = []
        family_caps = FAMILY_CAPABILITIES.get(family, [])

        # Test pairwise combinations
        for i, cap_a in enumerate(family_caps):
            for cap_b in family_caps[i+1:]:
                result = self.compose([cap_a, cap_b], f"{family}: {cap_a} → {cap_b}", "sequential", test_input)
                results.append(result)

        return results

    def test_cross_family(
        self,
        family_a: str,
        family_b: str,
        test_input: Any = None
    ) -> List[CompositionResult]:
        """Test compositions between two families."""
        results = []
        caps_a = FAMILY_CAPABILITIES.get(family_a, [])
        caps_b = FAMILY_CAPABILITIES.get(family_b, [])

        for cap_a in caps_a:
            for cap_b in caps_b:
                result = self.compose([cap_a, cap_b], f"{family_a}.{cap_a} → {family_b}.{cap_b}", "sequential", test_input)
                results.append(result)

        return results

    def test_pipeline(
        self,
        tools: List[str],
        stages: List[str],
        test_input: Any = None
    ) -> CompositionResult:
        """Test a multi-stage pipeline."""
        description = " → ".join(stages)
        return self.compose(tools, description, "pipeline", test_input)

    def record_result(self, result: CompositionResult):
        """Record a composition result to the catalog."""
        self._compositions.append(result)
        self._save_result(result)

    def record_results(self, results: List[CompositionResult]):
        """Record multiple composition results."""
        for result in results:
            self.record_result(result)

    def _save_result(self, result: CompositionResult):
        """Save result to catalog file."""
        catalog_file = os.path.join(
            self.catalog_path,
            f"{result.composition_id}.json"
        )
        with open(catalog_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

    def get_catalog(self) -> List[Dict[str, Any]]:
        """Get all recorded composition results."""
        results = []
        for filename in os.listdir(self.catalog_path):
            if filename.endswith('.json'):
                with open(os.path.join(self.catalog_path, filename)) as f:
                    results.append(json.load(f))
        return results

    def get_best_compositions(
        self,
        min_success_rate: float = 0.8,
        max_delta_phi: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Get best performing compositions."""
        catalog = self.get_catalog()
        return [
            r for r in catalog
            if r.get("success", False)
            and r.get("output_quality", 0) >= min_success_rate
            and r.get("delta_phi", 0) <= max_delta_phi
        ]

    def get_tool_compatibility(self, tool_id: str) -> Dict[str, List[str]]:
        """Get what tools a given tool has been successfully composed with."""
        return {
            "tested_with": self._composition_cache.get(tool_id, []),
            "success_count": len(self._composition_cache.get(tool_id, [])),
        }

    def generate_composition_matrix(self) -> Dict[str, Dict[str, Any]]:
        """Generate a matrix of all possible compositions."""
        matrix = {}
        tools = list(self._tools.keys())

        for i, tool_a in enumerate(tools):
            matrix[tool_a] = {}
            for tool_b in tools[i+1:]:
                cached = tool_b in self._composition_cache.get(tool_a, [])
                matrix[tool_a][tool_b] = {
                    "tested": cached,
                    "composition_id": f"{tool_a}_{tool_b}" if cached else None,
                }

        return matrix


class CompositionTemplate:
    """Pre-defined composition templates for common patterns."""

    TEMPLATES = {
        "grain_chain": {
            "name": "Grain Chain (8-stage)",
            "description": "Complete 8-stage atom pipeline",
            "stages": ["tarpit", "snap", "e8", "mdhg", "morphon", "walls", "receipt", "mint"],
            "tools": ["tarpit_encode", "snap_label", "e8_embed", "mdhg_hash", "morphon_create", "wall_create", "receipt_sign", "mint_coin"],
        },
        "e8_bond_synthesis": {
            "name": "E8 Bond Synthesis",
            "description": "E8 embedding + bond chemistry + synthesis",
            "stages": ["e8_embed", "bond_check", "synthesize"],
            "tools": ["e8_embed", "bond_chemistry", "cross_field_synth"],
        },
        "memory_ingest": {
            "name": "Memory Ingest Pipeline",
            "description": "Ingest content through memory system",
            "stages": ["ingest", "process", "store", "route_brain"],
            "tools": ["memory_ingest", "hodge_decompose", "morphon_lifecycle", "brain_route"],
        },
        "snap_cluster": {
            "name": "SNAP Cluster Pipeline",
            "description": "SNAP labeling + clustering + inference",
            "stages": ["snap_14_pass", "cluster", "infer"],
            "tools": ["snap_enricher", "snap_cluster", "snap_inference"],
        },
        "tarPit_bond_morphon": {
            "name": "TarPit Bond Morphon",
            "description": "Encode, bond, morphon lifecycle",
            "stages": ["e6_encode", "bond_check", "morphon_exec"],
            "tools": ["tarpit_encode", "bond_check", "morphon_execute"],
        },
    }

    @classmethod
    def get_template(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get a composition template by name."""
        return cls.TEMPLATES.get(name)

    @classmethod
    def list_templates(cls) -> List[str]:
        """List all available templates."""
        return list(cls.TEMPLATES.keys())

    @classmethod
    def create_from_template(
        cls,
        harness: CompositionHarness,
        template_name: str,
        test_input: Any = None
    ) -> List[CompositionResult]:
        """Execute a template as a series of compositions."""
        template = cls.get_template(template_name)
        if not template:
            return []

        results = []
        tools = template["tools"]
        stages = template["stages"]

        # Execute pairwise for now (expand to full pipeline later)
        for i in range(len(tools) - 1):
            result = harness.compose(
                [tools[i], tools[i+1]],
                stages[i] + " → " + stages[i+1],
                "sequential",
                test_input
            )
            results.append(result)

        return results


def create_composition_harness() -> CompositionHarness:
    """Factory to create composition harness with tool registry."""
    from src.discovery import create_discovery_harness

    harness = CompositionHarness()

    # Get tools from discovery
    discovery = create_discovery_harness()
    harness.register_tools(discovery["tools"])

    return harness


if __name__ == "__main__":
    print("=== CMPLX PartsFactory Composition Harness ===\n")

    harness = create_composition_harness()

    print(f"Registered tools: {len(harness._tools)}")
    print(f"Tool IDs: {list(harness._tools.keys())[:20]}...")

    print("\nAvailable templates:")
    for template in CompositionTemplate.list_templates():
        t = CompositionTemplate.get_template(template)
        print(f"  - {template}: {t['description']}")

    print("\n=== Testing Pairwise Compositions ===\n")

    # Test key pairs
    test_pairs = [
        ("e8_embed", "bond_check"),
        ("tarpit_encode", "snap_label"),
        ("morphon_create", "receipt_sign"),
    ]

    for pair in test_pairs:
        if pair[0] in harness._tools and pair[1] in harness._tools:
            result = harness.test_pair(pair[0], pair[1], test_input="test data")
            print(f"{pair[0]} → {pair[1]}: {'✓' if result.success else '✗'} ({result.execution_time_ms:.1f}ms)")

    print(f"\nTotal compositions tested: {len(harness._compositions)}")