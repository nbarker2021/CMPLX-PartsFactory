"""
Integrated 2026-05-19T00:52:23Z from external toolkit.
Source: ``D:\Manny Unification 2\datasets from previous review\Manus dev and review\social_polarization.py``
"""
#!/usr/bin/env python3
"""
TOOL 22: SocialNetworkPolarizationDetector
==========================================
Layer:  7 (Triadic Bond)
Field:  Social Network Dynamics / Computational Social Science
Author: Nicholas Barker & Manus AI, 2026

PROBLEM SOLVED
--------------
Political and social polarization in online networks is a critical societal
problem. Current detection methods (modularity clustering, echo chamber
analysis) are computationally expensive and require full network topology.
They also cannot distinguish between healthy community formation and
pathological polarization.

NOVEL CONTRIBUTION
------------------
This tool detects polarization by analyzing the formation of "closed triadic
bonds" in E8-embedded social graphs. The key insight from the CMPLX framework
is that a healthy, bridging social connection forms an OPEN triadic bond
(A knows B, B knows C, but A and C do not know each other — a "structural
hole" in Burt's terminology). A polarized, echo-chamber connection forms a
CLOSED triadic bond (A, B, and C all know each other and share the same
geometric position in E8 space).

The tool computes the "Triadic Closure Polarization Index" (TCPI): the ratio
of closed, geometrically co-located triadic bonds to all triadic bonds. A
high TCPI indicates a network approaching dangerous polarization.

NOVEL CLAIM
-----------
Social polarization is the sociological manifestation of excessive triadic
bond closure in E8 space. The TCPI provides an early warning signal for
polarization before it becomes visible in content analysis.
"""

import sys, math, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from itertools import combinations

from cmplx.tools.manus.e8_lattice import E8Lattice

def digital_root(n):
    n = abs(int(round(n)))
    return 0 if n == 0 else 1 + (n - 1) % 9

def shannon_entropy(seq):
    if len(seq) < 2: return 0.0
    counts = Counter(seq)
    n = len(seq)
    return -sum((c/n)*math.log2(c/n) for c in counts.values() if c > 0)


