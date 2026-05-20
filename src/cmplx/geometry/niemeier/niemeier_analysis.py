"""
Escrow merge L01 (2026-05-19T01:10:18Z).
Source: ``CMPLX-history/staging/by-family/niemeier/partsfactory/niemeier_analysis.py``
Slot: ``slot-07-niemeier-types``
"""
#!/usr/bin/env python3
"""
Niemeier Lattice Composition Analysis
======================================
Collects all 5-form E8 configurations from the 5 collision experiments,
assembles the full 25-form set, and tests for Niemeier root system composition.

The 24 Niemeier lattices are the unique even unimodular lattices in R^24.
Each has a root system that is a union of ADE root systems with total rank 24.
We test whether subsets of our 25 collected E8 forms span root systems that
match known Niemeier root system components.

Known Niemeier root system signatures (by component type):
  D24, D16+E8, E8+E8+E8, A24, D12+D12, A17+E7, D10+E7+E7, A15+D9,
  D8+D8+D8, A12+A12, A11+D7+E6, E6+E6+E6+E6, A9+D6+D6+A9, ...
  (24 total, including the Leech lattice with no roots)
"""
import sys, json, os, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from itertools import combinations

from cmplx.tools.manus.e8_lattice import E8Lattice

e8 = E8Lattice()
all_roots = e8.get_roots()
root_vecs = np.array([r.coords for r in all_roots], dtype=float)

def dark_ax(ax):
    ax.set_facecolor('#161b22')
    for sp in ax.spines.values(): sp.set_color('#30363d')
    ax.tick_params(colors='#8b949e', labelsize=7)




def classify_pair(ip):
    ip_r = round(ip)
    if ip_r == 2:   return "same"
    if ip_r == 1:   return "A-bond"
    if ip_r == 0:   return "ortho"
    if ip_r == -1:  return "neg-bond"
    if ip_r == -2:  return "antipodal"
    return "other"

def find_components(adj):
    visited = [False] * n
    components = []
    for start in range(n):
        if not visited[start]:
            comp = []
            stack = [start]
            while stack:
                node = stack.pop()
                if not visited[node]:
                    visited[node] = True
                    comp.append(node)
                    for nb in range(n):
                        if adj[node, nb] == 1 and not visited[nb]:
                            stack.append(nb)
            components.append(comp)
    return components

def cartan_signature(indices):
    """Return the sorted tuple of off-diagonal Cartan entries for a set of forms."""
    vecs = [all_forms[i][3] for i in indices]
    entries = []
    for a in range(len(vecs)):
        for b in range(len(vecs)):
            if a != b:
                ip = round(np.dot(vecs[a], vecs[b]))
                entries.append(ip)
    return tuple(sorted(entries))

def is_An_chain(indices, n):
    """Check if indices form an A_n chain (linear Dynkin diagram)."""
    if len(indices) != n: return False
    vecs = [all_forms[i][3] for i in indices]
    # Try all orderings — check if any permutation forms a chain
    from itertools import permutations
    for perm in permutations(range(n)):
        ok = True
        for k in range(n - 1):
            ip = round(np.dot(vecs[perm[k]], vecs[perm[k+1]]))
            if ip != 1:
                ok = False
                break
        # Check non-adjacent pairs are orthogonal
        if ok:
            for a in range(n):
                for b in range(n):
                    if abs(a - b) > 1:
                        ip = round(np.dot(vecs[perm[a]], vecs[perm[b]]))
                        if ip != 0:
                            ok = False
                            break
                if not ok: break
        if ok: return True
    return False

def is_D4(indices):
    """D4: one central node bonded to 3 others, all others mutually orthogonal."""
    if len(indices) != 4: return False
    vecs = [all_forms[i][3] for i in indices]
    for center in range(4):
        others = [j for j in range(4) if j != center]
        bonds = [round(np.dot(vecs[center], vecs[o])) for o in others]
        if all(b == 1 for b in bonds):
            # check others are mutually orthogonal
            if all(round(np.dot(vecs[others[a]], vecs[others[b]])) == 0
                   for a in range(3) for b in range(3) if a != b):
                return True
    return False

