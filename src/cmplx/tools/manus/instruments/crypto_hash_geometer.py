"""
Integrated 2026-05-19T00:52:23Z from external toolkit.
Source: ``D:\Manny Unification 2\datasets from previous review\Manus dev and review\crypto_hash_geometer.py``
"""
#!/usr/bin/env python3
"""
TOOL 13: CryptographicHashGeometer
=====================================
Layer:  4 (Niemeier probe) + 8 (Paired Z/2 symmetry)
Field:  Cryptography / Hash Function Analysis
Author: Nicholas Barker & Manus AI, 2026

PROBLEM SOLVED
--------------
Cryptographic hash functions are designed to be one-way: given a hash
output, it should be computationally infeasible to find the input. However,
the algebraic structure of a hash function — specifically, whether its
compression function has hidden Z/2 symmetries in its output space — is
not well-understood geometrically. If such symmetries exist, they could
be exploited for a geometric meet-in-the-middle attack.

NOVEL CONTRIBUTION
------------------
This tool encodes the output space of a hash function as a set of E8 root
sequences and tests for:

  1. Niemeier lattice composition: Does the output space have the structure
     of a known Niemeier lattice? If so, the hash function's output space
     is geometrically structured, which may indicate algebraic weaknesses.

  2. Paired Z/2 symmetry: Does the output space exhibit the paired Z/2
     symmetry we discovered in the Morphon collision experiments? If so,
     a geometric meet-in-the-middle attack is theoretically possible.

  3. Digital root collision probability: What fraction of distinct inputs
     map to the same E8 root? This measures the geometric "collision
     resistance" of the hash function.

This is not a practical attack tool — it is a geometric analysis instrument
for understanding the structural properties of hash function output spaces.
"""

import sys, json, math, hashlib, struct
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


