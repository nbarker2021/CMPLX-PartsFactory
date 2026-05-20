"""
Integrated 2026-05-19T00:52:23Z from external toolkit.
Source: ``D:\Manny Unification 2\datasets from previous review\Manus dev and review\cmplx_tool_registry.py``
"""
#!/usr/bin/env python3
"""
CMPLX Tool Registry — v3.0.0
==============================

Unified domain adapter registry for all 30 CMPLX novel scientific tools.

Each adapter converts domain-specific raw data into the three-rail E8
feature vector format required by the EnhancedManifold pipeline:

    {'alpha': np.ndarray(8), 'beta': np.ndarray(8), 'gamma': np.ndarray(8)}

Rail semantics:
    alpha  (dims  0-7):  Primary structure / spatial encoding
    beta   (dims  8-15): Interaction context / relational encoding
    gamma  (dims 16-23): Temporal dynamics / derivative encoding

Usage:
    from cmplx_tool_registry import CMPLXToolRegistry
    registry = CMPLXToolRegistry()
    registry.register_all(domain_adapter_registry)

Architecture:
    This module is the bridge between the 30 CMPLX novel tools (Batches 1-3)
    and the EnhancedManifold v2 deployment system. It implements the
    SUBMIT stage's domain adapter layer for all scientific domains.

    Tools 1-10:  Batch 1 — Biochemistry, Quantum, Economics, Pharmacology,
                            Genomics, Materials, Neuroscience, Climate,
                            Complexity, Complex Systems
    Tools 11-20: Batch 2 — Astrophysics, Virology, Cryptography, Topology,
                            Linguistics, Ecology, Fluid Dynamics, Number Theory,
                            Condensed Matter, Meta-Science
    Tools 21-30: Batch 3 — Quantum Biology, Sociology, Materials (HEA),
                            Neuroscience (Consciousness), Seismology, Astrophysics
                            (Dark Matter), Oceanography, Immunology, Finance,
                            Meta-Science (Universal Attractors)
"""

import json
import math
import hashlib
import numpy as np
from typing import Dict, Any, Callable, List, Optional
from pathlib import Path


# ============================================================
# UTILITY: Normalise an arbitrary list to a fixed-length
# 8D float array. Used by all adapters.
# ============================================================

def _to8(values: Any, scale: float = 1.0) -> np.ndarray:
    """Convert any numeric iterable to a normalised 8D float array."""
    arr = np.array(values, dtype=float).ravel()
    if len(arr) < 8:
        arr = np.pad(arr, (0, 8 - len(arr)))
    else:
        arr = arr[:8]
    if scale != 1.0:
        arr = arr / scale
    return arr


def _hash_to_8d(text: str) -> np.ndarray:
    """Convert a string to a deterministic 8D float array via SHA-256."""
    h = hashlib.sha256(text.encode()).digest()
    return np.frombuffer(h[:8], dtype=np.uint8).astype(float) / 255.0


# ============================================================
# BATCH 1 — TOOLS 1-10
# ============================================================

def _t01_protein_fold_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T01 ProteinFoldMorphon — Biochemistry
    α: dihedral angles (phi/psi), β: residue pair interactions, γ: fold rate
    """
    phi_psi = _to8(data.get('dihedral_angles', [0]*8), scale=180.0)
    residues = _to8(data.get('residue_features', [0]*8))
    dynamics = _to8(data.get('fold_rate', [0]*8))
    return {'alpha': phi_psi, 'beta': residues, 'gamma': dynamics}


def _t02_quantum_circuit_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T02 QuantumCircuitLambdaReducer — Quantum Computing
    α: full gate encoding (all 8 axes for lambda normal form)
    β: qubit entanglement structure, γ: circuit depth / temporal
    """
    gate_enc = _to8(data.get('gate_sequence', [0]*8))
    entangle = _to8(data.get('entanglement_map', [0]*8))
    depth_ts = _to8(data.get('circuit_depth_profile', [0]*8))
    return {'alpha': gate_enc, 'beta': entangle, 'gamma': depth_ts}


