"""
Integrated 2026-05-19T00:52:23Z from external toolkit.
Source: ``D:\Manny Unification 2\datasets from previous review\Manus dev and review\enhanced_manifold_v3.py``
"""
#!/usr/bin/env python3
"""
Enhanced Manifold v3 — CMPLX Tool Suite Integration
=====================================================

This is the production entrypoint for the CMPLX Leech Manifold system
with all 30 novel scientific tools integrated.

Changes over v2 (enhanced_manifold.py):
  1. CMPLXToolRegistry integration — all 30 tools registered as domain adapters
  2. BraidEngine integrated at graph level — manifold-to-manifold navigation
  3. tools_v3.json loaded at startup — full 30-tool axis configuration
  4. Flask API entrypoint — exposes process() and status() as HTTP endpoints
  5. Improved _auto_label() — domain-aware SNAP labeling for all 30 domains
  6. Improved conservation gate — real-time delta_phi tracking per item
  7. ManifoldGraph awareness — this instance registers itself as a node

Docker entrypoint:
  CMD: ["python3", "enhanced_manifold_v3.py", "--port", "9400"]

Environment variables:
  TOOL_CONFIG_PATH  — path to tools_v3.json (default: /config/tools_v3.json)
  LEECH_LOCK        — URL of the leech-lock service
  HINGE_CONTROLLER  — URL of the hinge-controller service
  PORT              — HTTP port for this service (default: 9400)

Pipeline (unchanged from v2, now with 30 tools):
  Input → DomainAdapter (30 tools) → AtlasCanonicalizer → SpeedLight cache →
  DR 3-6-9 route → SNAP label → CA gate check → [Percolation OR Full eval] →
  MORSR explore (sparse) → Actuator repair (degraded) → Braid navigate →
  Slice observe → Place → Receipt → Causal DAG learns
"""

import os
import sys
import json
import hashlib
import math
import time
import argparse
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, Any, Callable
from collections import defaultdict, Counter
from enum import Enum

# ── Try to import the v2 components ──────────────────────────────────────────
# In Docker, these are co-located. In development, adjust sys.path as needed.
try:
    from hinge_controller import ManifoldController, E8Hinges
    from integrated_manifold import (
        SNAPLabel, SpeedLightCache, PercolationIndex,
        MicroSwarmManager, DomainAdapterRegistry, SwarmCapsule,
    )
    from enhanced_manifold import (
        AtlasCanonicalizer, CAGate, DigitalRootRouter, PolicyOrchestrator,
        MORSRExplorer, ActuatorRepair, SliceObserver,
        ReceiptCausalDAG, ConservationAuditor,
    )
    _MANIFOLD_AVAILABLE = True
except ImportError:
    _MANIFOLD_AVAILABLE = False
    print("[WARNING] Core manifold components not found. Running in REGISTRY-ONLY mode.")
    print("          Set PYTHONPATH to include the controller directory.")

# ── Tool registry ─────────────────────────────────────────────────────────────
from cmplx.tools.manus.registry import CMPLXToolRegistry


# ============================================================
# BRAID ENGINE (from manifold_graph.py — integrated here)
# ============================================================

