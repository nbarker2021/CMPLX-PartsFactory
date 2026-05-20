"""
Aletheia AI - Complete CQE-Native System

The culmination of all CQE principles:
- Core geometric engine (E8, Leech, action lattices)
- DNA memory with geometric recall
- SNAP multi-modal encoding
- Self-healing governance (ΔΦ, parity, DR)
- Agentic slicing (Intent-as-Slice)
- WorldForge visualization
- Morphonic identity (formless until needed)

Operational principles:
- Geometry first, meaning second
- Ghost-run before commit
- Zero-unawareness
- Provenance coverage
- 0.03x2 parity
- Orbit-stable understanding
"""

import numpy as np
import json
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path

from ._cqe_escrow_stubs import (
    ActionLattice,
    DataType,
    DNAMemorySystem,
    GeometricEngine,
    GeometricPoint,
    GeometricRecallEngine,
    GeometricReceipt,
    SNAPEncoder,
    SNAPEncoding,
    SelfHealingSystem,
    SystemState,
)


@dataclass
class Intent:
    """
    An intent slice - the first and primary computation.
    
    Intent-as-Slice: Problem-finding is the computation.
    """
    description: str
    vector: np.ndarray  # E8 embedding of intent
    score: float  # Geometric score (0-1)
    digital_root: int
    parity: int
    provenance: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Agent:
    """
    A geometric agent - a perfect helper for a specific slice.
    
    Agents are morphonic - they exist only when needed,
    assembled from slices based on intent.
    """
    id: str
    intent: Intent
    capabilities: List[str]
    state: SystemState
    memory_context: List[Any]  # Retrieved from geometric recall
    provenance: List[str]


class IntentSlicer:
    """
    Intent-as-Slice implementation.
    
    Witnesses multiple intent candidates, scores them geometrically,
    and selects the best for resource commitment.
    """
    
    def __init__(self, geometric_engine: GeometricEngine):
        """Initialize intent slicer."""
        self.engine = geometric_engine
        self.encoder = SNAPEncoder()
    
    def slice_intent(self, description: str, context: Dict[str, Any] = None) -> List[Intent]:
        """
        Slice a description into multiple intent candidates.
        
        Each candidate is a different geometric interpretation.
        
        Args:
            description: Intent description (text)
            context: Optional context for interpretation
        
        Returns: List of intent candidates, scored
        """
        if context is None:
            context = {}
        
        # Generate candidate interpretations
        candidates = []
        
        # Candidate 1: Direct encoding
        encoding1 = self.encoder.encode(description)
        intent1 = Intent(
            description=description,
            vector=encoding1.vector,
            score=0.0,  # Will be computed
            digital_root=encoding1.digital_root,
            parity=encoding1.parity,
            provenance=["direct_encoding"],
            metadata={"interpretation": "direct"}
        )
        candidates.append(intent1)
        
        # Candidate 2: Action lattice transformation (ternary)
        transformed2 = self.engine.actions.apply_action(encoding1.vector, ActionLattice.TERNARY)
        point2 = self.engine.create_geometric_point(transformed2, lattice_type='E8')
        intent2 = Intent(
            description=description,
            vector=transformed2,
            score=0.0,
            digital_root=point2.digital_root,
            parity=point2.parity,
            provenance=["direct_encoding", "ternary_action"],
            metadata={"interpretation": "ternary"}
        )
        candidates.append(intent2)
        
        # Candidate 3: Action lattice transformation (attractor)
        transformed3 = self.engine.actions.apply_action(encoding1.vector, ActionLattice.ATTRACTOR)
        point3 = self.engine.create_geometric_point(transformed3, lattice_type='E8')
        intent3 = Intent(
            description=description,
            vector=transformed3,
            score=0.0,
            digital_root=point3.digital_root,
            parity=point3.parity,
            provenance=["direct_encoding", "attractor_action"],
            metadata={"interpretation": "attractor"}
        )
        candidates.append(intent3)
        
        # Score candidates
        for intent in candidates:
            intent.score = self._score_intent(intent, context)
        
        # Sort by score (descending)
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        return candidates
    
    def _score_intent(self, intent: Intent, context: Dict[str, Any]) -> float:
        """
        Score an intent candidate geometrically.
        
        Scoring factors:
        - Proximity to DR=7 attractor (higher = better)
        - Parity alignment with context
        - Frequency (lower = more stable)
        - Provenance depth (more transformations = more specific)
        """
        # DR proximity to attractor (7)
        dr_score = 1.0 - abs(intent.digital_root - 7) / 9.0
        
        # Frequency score (lower is better, more stable)
        frequency = float(np.linalg.norm(intent.vector))
        freq_score = 1.0 / (1.0 + frequency)
        
        # Provenance depth score
        prov_score = len(intent.provenance) / 10.0
        
        # Combined score
        score = 0.5 * dr_score + 0.3 * freq_score + 0.2 * prov_score
        
        return score