def _t03_economic_phase_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T03 EconomicPhaseBoundaryDetector — Economics
    α: market state, β: policy indicators, γ: sentiment dynamics
    """
    market = _to8(data.get('market_state', [0]*8))
    policy = _to8(data.get('policy_indicators', [0]*8))
    sentiment = _to8(data.get('sentiment', [0]*8))
    return {'alpha': market, 'beta': policy, 'gamma': sentiment}


def _t04_drug_interaction_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T04 MorphonCollisionDrugInteraction — Pharmacology
    α: molecule A E8 encoding, β: molecule B E8 encoding, γ: binding dynamics
    """
    mol_a = _to8(data.get('molecule_a_features', [0]*8))
    mol_b = _to8(data.get('molecule_b_features', [0]*8))
    binding = _to8(data.get('binding_dynamics', [0]*8))
    return {'alpha': mol_a, 'beta': mol_b, 'gamma': binding}


def _t05_genomic_aligner_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T05 NiemeierLatticeGenomicAligner — Genomics
    α: sequence A encoding, β: sequence B encoding, γ: alignment features
    """
    seq_a = _to8(data.get('sequence_a', [0]*8))
    seq_b = _to8(data.get('sequence_b', [0]*8))
    align = _to8(data.get('alignment_features', [0]*8))
    return {'alpha': seq_a, 'beta': seq_b, 'gamma': align}


def _t06_materials_entropy_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T06 MultiScaleEntropyMaterialsClassifier — Materials Science
    α: local atomic environment, β: neighbor shell, γ: bulk properties
    """
    local = _to8(data.get('local_environment', [0]*8))
    shell = _to8(data.get('neighbor_shell', [0]*8))
    bulk = _to8(data.get('bulk_properties', [0]*8))
    return {'alpha': local, 'beta': shell, 'gamma': bulk}


def _t07_neural_topology_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T07 TriadicBondNeuralTopologyDetector — Neuroscience
    α: 3-neuron motif encodings, β: synaptic weight matrix slice, γ: firing dynamics
    """
    motifs = _to8(data.get('motif_features', [0]*8))
    weights = _to8(data.get('synaptic_weights', [0]*8))
    firing = _to8(data.get('firing_dynamics', [0]*8))
    return {'alpha': motifs, 'beta': weights, 'gamma': firing}


def _t08_climate_state_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T08 Leech48DClimateStateEmbedder — Climate Science
    α: atmospheric state, β: ocean-land coupling, γ: temporal derivative
    """
    atmos = _to8(data.get('atmospheric_state', [0]*8))
    ocean = _to8(data.get('ocean_land_coupling', [0]*8))
    temporal = _to8(data.get('temporal_derivative', [0]*8))
    return {'alpha': atmos, 'beta': ocean, 'gamma': temporal}


def _t09_rule30_lambda_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T09 Rule30LambdaShortcutEngine — Complexity Theory
    α: three reduction path encodings, β: rule encoding, γ: temporal step
    """
    paths = _to8(data.get('reduction_paths', [0]*8))
    rule = _to8(data.get('rule_encoding', [0]*8))
    step = _to8(data.get('temporal_step', [0]*8))
    return {'alpha': paths, 'beta': rule, 'gamma': step}


def _t10_emergent_stability_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T10 EmergentStabilityClassifier — Complex Systems
    α: local stability features, β: meso-scale interactions, γ: global attractor
    """
    local = _to8(data.get('local_stability', [0]*8))
    meso = _to8(data.get('meso_interactions', [0]*8))
    global_attr = _to8(data.get('global_attractor', [0]*8))
    return {'alpha': local, 'beta': meso, 'gamma': global_attr}


# ============================================================
# BATCH 2 — TOOLS 11-20
# ============================================================

def _t11_gravitational_wave_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T11 GravitationalWaveMorphon — Astrophysics
    α: strain signal E8 projection, β: source parameters, γ: temporal frequency
    """
    strain = _to8(data.get('strain_signal', [0]*8))
    source = _to8(data.get('source_parameters', [0]*8))
    freq = _to8(data.get('frequency_profile', [0]*8))
    return {'alpha': strain, 'beta': source, 'gamma': freq}


def _t12_viral_mutation_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T12 ViralMutationPathwayPredictor — Virology
    α: codon encoding, β: protein structure impact, γ: evolutionary rate
    """
    codon = _to8(data.get('codon_features', [0]*8))
    protein = _to8(data.get('protein_impact', [0]*8))
    evo_rate = _to8(data.get('evolutionary_rate', [0]*8))
    return {'alpha': codon, 'beta': protein, 'gamma': evo_rate}