class BraidEngine:
    """
    Weyl word reduction for E8 Dynkin diagram navigation.

    Reduces sequences of simple reflections to canonical form using:
      σᵢσᵢ = identity          (cancellation)
      σᵢσⱼ = σⱼσᵢ              (commutation, non-adjacent)
      σᵢσⱼσᵢ = σⱼσᵢσⱼ          (braid relation, adjacent)

    Used at the graph level to compute shortest navigation paths
    between manifold nodes.
    """

    # E8 Dynkin diagram adjacency (1-indexed, standard notation)
    EDGES = {(1,3), (3,4), (4,5), (5,6), (6,7), (7,8), (2,4)}

    @classmethod
    def adjacent(cls, a: int, b: int) -> bool:
        return (min(a, b), max(a, b)) in cls.EDGES

    def reduce(self, word: List[int]) -> List[int]:
        """Reduce a Weyl group word to canonical form."""
        w = list(word)
        changed = True
        while changed:
            changed = False
            i = 0
            while i < len(w) - 1:
                a, b = w[i], w[i+1]
                if a == b:                                      # Cancel
                    del w[i:i+2]; changed = True; continue
                if not self.adjacent(a, b) and a > b:          # Commute
                    w[i], w[i+1] = b, a; changed = True; i += 1; continue
                if i + 2 < len(w) and w[i+2] == a and self.adjacent(a, b):
                    if a > b:                                   # Braid
                        w[i:i+3] = [b, a, b]; changed = True
                    i += 2; continue
                i += 1
        return w

    def path_length(self, word: List[int]) -> int:
        return len(self.reduce(word))

    def compose(self, path_a: List[int], path_b: List[int]) -> List[int]:
        return self.reduce(path_a + path_b)

    def inverse(self, word: List[int]) -> List[int]:
        return self.reduce(list(reversed(word)))

    def navigate(self, source_axes: Set[int], target_axes: Set[int]) -> List[int]:
        """
        Compute a braid word that navigates from source to target axes.

        The word is constructed from the symmetric difference of the two
        axis sets — the axes that need to be activated or deactivated.
        """
        diff = sorted(source_axes.symmetric_difference(target_axes))
        # Map global axes (0-23) to simple root indices (1-8) per rail
        word = [(ax % 8) + 1 for ax in diff]
        return self.reduce(word)


# ============================================================
# DOMAIN-AWARE SNAP LABELER
# ============================================================

# Maps domain name → (structural_tags, semantic_tags)
_DOMAIN_SNAP_TAGS: Dict[str, Tuple[Set[str], Set[str]]] = {
    'protein':            ({'structured', 'vector_8d'},   {'biomolecule', 'fold', 'dihedral'}),
    'quantum_circuit':    ({'structured', 'vector_8d'},   {'quantum', 'gate', 'lambda'}),
    'economic':           ({'structured', 'vector_8d'},   {'market', 'policy', 'phase'}),
    'drug_interaction':   ({'structured', 'vector_16d'},  {'pharmacology', 'molecule', 'collision'}),
    'genomic':            ({'structured', 'vector_16d'},  {'sequence', 'alignment', 'niemeier'}),
    'materials':          ({'structured', 'vector_8d'},   {'crystal', 'entropy', 'phase'}),
    'neural_topology':    ({'structured', 'vector_8d'},   {'neuron', 'motif', 'triadic'}),
    'climate':            ({'structured', 'vector_24d'},  {'atmosphere', 'ocean', 'leech'}),
    'rule30':             ({'structured', 'vector_5d'},   {'automaton', 'lambda', 'complexity'}),
    'emergent_stability': ({'structured', 'vector_24d'},  {'emergence', 'attractor', 'stability'}),
    'gravitational_wave': ({'structured', 'vector_8d'},   {'astrophysics', 'strain', 'morphon'}),
    'viral_mutation':     ({'structured', 'vector_8d'},   {'virology', 'codon', 'evolution'}),
    'crypto_hash':        ({'structured', 'vector_16d'},  {'cryptography', 'sha256', 'geometry'}),
    'knot_theory':        ({'structured', 'vector_6d'},   {'topology', 'writhe', 'invariant'}),
    'semantic_drift':     ({'structured', 'vector_8d'},   {'linguistics', 'drift', 'temporal'}),
    'ecosystem':          ({'structured', 'vector_14d'},  {'ecology', 'species', 'cascade'}),
    'turbulence':         ({'structured', 'vector_8d'},   {'fluid', 'velocity', 'reynolds'}),
    'prime_gap':          ({'structured', 'vector_8d'},   {'number_theory', 'prime', 'gap'}),
    'superconductor':     ({'structured', 'vector_12d'},  {'condensed_matter', 'order_parameter', 'phase'}),
    'cross_domain':       ({'structured', 'vector_24d'},  {'meta_science', 'emergence', 'universality'}),
    'quantum_biology':    ({'structured', 'vector_8d'},   {'quantum', 'biology', 'coherence'}),
    'social_network':     ({'structured', 'vector_12d'},  {'sociology', 'opinion', 'polarization'}),
    'hea_design':         ({'structured', 'vector_10d'},  {'materials', 'alloy', 'entropy'}),
    'consciousness':      ({'structured', 'vector_16d'},  {'neuroscience', 'phi', 'integration'}),
    'earthquake':         ({'structured', 'vector_12d'},  {'seismology', 'precursor', 'strain'}),
    'dark_matter':        ({'structured', 'vector_12d'},  {'astrophysics', 'halo', 'dark_matter'}),
    'ocean_acidification':({'structured', 'vector_12d'},  {'oceanography', 'pH', 'carbonate'}),
    'immune_repertoire':  ({'structured', 'vector_14d'},  {'immunology', 'vdj', 'diversity'}),
    'financial_risk':     ({'structured', 'vector_14d'},  {'finance', 'systemic_risk', 'contagion'}),
    'universal_attractor':({'structured', 'vector_24d'},  {'meta_science', 'attractor', 'universal'}),
}