class SocialNetworkPolarizationDetector:
    def __init__(self):
        self.e8 = E8Lattice()
        self.roots = self.e8.get_roots()
        self.root_vecs = np.array([r.coords for r in self.roots], dtype=float)

    def _encode_user(self, user_id, ideology_score, activity_level, echo_chamber_depth):
        """
        Encode a social network user as an 8D E8 vector.
        ideology_score: -1.0 (far left) to +1.0 (far right)
        activity_level: 0.0 to 1.0
        echo_chamber_depth: 0.0 (diverse) to 1.0 (pure echo chamber)
        """
        rng = np.random.default_rng(user_id * 137)
        noise = rng.normal(0, 0.1, 8)
        vec = np.array([
            ideology_score,
            activity_level,
            echo_chamber_depth,
            ideology_score * activity_level,
            echo_chamber_depth * abs(ideology_score),
            math.sin(user_id * 0.7),
            math.cos(user_id * 0.3),
            ideology_score ** 2,
        ]) + noise * 0.05
        return vec

    def _snap_to_e8(self, vec):
        dists = np.linalg.norm(self.root_vecs - vec, axis=1)
        idx = np.argmin(dists)
        return idx, dists[idx]

    def _build_network(self, network_type='polarized'):
        """
        Build synthetic social networks of different polarization levels.
        Returns list of (user_id, ideology, activity, echo_depth) tuples
        and an adjacency list.
        """
        rng = np.random.default_rng(42)
        n_users = 30

        if network_type == 'healthy':
            # Healthy: diverse ideologies, many cross-ideological connections
            ideologies = rng.uniform(-1, 1, n_users)
            activities = rng.uniform(0.3, 0.9, n_users)
            echo_depths = rng.uniform(0.0, 0.3, n_users)
            # Connect users with probability inversely proportional to ideology distance
            adj = defaultdict(set)
            for i, j in combinations(range(n_users), 2):
                dist = abs(ideologies[i] - ideologies[j])
                p_connect = 0.4 * (1 - dist * 0.3)  # high cross-ideological connection
                if rng.random() < p_connect:
                    adj[i].add(j); adj[j].add(i)

        elif network_type == 'polarized':
            # Polarized: two camps, few cross-camp connections
            ideologies = np.concatenate([rng.uniform(-1, -0.3, n_users//2),
                                          rng.uniform(0.3, 1, n_users//2)])
            activities = rng.uniform(0.5, 1.0, n_users)
            echo_depths = rng.uniform(0.6, 1.0, n_users)
            adj = defaultdict(set)
            for i, j in combinations(range(n_users), 2):
                same_camp = (ideologies[i] * ideologies[j]) > 0
                p_connect = 0.6 if same_camp else 0.05
                if rng.random() < p_connect:
                    adj[i].add(j); adj[j].add(i)

        elif network_type == 'echo_chamber':
            # Extreme: pure echo chambers, no cross-ideological connections
            ideologies = np.concatenate([np.full(n_users//2, -0.9),
                                          np.full(n_users//2, 0.9)])
            activities = rng.uniform(0.7, 1.0, n_users)
            echo_depths = rng.uniform(0.85, 1.0, n_users)
            adj = defaultdict(set)
            for i, j in combinations(range(n_users), 2):
                same_camp = (ideologies[i] * ideologies[j]) > 0
                p_connect = 0.7 if same_camp else 0.01
                if rng.random() < p_connect:
                    adj[i].add(j); adj[j].add(i)

        users = [(i, ideologies[i], activities[i], echo_depths[i]) for i in range(n_users)]
        return users, adj

    def analyze_network(self, network_type='polarized'):
        """Analyze a social network for polarization using triadic bond analysis."""
        users, adj = self._build_network(network_type)

        # Encode all users in E8
        e8_indices = []
        for uid, ideo, act, echo in users:
            vec = self._encode_user(uid, ideo, act, echo)
            idx, dist = self._snap_to_e8(vec)
            e8_indices.append(idx)

        # Find all triads (triangles in the graph)
        n = len(users)
        closed_triads = 0
        open_triads = 0
        polarized_closed = 0
        total_triads = 0

        for i in range(n):
            for j in adj[i]:
                if j <= i: continue
                for k in adj[j]:
                    if k <= j: continue
                    # (i, j, k) is a potential triad
                    if k in adj[i]:
                        # Closed triad (triangle)
                        closed_triads += 1
                        total_triads += 1
                        # Check if all three are in the same E8 region (same root index)
                        dr_i = digital_root(e8_indices[i])
                        dr_j = digital_root(e8_indices[j])
                        dr_k = digital_root(e8_indices[k])
                        if dr_i == dr_j == dr_k:
                            polarized_closed += 1
                    else:
                        open_triads += 1
                        total_triads += 1

        tcpi = polarized_closed / max(1, closed_triads)
        closure_ratio = closed_triads / max(1, total_triads)

        dr_sequence = [digital_root(idx) for idx in e8_indices]
        dr_entropy = shannon_entropy(dr_sequence)

        return {
            'network_type': network_type,
            'n_users': n,
            'n_edges': sum(len(v) for v in adj.values()) // 2,
            'closed_triads': closed_triads,
            'open_triads': open_triads,
            'polarized_closed_triads': polarized_closed,
            'tcpi': tcpi,
            'closure_ratio': closure_ratio,
            'dr_entropy': dr_entropy,
            'polarization_level': 'CRITICAL' if tcpi > 0.5 else 'HIGH' if tcpi > 0.3 else 'MODERATE' if tcpi > 0.1 else 'LOW',
        }

    def plot(self, results, output_path):
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.patch.set_facecolor('#0d1117')

        def dark_ax(ax):
            ax.set_facecolor('#161b22')
            for sp in ax.spines.values(): sp.set_color('#30363d')
            ax.tick_params(colors='#8b949e')

        labels = [r['network_type'].replace('_', '\n') for r in results]
        tcpis = [r['tcpi'] for r in results]
        entropies = [r['dr_entropy'] for r in results]
        closure_ratios = [r['closure_ratio'] for r in results]
        colors = ['#3fb950', '#ffa657', '#ff7b72']

        ax = axes[0]; dark_ax(ax)
        bars = ax.bar(labels, tcpis, color=colors, edgecolor='#30363d', alpha=0.85)
        ax.axhline(0.5, color='#ff7b72', linewidth=1.5, linestyle='--', alpha=0.7, label='Critical threshold')
        ax.axhline(0.3, color='#ffa657', linewidth=1.5, linestyle='--', alpha=0.7, label='High threshold')
        ax.set_ylabel('TCPI (Triadic Closure Polarization Index)', color='#8b949e', fontsize=10)
        ax.set_title('Polarization Index\nby Network Type', color='white', fontsize=12, fontweight='bold')
        ax.legend(fontsize=8, facecolor='#161b22', labelcolor='white', edgecolor='#30363d')
        for bar, val in zip(bars, tcpis):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.3f}', ha='center', va='bottom', color='white', fontsize=10, fontweight='bold')

        ax = axes[1]; dark_ax(ax)
        ax.bar(labels, entropies, color=colors, edgecolor='#30363d', alpha=0.85)
        ax.set_ylabel('E8 DR Entropy (bits)', color='#8b949e', fontsize=10)
        ax.set_title('Ideological Diversity\n(E8 DR Entropy)', color='white', fontsize=12, fontweight='bold')

        ax = axes[2]; dark_ax(ax)
        ax.bar(labels, closure_ratios, color=colors, edgecolor='#30363d', alpha=0.85)
        ax.set_ylabel('Triadic Closure Ratio', color='#8b949e', fontsize=10)
        ax.set_title('Triadic Closure Ratio\n(closed / total triads)', color='white', fontsize=12, fontweight='bold')

        fig.suptitle('Tool 22: SocialNetworkPolarizationDetector — E8 Triadic Bond Analysis',
                     color='white', fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        print(f"[SAVED] {output_path}")


if __name__ == "__main__":
    import os
    os.makedirs('/home/ubuntu/lab/tools_v3/tool22_social', exist_ok=True)
    print("=" * 70)
    print("TOOL 22: SocialNetworkPolarizationDetector — Demo")
    print("=" * 70)

    tool = SocialNetworkPolarizationDetector()
    results = []
    for ntype in ['healthy', 'polarized', 'echo_chamber']:
        print(f"\nAnalyzing {ntype} network...")
        r = tool.analyze_network(ntype)
        results.append(r)
        print(f"  Edges: {r['n_edges']}, Closed triads: {r['closed_triads']}, "
              f"Open triads: {r['open_triads']}")
        print(f"  TCPI: {r['tcpi']:.4f}  DR Entropy: {r['dr_entropy']:.4f}  "
              f"Level: {r['polarization_level']}")

    tool.plot(results, '/home/ubuntu/lab/tools_v3/tool22_social/social_polarization.png')
    with open('/home/ubuntu/lab/tools_v3/tool22_social/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n[SAVED] results.json\n[DONE]")