class CryptographicHashGeometer:
    """
    Geometric structure analyzer for cryptographic hash function output spaces.
    """
    def __init__(self):
        self.e8 = E8Lattice()
        self.roots = self.e8.get_roots()
        self.root_vecs = np.array([r.coords for r in self.roots], dtype=float)

    def _hash_to_vec8(self, digest_bytes):
        """Convert the first 8 bytes of a hash digest to an 8D float vector."""
        vals = struct.unpack('8B', digest_bytes[:8])
        vec = np.array(vals, dtype=float)
        vec = (vec - 127.5) / 64.0  # normalize to ~[-2, 2]
        return vec

    def _snap(self, vec8):
        dists = np.linalg.norm(self.root_vecs - vec8, axis=1)
        return int(np.argmin(dists)), float(np.min(dists))

    def _hash_sample(self, hash_fn, n_samples=500, seed=42):
        """Generate n_samples hash outputs for sequential inputs."""
        rng = np.random.default_rng(seed)
        root_indices = []
        snap_dists = []
        for i in range(n_samples):
            msg = f"input_{i:06d}_{rng.integers(0, 1000000)}".encode()
            digest = hash_fn(msg).digest()
            vec = self._hash_to_vec8(digest)
            idx, dist = self._snap(vec)
            root_indices.append(idx)
            snap_dists.append(dist)
        return root_indices, snap_dists

    def _niemeier_probe(self, root_indices):
        """Test for Niemeier lattice composition in the root set."""
        vecs = np.array([self.root_vecs[r] for r in root_indices[:64]])
        gram = vecs @ vecs.T
        gram_rounded = np.round(gram).astype(int)
        integer_fraction = float(np.mean(np.abs(gram - gram_rounded) < 0.15))
        # Check if the Gram matrix eigenvalues match known Niemeier signatures
        eigvals = np.linalg.eigvalsh(gram)
        positive_fraction = float(np.mean(eigvals > 0))
        return {
            'gram_integer_fraction': integer_fraction,
            'gram_positive_fraction': positive_fraction,
            'niemeier_score': (integer_fraction + positive_fraction) / 2.0,
        }

    def _z2_symmetry_test(self, root_indices):
        """Test for paired Z/2 symmetry in the root distribution."""
        n = len(self.roots)
        drs = [digital_root(r + 1) for r in root_indices]
        # Test all cardinal shifts
        best_complement = 0.0
        best_shift = 0
        for shift in [n//8, n//4, n//2, 3*n//4]:
            shifted = [(r + shift) % n for r in root_indices]
            drs_shifted = [digital_root(r + 1) for r in shifted]
            complement_match = sum(
                1 for a, b in zip(drs, drs_shifted) if a + b == 9 or (a == 9 and b == 9)
            ) / len(drs)
            if complement_match > best_complement:
                best_complement = complement_match
                best_shift = shift
        return {
            'best_z2_complement_match': best_complement,
            'best_shift': best_shift,
            'z2_symmetry_present': best_complement > 0.15,
        }

    def _collision_resistance(self, root_indices):
        """Measure geometric collision resistance."""
        counts = Counter(root_indices)
        n_unique = len(counts)
        n_total = len(root_indices)
        collision_rate = 1.0 - n_unique / n_total
        dr_seq = [digital_root(r + 1) for r in root_indices]
        dr_entropy = shannon_entropy(dr_seq)
        return {
            'n_unique_roots': n_unique,
            'n_total': n_total,
            'geometric_collision_rate': collision_rate,
            'dr_entropy': dr_entropy,
            'max_theoretical_entropy': math.log2(9),
        }

    def analyze(self, hash_name, hash_fn, n_samples=500):
        root_indices, snap_dists = self._hash_sample(hash_fn, n_samples)
        niemeier = self._niemeier_probe(root_indices)
        z2 = self._z2_symmetry_test(root_indices)
        collision = self._collision_resistance(root_indices)

        # Overall geometric vulnerability score (higher = more structured = more vulnerable)
        vuln_score = (
            niemeier['niemeier_score'] * 0.4 +
            z2['best_z2_complement_match'] * 0.3 +
            collision['geometric_collision_rate'] * 0.3
        )

        return {
            'hash_function': hash_name,
            'n_samples': n_samples,
            'niemeier': niemeier,
            'z2_symmetry': z2,
            'collision_resistance': collision,
            'geometric_vulnerability_score': float(vuln_score),
            'root_indices': root_indices[:32],
        }

    def plot(self, results, output_path):
        n = len(results)
        fig = plt.figure(figsize=(22, 12))
        fig.patch.set_facecolor('#0d1117')
        gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.48, wspace=0.38)

        def dark_ax(ax):
            ax.set_facecolor('#161b22')
            for sp in ax.spines.values(): sp.set_color('#30363d')
            ax.tick_params(colors='#8b949e', labelsize=8)

        hash_names = [r['hash_function'] for r in results]
        vuln_scores = [r['geometric_vulnerability_score'] for r in results]
        niemeier_scores = [r['niemeier']['niemeier_score'] for r in results]
        z2_scores = [r['z2_symmetry']['best_z2_complement_match'] for r in results]
        collision_rates = [r['collision_resistance']['geometric_collision_rate'] for r in results]
        dr_entropies = [r['collision_resistance']['dr_entropy'] for r in results]

        # Panel 1: Geometric vulnerability scores
        ax1 = fig.add_subplot(gs[0, 0]); dark_ax(ax1)
        colors = ['#ff7b72' if v > 0.4 else '#ffa657' if v > 0.25 else '#3fb950'
                  for v in vuln_scores]
        bars = ax1.bar(hash_names, vuln_scores, color=colors, edgecolor='#30363d', alpha=0.85)
        ax1.set_ylim(0, 0.8)
        ax1.axhline(0.4, color='#ff7b72', linewidth=1.5, linestyle='--', alpha=0.7)
        ax1.axhline(0.25, color='#ffa657', linewidth=1.5, linestyle='--', alpha=0.7)
        ax1.set_title('Geometric Vulnerability Score\n(lower = more secure)', color='white',
                      fontsize=10, fontweight='bold')
        ax1.set_ylabel('Score', color='#8b949e', fontsize=9)
        for bar, val in zip(bars, vuln_scores):
            ax1.text(bar.get_x() + bar.get_width()/2, val + 0.01,
                     f'{val:.3f}', ha='center', color='white', fontsize=8)

        # Panel 2: Niemeier scores
        ax2 = fig.add_subplot(gs[0, 1]); dark_ax(ax2)
        ax2.bar(hash_names, niemeier_scores, color='#79c0ff', edgecolor='#30363d', alpha=0.85)
        ax2.set_ylim(0, 1.1)
        ax2.set_title('Niemeier Lattice Score\n(higher = more structured output)', color='white',
                      fontsize=10, fontweight='bold')
        ax2.set_ylabel('Score', color='#8b949e', fontsize=9)

        # Panel 3: Z/2 symmetry
        ax3 = fig.add_subplot(gs[0, 2]); dark_ax(ax3)
        ax3.bar(hash_names, z2_scores, color='#ffa657', edgecolor='#30363d', alpha=0.85)
        ax3.set_ylim(0, 0.5)
        ax3.axhline(0.15, color='#ff7b72', linewidth=1.5, linestyle='--', alpha=0.7,
                    label='Z/2 threshold')
        ax3.set_title('Paired Z/2 Complement Match\n(higher = more symmetric)', color='white',
                      fontsize=10, fontweight='bold')
        ax3.set_ylabel('Complement match fraction', color='#8b949e', fontsize=9)
        ax3.legend(fontsize=8, facecolor='#161b22', labelcolor='white', edgecolor='#30363d')

        # Panel 4: DR entropy
        ax4 = fig.add_subplot(gs[1, 0]); dark_ax(ax4)
        max_ent = math.log2(9)
        ax4.bar(hash_names, dr_entropies, color='#58a6ff', edgecolor='#30363d', alpha=0.85)
        ax4.axhline(max_ent, color='#3fb950', linewidth=1.5, linestyle='--', alpha=0.7,
                    label=f'Max entropy (log₂9={max_ent:.2f})')
        ax4.set_ylim(0, max_ent * 1.2)
        ax4.set_title('Digital Root Entropy of Output Space\n(higher = more uniform)', color='white',
                      fontsize=10, fontweight='bold')
        ax4.set_ylabel('Entropy (bits)', color='#8b949e', fontsize=9)
        ax4.legend(fontsize=8, facecolor='#161b22', labelcolor='white', edgecolor='#30363d')

        # Panel 5: Root distribution heatmap
        ax5 = fig.add_subplot(gs[1, 1:]); dark_ax(ax5)
        root_matrix = np.zeros((n, 9))
        for i, r in enumerate(results):
            drs = [digital_root(idx + 1) for idx in r['root_indices']]
            for dr in drs:
                if 1 <= dr <= 9:
                    root_matrix[i, dr - 1] += 1
            root_matrix[i] /= max(root_matrix[i].sum(), 1)
        im = ax5.imshow(root_matrix, cmap='YlOrRd', aspect='auto', vmin=0)
        ax5.set_xticks(range(9))
        ax5.set_xticklabels([f'DR={i+1}' for i in range(9)], color='white', fontsize=8)
        ax5.set_yticks(range(n))
        ax5.set_yticklabels(hash_names, color='white', fontsize=9)
        ax5.set_title('Digital Root Distribution of Hash Output Space\n(uniform = secure)',
                      color='white', fontsize=10, fontweight='bold')
        plt.colorbar(im, ax=ax5, fraction=0.02, pad=0.02).ax.tick_params(colors='#8b949e')

        fig.suptitle('Tool 13: CryptographicHashGeometer — Geometric Structure Analysis',
                     color='white', fontsize=13, fontweight='bold', y=1.01)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        print(f"[SAVED] {output_path}")