# ============================================================
# ENHANCED MANIFOLD v3
# ============================================================

class EnhancedManifoldV3:
    """
    Full pipeline with all 30 CMPLX tools integrated.

    Extends EnhancedManifold v2 with:
      - CMPLXToolRegistry: all 30 domain adapters registered
      - BraidEngine: Weyl word navigation between manifold regions
      - Domain-aware SNAP labeling for all 30 scientific domains
      - Real-time delta_phi tracking per item (not just periodic audit)
      - tools_v3.json configuration for all 30 tools
    """

    def __init__(self, tool_config_path: str = '/config/tools_v3.json'):
        # ── Tool registry ──────────────────────────────────────────────────
        self.tool_registry = CMPLXToolRegistry(tool_config_path)
        self._tool_configs = self.tool_registry.get_tool_configs()

        # ── Core manifold components (if available) ────────────────────────
        if _MANIFOLD_AVAILABLE:
            self.manifold = ManifoldController()
            self.cache = SpeedLightCache()
            self.percolation = PercolationIndex(match_depth=3, min_neighbors=4, min_overlap=0.5)
            self.swarm = MicroSwarmManager()
            self.adapters = DomainAdapterRegistry()
            # Inject all 30 tool adapters into the registry
            self.tool_registry.register_all(self.adapters)

            # Enhanced v2 systems
            self.canonicalizer = AtlasCanonicalizer()
            self.ca_gate = CAGate()
            self.dr_router = DigitalRootRouter()
            self.policy = PolicyOrchestrator()
            self.morsr = MORSRExplorer()
            self.repair = ActuatorRepair()
            self.observer = SliceObserver()
            self.causal_dag = ReceiptCausalDAG()
            self.auditor = ConservationAuditor()
        else:
            # Stub mode: only registry and braid engine are active
            self.adapters = None
            self.canonicalizer = None

        # ── New v3 systems ─────────────────────────────────────────────────
        self.braid = BraidEngine()

        # ── State ──────────────────────────────────────────────────────────
        self.receipts: List[Dict] = []
        self.last_hash = "0" * 64
        self.items_processed = 0
        self.audit_interval = 100
        self.cumulative_dphi = 0.0

    # ── Receipt chain ──────────────────────────────────────────────────────

    def _receipt(self, event: str, data: Dict) -> Dict:
        r = {"timestamp": time.time(), "event": event,
             "prev_hash": self.last_hash, "data": data}
        r["hash"] = hashlib.sha256(
            json.dumps(r, sort_keys=True, default=str).encode()
        ).hexdigest()
        self.last_hash = r["hash"]
        self.receipts.append(r)
        return r

    # ── Domain-aware SNAP labeling ─────────────────────────────────────────

    def _auto_label(self, domain: str, data: Any, key: str) -> 'SNAPLabel':
        if not _MANIFOLD_AVAILABLE:
            return None

        label = SNAPLabel(item_key=key)
        label.domain.add(domain)

        # Domain-specific tags
        tags = _DOMAIN_SNAP_TAGS.get(domain, ({'structured'}, {'generic'}))
        label.structural |= tags[0]
        label.semantic |= tags[1]

        # Data-driven structural tags
        if isinstance(data, dict):
            for k in list(data.keys())[:5]:
                label.structural.add(f"field:{k}")

        label.quality.add("pending_eval")
        label.risk.add("standard")
        return label

    # ── Braid navigation ───────────────────────────────────────────────────

    def navigate(self, source_tool_id: str, target_tool_id: str) -> Dict:
        """
        Compute the braid navigation word between two tool manifold regions.

        Returns the canonical Weyl word and its length (navigation cost).
        """
        # Find required axes for each tool
        source_axes = set()
        target_axes = set()
        for tc in self._tool_configs:
            if tc['tool_id'] == source_tool_id:
                source_axes = set(tc.get('required_axes', []))
            if tc['tool_id'] == target_tool_id:
                target_axes = set(tc.get('required_axes', []))

        word = self.braid.navigate(source_axes, target_axes)
        shared = source_axes & target_axes
        coupling = len(shared) / max(len(source_axes | target_axes), 1)

        return {
            'source': source_tool_id,
            'target': target_tool_id,
            'braid_word': word,
            'braid_length': len(word),
            'shared_axes': sorted(shared),
            'coupling': coupling,
        }

    # ── Main process method ────────────────────────────────────────────────

    def process(self, domain: str, raw_data: Any,
                snap_labels: Optional['SNAPLabel'] = None) -> Dict[str, Any]:
        """
        Process a submission through the full six-stage pipeline.

        Args:
            domain: One of the 30 registered domain names (e.g. 'earthquake')
            raw_data: Domain-specific data dictionary
            snap_labels: Optional pre-computed SNAP labels

        Returns:
            Result dictionary with item_key, path, lane, leech_coords, etc.
        """
        if not _MANIFOLD_AVAILABLE:
            # Registry-only mode: just adapt and return features
            self.items_processed += 1
            features = self.tool_registry.adapt(domain, raw_data)
            item_key = hashlib.sha256(
                json.dumps(raw_data, sort_keys=True, default=str).encode()
            ).hexdigest()[:16]
            self._receipt("adapt_only", {"domain": domain, "item_key": item_key})
            return {
                "item_key": item_key,
                "domain": domain,
                "path": "registry_only",
                "features": {k: v.tolist() for k, v in features.items()},
            }

        self.items_processed += 1

        # 1. Domain adapter (using the tool registry)
        rail_features = self.adapters.adapt(domain, raw_data)

        # 2. Atlas canonicalization
        canon_key, canon_data = self.canonicalizer.canonicalize(raw_data)
        item_key = canon_key[:16]

        # 3. SpeedLight cache
        if canon_key in self.cache.mem:
            self.cache.stats['hits'] += 1
            self._receipt("cache_hit", {"item_key": item_key, "path": "speedlight"})
            self.causal_dag.record_path("speedlight", 1.0)
            return {"item_key": item_key, "path": "speedlight",
                    "result": self.cache.mem[canon_key]}
        self.cache.stats['misses'] += 1

        # 4. Digital root routing
        route = self.dr_router.route(canon_key)

        # 5. SNAP labels
        if snap_labels is None:
            snap_labels = self._auto_label(domain, raw_data, item_key)

        # 6. Leech coordinates (quick estimate)
        coords = np.concatenate([
            rail_features.get('alpha', np.zeros(8))[:8],
            rail_features.get('beta', np.zeros(8))[:8],
            rail_features.get('gamma', np.zeros(8))[:8],
        ])
        norm = np.linalg.norm(coords)
        if norm > 1e-10:
            coords = coords / norm

        # 7. Percolation check
        can_gate_perc, gate_info = self.percolation.can_gate(snap_labels, coords)

        # 8. CA dynamic gate
        should_gate, ca_reason = self.ca_gate.should_gate(coords, can_gate_perc)

        # 9. Borderline → PolicyOrchestrator
        if can_gate_perc and not should_gate:
            cell = self.ca_gate.get_cell(coords)
            policy_result = self.policy.evaluate_borderline(
                gate_info.get('mean_overlap', 0.5),
                cell['trust'], cell['gate_accuracy'],
            )
            should_gate = policy_result['adaptive_recommendation']
            ca_reason = f"policy_{policy_result['best_strategy']}"

        # 10. Execute
        if should_gate:
            path = f"gated_{ca_reason}"
            self.percolation.gated_items += 1
            self.ca_gate.update_cell(coords, True, True)
            self._receipt("gated", {"item_key": item_key, "path": path,
                                     "lane": route['lane'], "dr": route['dr'],
                                     "delta_phi": 0.0})
            self.percolation.register(item_key, snap_labels, coords)
            self.causal_dag.record_path(path, 0.9)
            result = {"item_key": item_key, "path": path, "lane": route,
                      "leech_coords": coords.tolist(), "snap_depth": snap_labels.depth}
            self.cache.mem[canon_key] = result
            return result

        # Full path
        self.percolation.full_eval_items += 1

        # 10a. MORSR explore if sparse
        morsr_probes = []
        if not can_gate_perc:
            pattern = {'creative': 'spiral', 'expansion': 'cascade',
                       'consolidation': 'ripple', 'transformative': 'chaos'
                       }.get(route['lane'], 'ripple')
            morsr_probes = self.morsr.explore(coords, radius=0.3, pattern=pattern)
            for probe in morsr_probes:
                probe_gate, _ = self.percolation.can_gate(snap_labels, probe)
                if probe_gate:
                    self._receipt("morsr_shortcut", {
                        "item_key": item_key, "pattern": pattern,
                        "probe_found_neighbor": True
                    })
                    break

        # 10b. Full manifold deployment
        manifold_report = self.manifold.deploy(rail_features, self._tool_configs)

        # 10c. Slice observables per hinge
        observables = {}
        for hinge_id, hinge in self.manifold.hinges.items():
            if hinge.projection is not None:
                observables[hinge_id] = self.observer.observe(
                    hinge.projection, hinge.root_vector
                )

        # 10d. Actuator repair for degraded hinges
        repairs_applied = 0
        for hinge_id, hinge in self.manifold.hinges.items():
            if hinge.consistency_score < 0.5 and hinge.projection is not None:
                neighbor_projs = [
                    self.manifold.hinges[nid].projection
                    for nid in hinge.neighbor_hinge_ids
                    if nid in self.manifold.hinges and
                    self.manifold.hinges[nid].projection is not None
                ]
                if neighbor_projs:
                    repaired, repair_info = self.repair.repair(
                        hinge.projection, neighbor_projs, mode='balance'
                    )
                    if repair_info['improvement'] > 0:
                        hinge.projection = repaired
                        repairs_applied += 1

        # 10e. Final Leech coordinates
        p4 = manifold_report.get("phases", {}).get("4_leech_lock", {})
        leech_coords = (np.array(p4.get("leech_coords", coords.tolist()))
                        if p4.get("status") == "LOCKED" else coords)

        # 10f. Conservation tracking (real-time ΔΦ)
        delta_phi = float(-np.linalg.norm(leech_coords - coords))  # negative = information gain
        self.cumulative_dphi += delta_phi

        # 10g. Register + receipt
        self.percolation.register(item_key, snap_labels, leech_coords)
        self.ca_gate.update_cell(leech_coords, False, True)

        self._receipt("full_eval", {
            "item_key": item_key,
            "domain": domain,
            "lane": route['lane'],
            "dr": route['dr'],
            "manifold_status": manifold_report.get("status"),
            "observables_count": len(observables),
            "repairs_applied": repairs_applied,
            "morsr_probes": len(morsr_probes),
            "delta_phi": delta_phi,
            "cumulative_dphi": self.cumulative_dphi,
        })

        self.causal_dag.record_path("full_manifold", 1.0)

        result = {
            "item_key": item_key,
            "domain": domain,
            "path": "full_manifold",
            "lane": route,
            "leech_coords": leech_coords.tolist(),
            "snap_depth": snap_labels.depth,
            "manifold_status": manifold_report.get("status"),
            "observables": {k: v for k, v in list(observables.items())[:3]},
            "repairs": repairs_applied,
            "delta_phi": delta_phi,
        }
        self.cache.mem[canon_key] = result

        # Periodic conservation audit
        if self.items_processed % self.audit_interval == 0:
            audit = self.auditor.audit(self.receipts)
            self._receipt("conservation_audit", audit)

        return result

    # ── Status ─────────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        base = {
            "version": "3.0.0",
            "items_processed": self.items_processed,
            "tools_registered": self.tool_registry.status()['total_tools'],
            "domains_registered": self.tool_registry.status()['total_domains'],
            "receipts": len(self.receipts),
            "cumulative_dphi": self.cumulative_dphi,
            "conservation_holds": self.cumulative_dphi <= 1e-10,
            "chain_intact": self._verify_chain(),
        }
        if _MANIFOLD_AVAILABLE:
            coverage = self.percolation.coverage_report()
            ca_classes = Counter()
            for cell in self.ca_gate.cells.values():
                ca_classes[cell['class'].value] += 1
            base.update({
                "percolation": coverage,
                "speedlight": self.cache.stats,
                "ca_gate_classes": dict(ca_classes),
                "ca_cells_active": len(self.ca_gate.cells),
                "dag_routing_weights": self.causal_dag.suggest_routing(),
                "swarm_active": len(self.swarm.active_capsules),
            })
        return base

    def _verify_chain(self) -> bool:
        prev = "0" * 64
        for r in self.receipts:
            if r["prev_hash"] != prev:
                return False
            prev = r["hash"]
        return True