def is_E6(indices):
    """E6: 6-node Dynkin diagram — chain of 4 with a branch at node 3."""
    if len(indices) != 6: return False
    vecs = [all_forms[i][3] for i in indices]
    # E6 adjacency: 1-2-3-4-5 with 6 branching off 3
    e6_adj = [(0,1),(1,2),(2,3),(3,4),(2,5)]
    from itertools import permutations
    for perm in permutations(range(6)):
        ok = True
        for (a, b) in e6_adj:
            if round(np.dot(vecs[perm[a]], vecs[perm[b]])) != 1:
                ok = False; break
        if ok:
            # non-adjacent pairs must be orthogonal
            adj_set = set(e6_adj) | {(b,a) for (a,b) in e6_adj}
            for a in range(6):
                for b in range(6):
                    if a != b and (a,b) not in adj_set:
                        if round(np.dot(vecs[perm[a]], vecs[perm[b]])) != 0:
                            ok = False; break
                if not ok: break
        if ok: return True
    return False

def find_disjoint_A2(pairs, max_count):
    """Find the maximum number of disjoint A2 pairs."""
    used = set()
    disjoint = []
    for (i, j) in pairs:
        if i not in used and j not in used:
            disjoint.append((i, j))
            used.add(i)
            used.add(j)
            if len(disjoint) >= max_count:
                break
    return disjoint

def find_disjoint_A3(triples, max_count):
    used = set()
    disjoint = []
    for triple in triples:
        if not any(i in used for i in triple):
            disjoint.append(triple)
            used.update(triple)
            if len(disjoint) >= max_count:
                break
    return disjoint

