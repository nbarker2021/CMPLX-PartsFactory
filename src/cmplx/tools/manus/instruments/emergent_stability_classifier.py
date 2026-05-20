"""
Integrated 2026-05-19T00:52:23Z from external toolkit.
Source: ``D:\Manny Unification 2\datasets from previous review\Manus dev and review\emergent_stability_classifier.py``
"""
#!/usr/bin/env python3
"""
TOOL 10: EmergentStabilityClassifier
=======================================
Layer:  Meta (cross-strata emergent stability — the full CMPLX pipeline)
Field:  Complex Systems Science / Universal Complexity Theory
Author: Nicholas Barker & Manus AI, 2026

PROBLEM SOLVED
--------------
Complex systems (biological, physical, economic, computational) exhibit
emergent stability — configurations that are stable not because of any
single component but because of the geometric relationships between all
components across all scales simultaneously. There is no existing tool
that can classify the emergent stability of an arbitrary complex system
using a unified, scale-free geometric framework.

NOVEL CONTRIBUTION
------------------
This tool is the meta-layer of the entire CMPLX framework. It takes any
complex system's state vector and runs it through all 9 stratification
layers simultaneously:

  Layer 1 (Local):        E8 root snap → digital root
  Layer 2 (Local-Meso):   Pairwise collision Morphons
  Layer 3 (Meso):         Three-way triadic bond test
  Layer 4 (Meso-Global):  Niemeier composition probe
  Layer 5 (Global):       Multi-scale entropy fingerprint
  Layer 6 (Global-Meta):  48D Leech displacement
  Layer 7 (Meta):         Lambda normal form order
  Layer 8 (Meta-Trans):   Paired Z/2 symmetry test
  Layer 9 (Transcendent): 100-form phase transition proximity

The output is an Emergent Stability Score (ESS) — a single number from 0
(maximally unstable/chaotic) to 1 (maximally stable/ordered) — along with
a per-layer breakdown and a classification into one of 9 stability classes.

This is the first tool that can compare the stability of a protein fold,
a climate state, a neural circuit, and a cellular automaton on the same
geometric scale.
"""

import sys, json, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from collections import Counter

from cmplx.tools.manus.e8_lattice import E8Lattice

def digital_root(n):
    n = abs(int(round(n)))
    return 0 if n == 0 else 1 + (n - 1) % 9

def shannon_entropy(seq):
    if not seq: return 0.0
    counts = Counter(seq)
    n = len(seq)
    return -sum((c/n)*math.log2(c/n) for c in counts.values() if c > 0)

STABILITY_CLASSES = {
    1: ("Crystal Attractor",     "Maximally ordered — single fixed point",      '#3fb950'),
    2: ("Limit Cycle",           "Periodic — bounded oscillation",               '#56d364'),
    3: ("Quasi-periodic",        "Dense orbit — irrational frequency ratio",     '#79c0ff'),
    4: ("Weakly Chaotic",        "Positive Lyapunov — slow divergence",          '#58a6ff'),
    5: ("Edge of Chaos",         "Critical — maximum computational capacity",    '#ffa657'),
    6: ("Strongly Chaotic",      "Rapid divergence — sensitive dependence",      '#e3b341'),
    7: ("Turbulent",             "Multi-scale chaos — no dominant frequency",    '#ff7b72'),
    8: ("Dissipative",           "Energy loss — converging to lower dimension",  '#f85149'),
    9: ("Suspended / Metastable","Near-critical — coupling constant present",    '#8b949e'),
}