# ============================================================
# FLASK API ENTRYPOINT
# ============================================================

def create_app(manifold: EnhancedManifoldV3):
    """Create a Flask app exposing the manifold as an HTTP service."""
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("[ERROR] Flask not installed. Run: pip install flask")
        return None

    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "healthy", "version": "3.0.0"})

    @app.route('/process', methods=['POST'])
    def process():
        body = request.get_json(force=True)
        domain = body.get('domain', 'generic')
        data = body.get('data', {})
        result = manifold.process(domain, data)
        return jsonify(result)

    @app.route('/navigate', methods=['POST'])
    def navigate():
        body = request.get_json(force=True)
        source = body.get('source_tool_id', '')
        target = body.get('target_tool_id', '')
        result = manifold.navigate(source, target)
        return jsonify(result)

    @app.route('/status', methods=['GET'])
    def status():
        return jsonify(manifold.status())

    @app.route('/tools', methods=['GET'])
    def tools():
        return jsonify({
            'tools': manifold.tool_registry.list_tools(),
            'domains': manifold.tool_registry.list_domains(),
        })

    return app


# ============================================================
# STANDALONE DEMO (no manifold components required)
# ============================================================

def demo():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   ENHANCED MANIFOLD v3 — 30-TOOL INTEGRATION DEMO           ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    m = EnhancedManifoldV3(tool_config_path='tools_v3.json')
    print(f"\n  Mode: {'FULL MANIFOLD' if _MANIFOLD_AVAILABLE else 'REGISTRY-ONLY'}")
    print(f"  Tools: {m.tool_registry.status()['total_tools']}")
    print(f"  Domains: {m.tool_registry.status()['total_domains']}")

    # Test all 30 domains
    test_cases = [
        ('protein',             {'dihedral_angles': [1.0]*8, 'residue_features': [0.5]*8, 'fold_rate': [0.1]*8}),
        ('quantum_circuit',     {'gate_sequence': [0.3]*8, 'entanglement_map': [0.7]*8, 'circuit_depth_profile': [0.2]*8}),
        ('economic',            {'market_state': [0.5]*8, 'policy_indicators': [0.2]*8, 'sentiment': [0.8]*8}),
        ('drug_interaction',    {'molecule_a_features': [0.4]*8, 'molecule_b_features': [0.6]*8, 'binding_dynamics': [0.3]*8}),
        ('genomic',             {'sequence_a': [0.1]*8, 'sequence_b': [0.9]*8, 'alignment_features': [0.5]*8}),
        ('materials',           {'local_environment': [0.3]*8, 'neighbor_shell': [0.5]*8, 'bulk_properties': [0.7]*8}),
        ('neural_topology',     {'motif_features': [0.2]*8, 'synaptic_weights': [0.8]*8, 'firing_dynamics': [0.4]*8}),
        ('climate',             {'atmospheric_state': [0.6]*8, 'ocean_land_coupling': [0.4]*8, 'temporal_derivative': [0.1]*8}),
        ('rule30',              {'reduction_paths': [0.5]*8, 'rule_encoding': [0.3]*8, 'temporal_step': [0.7]*8}),
        ('emergent_stability',  {'local_stability': [0.9]*8, 'meso_interactions': [0.5]*8, 'global_attractor': [0.1]*8}),
        ('gravitational_wave',  {'strain_signal': [0.01]*8, 'source_parameters': [0.5]*8, 'frequency_profile': [0.3]*8}),
        ('viral_mutation',      {'codon_features': [0.4]*8, 'protein_impact': [0.6]*8, 'evolutionary_rate': [0.2]*8}),
        ('crypto_hash',         {'input_block': [0.5]*8, 'output_block': [0.7]*8, 'avalanche_profile': [0.9]*8}),
        ('knot_theory',         {'gauss_code_writhe': [0.3]*8, 'crossing_signs': [0.7]*8, 'knot_invariants': [0.5]*8}),
        ('semantic_drift',      {'word_context': [0.4]*8, 'semantic_neighbourhood': [0.6]*8, 'temporal_drift': [0.2]*8}),
        ('ecosystem',           {'species_interactions': [0.5]*8, 'resource_flow': [0.3]*8, 'seasonal_dynamics': [0.7]*8}),
        ('turbulence',          {'velocity_gradient': [0.8]*8, 'pressure_field': [0.4]*8, 'time_derivative': [0.2]*8}),
        ('prime_gap',           {'prime_sequence': [2,3,5,7,11,13,17,19], 'gap_statistics': [1,2,2,4,2,4,2,4], 'modular_structure': [0.5]*8}),
        ('superconductor',      {'order_parameter': [0.9]*8, 'crystal_structure': [0.5]*8, 'thermodynamic_state': [0.1]*8}),
        ('cross_domain',        {'domain_a_features': [0.3]*8, 'domain_b_features': [0.7]*8, 'cross_domain_delta': [0.4]*8}),
        ('quantum_biology',     {'quantum_state_vector': [0.5]*8, 'environment_coupling': [0.3]*8, 'decoherence_rates': [0.1]*8}),
        ('social_network',      {'opinion_distribution': [0.2]*8, 'network_topology_metrics': [0.6]*8, 'opinion_velocity': [0.4]*8}),
        ('hea_design',          {'elemental_composition': [0.2,0.2,0.2,0.2,0.2,0,0,0], 'lattice_configuration': [1,0,0,0.1,0,0,0,0], 'thermodynamic_indicators': [0.5]*8}),
        ('consciousness',       {'neural_synchrony': [0.7]*8, 'phi_decomposition': [0.4]*8, 'global_workspace': [0.6]*8}),
        ('earthquake',          {'seismic_wave_features': [0.3]*8, 'geodetic_strain_tensor': [0.1]*8, 'temporal_precursor_features': [0.05]*8}),
        ('dark_matter',         {'halo_density_profile': [0.5]*8, 'particle_interaction_model': [0.3]*8, 'observational_signatures': [0.1]*8}),
        ('ocean_acidification', {'chemical_state': [8.1,400,1.5,2100,2300,15,35,5], 'biological_impact': [0.3]*8, 'temporal_trends': [0.05]*8}),
        ('immune_repertoire',   {'vdj_segment_usage': [0.2]*8, 'diversity_metrics': [0.7]*8, 'response_dynamics': [0.5]*8}),
        ('financial_risk',      {'network_topology': [0.6]*8, 'asset_correlations': [0.8]*8, 'contagion_dynamics': [0.4]*8}),
        ('universal_attractor', {'structural_features': [0.5]*8, 'cross_domain_coupling': [0.3]*8, 'temporal_features': [0.2]*8}),
    ]

    print(f"\n{'─'*60}")
    print(f"  {'Domain':<22} {'Path':<20} {'Key':<18}")
    print(f"{'─'*60}")

    for domain, data in test_cases:
        r = m.process(domain, data)
        key = r.get('item_key', '?')[:16]
        path = r.get('path', '?')[:18]
        print(f"  {domain:<22} {path:<20} {key}")

    # Braid navigation demo
    print(f"\n{'─'*60}")
    print("  BRAID NAVIGATION DEMO")
    print(f"{'─'*60}")
    nav_pairs = [
        ('T01_protein_fold_morphon', 'T04_morphon_collision_drug'),
        ('T08_leech_48d_climate',    'T10_emergent_stability_classifier'),
        ('T25_earthquake_precursors', 'T29_financial_systemic_risk'),
        ('T11_gravitational_wave_morphon', 'T26_dark_matter_detection'),
    ]
    for src, tgt in nav_pairs:
        nav = m.navigate(src, tgt)
        print(f"  {src.split('_')[0]:>4} → {tgt.split('_')[0]:<4}  "
              f"braid_len={nav['braid_length']:2d}  "
              f"coupling={nav['coupling']:.2f}  "
              f"shared={len(nav['shared_axes'])} axes")

    # Status
    print(f"\n{'─'*60}")
    print("  SYSTEM STATUS")
    print(f"{'─'*60}")
    s = m.status()
    print(f"  Version:        {s['version']}")
    print(f"  Items:          {s['items_processed']}")
    print(f"  Tools:          {s['tools_registered']}")
    print(f"  Receipts:       {s['receipts']}")
    print(f"  Chain intact:   {s['chain_intact']}")
    print(f"  ΔΦ cumulative:  {s['cumulative_dphi']:.6f}")
    print(f"  Conservation:   {'✓ holds' if s['conservation_holds'] else '✗ violated'}")


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Enhanced Manifold v3 — CMPLX Tool Suite')
    parser.add_argument('--port', type=int, default=9400, help='HTTP port')
    parser.add_argument('--config', default=os.environ.get('TOOL_CONFIG_PATH', 'tools_v3.json'),
                        help='Path to tools_v3.json')
    parser.add_argument('--demo', action='store_true', help='Run demo and exit')
    parser.add_argument('--serve', action='store_true', help='Start HTTP server')
    args = parser.parse_args()

    if args.demo or (not args.serve):
        demo()

    if args.serve:
        manifold = EnhancedManifoldV3(tool_config_path=args.config)
        app = create_app(manifold)
        if app:
            print(f"\n[EnhancedManifoldV3] Starting HTTP server on port {args.port}")
            app.run(host='0.0.0.0', port=args.port, debug=False)