def _t13_crypto_hash_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T13 CryptographicHashGeometer — Cryptography
    α: input block encoding, β: output block encoding, γ: avalanche dynamics
    """
    input_block = _to8(data.get('input_block', [0]*8))
    output_block = _to8(data.get('output_block', [0]*8))
    avalanche = _to8(data.get('avalanche_profile', [0]*8))
    return {'alpha': input_block, 'beta': output_block, 'gamma': avalanche}


def _t14_knot_invariant_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T14 KnotInvariantMorphonClassifier — Topology
    α: Gauss code writhe encoding, β: crossing sign pairs, γ: invariant dynamics
    """
    writhe = _to8(data.get('gauss_code_writhe', [0]*8))
    crossings = _to8(data.get('crossing_signs', [0]*8))
    invariants = _to8(data.get('knot_invariants', [0]*8))
    return {'alpha': writhe, 'beta': crossings, 'gamma': invariants}


def _t15_semantic_drift_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T15 SemanticDriftMorphonTracker — Linguistics
    α: word context encoding, β: semantic neighbourhood, γ: temporal drift
    """
    context = _to8(data.get('word_context', [0]*8))
    neighbourhood = _to8(data.get('semantic_neighbourhood', [0]*8))
    drift = _to8(data.get('temporal_drift', [0]*8))
    return {'alpha': context, 'beta': neighbourhood, 'gamma': drift}


def _t16_ecosystem_cascade_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T16 EcosystemCascadePredictor — Ecology
    α: species interaction matrix, β: resource flow encoding, γ: seasonal dynamics
    """
    species = _to8(data.get('species_interactions', [0]*8))
    resources = _to8(data.get('resource_flow', [0]*8))
    seasonal = _to8(data.get('seasonal_dynamics', [0]*8))
    return {'alpha': species, 'beta': resources, 'gamma': seasonal}


def _t17_turbulence_onset_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T17 TurbulenceOnsetDetector — Fluid Dynamics
    α: velocity gradient tensor, β: pressure field, γ: temporal derivative
    """
    vel_grad = _to8(data.get('velocity_gradient', [0]*8))
    pressure = _to8(data.get('pressure_field', [0]*8))
    temporal = _to8(data.get('time_derivative', [0]*8))
    return {'alpha': vel_grad, 'beta': pressure, 'gamma': temporal}


def _t18_prime_gap_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T18 PrimeGapMorphonPredictor — Number Theory
    α: prime sequence encoding (full rail), β: gap statistics, γ: modular structure
    """
    primes = _to8(data.get('prime_sequence', [0]*8))
    gaps = _to8(data.get('gap_statistics', [0]*8))
    modular = _to8(data.get('modular_structure', [0]*8))
    return {'alpha': primes, 'beta': gaps, 'gamma': modular}


def _t19_superconductor_phase_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T19 SuperconductorPhaseClassifier — Condensed Matter
    α: order parameter E8 encoding, β: crystal structure, γ: temperature/field dynamics
    """
    order_param = _to8(data.get('order_parameter', [0]*8))
    crystal = _to8(data.get('crystal_structure', [0]*8))
    thermo = _to8(data.get('thermodynamic_state', [0]*8))
    return {'alpha': order_param, 'beta': crystal, 'gamma': thermo}


def _t20_cross_domain_emergence_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T20 CrossDomainEmergenceDetector — Meta-Science
    α: domain A geometric fingerprint, β: domain B fingerprint, γ: cross-domain delta
    """
    domain_a = _to8(data.get('domain_a_features', [0]*8))
    domain_b = _to8(data.get('domain_b_features', [0]*8))
    delta = _to8(data.get('cross_domain_delta', [0]*8))
    return {'alpha': domain_a, 'beta': domain_b, 'gamma': delta}


# ============================================================
# BATCH 3 — TOOLS 21-30
# ============================================================