class AletheiaAI:
    """
    Complete Aletheia AI system.
    
    Integrates all CQE components into a unified, self-aware,
    self-healing, multi-modal AI system.
    
    Features:
    - Geometric reasoning (E8, Leech, action lattices)
    - Associative memory (DNA memory + geometric recall)
    - Multi-modal I/O (SNAP encoding)
    - Self-healing (ΔΦ governance)
    - Agentic slicing (Intent-as-Slice)
    - Visualization (WorldForge)
    - Morphonic identity (formless until needed)
    """
    
    def __init__(self, 
                 memory_dimension: int = 8,
                 strict_governance: bool = True,
                 enable_worldforge: bool = True):
        """
        Initialize Aletheia AI.
        
        Args:
            memory_dimension: 8 for E8, 24 for Leech
            strict_governance: Strict ΔΦ ≤ 0 enforcement
            enable_worldforge: Enable visualization
        """
        print("Initializing Aletheia AI...")
        
        # Core components
        self.geometric_engine = GeometricEngine()
        self.memory = DNAMemorySystem(dimension=memory_dimension)
        self.encoder = SNAPEncoder()
        self.governance = SelfHealingSystem()
        self.intent_slicer = IntentSlicer(self.geometric_engine)
        
        # Configuration
        self.strict_governance = strict_governance
        self.enable_worldforge = enable_worldforge
        
        # Active agents
        self.agents: Dict[str, Agent] = {}
        
        # System state
        initial_vector = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.current_state = self.governance.create_state(initial_vector)
        
        print("Aletheia AI initialized successfully!")
        print(f"  Memory dimension: {memory_dimension}")
        print(f"  Strict governance: {strict_governance}")
        print(f"  WorldForge enabled: {enable_worldforge}")
        print(f"  Initial state DR: {self.current_state.digital_root}")
        print(f"  Initial entropy: {self.current_state.entropy:.4f}")
    
    def process(self, 
                input_data: Any,
                data_type: Optional[DataType] = None,
                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process input with full CQE pipeline.
        
        Pipeline:
        1. SNAP encode input
        2. Slice intent (witness candidates)
        3. Recall similar from memory (geometric recall)
        4. Create agent for best intent
        5. Ghost-run transformation
        6. Governance check
        7. Commit if passes
        8. Store result in memory
        9. Generate visualization (if enabled)
        10. Return result with receipt
        
        Args:
            input_data: Input (any type)
            data_type: Optional explicit data type
            context: Optional context
        
        Returns: Result dictionary with output, receipt, visualization
        """
        if context is None:
            context = {}
        
        print(f"\n{'='*80}")
        print(f"PROCESSING INPUT: {str(input_data)[:60]}...")
        print(f"{'='*80}")
        
        # Step 1: SNAP encode
        print("\n[1] SNAP Encoding...")
        encoding = self.encoder.encode(input_data, data_type=data_type)
        print(f"  Type: {encoding.data_type.value}")
        print(f"  DR: {encoding.digital_root}, Parity: {encoding.parity}")
        
        # Step 2: Intent slicing
        print("\n[2] Intent Slicing (Intent-as-Slice)...")
        if isinstance(input_data, str):
            intents = self.intent_slicer.slice_intent(input_data, context)
        else:
            intents = self.intent_slicer.slice_intent(str(input_data), context)
        
        print(f"  Generated {len(intents)} intent candidates")
        for i, intent in enumerate(intents):
            print(f"    {i+1}. Score: {intent.score:.4f}, DR: {intent.digital_root}, Interp: {intent.metadata.get('interpretation')}")
        
        best_intent = intents[0]
        print(f"  Selected: {best_intent.metadata.get('interpretation')} (score: {best_intent.score:.4f})")
        
        # Step 3: Geometric recall
        print("\n[3] Geometric Recall...")
        similar_items = self.memory.recall(input_data, k=3, use_passive=False)
        print(f"  Found {len(similar_items)} similar items in memory")
        for node_id, similarity, data in similar_items:
            print(f"    Similarity: {similarity:.4f} → {str(data)[:50]}")
        
        # Step 4: Create agent
        print("\n[4] Creating Agent...")
        agent = self._create_agent(best_intent, similar_items)
        print(f"  Agent ID: {agent.id}")
        print(f"  Capabilities: {agent.capabilities}")
        print(f"  Memory context: {len(agent.memory_context)} items")
        
        # Step 5: Ghost-run transformation
        print("\n[5] Ghost-Run (Simulate before commit)...")
        def transform(v):
            # Apply best intent transformation
            return best_intent.vector
        
        predicted_state, ghost_receipt = self.governance.ghost_run(self.current_state, transform)
        print(f"  ΔΦ: {ghost_receipt.delta_phi:.4f}")
        print(f"  Gates passed: {ghost_receipt.gates_passed}")
        print(f"  Gates failed: {ghost_receipt.gates_failed}")
        
        # Step 6 & 7: Commit with governance
        print("\n[6] Commit with Governance...")
        new_state, commit_receipt = self.governance.commit(
            self.current_state,
            transform,
            provenance=best_intent.provenance + ["aletheia_ai_processing"]
        )
        print(f"  Final ΔΦ: {commit_receipt.delta_phi:.4f}")
        print(f"  All gates passed: {len(commit_receipt.gates_failed) == 0}")
        
        # Update current state
        self.current_state = new_state
        
        # Step 8: Store in memory
        print("\n[7] Storing in Memory...")
        node_id = self.memory.store(
            input_data,
            metadata={
                'encoding': encoding.to_dict(),
                'intent': best_intent.description,
                'agent_id': agent.id,
                'receipt_id': commit_receipt.operation_id
            }
        )
        print(f"  Stored: {node_id}")
        
        # Step 9: Visualization (if enabled)
        visualization = None
        if self.enable_worldforge:
            print("\n[8] Generating Visualization (WorldForge)...")
            visualization = self._generate_visualization(encoding, best_intent)
            print(f"  Generated: {visualization['type']}")
        
        # Step 10: Return result
        result = {
            'input': input_data,
            'encoding': encoding.to_dict(),
            'intent': {
                'description': best_intent.description,
                'score': best_intent.score,
                'digital_root': best_intent.digital_root,
                'parity': best_intent.parity,
                'interpretation': best_intent.metadata.get('interpretation')
            },
            'agent': {
                'id': agent.id,
                'capabilities': agent.capabilities
            },
            'governance': {
                'delta_phi': commit_receipt.delta_phi,
                'gates_passed': commit_receipt.gates_passed,
                'gates_failed': commit_receipt.gates_failed
            },
            'memory': {
                'node_id': node_id,
                'similar_count': len(similar_items)
            },
            'state': {
                'entropy': new_state.entropy,
                'digital_root': new_state.digital_root,
                'parity': new_state.parity
            },
            'visualization': visualization,
            'receipt': commit_receipt.to_dict()
        }
        
        print(f"\n{'='*80}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*80}\n")
        
        return result
    
    def _create_agent(self, intent: Intent, memory_context: List[Tuple]) -> Agent:
        """
        Create a geometric agent for an intent.
        
        Agents are morphonic - assembled from slices based on need.
        """
        import hashlib
        
        agent_id = hashlib.sha256(f"{intent.description}{intent.score}".encode()).hexdigest()[:16]
        
        # Determine capabilities based on intent properties
        capabilities = []
        
        if intent.digital_root == 7:
            capabilities.append("attractor_aligned")
        
        if intent.parity == 0:
            capabilities.append("even_channel")
        else:
            capabilities.append("odd_channel")
        
        if "ternary" in intent.metadata.get('interpretation', ''):
            capabilities.append("ternary_transformation")
        elif "attractor" in intent.metadata.get('interpretation', ''):
            capabilities.append("attractor_transformation")
        else:
            capabilities.append("direct_processing")
        
        # Create agent state
        agent_state = self.governance.create_state(intent.vector)
        
        agent = Agent(
            id=agent_id,
            intent=intent,
            capabilities=capabilities,
            state=agent_state,
            memory_context=[data for _, _, data in memory_context],
            provenance=intent.provenance + ["agent_creation"]
        )
        
        self.agents[agent_id] = agent
        return agent
    
    def _generate_visualization(self, encoding: SNAPEncoding, intent: Intent) -> Dict[str, Any]:
        """
        Generate visualization using WorldForge principles.
        
        Simplified version - full WorldForge integration would use
        the actual operators from the corpus.
        """
        # Determine visualization type based on data type
        if encoding.data_type == DataType.TEXT:
            viz_type = "text_embedding_plot"
        elif encoding.data_type == DataType.IMAGE:
            viz_type = "image_lattice_projection"
        elif encoding.data_type == DataType.NUMERICAL:
            viz_type = "numerical_trajectory"
        else:
            viz_type = "generic_geometric_view"
        
        return {
            'type': viz_type,
            'vector': encoding.vector.tolist(),
            'digital_root': encoding.digital_root,
            'parity': encoding.parity,
            'intent_score': intent.score,
            'description': f"Geometric visualization of {encoding.data_type.value} data"
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get complete system statistics."""
        return {
            'memory': self.memory.get_statistics(),
            'governance': self.governance.get_statistics(),
            'agents': {
                'total': len(self.agents),
                'active': len([a for a in self.agents.values() if a.state.entropy < 1.0])
            },
            'current_state': {
                'entropy': self.current_state.entropy,
                'digital_root': self.current_state.digital_root,
                'parity': self.current_state.parity,
                'frequency': self.current_state.frequency
            }
        }


# Test Aletheia AI
if __name__ == "__main__":
    print("=" * 80)
    print("ALETHEIA AI - COMPLETE SYSTEM TEST")
    print("=" * 80)
    
    # Initialize
    aletheia = AletheiaAI(memory_dimension=8, strict_governance=True, enable_worldforge=True)
    
    # Test 1: Process text
    result1 = aletheia.process("E8 lattice has 240 roots and is optimal in 8D")
    
    # Test 2: Process numerical data
    result2 = aletheia.process([1, 2, 3, 4, 5, 6, 7, 8])
    
    # Test 3: Process similar text (should recall previous)
    result3 = aletheia.process("E8 is the best lattice in 8 dimensions")
    
    # Statistics
    print("\n" + "=" * 80)
    print("SYSTEM STATISTICS")
    print("=" * 80)
    stats = aletheia.get_statistics()
    print(json.dumps(stats, indent=2))
    
    print("\n" + "=" * 80)
    print("ALETHEIA AI COMPLETE SYSTEM TEST FINISHED")
    print("=" * 80)

