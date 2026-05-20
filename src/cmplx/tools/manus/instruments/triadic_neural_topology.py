"""
Integrated 2026-05-19T00:52:23Z from external toolkit.
Source: ``D:\Manny Unification 2\datasets from previous review\Manus dev and review\triadic_neural_topology.py``
"""
#!/usr/bin/env python3
"""
TOOL 7: TriadicBondNeuralTopologyDetector
==========================================
Layer:  Global (full-experiment triadic bond — terminal Morphon)
Field:  Computational Neuroscience / Connectomics
Author: Nicholas Barker & Manus AI, 2026

PROBLEM SOLVED
--------------
Neural connectome analysis identifies pairwise connections (edges) and
community structure (modules), but has no principled tool for detecting
*triadic bond configurations* — three-neuron motifs where the interaction
between any two is fundamentally altered by the presence of the third.
These are the computational units of working memory and attention, but
current graph-theoretic tools treat them as ordinary triangles.

NOVEL CONTRIBUTION
------------------
Each neuron's firing pattern (a time series of spike rates) is encoded as
an E8 root. Three neurons form a Triadic Bond if and only if:
  1. Their pairwise collision Morphons all have the same digital root.
  2. The three-way collision Morphon (the "global terminal") has a DR that
     is the digital root of the sum of the three pairwise DRs.
  3. The three-way Morphon's E8 root is NOT reachable by any pairwise
     collision alone (it is a genuinely emergent configuration).

This provides a new, geometrically grounded definition of a neural motif
that captures the emergent computational properties of three-neuron circuits.
"""

import sys, json, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from itertools import combinations

from cmplx.tools.manus.e8_lattice import E8Lattice

def digital_root(n):
    n = abs(int(round(n)))
    return 0 if n == 0 else 1 + (n - 1) % 9