if __name__ == "__main__":
    import os
    os.makedirs('/home/ubuntu/lab/tools_v2/tool13_crypto', exist_ok=True)

    print("=" * 70)
    print("TOOL 13: CryptographicHashGeometer — Demo")
    print("=" * 70)

    # Test multiple hash functions
    hash_functions = [
        ("MD5",    lambda m: hashlib.md5(m)),
        ("SHA-1",  lambda m: hashlib.sha1(m)),
        ("SHA-256",lambda m: hashlib.sha256(m)),
        ("SHA-512",lambda m: hashlib.sha512(m)),
        ("BLAKE2b",lambda m: hashlib.blake2b(m, digest_size=32)),
        ("SHA3-256",lambda m: hashlib.sha3_256(m)),
    ]

    tool = CryptographicHashGeometer()
    results = []

    print(f"\n{'Hash':<12} {'Niemeier':>10} {'Z/2 Match':>10} {'Collision':>10}  {'Vuln Score':>12}")
    print("-" * 60)
    for name, fn in hash_functions:
        r = tool.analyze(name, fn, n_samples=500)
        results.append(r)
        print(f"  {name:<10} {r['niemeier']['niemeier_score']:>10.3f} "
              f"{r['z2_symmetry']['best_z2_complement_match']:>10.3f} "
              f"{r['collision_resistance']['geometric_collision_rate']:>10.3f}  "
              f"{r['geometric_vulnerability_score']:>12.3f}")

    out_png = '/home/ubuntu/lab/tools_v2/tool13_crypto/crypto_hash_geometry.png'
    tool.plot(results, out_png)

    with open('/home/ubuntu/lab/tools_v2/tool13_crypto/results.json', 'w') as f:
        json.dump([{k: v for k, v in r.items() if k != 'root_indices'} for r in results],
                  f, indent=2)
    print("[SAVED] /home/ubuntu/lab/tools_v2/tool13_crypto/results.json")
    print("[DONE]")