def _t21_quantum_biology_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T21 QuantumBiologyCoherence — Quantum Biology
    α: quantum state vector (density matrix diagonal), β: biological environment
       coupling (phonon bath modes), γ: decoherence rate profile
    """
    qstate = _to8(data.get('quantum_state_vector', [0]*8))
    env_coupling = _to8(data.get('environment_coupling', [0]*8))
    decoherence = _to8(data.get('decoherence_rates', [0]*8))
    return {'alpha': qstate, 'beta': env_coupling, 'gamma': decoherence}


def _t22_social_polarization_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T22 SocialNetworkPolarization — Sociology
    α: agent opinion distribution (8-bin histogram), β: network topology metrics
       (degree, clustering, betweenness, etc.), γ: opinion velocity over time
    """
    opinions = _to8(data.get('opinion_distribution', [0]*8))
    topology = _to8(data.get('network_topology_metrics', [0]*8))
    velocity = _to8(data.get('opinion_velocity', [0]*8))
    return {'alpha': opinions, 'beta': topology, 'gamma': velocity}


def _t23_hea_design_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T23 HighEntropyAlloyDesigner — Materials Science (HEA)
    α: elemental composition vector (molar fractions of 5+ elements padded to 8),
    β: lattice configuration (FCC/BCC/HCP indicators + distortion), γ: thermodynamic
       stability indicators (mixing enthalpy, entropy, VEC)
    """
    composition = _to8(data.get('elemental_composition', [0]*8))
    lattice = _to8(data.get('lattice_configuration', [0]*8))
    thermo = _to8(data.get('thermodynamic_indicators', [0]*8))
    return {'alpha': composition, 'beta': lattice, 'gamma': thermo}


def _t24_consciousness_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T24 ConsciousnessIntegrationMapper — Neuroscience (Consciousness)
    α: neural synchrony patterns (8 frequency bands), β: integrated information
       complexity (Phi decomposition, 8 components), γ: global workspace dynamics
    """
    synchrony = _to8(data.get('neural_synchrony', [0]*8))
    phi = _to8(data.get('phi_decomposition', [0]*8))
    workspace = _to8(data.get('global_workspace', [0]*8))
    return {'alpha': synchrony, 'beta': phi, 'gamma': workspace}


def _t25_earthquake_precursor_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T25 EarthquakePrecursorDetector — Seismology
    α: seismic wave features (P/S wave amplitudes, frequency content),
    β: geodetic strain tensor (8 independent components), γ: long-term temporal
       patterns (radon anomalies, ionospheric TEC, groundwater level)
    """
    wave_features = _to8(data.get('seismic_wave_features', [0]*8))
    strain_tensor = _to8(data.get('geodetic_strain_tensor', [0]*8))
    temporal = _to8(data.get('temporal_precursor_features', [0]*8))
    return {'alpha': wave_features, 'beta': strain_tensor, 'gamma': temporal}


def _t26_dark_matter_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T26 DarkMatterHaloClassifier — Astrophysics (Dark Matter)
    α: halo density profile (NFW fit parameters + shape), β: particle interaction
       model (cross-section, mass, spin), γ: observational signatures (rotation
       curve, lensing, gamma-ray flux)
    """
    density_profile = _to8(data.get('halo_density_profile', [0]*8))
    particle_model = _to8(data.get('particle_interaction_model', [0]*8))
    observations = _to8(data.get('observational_signatures', [0]*8))
    return {'alpha': density_profile, 'beta': particle_model, 'gamma': observations}


def _t27_ocean_acidification_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T27 OceanAcidificationRegimeDetector — Oceanography
    α: chemical state (pH, pCO2, aragonite saturation, DIC, alkalinity, T, S, O2),
    β: biological impact (calcification rates, shell dissolution, species stress),
    γ: temporal trend features (rate of change, seasonal cycle amplitude, anomaly)
    """
    chem_state = _to8(data.get('chemical_state', [0]*8))
    bio_impact = _to8(data.get('biological_impact', [0]*8))
    temporal = _to8(data.get('temporal_trends', [0]*8))
    return {'alpha': chem_state, 'beta': bio_impact, 'gamma': temporal}


def _t28_immune_repertoire_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T28 ImmuneRepertoireClassifier — Immunology
    α: V(D)J segment usage frequencies (8 dominant segments), β: clonal diversity
       and entropy metrics (Shannon entropy, clonality, richness, evenness, etc.),
    γ: temporal response dynamics (expansion rate, contraction, memory formation)
    """
    vdj_usage = _to8(data.get('vdj_segment_usage', [0]*8))
    diversity = _to8(data.get('diversity_metrics', [0]*8))
    dynamics = _to8(data.get('response_dynamics', [0]*8))
    return {'alpha': vdj_usage, 'beta': diversity, 'gamma': dynamics}