class TriadicBondNeuralTopologyDetector:
    def __init__(self):
        self.e8 = E8Lattice()
        self.roots = self.e8.get_roots()
        self.root_vecs = np.array([r.coords for r in self.roots], dtype=float)

    def _spike_train_to_e8(self, spike_rates, window=8):
        """Encode a spike rate time series as a sequence of E8 roots."""
        rates = np.array(spike_rates, dtype=float)
        # Normalize
        if rates.std() > 0:
            rates = (rates - rates.mean()) / rates.std()
        # Sliding window → 8D vectors → E8 roots
        root_indices = []
        for i in range(0, len(rates) - window + 1, window // 2):
            vec = rates[i:i+window]
            if len(vec) < window:
                vec = np.pad(vec, (0, window - len(vec)))
            dists = np.linalg.norm(self.root_vecs - vec, axis=1)
            root_indices.append(int(np.argmin(dists)))
        return root_indices

    def _collision_morphon(self, roots_a, roots_b, n_steps=6):
        """Compute the collision Morphon between two root sequences."""
        # Use the mean root vector of each sequence
        vec_a = np.mean([self.root_vecs[i % len(self.roots)] for i in roots_a], axis=0)
        vec_b = np.mean([self.root_vecs[i % len(self.roots)] for i in roots_b], axis=0)
        state = (vec_a + vec_b) / 2.0
        for _ in range(n_steps):
            dists = np.linalg.norm(self.root_vecs - state, axis=1)
            nearest = self.root_vecs[np.argmin(dists)]
            state = 0.618 * nearest + 0.382 * state
        dists = np.linalg.norm(self.root_vecs - state, axis=1)
        terminal_idx = int(np.argmin(dists))
        return terminal_idx, digital_root(terminal_idx + 1)

    def _three_way_collision(self, roots_a, roots_b, roots_c, n_steps=9):
        """Compute the three-way collision Morphon."""
        vec_a = np.mean([self.root_vecs[i % len(self.roots)] for i in roots_a], axis=0)
        vec_b = np.mean([self.root_vecs[i % len(self.roots)] for i in roots_b], axis=0)
        vec_c = np.mean([self.root_vecs[i % len(self.roots)] for i in roots_c], axis=0)
        state = (vec_a + vec_b + vec_c) / 3.0
        for _ in range(n_steps):
            dists = np.linalg.norm(self.root_vecs - state, axis=1)
            nearest = self.root_vecs[np.argmin(dists)]
            state = 0.618 * nearest + 0.382 * state
        dists = np.linalg.norm(self.root_vecs - state, axis=1)
        terminal_idx = int(np.argmin(dists))
        return terminal_idx, digital_root(terminal_idx + 1)

    def _is_triadic_bond(self, dr_ab, dr_bc, dr_ac, dr_abc, root_ab, root_bc, root_ac, root_abc):
        """
        Test the three triadic bond conditions.
        """
        # Condition 1: Pairwise DRs are all equal
        cond1 = (dr_ab == dr_bc == dr_ac)
        # Condition 2: Three-way DR = DR(sum of pairwise DRs)
        cond2 = (dr_abc == digital_root(dr_ab + dr_bc + dr_ac))
        # Condition 3: Three-way root is NOT any pairwise root
        cond3 = (root_abc not in {root_ab, root_bc, root_ac})
        return cond1, cond2, cond3, (cond1 and cond2 and cond3)

    def analyze_connectome(self, neurons):
        """
        Analyze a neural connectome for triadic bond configurations.
        neurons: list of (name, spike_rates) tuples
        Returns all triadic bond detections.
        """
        # Encode all neurons
        encoded = {}
        for name, rates in neurons:
            encoded[name] = self._spike_train_to_e8(rates)

        names = [n for n, _ in neurons]
        triadic_bonds = []
        all_triplets = []

        for na, nb, nc in combinations(names, 3):
            roots_a = encoded[na]
            roots_b = encoded[nb]
            roots_c = encoded[nc]

            # Pairwise collisions
            root_ab, dr_ab = self._collision_morphon(roots_a, roots_b)
            root_bc, dr_bc = self._collision_morphon(roots_b, roots_c)
            root_ac, dr_ac = self._collision_morphon(roots_a, roots_c)

            # Three-way collision
            root_abc, dr_abc = self._three_way_collision(roots_a, roots_b, roots_c)

            cond1, cond2, cond3, is_bond = self._is_triadic_bond(
                dr_ab, dr_bc, dr_ac, dr_abc,
                root_ab, root_bc, root_ac, root_abc)

            triplet = {
                "neurons": [na, nb, nc],
                "dr_ab": dr_ab, "dr_bc": dr_bc, "dr_ac": dr_ac,
                "dr_abc": dr_abc,
                "root_ab": root_ab, "root_bc": root_bc,
                "root_ac": root_ac, "root_abc": root_abc,
                "cond1_equal_pairwise_dr": cond1,
                "cond2_triadic_dr_relation": cond2,
                "cond3_emergent_root": cond3,
                "is_triadic_bond": is_bond,
                "bond_strength": sum([cond1, cond2, cond3]) / 3.0,
            }
            all_triplets.append(triplet)
            if is_bond:
                triadic_bonds.append(triplet)

        return {
            "n_neurons": len(neurons),
            "n_triplets_tested": len(all_triplets),
            "n_triadic_bonds": len(triadic_bonds),
            "triadic_bond_rate": len(triadic_bonds) / max(len(all_triplets), 1),
            "triadic_bonds": triadic_bonds,
            "all_triplets": all_triplets,
        }

    def plot(self, result, output_path, title="Triadic Bond Neural Topology Detector"):
        fig = plt.figure(figsize=(22, 14))
        fig.patch.set_facecolor('#0d1117')
        gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.38)

        def dark_ax(ax):
            ax.set_facecolor('#161b22')
            for sp in ax.spines.values(): sp.set_color('#30363d')
            ax.tick_params(colors='#8b949e', labelsize=8)

        triplets = result['all_triplets']
        bonds = result['triadic_bonds']

        # Panel 1: Bond strength distribution
        ax1 = fig.add_subplot(gs[0, 0]); dark_ax(ax1)
        strengths = [t['bond_strength'] for t in triplets]
        ax1.hist(strengths, bins=[0, 1/3+0.01, 2/3+0.01, 1.01],
                 color='#58a6ff',
                 edgecolor='#30363d', alpha=0.85)
        ax1.set_xlabel('Bond Strength (0=none, 1=full triadic)', color='#8b949e', fontsize=9)
        ax1.set_ylabel('Triplet count', color='#8b949e', fontsize=9)
        ax1.set_title('Triadic Bond Strength Distribution', color='white', fontsize=10, fontweight='bold')
        ax1.text(0.95, 0.95, f"Full bonds: {result['n_triadic_bonds']}\n"
                              f"Rate: {result['triadic_bond_rate']:.1%}",
                 transform=ax1.transAxes, color='white', fontsize=10,
                 ha='right', va='top', fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='#161b22', edgecolor='#3fb950'))

        # Panel 2: Condition satisfaction heatmap
        ax2 = fig.add_subplot(gs[0, 1]); dark_ax(ax2)
        cond_matrix = np.array([[int(t['cond1_equal_pairwise_dr']),
                                  int(t['cond2_triadic_dr_relation']),
                                  int(t['cond3_emergent_root'])] for t in triplets])
        if len(cond_matrix) > 0:
            im = ax2.imshow(cond_matrix.T, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
            ax2.set_yticks([0,1,2])
            ax2.set_yticklabels(['Cond 1\n(Equal DR)', 'Cond 2\n(DR Relation)', 'Cond 3\n(Emergent)'],
                                color='white', fontsize=8)
            ax2.set_xlabel('Triplet index', color='#8b949e', fontsize=9)
            ax2.set_title('Triadic Bond Condition Satisfaction\n(Green=Met, Red=Failed)',
                          color='white', fontsize=10, fontweight='bold')

        # Panel 3: DR distribution of three-way collisions
        ax3 = fig.add_subplot(gs[0, 2]); dark_ax(ax3)
        abc_drs = [t['dr_abc'] for t in triplets]
        from collections import Counter
        dr_counts = Counter(abc_drs)
        dr_colors = {1:'#ff7b72',2:'#58a6ff',3:'#3fb950',4:'#ffa657',
                     5:'#d2a8ff',6:'#79c0ff',7:'#56d364',8:'#e3b341',9:'#8b949e'}
        ax3.bar(sorted(dr_counts.keys()),
                [dr_counts[k] for k in sorted(dr_counts.keys())],
                color=[dr_colors.get(k,'#58a6ff') for k in sorted(dr_counts.keys())],
                edgecolor='#30363d', alpha=0.85)
        ax3.set_xlabel('Three-way Collision DR', color='#8b949e', fontsize=9)
        ax3.set_ylabel('Count', color='#8b949e', fontsize=9)
        ax3.set_title('Three-Way Collision DR Distribution', color='white', fontsize=10, fontweight='bold')

        # Panel 4: Triadic bond details table
        ax4 = fig.add_subplot(gs[1, :]); ax4.set_facecolor('#161b22'); ax4.axis('off')
        display_bonds = bonds[:10] if bonds else triplets[:10]
        headers = ['Neurons', 'DR_AB', 'DR_BC', 'DR_AC', 'DR_ABC', 'C1', 'C2', 'C3', 'Bond']
        col_x = [0.01, 0.30, 0.39, 0.48, 0.57, 0.66, 0.73, 0.80, 0.87]
        y0 = 0.95
        for hx, hdr in zip(col_x, headers):
            ax4.text(hx, y0, hdr, transform=ax4.transAxes,
                     color='#ffa657', fontsize=9, fontweight='bold', va='top', fontfamily='monospace')
        for i, t in enumerate(display_bonds):
            y = y0 - 0.085 * (i + 1)
            bond_color = '#3fb950' if t['is_triadic_bond'] else '#8b949e'
            vals = ['+'.join(t['neurons']), str(t['dr_ab']), str(t['dr_bc']),
                    str(t['dr_ac']), str(t['dr_abc']),
                    '✓' if t['cond1_equal_pairwise_dr'] else '✗',
                    '✓' if t['cond2_triadic_dr_relation'] else '✗',
                    '✓' if t['cond3_emergent_root'] else '✗',
                    'YES' if t['is_triadic_bond'] else 'no']
            for vx, val in zip(col_x, vals):
                ax4.text(vx, y, val, transform=ax4.transAxes,
                         color=bond_color if vx == col_x[8] else '#c9d1d9',
                         fontsize=8.5, va='top', fontfamily='monospace')

        fig.suptitle(title, color='white', fontsize=13, fontweight='bold', y=1.01)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        print(f"[SAVED] {output_path}")


if __name__ == "__main__":
    import os
    os.makedirs('/home/ubuntu/lab/tools/tool07_neuro', exist_ok=True)

    print("=" * 65)
    print("TOOL 7: TriadicBondNeuralTopologyDetector — Demo")
    print("=" * 65)

    rng = np.random.default_rng(42)
    T = 200  # 200 time bins

    def oscillator(freq, phase=0, noise=0.1):
        t = np.arange(T)
        return (np.sin(2*np.pi*freq*t/T + phase) +
                rng.normal(0, noise, T)).tolist()

    def poisson_neuron(rate=0.3):
        return (rng.poisson(rate, T)).astype(float).tolist()

    # Create a network with known triadic bonds
    # Group A: three neurons with the same oscillation frequency (should form triadic bonds)
    # Group B: three neurons with different frequencies (should NOT form triadic bonds)
    neurons = [
        ("N1_alpha", oscillator(5, 0.0, 0.05)),     # Group A: 5Hz, phase 0
        ("N2_alpha", oscillator(5, 0.2, 0.05)),     # Group A: 5Hz, phase 0.2
        ("N3_alpha", oscillator(5, 0.4, 0.05)),     # Group A: 5Hz, phase 0.4
        ("N4_beta",  oscillator(10, 0.0, 0.05)),    # Group B: 10Hz
        ("N5_gamma", oscillator(40, 0.0, 0.05)),    # Group B: 40Hz
        ("N6_delta", oscillator(2, 0.0, 0.05)),     # Group B: 2Hz
        ("N7_noise", poisson_neuron(0.3)),           # Random noise neuron
        ("N8_noise", poisson_neuron(0.5)),           # Random noise neuron
    ]

    tool = TriadicBondNeuralTopologyDetector()
    result = tool.analyze_connectome(neurons)

    print(f"\nNeurons: {result['n_neurons']}")
    print(f"Triplets tested: {result['n_triplets_tested']}")
    print(f"Triadic bonds found: {result['n_triadic_bonds']} ({result['triadic_bond_rate']:.1%})")

    if result['triadic_bonds']:
        print(f"\nTriadic bonds:")
        for b in result['triadic_bonds']:
            print(f"  {'+'.join(b['neurons'])}  DR_ABC={b['dr_abc']}  "
                  f"Conditions: C1={b['cond1_equal_pairwise_dr']} "
                  f"C2={b['cond2_triadic_dr_relation']} "
                  f"C3={b['cond3_emergent_root']}")

    out_png = '/home/ubuntu/lab/tools/tool07_neuro/triadic_neural_topology.png'
    tool.plot(result, out_png)

    summary = {k: v for k, v in result.items() if k != 'all_triplets'}
    with open('/home/ubuntu/lab/tools/tool07_neuro/results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("[SAVED] /home/ubuntu/lab/tools/tool07_neuro/results.json")
    print("[DONE]")