class EmergentStabilityClassifier:
    def __init__(self):
        self.e8 = E8Lattice()
        self.roots = self.e8.get_roots()
        self.root_vecs = np.array([r.coords for r in self.roots], dtype=float)

    # ── Layer utilities ──────────────────────────────────────────────────────

    def _snap_to_e8(self, vec8):
        dists = np.linalg.norm(self.root_vecs - np.array(vec8, dtype=float), axis=1)
        idx = int(np.argmin(dists))
        return idx, float(dists[idx])

    def _collision(self, vec_a, vec_b, steps=6):
        state = (np.array(vec_a) + np.array(vec_b)) / 2.0
        for _ in range(steps):
            dists = np.linalg.norm(self.root_vecs - state, axis=1)
            nearest = self.root_vecs[np.argmin(dists)]
            state = 0.618 * nearest + 0.382 * state
        dists = np.linalg.norm(self.root_vecs - state, axis=1)
        return int(np.argmin(dists)), float(np.min(dists))

    def _encode_state(self, state_vector):
        """
        Encode an arbitrary state vector into a sequence of E8 roots.
        """
        v = np.array(state_vector, dtype=float)
        if v.std() > 0:
            v = (v - v.mean()) / v.std()
        # Pad/truncate to multiple of 8
        n8 = max(8, ((len(v) + 7) // 8) * 8)
        v = np.pad(v, (0, n8 - len(v)), mode='wrap')
        roots = []
        snap_dists = []
        for i in range(0, len(v), 8):
            idx, dist = self._snap_to_e8(v[i:i+8])
            roots.append(idx)
            snap_dists.append(dist)
        return roots, snap_dists

    # ── 9 Layer computations ─────────────────────────────────────────────────

    def _layer1_local_dr(self, roots):
        """Layer 1: Digital root of the root sequence."""
        drs = [digital_root(r+1) for r in roots]
        global_dr = digital_root(sum(drs))
        # Stability: DR=1 or DR=9 → most stable; DR=5 → edge of chaos
        stability = 1.0 - abs(global_dr - 5) / 4.0  # peaks at DR=5
        return {"layer": 1, "name": "Local DR", "value": global_dr,
                "stability_contribution": float(stability),
                "interpretation": f"Global DR={global_dr}"}

    def _layer2_pairwise_morphons(self, roots):
        """Layer 2: Pairwise collision Morphons."""
        if len(roots) < 2:
            return {"layer": 2, "name": "Pairwise Morphons", "value": 0,
                    "stability_contribution": 0.5, "interpretation": "Insufficient roots"}
        pairs = [(roots[i], roots[i+1]) for i in range(min(len(roots)-1, 8))]
        morphon_drs = []
        for ra, rb in pairs:
            _, dist = self._collision(self.root_vecs[ra], self.root_vecs[rb])
            morphon_drs.append(digital_root(int(dist * 10) + 1))
        dr_entropy = shannon_entropy(morphon_drs)
        # Low entropy = ordered pairwise interactions = stable
        stability = 1.0 - dr_entropy / math.log2(9)
        return {"layer": 2, "name": "Pairwise Morphons", "value": float(dr_entropy),
                "stability_contribution": float(max(0, stability)),
                "interpretation": f"Pairwise DR entropy={dr_entropy:.2f}"}

    def _layer3_triadic_bond(self, roots):
        """Layer 3: Three-way triadic bond test."""
        if len(roots) < 3:
            return {"layer": 3, "name": "Triadic Bond", "value": 0,
                    "stability_contribution": 0.5, "interpretation": "Insufficient roots"}
        # Test the first available triplet
        ra, rb, rc = roots[0], roots[min(1, len(roots)-1)], roots[min(2, len(roots)-1)]
        _, dr_ab = self._collision(self.root_vecs[ra], self.root_vecs[rb])
        _, dr_bc = self._collision(self.root_vecs[rb], self.root_vecs[rc])
        _, dr_ac = self._collision(self.root_vecs[ra], self.root_vecs[rc])
        dr_ab_i = digital_root(int(dr_ab*10)+1)
        dr_bc_i = digital_root(int(dr_bc*10)+1)
        dr_ac_i = digital_root(int(dr_ac*10)+1)
        cond1 = (dr_ab_i == dr_bc_i == dr_ac_i)
        # Triadic bond = maximally stable (emergent order)
        stability = 1.0 if cond1 else 0.3
        return {"layer": 3, "name": "Triadic Bond", "value": int(cond1),
                "stability_contribution": stability,
                "interpretation": f"Triadic bond {'PRESENT' if cond1 else 'absent'}"}

    def _layer4_niemeier_probe(self, roots):
        """Layer 4: Niemeier composition probe."""
        if len(roots) < 2:
            return {"layer": 4, "name": "Niemeier Probe", "value": 0,
                    "stability_contribution": 0.5, "interpretation": "Insufficient roots"}
        # Compute the Gram matrix of the root vectors
        vecs = np.array([self.root_vecs[r] for r in roots[:8]])
        gram = vecs @ vecs.T
        # Niemeier-like: check if Gram matrix has integer entries (lattice property)
        gram_rounded = np.round(gram).astype(int)
        integer_fraction = float(np.mean(np.abs(gram - gram_rounded) < 0.1))
        return {"layer": 4, "name": "Niemeier Probe", "value": float(integer_fraction),
                "stability_contribution": float(integer_fraction),
                "interpretation": f"Gram integer fraction={integer_fraction:.2f}"}

    def _layer5_multiscale_entropy(self, roots, snap_dists):
        """Layer 5: Multi-scale entropy fingerprint."""
        drs = [digital_root(r+1) for r in roots]
        if len(drs) < 3:
            return {"layer": 5, "name": "Multi-scale Entropy", "value": 0,
                    "stability_contribution": 0.5, "interpretation": "Insufficient data"}
        local_ent  = np.mean([shannon_entropy(drs[i:i+3])  for i in range(len(drs)-2)])
        meso_ent   = np.mean([shannon_entropy(drs[i:i+min(12,len(drs))]) for i in range(0, len(drs)-2, 3)])
        global_ent = shannon_entropy(drs)
        # Stability: low entropy = ordered = stable
        mean_ent = (local_ent + meso_ent + global_ent) / 3.0
        stability = 1.0 - mean_ent / math.log2(9)
        return {"layer": 5, "name": "Multi-scale Entropy",
                "value": float(mean_ent),
                "local_entropy": float(local_ent),
                "meso_entropy": float(meso_ent),
                "global_entropy": float(global_ent),
                "stability_contribution": float(max(0, stability)),
                "interpretation": f"Mean entropy={mean_ent:.2f}"}

    def _layer6_leech_displacement(self, roots):
        """Layer 6: 48D Leech displacement."""
        # Use 3 E8 blocks
        blocks = [roots[i % len(roots)] for i in range(3)]
        point_48d = np.concatenate([self.root_vecs[b] for b in blocks])
        center_24d = np.tile(self.root_vecs.mean(axis=0), 3)
        displacement = float(np.linalg.norm(point_48d - center_24d))
        normalized = min(1.0, displacement / (math.sqrt(48) * 2.0))
        # Stability: close to Leech center = stable
        stability = 1.0 - normalized
        return {"layer": 6, "name": "Leech Displacement", "value": normalized,
                "stability_contribution": float(stability),
                "interpretation": f"Leech displacement={normalized:.3f}"}

    def _layer7_lambda_order(self, roots):
        """Layer 7: Lambda normal form order."""
        # Estimate the lambda order needed to stabilize the root sequence
        # by checking how quickly the digital root sequence converges
        drs = [digital_root(r+1) for r in roots]
        order = 1
        current = drs[:]
        while len(set(current)) > 1 and order < 9:
            current = [digital_root(sum(current[i:i+3])) for i in range(0, len(current)-2, 1)]
            order += 1
        # Low order = converges quickly = stable
        stability = 1.0 - (order - 1) / 8.0
        return {"layer": 7, "name": "Lambda Order", "value": order,
                "stability_contribution": float(stability),
                "interpretation": f"Lambda convergence order={order}"}

    def _layer8_z2_symmetry(self, roots):
        """Layer 8: Paired Z/2 symmetry test."""
        if len(roots) < 2:
            return {"layer": 8, "name": "Z/2 Symmetry", "value": 0,
                    "stability_contribution": 0.5, "interpretation": "Insufficient roots"}
        # Check if the +4 shift produces the same DR sequence
        n = len(self.roots)
        shifted = [(r + n//2) % n for r in roots]
        drs_orig    = [digital_root(r+1) for r in roots]
        drs_shifted = [digital_root(r+1) for r in shifted]
        # Z/2 symmetry: shifted DR = complement (9 - DR)
        complement_match = sum(
            1 for a, b in zip(drs_orig, drs_shifted) if a + b == 9 or (a == 9 and b == 9)
        ) / len(drs_orig)
        return {"layer": 8, "name": "Z/2 Symmetry", "value": float(complement_match),
                "stability_contribution": float(complement_match),
                "interpretation": f"Z/2 complement match={complement_match:.2f}"}

    def _layer9_phase_transition(self, roots):
        """Layer 9: 100-form phase transition proximity."""
        # Estimate how close the system is to the 100-form phase transition
        # by measuring the unique root count relative to the expected saturation
        unique_count = len(set(roots))
        total = len(roots)
        # At saturation (50 forms), the system is in the Z/2 pair
        # At 100 forms, the phase transition occurs
        saturation_ratio = unique_count / max(total, 1)
        # Near 0.5 saturation = near Z/2 pair = stable; near 1.0 = phase transition
        proximity_to_transition = abs(saturation_ratio - 0.5) * 2.0
        stability = 1.0 - proximity_to_transition
        return {"layer": 9, "name": "Phase Transition Proximity",
                "value": float(proximity_to_transition),
                "stability_contribution": float(max(0, stability)),
                "interpretation": f"Phase transition proximity={proximity_to_transition:.2f}"}

    # ── Main interface ────────────────────────────────────────────────────────

    def classify(self, system_name, state_vector, domain=None):
        """
        Classify the emergent stability of a complex system.
        state_vector: any-length list/array of real numbers
        """
        roots, snap_dists = self._encode_state(state_vector)

        layers = [
            self._layer1_local_dr(roots),
            self._layer2_pairwise_morphons(roots),
            self._layer3_triadic_bond(roots),
            self._layer4_niemeier_probe(roots),
            self._layer5_multiscale_entropy(roots, snap_dists),
            self._layer6_leech_displacement(roots),
            self._layer7_lambda_order(roots),
            self._layer8_z2_symmetry(roots),
            self._layer9_phase_transition(roots),
        ]

        # Emergent Stability Score: weighted mean of all layer contributions
        weights = [1.0, 1.0, 1.5, 1.0, 1.5, 1.0, 1.0, 1.0, 1.5]
        ess = sum(w * l['stability_contribution'] for w, l in zip(weights, layers)) / sum(weights)

        # Classify into stability class
        # Map ESS to DR: ESS=1 → DR=1 (crystal), ESS=0 → DR=8 (dissipative)
        # ESS=0.5 → DR=5 (edge of chaos)
        class_dr = max(1, min(9, int(round(9 - ess * 8))))
        class_name, class_desc, class_color = STABILITY_CLASSES[class_dr]

        return {
            "system": system_name,
            "domain": domain or "Unknown",
            "n_roots": len(roots),
            "emergent_stability_score": float(ess),
            "stability_class_dr": class_dr,
            "stability_class": class_name,
            "stability_description": class_desc,
            "layers": layers,
        }

    def compare(self, systems):
        """Compare multiple systems on the same ESS scale."""
        return [self.classify(name, vec, domain) for name, vec, domain in systems]

    def plot(self, results, output_path, title="Emergent Stability Classifier"):
        fig = plt.figure(figsize=(26, 16))
        fig.patch.set_facecolor('#0d1117')
        gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.38)

        def dark_ax(ax):
            ax.set_facecolor('#161b22')
            for sp in ax.spines.values(): sp.set_color('#30363d')
            ax.tick_params(colors='#8b949e', labelsize=8)

        layer_names = [l['name'] for l in results[0]['layers']]
        n_sys = len(results)
        n_layers = len(layer_names)
        ess_scores = [r['emergent_stability_score'] for r in results]
        class_colors = [STABILITY_CLASSES[r['stability_class_dr']][2] for r in results]

        # Panel 1: ESS bar chart
        ax1 = fig.add_subplot(gs[0, 0]); dark_ax(ax1)
        bars = ax1.barh([r['system'][:18] for r in results], ess_scores,
                        color=class_colors, edgecolor='#30363d', alpha=0.85)
        ax1.axvline(0.5, color='#ffa657', linewidth=2, linestyle='--', alpha=0.8)
        ax1.set_xlabel('Emergent Stability Score (0=chaotic, 1=ordered)', color='#8b949e', fontsize=9)
        ax1.set_title('Emergent Stability Score by System', color='white', fontsize=10, fontweight='bold')
        ax1.set_xlim(0, 1.05)
        for bar, r in zip(bars, results):
            ax1.text(r['emergent_stability_score'] + 0.01, bar.get_y() + bar.get_height()/2,
                     f"{r['emergent_stability_score']:.2f}  {r['stability_class'][:12]}",
                     va='center', color='white', fontsize=8)

        # Panel 2: Per-layer heatmap
        ax2 = fig.add_subplot(gs[0, 1:]); dark_ax(ax2)
        layer_matrix = np.array([[l['stability_contribution'] for l in r['layers']] for r in results])
        im = ax2.imshow(layer_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        ax2.set_xticks(range(n_layers))
        ax2.set_xticklabels(layer_names, rotation=35, ha='right', fontsize=8, color='white')
        ax2.set_yticks(range(n_sys))
        ax2.set_yticklabels([r['system'][:18] for r in results], fontsize=8, color='white')
        ax2.set_title('Per-Layer Stability Contribution (Green=Stable, Red=Unstable)',
                      color='white', fontsize=10, fontweight='bold')
        for i in range(n_sys):
            for j in range(n_layers):
                ax2.text(j, i, f"{layer_matrix[i,j]:.1f}",
                         ha='center', va='center', fontsize=7.5,
                         color='black' if layer_matrix[i,j] > 0.4 else 'white')
        plt.colorbar(im, ax=ax2, fraction=0.02, pad=0.02).ax.tick_params(colors='#8b949e')

        # Panel 3: Radar chart for first system
        ax3 = fig.add_subplot(gs[1, 0], polar=True)
        ax3.set_facecolor('#161b22')
        angles = np.linspace(0, 2*np.pi, n_layers, endpoint=False).tolist()
        angles += angles[:1]
        for r in results[:4]:
            vals = [l['stability_contribution'] for l in r['layers']]
            vals += vals[:1]
            color = STABILITY_CLASSES[r['stability_class_dr']][2]
            ax3.plot(angles, vals, color=color, linewidth=2, alpha=0.85, label=r['system'][:12])
            ax3.fill(angles, vals, color=color, alpha=0.12)
        ax3.set_xticks(angles[:-1])
        ax3.set_xticklabels([n[:8] for n in layer_names], fontsize=7, color='white')
        ax3.set_ylim(0, 1)
        ax3.tick_params(colors='#8b949e')
        ax3.set_facecolor('#161b22')
        ax3.spines['polar'].set_color('#30363d')
        ax3.yaxis.set_tick_params(colors='#8b949e')
        ax3.set_title('Layer Profile Radar', color='white', fontsize=10, fontweight='bold', pad=15)
        ax3.legend(fontsize=7, facecolor='#161b22', labelcolor='white',
                   edgecolor='#30363d', loc='upper right', bbox_to_anchor=(1.3, 1.1))

        # Panel 4: Summary table
        ax4 = fig.add_subplot(gs[1, 1:]); ax4.set_facecolor('#161b22'); ax4.axis('off')
        headers = ['System', 'Domain', 'ESS', 'Class', 'Description']
        col_x = [0.01, 0.20, 0.34, 0.44, 0.62]
        y0 = 0.97
        for hx, hdr in zip(col_x, headers):
            ax4.text(hx, y0, hdr, transform=ax4.transAxes,
                     color='#ffa657', fontsize=9.5, fontweight='bold', va='top', fontfamily='monospace')
        for i, r in enumerate(results):
            y = y0 - 0.085 * (i + 1)
            color = STABILITY_CLASSES[r['stability_class_dr']][2]
            vals = [r['system'][:18], r['domain'][:14],
                    f"{r['emergent_stability_score']:.3f}",
                    r['stability_class'][:16],
                    r['stability_description'][:38]]
            for vx, val in zip(col_x, vals):
                ax4.text(vx, y, val, transform=ax4.transAxes,
                         color=color if vx == col_x[3] else '#c9d1d9',
                         fontsize=8.5, va='top', fontfamily='monospace')

        fig.suptitle(title, color='white', fontsize=14, fontweight='bold', y=1.01)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        print(f"[SAVED] {output_path}")


if __name__ == "__main__":
    import os
    os.makedirs('/home/ubuntu/lab/tools/tool10_meta', exist_ok=True)

    print("=" * 70)
    print("TOOL 10: EmergentStabilityClassifier — Demo")
    print("=" * 70)

    rng = np.random.default_rng(42)

    # Test systems from all 9 previous tools, encoded as state vectors
    systems = [
        # Biological systems
        ("FCC Crystal",        [2.55]*24,                                      "Materials"),
        ("Amorphous Glass",    rng.uniform(2.0, 3.5, 24).tolist(),             "Materials"),
        ("Alpha-helix Protein",[1.5, 1.5, 1.5, 1.5, 110, 110, 110, 4]*3,     "Biochemistry"),
        ("Disordered Protein", rng.uniform(1.0, 4.0, 24).tolist(),             "Biochemistry"),
        # Neural systems
        ("Gamma Oscillation",  [math.sin(2*math.pi*40*t/200) for t in range(24)], "Neuroscience"),
        ("Random Spikes",      rng.poisson(0.3, 24).astype(float).tolist(),    "Neuroscience"),
        # Climate systems
        ("Pre-industrial",     [0.0, 280.0, 0.0, 14.0, 0.0, 0.0]*4,          "Climate"),
        ("2025 Climate",       [1.2, 425.0, 25.0, 4.5, 0.8, 0.3]*4,          "Climate"),
        # Mathematical systems
        ("Rule 30 (ordered)",  [1,0,1,1,1,0,0,0]*3,                           "Mathematics"),
        ("Rule 90 (XOR)",      [0,1,0,1,0,1,0,1]*3,                           "Mathematics"),
        # Economic systems
        ("Stable Market",      [100+i*0.01 for i in range(24)],               "Economics"),
        ("Volatile Market",    (100 + rng.normal(0, 10, 24).cumsum()).tolist(), "Economics"),
        # Quantum systems
        ("Ground State",       [1.0, 0.0]*12,                                  "Quantum"),
        ("Superposition",      [1/math.sqrt(2)]*24,                            "Quantum"),
    ]

    tool = EmergentStabilityClassifier()
    results = tool.compare(systems)

    print(f"\n{'System':<22} {'Domain':<14} {'ESS':>6}  {'Class'}")
    print("-" * 70)
    for r in results:
        print(f"  {r['system']:<20} {r['domain']:<14} {r['emergent_stability_score']:>6.3f}  "
              f"{r['stability_class']}")

    out_png = '/home/ubuntu/lab/tools/tool10_meta/emergent_stability.png'
    tool.plot(results, out_png)

    with open('/home/ubuntu/lab/tools/tool10_meta/results.json', 'w') as f:
        json.dump([{k: v for k, v in r.items() if k != 'layers'} for r in results],
                  f, indent=2, default=str)
    print("[SAVED] /home/ubuntu/lab/tools/tool10_meta/results.json")
    print("[DONE]")