def _t29_financial_risk_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T29 FinancialSystemicRiskDetector — Finance
    α: inter-bank network topology (degree, centrality, clustering, etc.),
    β: asset correlation matrix (8 principal components of the correlation matrix),
    γ: contagion dynamics (default probability, leverage, liquidity, VaR, etc.)
    """
    network_topo = _to8(data.get('network_topology', [0]*8))
    asset_corr = _to8(data.get('asset_correlations', [0]*8))
    contagion = _to8(data.get('contagion_dynamics', [0]*8))
    return {'alpha': network_topo, 'beta': asset_corr, 'gamma': contagion}


def _t30_universal_attractor_adapter(data: Dict) -> Dict[str, np.ndarray]:
    """
    T30 UniversalAttractorMapper — Meta-Science
    α: domain-agnostic structural features (E8 root distribution, DR histogram),
    β: cross-domain coupling features (shared root counts, Niemeier scores),
    γ: temporal/evolutionary features (attractor stability, basin depth, drift)
    """
    structural = _to8(data.get('structural_features', [0]*8))
    coupling = _to8(data.get('cross_domain_coupling', [0]*8))
    temporal = _to8(data.get('temporal_features', [0]*8))
    return {'alpha': structural, 'beta': coupling, 'gamma': temporal}


# ============================================================
# REGISTRY CLASS
# ============================================================

# Map from tool_id → adapter function
_ADAPTER_MAP: Dict[str, Callable] = {
    # Batch 1
    'T01_protein_fold_morphon':       _t01_protein_fold_adapter,
    'T02_quantum_circuit_lambda':     _t02_quantum_circuit_adapter,
    'T03_economic_phase_boundary':    _t03_economic_phase_adapter,
    'T04_morphon_collision_drug':     _t04_drug_interaction_adapter,
    'T05_niemeier_genomic_aligner':   _t05_genomic_aligner_adapter,
    'T06_multiscale_entropy_materials': _t06_materials_entropy_adapter,
    'T07_triadic_bond_neural':        _t07_neural_topology_adapter,
    'T08_leech_48d_climate':          _t08_climate_state_adapter,
    'T09_rule30_lambda_shortcut':     _t09_rule30_lambda_adapter,
    'T10_emergent_stability_classifier': _t10_emergent_stability_adapter,
    # Batch 2
    'T11_gravitational_wave_morphon': _t11_gravitational_wave_adapter,
    'T12_viral_mutation_pathway':     _t12_viral_mutation_adapter,
    'T13_cryptographic_hash_geometer': _t13_crypto_hash_adapter,
    'T14_knot_invariant_morphon':     _t14_knot_invariant_adapter,
    'T15_semantic_drift_tracker':     _t15_semantic_drift_adapter,
    'T16_ecosystem_cascade_predictor': _t16_ecosystem_cascade_adapter,
    'T17_turbulence_onset_detector':  _t17_turbulence_onset_adapter,
    'T18_prime_gap_morphon':          _t18_prime_gap_adapter,
    'T19_superconductor_phase':       _t19_superconductor_phase_adapter,
    'T20_cross_domain_emergence':     _t20_cross_domain_emergence_adapter,
    # Batch 3
    'T21_quantum_biology_coherence':  _t21_quantum_biology_adapter,
    'T22_social_network_polarization': _t22_social_polarization_adapter,
    'T23_hea_design':                 _t23_hea_design_adapter,
    'T24_consciousness_integration':  _t24_consciousness_adapter,
    'T25_earthquake_precursors':      _t25_earthquake_precursor_adapter,
    'T26_dark_matter_detection':      _t26_dark_matter_adapter,
    'T27_ocean_acidification':        _t27_ocean_acidification_adapter,
    'T28_immune_repertoire_analysis': _t28_immune_repertoire_adapter,
    'T29_financial_systemic_risk':    _t29_financial_risk_adapter,
    'T30_universal_attractor_mapping': _t30_universal_attractor_adapter,
}

# Map from domain name (used in EnhancedManifold.process()) → adapter function
# These are the short-form domain keys that the DomainAdapterRegistry uses.
_DOMAIN_MAP: Dict[str, Callable] = {
    # Batch 1
    'protein':            _t01_protein_fold_adapter,
    'quantum_circuit':    _t02_quantum_circuit_adapter,
    'economic':           _t03_economic_phase_adapter,
    'drug_interaction':   _t04_drug_interaction_adapter,
    'genomic':            _t05_genomic_aligner_adapter,
    'materials':          _t06_materials_entropy_adapter,
    'neural_topology':    _t07_neural_topology_adapter,
    'climate':            _t08_climate_state_adapter,
    'rule30':             _t09_rule30_lambda_adapter,
    'emergent_stability': _t10_emergent_stability_adapter,
    # Batch 2
    'gravitational_wave': _t11_gravitational_wave_adapter,
    'viral_mutation':     _t12_viral_mutation_adapter,
    'crypto_hash':        _t13_crypto_hash_adapter,
    'knot_theory':        _t14_knot_invariant_adapter,
    'semantic_drift':     _t15_semantic_drift_adapter,
    'ecosystem':          _t16_ecosystem_cascade_adapter,
    'turbulence':         _t17_turbulence_onset_adapter,
    'prime_gap':          _t18_prime_gap_adapter,
    'superconductor':     _t19_superconductor_phase_adapter,
    'cross_domain':       _t20_cross_domain_emergence_adapter,
    # Batch 3
    'quantum_biology':    _t21_quantum_biology_adapter,
    'social_network':     _t22_social_polarization_adapter,
    'hea_design':         _t23_hea_design_adapter,
    'consciousness':      _t24_consciousness_adapter,
    'earthquake':         _t25_earthquake_precursor_adapter,
    'dark_matter':        _t26_dark_matter_adapter,
    'ocean_acidification': _t27_ocean_acidification_adapter,
    'immune_repertoire':  _t28_immune_repertoire_adapter,
    'financial_risk':     _t29_financial_risk_adapter,
    'universal_attractor': _t30_universal_attractor_adapter,
}


class CMPLXToolRegistry:
    """
    Unified registry for all 30 CMPLX novel scientific tool adapters.

    Provides two integration modes:
      1. register_all(domain_adapter_registry): Inject all adapters into
         an existing DomainAdapterRegistry instance.
      2. adapt(tool_id_or_domain, data): Direct adapter call by tool ID
         or domain name.
    """

    def __init__(self, tool_config_path: Optional[str] = None):
        self._adapters_by_id = _ADAPTER_MAP.copy()
        self._adapters_by_domain = _DOMAIN_MAP.copy()
        self._tool_configs: List[Dict] = []

        if tool_config_path:
            self._load_tool_configs(tool_config_path)

    def _load_tool_configs(self, path: str):
        """Load tool configurations from a JSON file."""
        p = Path(path)
        if p.exists():
            with open(p) as f:
                data = json.load(f)
            self._tool_configs = data.get('tools', [])
        else:
            print(f"[CMPLXToolRegistry] Warning: tool config not found at {path}")

    def register_all(self, domain_adapter_registry):
        """
        Inject all 30 domain adapters into an existing DomainAdapterRegistry.

        Args:
            domain_adapter_registry: An instance of DomainAdapterRegistry
                                     from integrated_manifold.py
        """
        for domain_key, adapter_fn in self._adapters_by_domain.items():
            domain_adapter_registry.adapters[domain_key] = adapter_fn
        print(f"[CMPLXToolRegistry] Registered {len(self._adapters_by_domain)} domain adapters.")

    def adapt(self, key: str, data: Dict) -> Dict[str, np.ndarray]:
        """
        Adapt raw data using the adapter for the given tool_id or domain name.

        Args:
            key: Either a tool_id (e.g. 'T25_earthquake_precursors') or
                 a domain name (e.g. 'earthquake')
            data: Raw input data dictionary

        Returns:
            {'alpha': np.ndarray(8), 'beta': np.ndarray(8), 'gamma': np.ndarray(8)}
        """
        fn = self._adapters_by_id.get(key) or self._adapters_by_domain.get(key)
        if fn is None:
            # Fallback: generic adapter
            features = np.array(data.get('features', [0]*24)[:24], dtype=float)
            return {
                'alpha': features[:8],
                'beta': features[8:16] if len(features) > 8 else np.zeros(8),
                'gamma': features[16:24] if len(features) > 16 else np.zeros(8),
            }
        return fn(data)

    def get_tool_configs(self) -> List[Dict]:
        """Return the list of tool configurations for use in EnhancedManifold."""
        return self._tool_configs

    def list_tools(self) -> List[str]:
        """Return all registered tool IDs."""
        return sorted(self._adapters_by_id.keys())

    def list_domains(self) -> List[str]:
        """Return all registered domain names."""
        return sorted(self._adapters_by_domain.keys())

    def status(self) -> Dict:
        """Return registry status summary."""
        return {
            'total_tools': len(self._adapters_by_id),
            'total_domains': len(self._adapters_by_domain),
            'tool_configs_loaded': len(self._tool_configs),
            'tools': self.list_tools(),
        }


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   CMPLX Tool Registry v3.0.0 — Self-Test                    ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    registry = CMPLXToolRegistry()
    print(f"\n  Tools registered: {registry.status()['total_tools']}")
    print(f"  Domains registered: {registry.status()['total_domains']}")

    # Test each adapter with synthetic data
    test_data = {k: list(np.random.randn(8)) for k in [
        'dihedral_angles', 'residue_features', 'fold_rate',
        'gate_sequence', 'entanglement_map', 'circuit_depth_profile',
        'market_state', 'policy_indicators', 'sentiment',
        'molecule_a_features', 'molecule_b_features', 'binding_dynamics',
        'sequence_a', 'sequence_b', 'alignment_features',
        'local_environment', 'neighbor_shell', 'bulk_properties',
        'motif_features', 'synaptic_weights', 'firing_dynamics',
        'atmospheric_state', 'ocean_land_coupling', 'temporal_derivative',
        'reduction_paths', 'rule_encoding', 'temporal_step',
        'local_stability', 'meso_interactions', 'global_attractor',
        'strain_signal', 'source_parameters', 'frequency_profile',
        'codon_features', 'protein_impact', 'evolutionary_rate',
        'input_block', 'output_block', 'avalanche_profile',
        'gauss_code_writhe', 'crossing_signs', 'knot_invariants',
        'word_context', 'semantic_neighbourhood', 'temporal_drift',
        'species_interactions', 'resource_flow', 'seasonal_dynamics',
        'velocity_gradient', 'pressure_field', 'time_derivative',
        'prime_sequence', 'gap_statistics', 'modular_structure',
        'order_parameter', 'crystal_structure', 'thermodynamic_state',
        'domain_a_features', 'domain_b_features', 'cross_domain_delta',
        'quantum_state_vector', 'environment_coupling', 'decoherence_rates',
        'opinion_distribution', 'network_topology_metrics', 'opinion_velocity',
        'elemental_composition', 'lattice_configuration', 'thermodynamic_indicators',
        'neural_synchrony', 'phi_decomposition', 'global_workspace',
        'seismic_wave_features', 'geodetic_strain_tensor', 'temporal_precursor_features',
        'halo_density_profile', 'particle_interaction_model', 'observational_signatures',
        'chemical_state', 'biological_impact', 'temporal_trends',
        'vdj_segment_usage', 'diversity_metrics', 'response_dynamics',
        'network_topology', 'asset_correlations', 'contagion_dynamics',
        'structural_features', 'cross_domain_coupling', 'temporal_features',
    ]}

    all_pass = True
    for tool_id, fn in sorted(_ADAPTER_MAP.items()):
        result = fn(test_data)
        ok = (
            isinstance(result, dict) and
            set(result.keys()) == {'alpha', 'beta', 'gamma'} and
            all(isinstance(v, np.ndarray) and v.shape == (8,) for v in result.values())
        )
        if not ok:
            print(f"  FAIL: {tool_id}")
            all_pass = False

    if all_pass:
        print(f"\n  All {len(_ADAPTER_MAP)} adapters: PASS ✓")
    else:
        print(f"\n  Some adapters FAILED ✗")