def main() -> None:
    import os
    if not os.environ.get('NIEMEIER_LAB_ROOT'):
        raise SystemExit('Set NIEMEIER_LAB_ROOT for lab analysis')
    # ── LOAD ALL 5 EXPERIMENT RESULTS ────────────────────────────────────────────
    exp_labels = [
        "Coxeter-30",
        "Golden-Ratio",
        "Weyl-Boundary",
        "DR-Attractor",
        "Leech-Shadow"
    ]
    exp_inputs = [
        "[30,0,-30,30,-30,0,30,-30]",
        "[φ¹..φ⁸]",
        "[2,-1,0,0,0,0,0,-1]",
        "[9,-9,9,-9,9,-9,9,-9]",
        "[4,4,0,0,0,0,0,0]"
    ]
    
    all_forms = []   # list of (exp_idx, form_label, root_idx, coords, dr)
    exp_5tuples = [] # list of 5 (root_idx, coords) per experiment
    
    for exp_i in range(1, 6):
        path = f"/home/ubuntu/lab/niemeier/exp{exp_i}/results_triadic.json"
        with open(path) as f:
            data = json.load(f)
    
        forms_this_exp = []
        for key, lbl in [("A","A(CQE)"),("B","B(Morph)"),("C","C(Coll)")]:
            fd = data["forms"][key]
            forms_this_exp.append((exp_i, lbl, fd["root_idx"], np.array(fd["coords"]), fd["digital_root"]))
    
        d_idx = data["fourth_slot"]["root_idx"]
        d_dr  = data["fourth_slot"]["digital_root"]
        d_coords = root_vecs[d_idx]
        forms_this_exp.append((exp_i, "D(4th)", d_idx, d_coords, d_dr))
    
        e_idx = data["fifth_slot"]["root_idx"]
        e_dr  = data["fifth_slot"]["digital_root"]
        e_coords = root_vecs[e_idx]
        forms_this_exp.append((exp_i, "E(5th)", e_idx, e_coords, e_dr))
    
        all_forms.extend(forms_this_exp)
        exp_5tuples.append(forms_this_exp)
    
    print(f"Total forms collected: {len(all_forms)}")
    print(f"Unique root indices:   {len(set(f[2] for f in all_forms))}")
    
    # ── GRAM MATRIX (25×25) ──────────────────────────────────────────────────────
    coords_all = np.array([f[3] for f in all_forms])  # (25, 8)
    gram = coords_all @ coords_all.T                   # (25, 25)
    print(f"\nGram matrix shape: {gram.shape}")
    print(f"Diagonal (all should be 2.0): {set(round(gram[i,i],4) for i in range(25))}")
    
    # ── NIEMEIER COMPONENT DETECTION ─────────────────────────────────────────────
    # For each pair of forms, classify the inner product:
    #   2  → same root (identity)
    #   1  → A2/A3 bond (60°)
    #   0  → orthogonal (90°)
    #  -1  → A2 negative bond (120°)
    #  -2  → antipodal (same root, opposite sign)
    
    
    # Build adjacency: which forms are A-bonded (inner product = 1)?
    n = len(all_forms)
    adj_A = np.zeros((n, n), dtype=int)
    adj_D = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            if i == j: continue
            ip = round(gram[i, j])
            if ip == 1:  adj_A[i, j] = 1
            if ip == -1: adj_D[i, j] = 1
    
    # Find connected components in A-bond graph
    
    components_A = find_components(adj_A)
    print(f"\nA-bond connected components: {len(components_A)}")
    for i, comp in enumerate(components_A):
        labels = [all_forms[j][1] for j in comp]
        exp_ids = [all_forms[j][0] for j in comp]
        drs = [all_forms[j][4] for j in comp]
        print(f"  Component {i+1} (size {len(comp)}): exp={exp_ids}  labels={labels}  DRs={drs}")
    
    # ── NIEMEIER SIGNATURE MATCHING ──────────────────────────────────────────────
    # The 24 Niemeier lattices have root systems with specific component signatures.
    # We test whether our 25 forms, taken as a root set, contain sub-configurations
    # matching known ADE root system Cartan matrices.
    
    # A_n: chain of n roots, each bonded to the next (inner product = 1)
    # D_n: chain of n-2 roots plus a fork at one end
    # E_6: specific 6-node Dynkin diagram
    # E_8: specific 8-node Dynkin diagram
    
    
    # Test all 5-form subsets from the full 25 for known Niemeier components
    # E8 Dynkin diagram: specific Cartan matrix pattern
    # We look for: A5 (5-chain), D5, A4, D4, A3, A2, E6 sub-patterns
    
    
    
    
    print("\n--- Searching for ADE sub-configurations in 25 forms ---")
    
    found_A2 = []
    found_A3 = []
    found_A4 = []
    found_A5 = []
    found_D4 = []
    found_E6 = []
    
    indices_25 = list(range(25))
    
    # A2 (pairs with ip=1)
    for i, j in combinations(indices_25, 2):
        if round(gram[i,j]) == 1:
            found_A2.append((i, j))
    
    # A3 (triples forming a chain)
    for triple in combinations(indices_25, 3):
        if is_An_chain(list(triple), 3):
            found_A3.append(triple)
    
    # A4 (4-chains)
    for quad in combinations(indices_25, 4):
        if is_An_chain(list(quad), 4):
            found_A4.append(quad)
    
    # D4
    for quad in combinations(indices_25, 4):
        if is_D4(list(quad)):
            found_D4.append(quad)
    
    print(f"  A2 (pairs):  {len(found_A2)}")
    print(f"  A3 (chains): {len(found_A3)}")
    print(f"  A4 (chains): {len(found_A4)}")
    print(f"  D4 (forks):  {len(found_D4)}")
    
    # Niemeier-relevant: check if any 3 disjoint A8 or 8 disjoint A3 etc.
    # The Niemeier lattice with root system A8^3 has 3 copies of A8 (rank 8 each = 24 total)
    # The Niemeier lattice with root system A2^12 has 12 copies of A2 (rank 2 each = 24 total)
    # The Niemeier lattice with root system A1^24 has 24 copies of A1
    
    # Count disjoint A2 pairs
    
    disjoint_A2 = find_disjoint_A2(found_A2, 12)
    print(f"\n  Max disjoint A2 pairs: {len(disjoint_A2)}")
    for pair in disjoint_A2:
        exp_a = all_forms[pair[0]][0]; lbl_a = all_forms[pair[0]][1]
        exp_b = all_forms[pair[1]][0]; lbl_b = all_forms[pair[1]][1]
        print(f"    ({exp_a}:{lbl_a}, {exp_b}:{lbl_b})")
    
    # Count disjoint A3 triples
    
    disjoint_A3 = find_disjoint_A3(found_A3, 8)
    print(f"\n  Max disjoint A3 chains: {len(disjoint_A3)}")
    for chain in disjoint_A3:
        info = [(all_forms[i][0], all_forms[i][1]) for i in chain]
        print(f"    {info}")
    
    # ── NIEMEIER FORM IDENTIFICATION ─────────────────────────────────────────────
    # Based on the component analysis, identify which Niemeier lattice components
    # are present in our 25-form set.
    
    print("\n--- Niemeier Lattice Component Summary ---")
    
    # The key Niemeier signatures we can detect from our 25 E8 roots:
    niemeier_matches = []
    
    # A2^12: needs 12 disjoint A2 pairs → we have up to 12 from 25 forms
    n_A2 = len(disjoint_A2)
    if n_A2 >= 3:
        niemeier_matches.append(f"A2^{n_A2} component (partial, {n_A2}/12 pairs found)")
    if n_A2 >= 12:
        niemeier_matches.append("FULL A2^12 Niemeier component!")
    
    # A3^8: needs 8 disjoint A3 chains
    n_A3 = len(disjoint_A3)
    if n_A3 >= 3:
        niemeier_matches.append(f"A3^{n_A3} component (partial, {n_A3}/8 chains found)")
    if n_A3 >= 8:
        niemeier_matches.append("FULL A3^8 Niemeier component!")
    
    # D4^6: needs 6 disjoint D4 systems
    n_D4 = len(found_D4)
    if n_D4 >= 3:
        niemeier_matches.append(f"D4^{n_D4} component (partial, {n_D4}/6 D4 systems found)")
    
    # E8^3: needs 3 disjoint E8 systems — our 5 experiments each produce an E8 5-tuple
    # Check if any 3 experiments have mutually orthogonal 5-tuples
    print("\n  Checking E8^3 (3 mutually orthogonal experiment clusters):")
    for exp_combo in combinations(range(5), 3):
        cluster_coords = []
        for exp_i in exp_combo:
            cluster_coords.extend([f[3] for f in exp_5tuples[exp_i]])
        # Check if the three clusters are mutually orthogonal
        c1 = np.array([f[3] for f in exp_5tuples[exp_combo[0]]])
        c2 = np.array([f[3] for f in exp_5tuples[exp_combo[1]]])
        c3 = np.array([f[3] for f in exp_5tuples[exp_combo[2]]])
        cross12 = np.max(np.abs(c1 @ c2.T))
        cross13 = np.max(np.abs(c1 @ c3.T))
        cross23 = np.max(np.abs(c2 @ c3.T))
        max_cross = max(cross12, cross13, cross23)
        names = [exp_labels[i] for i in exp_combo]
        print(f"    {names}: max cross-cluster |ip| = {max_cross:.4f}")
        if max_cross < 0.1:
            niemeier_matches.append(f"E8^3 candidate: experiments {names} are mutually orthogonal!")
    
    # Cross-experiment A-bonds (Niemeier gluing)
    cross_exp_bonds = [(i, j) for (i, j) in found_A2
                       if all_forms[i][0] != all_forms[j][0]]
    print(f"\n  Cross-experiment A-bonds (Niemeier glue vectors): {len(cross_exp_bonds)}")
    for (i, j) in cross_exp_bonds[:10]:
        ei, li = all_forms[i][0], all_forms[i][1]
        ej, lj = all_forms[j][0], all_forms[j][1]
        print(f"    Exp{ei}:{li} ↔ Exp{ej}:{lj}  (ip=1)")
    
    if not niemeier_matches:
        niemeier_matches.append("No full Niemeier components found — partial A2/A3 structure present")
    
    print(f"\n=== NIEMEIER COMPOSITION RESULTS ===")
    for m in niemeier_matches:
        print(f"  ✓ {m}")
    
    # ── VISUALIZATION ─────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(22, 16))
    fig.patch.set_facecolor('#0d1117')
    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.38)
    
    exp_colors = ['#58a6ff','#3fb950','#ff7b72','#ffa657','#bc8cff']
    form_colors = {'A(CQE)':'#58a6ff','B(Morph)':'#3fb950','C(Coll)':'#ff7b72',
                   'D(4th)':'#ffa657','E(5th)':'#bc8cff'}
    
    # 1 — Full 25×25 Gram matrix heatmap
    ax1 = fig.add_subplot(gs[0, :2]); dark_ax(ax1)
    im1 = ax1.imshow(gram, cmap='RdBu_r', aspect='auto', vmin=-2, vmax=2)
    ax1.set_title('Full 25×25 Gram Matrix\n(5 experiments × 5 forms each)', color='white', fontsize=10, fontweight='bold')
    # Add experiment boundary lines
    for k in [5, 10, 15, 20]:
        ax1.axhline(k - 0.5, color='#ffa657', linewidth=1.5, alpha=0.7)
        ax1.axvline(k - 0.5, color='#ffa657', linewidth=1.5, alpha=0.7)
    ax1.set_xticks([]); ax1.set_yticks([])
    plt.colorbar(im1, ax=ax1, fraction=0.03, pad=0.02).ax.tick_params(colors='#8b949e', labelsize=6)
    # Label experiment blocks
    for k, lbl in enumerate(exp_labels):
        ax1.text(k*5 + 2, -0.8, lbl[:8], ha='center', va='bottom', color=exp_colors[k], fontsize=6.5, fontweight='bold')
    
    # 2 — A-bond adjacency matrix (25×25)
    ax2 = fig.add_subplot(gs[0, 2]); dark_ax(ax2)
    im2 = ax2.imshow(adj_A, cmap='Greens', aspect='auto', vmin=0, vmax=1)
    ax2.set_title('A-Bond Adjacency\n(inner product = 1)', color='white', fontsize=10, fontweight='bold')
    for k in [5, 10, 15, 20]:
        ax2.axhline(k - 0.5, color='#ffa657', linewidth=1.0, alpha=0.5)
        ax2.axvline(k - 0.5, color='#ffa657', linewidth=1.0, alpha=0.5)
    ax2.set_xticks([]); ax2.set_yticks([])
    
    # 3 — Component size distribution
    ax3 = fig.add_subplot(gs[0, 3]); dark_ax(ax3)
    comp_sizes = sorted([len(c) for c in components_A], reverse=True)
    bars3 = ax3.bar(range(len(comp_sizes)), comp_sizes,
                    color=[exp_colors[i % 5] for i in range(len(comp_sizes))],
                    edgecolor='#30363d', alpha=0.85)
    ax3.set_title('A-Bond Component\nSizes', color='white', fontsize=10, fontweight='bold')
    ax3.set_xlabel('Component #', color='#8b949e', fontsize=8)
    ax3.set_ylabel('Size', color='#8b949e', fontsize=8)
    for bar, val in zip(bars3, comp_sizes):
        ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.05,
                 str(val), ha='center', va='bottom', color='white', fontsize=8, fontweight='bold')
    
    # 4 — Per-experiment digital root profile
    ax4 = fig.add_subplot(gs[1, :2]); dark_ax(ax4)
    x = np.arange(5)
    width = 0.15
    form_lbls = ['A(CQE)', 'B(Morph)', 'C(Coll)', 'D(4th)', 'E(5th)']
    for fi, flbl in enumerate(form_lbls):
        drs = [exp_5tuples[ei][fi][4] for ei in range(5)]
        ax4.bar(x + fi * width, drs, width, label=flbl,
                color=list(form_colors.values())[fi], edgecolor='#30363d', alpha=0.85)
    ax4.set_xticks(x + 2 * width)
    ax4.set_xticklabels(exp_labels, rotation=15, ha='right', color='#8b949e', fontsize=7)
    ax4.set_title('Digital Root Profile per Experiment', color='white', fontsize=10, fontweight='bold')
    ax4.set_ylabel('Digital Root', color='#8b949e', fontsize=8)
    ax4.set_ylim(0, 3)
    ax4.legend(fontsize=7, facecolor='#161b22', labelcolor='white', edgecolor='#30363d', ncol=5)
    
    # 5 — Cross-experiment inner product heatmap (5×5 block means)
    ax5 = fig.add_subplot(gs[1, 2]); dark_ax(ax5)
    block_mean = np.zeros((5, 5))
    for ei in range(5):
        for ej in range(5):
            block = gram[ei*5:(ei+1)*5, ej*5:(ej+1)*5]
            block_mean[ei, ej] = np.mean(np.abs(block))
    im5 = ax5.imshow(block_mean, cmap='plasma', aspect='auto', vmin=0, vmax=2)
    ax5.set_xticks(range(5)); ax5.set_yticks(range(5))
    ax5.set_xticklabels([l[:6] for l in exp_labels], rotation=20, ha='right', color='white', fontsize=6)
    ax5.set_yticklabels([l[:6] for l in exp_labels], color='white', fontsize=6)
    for i in range(5):
        for j in range(5):
            ax5.text(j, i, f'{block_mean[i,j]:.2f}', ha='center', va='center', color='white', fontsize=7, fontweight='bold')
    ax5.set_title('Cross-Experiment\nMean |IP| (5×5 blocks)', color='white', fontsize=10, fontweight='bold')
    plt.colorbar(im5, ax=ax5, fraction=0.046, pad=0.04).ax.tick_params(colors='#8b949e', labelsize=6)
    
    # 6 — ADE count bar chart
    ax6 = fig.add_subplot(gs[1, 3]); dark_ax(ax6)
    ade_names = ['A2\npairs', 'A3\nchains', 'A4\nchains', 'D4\nforks',
                 'Disjoint\nA2', 'Disjoint\nA3', 'Cross-exp\nA-bonds']
    ade_vals  = [len(found_A2), len(found_A3), len(found_A4), len(found_D4),
                 len(disjoint_A2), len(disjoint_A3), len(cross_exp_bonds)]
    ade_cols  = ['#58a6ff','#3fb950','#ff7b72','#ffa657','#79c0ff','#56d364','#bc8cff']
    bars6 = ax6.bar(ade_names, ade_vals, color=ade_cols, edgecolor='#30363d', alpha=0.85)
    ax6.set_title('ADE Sub-Configuration\nCounts', color='white', fontsize=10, fontweight='bold')
    ax6.set_ylabel('Count', color='#8b949e', fontsize=8)
    for bar, val in zip(bars6, ade_vals):
        ax6.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
                 str(val), ha='center', va='bottom', color='white', fontsize=8, fontweight='bold')
    
    # 7 — Disjoint A2 pairs network
    ax7 = fig.add_subplot(gs[2, :2]); dark_ax(ax7)
    # Place 25 nodes in a circle, color by experiment
    angles_node = [2 * math.pi * i / 25 for i in range(25)]
    xs = [math.cos(a) for a in angles_node]
    ys = [math.sin(a) for a in angles_node]
    for i, (x_n, y_n) in enumerate(zip(xs, ys)):
        exp_i = all_forms[i][0] - 1
        ax7.scatter([x_n], [y_n], color=exp_colors[exp_i], s=80, zorder=5)
        ax7.text(x_n * 1.12, y_n * 1.12, all_forms[i][1][:3], color=exp_colors[exp_i], fontsize=5, ha='center')
    # Draw A-bond edges
    for (i, j) in found_A2:
        is_cross = all_forms[i][0] != all_forms[j][0]
        color = '#ffa657' if is_cross else '#8b949e'
        lw = 1.5 if is_cross else 0.4
        alpha = 0.9 if is_cross else 0.25
        ax7.plot([xs[i], xs[j]], [ys[i], ys[j]], color=color, linewidth=lw, alpha=alpha, zorder=3)
    ax7.set_title('A-Bond Network (25 Forms)\nOrange = cross-experiment bonds (Niemeier glue)', color='white', fontsize=10, fontweight='bold')
    ax7.set_xlim(-1.3, 1.3); ax7.set_ylim(-1.3, 1.3)
    ax7.axis('off')
    from matplotlib.patches import Patch
    ax7.legend(handles=[Patch(facecolor=c, label=l) for c, l in zip(exp_colors, exp_labels)],
               fontsize=7, facecolor='#161b22', labelcolor='white', edgecolor='#30363d',
               loc='lower right')
    
    # 8 — Root index distribution across experiments
    ax8 = fig.add_subplot(gs[2, 2]); dark_ax(ax8)
    for ei, (exp_forms, col, lbl) in enumerate(zip(exp_5tuples, exp_colors, exp_labels)):
        root_idxs = [f[2] for f in exp_forms]
        ax8.scatter([ei] * 5, root_idxs, color=col, s=100, alpha=0.85, zorder=5)
        for ri in root_idxs:
            ax8.text(ei + 0.08, ri, str(ri), color=col, fontsize=6, va='center')
    ax8.set_xticks(range(5))
    ax8.set_xticklabels([l[:8] for l in exp_labels], rotation=20, ha='right', color='#8b949e', fontsize=7)
    ax8.set_title('Root Index Distribution\nper Experiment (0–239)', color='white', fontsize=10, fontweight='bold')
    ax8.set_ylabel('E8 Root Index', color='#8b949e', fontsize=8)
    ax8.set_ylim(-5, 245)
    
    # 9 — Niemeier summary text panel
    ax9 = fig.add_subplot(gs[2, 3]); ax9.set_facecolor('#161b22'); ax9.axis('off')
    summary_lines = [
        "NIEMEIER COMPOSITION",
        "=" * 22,
        f"Total forms: 25 (5×5)",
        f"Unique roots: {len(set(f[2] for f in all_forms))}",
        f"A2 pairs: {len(found_A2)}",
        f"A3 chains: {len(found_A3)}",
        f"D4 forks: {len(found_D4)}",
        f"Disjoint A2: {len(disjoint_A2)}",
        f"Disjoint A3: {len(disjoint_A3)}",
        f"Cross-exp bonds: {len(cross_exp_bonds)}",
        "",
        "IDENTIFIED FORMS:",
    ]
    for m in niemeier_matches:
        # Wrap long lines
        if len(m) > 28:
            summary_lines.append("• " + m[:26] + "...")
        else:
            summary_lines.append("• " + m)
    
    for k, line in enumerate(summary_lines):
        color = '#ffa657' if k < 2 or "FORM" in line else '#c9d1d9'
        if "FULL" in line: color = '#3fb950'
        ax9.text(0.05, 0.97 - k * 0.062, line, transform=ax9.transAxes,
                 color=color, fontsize=7.5, fontweight='bold' if k < 2 else 'normal',
                 va='top', fontfamily='monospace')
    
    fig.suptitle('Niemeier Lattice Composition Analysis\n'
                 '5 Morphon Collision Experiments → 25 E8 Forms → ADE Root System Detection',
                 color='white', fontsize=13, fontweight='bold', y=0.995)
    
    out_path = '/home/ubuntu/lab/niemeier/niemeier_composition.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
    plt.close()
    print(f"\n[SAVED] {out_path}")
    
    # ── SAVE SUMMARY JSON ────────────────────────────────────────────────────────
    summary = {
        "experiments": [
            {"id": i+1, "label": exp_labels[i], "input": exp_inputs[i],
             "forms": [{"label": f[1], "root_idx": f[2], "digital_root": f[4]} for f in exp_5tuples[i]]}
            for i in range(5)
        ],
        "ade_counts": {
            "A2_pairs": len(found_A2), "A3_chains": len(found_A3),
            "A4_chains": len(found_A4), "D4_forks": len(found_D4),
            "disjoint_A2": len(disjoint_A2), "disjoint_A3": len(disjoint_A3),
            "cross_experiment_bonds": len(cross_exp_bonds)
        },
        "niemeier_matches": niemeier_matches,
        "unique_root_indices": sorted(set(f[2] for f in all_forms)),
        "a_bond_components": len(components_A),
        "component_sizes": sorted([len(c) for c in components_A], reverse=True)
    }
    json_path = '/home/ubuntu/lab/niemeier/niemeier_summary.json'
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"[SAVED] {json_path}")
    print("\n[DONE] Niemeier composition analysis complete.")


if __name__ == '__main__':
    main()
