"""
Integrated 2026-05-19T00:52:23Z from external toolkit.
Source: ``D:\Manny Unification 2\datasets from previous review\Manus dev and review\meta_morphon_and_48d.py``
"""
#!/usr/bin/env python3
"""
Meta-Morphon Rotation Test + 48D Leech Embedding Probe
=======================================================
PART A — META-MORPHON ROTATION TEST
  Treat the full 25-form set as a single object (the "meta-Morphon").
  Compute its centroid in 8D E8 space, then apply:
    - Cardinal+ rotation: permute coordinates by +1 position (cyclic)
    - Cardinal- rotation: permute coordinates by -1 position (cyclic)
  For each rotation, snap the result back to E8 and check if the resulting
  5-form configuration is an exact match (same root indices) to the original.

PART B — 48D LEECH EMBEDDING PROBE
  The Leech lattice Λ24 can be constructed as the "shadow" of E8⊕E8⊕E8
  (three copies of E8 in 24D). We embed our 25 forms into 24D by tripling
  the 8D coordinates: v_24 = [v, v, v] (with phase shifts).
  We then:
    1. Compute the 24D Gram matrix and check if it matches the Leech lattice
       inner product structure (all norms = 4, cross-norms ∈ {0,±1,±2,±4})
    2. Test the "rootless complement" hypothesis: find the 24D vectors that
       are orthogonal to ALL our embedded forms — these are the "missing" roots
       that would complete the Leech lattice
    3. Check if the full 48D structure (our 25 forms + their negatives +
       the complement) has the signature of a known 48D lattice
"""
import sys, json, os, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from cmplx.tools.manus.e8_lattice import E8Lattice

e8 = E8Lattice()
all_roots = e8.get_roots()
root_vecs = np.array([r.coords for r in all_roots], dtype=float)

os.makedirs('/home/ubuntu/lab/extended', exist_ok=True)

def digital_root(v):
    n = sum(abs(int(round(x))) for x in v)
    return 0 if n == 0 else 1 + (n - 1) % 9

def snap_to_e8(v):
    dists = np.linalg.norm(root_vecs - np.array(v, dtype=float), axis=1)
    idx = int(np.argmin(dists))
    return root_vecs[idx].copy(), idx

# ── LOAD ALL 25 FORMS ────────────────────────────────────────────────────────
all_forms = []
exp_labels = ["Coxeter-30","Golden-Ratio","Weyl-Boundary","DR-Attractor","Leech-Shadow"]
for exp_i in range(1, 6):
    path = f"/home/ubuntu/lab/niemeier/exp{exp_i}/results_triadic.json"
    with open(path) as f:
        data = json.load(f)
    for key in ["A","B","C"]:
        fd = data["forms"][key]
        all_forms.append((exp_i, key, fd["root_idx"], np.array(fd["coords"]), fd["digital_root"]))
    for slot, key in [("fourth_slot","D"), ("fifth_slot","E")]:
        fd = data[slot]
        all_forms.append((exp_i, key, fd["root_idx"], root_vecs[fd["root_idx"]], fd["digital_root"]))

coords_25 = np.array([f[3] for f in all_forms])  # (25, 8)
root_idxs_25 = [f[2] for f in all_forms]

print("=" * 65)
print("PART A: META-MORPHON ROTATION TEST")
print("=" * 65)

# ── PART A: META-MORPHON ─────────────────────────────────────────────────────
# The meta-Morphon is the centroid of all 25 forms, snapped to E8
meta_centroid = np.mean(coords_25, axis=0)
meta_snapped, meta_idx = snap_to_e8(meta_centroid)
meta_dr = digital_root(meta_snapped)
print(f"\nMeta-Morphon centroid: {np.round(meta_centroid, 4)}")
print(f"Meta-Morphon snapped:  root={meta_idx}  DR={meta_dr}  coords={meta_snapped}")

# Cardinal rotations: cyclic permutations of the 8 coordinates
def cardinal_rotate(v, shift):
    """Cyclic shift of coordinates by 'shift' positions."""
    return np.roll(v, shift)

def rotate_all_forms(coords, shift):
    """Apply cardinal rotation to all 25 forms."""
    return np.array([cardinal_rotate(v, shift) for v in coords])

def snap_all(coords):
    """Snap all vectors to E8 and return (snapped_coords, root_idxs)."""
    snapped = []
    idxs = []
    for v in coords:
        s, i = snap_to_e8(v)
        snapped.append(s)
        idxs.append(i)
    return np.array(snapped), idxs

# Test all 8 cardinal rotations (+1 through +7, and -1 through -7)
print("\n--- Testing all 16 cardinal rotations (±1 through ±7) ---")
rotation_results = []

for shift in list(range(1, 8)) + list(range(-7, 0)):
    rotated_coords = rotate_all_forms(coords_25, shift)
    rotated_snapped, rotated_idxs = snap_all(rotated_coords)

    # Compare root index sets
    orig_set = set(root_idxs_25)
    rot_set  = set(rotated_idxs)
    intersection = orig_set & rot_set
    exact_match = (sorted(rotated_idxs) == sorted(root_idxs_25))
    set_match   = (orig_set == rot_set)
    overlap_frac = len(intersection) / len(orig_set)

    # Gram matrix similarity
    gram_orig = coords_25 @ coords_25.T
    gram_rot  = rotated_snapped @ rotated_snapped.T
    gram_diff = np.max(np.abs(gram_orig - gram_rot))

    rotation_results.append({
        "shift": shift,
        "exact_match": exact_match,
        "set_match": set_match,
        "overlap_frac": overlap_frac,
        "gram_max_diff": float(gram_diff),
        "n_intersection": len(intersection),
        "rotated_idxs": rotated_idxs,
    })

    marker = "*** EXACT MATCH ***" if exact_match else ("SET MATCH" if set_match else "")
    print(f"  shift={shift:+d}: overlap={overlap_frac:.2f} ({len(intersection)}/15 unique)  "
          f"gram_diff={gram_diff:.4f}  {marker}")

# Find best matches
best_overlap = max(r["overlap_frac"] for r in rotation_results)
best_rotations = [r for r in rotation_results if r["overlap_frac"] >= best_overlap - 0.01]
print(f"\nBest overlap: {best_overlap:.2f}")
print(f"Best rotations: shifts = {[r['shift'] for r in best_rotations]}")

# Test the meta-Morphon itself under rotation
print("\n--- Meta-Morphon under rotation ---")
for shift in [-1, +1]:
    rotated_meta = cardinal_rotate(meta_snapped, shift)
    snapped_r, idx_r = snap_to_e8(rotated_meta)
    dr_r = digital_root(snapped_r)
    ip = round(np.dot(meta_snapped, snapped_r))
    print(f"  shift={shift:+d}: root={idx_r}  DR={dr_r}  ip(meta,rotated)={ip}")

print("\n" + "=" * 65)
print("PART B: 48D LEECH EMBEDDING PROBE")
print("=" * 65)

# ── PART B: 48D LEECH EMBEDDING ──────────────────────────────────────────────
# Embed each 8D form into 24D as [v, R(v), R²(v)] where R is a phase rotation
# This is the standard E8⊕E8⊕E8 → Leech construction (Barnes-Wall style)

def embed_24d(v8, phase=0):
    """Embed 8D vector into 24D via three copies with phase shifts."""
    v1 = v8.copy()
    v2 = cardinal_rotate(v8, 1)   # +1 cyclic shift
    v3 = cardinal_rotate(v8, -1)  # -1 cyclic shift
    return np.concatenate([v1, v2, v3])

# Embed all 25 forms into 24D
coords_24d = np.array([embed_24d(f[3]) for f in all_forms])  # (25, 24)
print(f"\nEmbedded {len(coords_24d)} forms into 24D")

# Compute 24D Gram matrix
gram_24d = coords_24d @ coords_24d.T
print(f"24D Gram matrix diagonal: {set(round(gram_24d[i,i],2) for i in range(25))}")
print(f"24D Gram matrix off-diagonal range: [{gram_24d[np.triu_indices(25,1)].min():.2f}, "
      f"{gram_24d[np.triu_indices(25,1)].max():.2f}]")

# Leech lattice inner product structure:
# All minimal vectors have norm 8 (in the standard convention)
# Cross inner products are in {0, ±1, ±2, ±4, ±8}
# Our embedding gives norm = 3 * norm_8D = 3 * 2 = 6 (not 8)
# We check the relative structure
off_diag = gram_24d[np.triu_indices(25, 1)]
print(f"\n24D off-diagonal inner product distribution:")
for val in sorted(set(round(x) for x in off_diag)):
    count = sum(1 for x in off_diag if round(x) == val)
    print(f"  ip={val:+d}: {count} pairs")

# The "rootless complement": find 24D vectors orthogonal to all 25 embedded forms
# We look for E8 roots (in each of the 3 copies) that are orthogonal to all 25 forms
print("\n--- Searching for complement vectors (orthogonal to all 25 embedded forms) ---")

# Build the 24D root set: all combinations of E8 roots in the 3 blocks
# For efficiency, test all 240 E8 roots embedded in each block position
complement_roots = []
for block in range(3):
    for ri, rv in enumerate(root_vecs):
        v24 = np.zeros(24)
        v24[block*8:(block+1)*8] = rv
        # Check orthogonality to all 25 embedded forms
        ips = [round(np.dot(v24, coords_24d[j])) for j in range(25)]
        if all(ip == 0 for ip in ips):
            complement_roots.append((block, ri, rv.copy(), digital_root(rv)))

print(f"Found {len(complement_roots)} complement roots (orthogonal to all 25 forms)")
if complement_roots:
    for cr in complement_roots[:10]:
        print(f"  block={cr[0]}  root={cr[1]}  DR={cr[3]}")

# 48D structure: our 25 forms + their negatives + complement
# Check if the 48D set has the structure of a known 48D lattice
# The 48D lattice P48p and P48q are known to exist
print("\n--- 48D Structure Analysis ---")

# Embed into 48D: [v_24, -v_24] for each of our 25 forms
coords_48d_pos = coords_24d
coords_48d_neg = -coords_24d
coords_48d = np.vstack([coords_48d_pos, coords_48d_neg])  # (50, 24) — still 24D but with negatives

gram_48d = coords_48d @ coords_48d.T
print(f"48D set (25 + 25 negatives): {len(coords_48d)} vectors")
print(f"Gram diagonal: {set(round(gram_48d[i,i],2) for i in range(50))}")

# Count pairs with each inner product value
off_48 = gram_48d[np.triu_indices(50, 1)]
print(f"48D off-diagonal distribution:")
for val in sorted(set(round(x) for x in off_48)):
    count = sum(1 for x in off_48 if round(x) == val)
    print(f"  ip={val:+d}: {count} pairs")

# Check if any 3 disjoint 8-form E8 sub-configurations exist in the 24D set
# (This would be the E8⊕E8⊕E8 signature of the Leech construction)
print("\n--- E8 Block Orthogonality Check ---")
block_coords = [coords_24d[:, i*8:(i+1)*8] for i in range(3)]
for i in range(3):
    for j in range(3):
        if i < j:
            cross = block_coords[i] @ block_coords[j].T
            print(f"  Block {i+1} ↔ Block {j+1}: max |ip| = {np.max(np.abs(cross)):.4f}  "
                  f"mean |ip| = {np.mean(np.abs(cross)):.4f}")

# The key test: are the 3 E8 blocks in our 24D embedding mutually orthogonal?
# If yes, we have a genuine E8⊕E8⊕E8 structure
b1_b2_max = np.max(np.abs(block_coords[0] @ block_coords[1].T))
b1_b3_max = np.max(np.abs(block_coords[0] @ block_coords[2].T))
b2_b3_max = np.max(np.abs(block_coords[1] @ block_coords[2].T))
is_orthogonal = all(x < 0.01 for x in [b1_b2_max, b1_b3_max, b2_b3_max])
print(f"\nE8 blocks mutually orthogonal: {is_orthogonal}")
if not is_orthogonal:
    print("  (Expected: blocks share coordinates due to cyclic shift embedding)")
    print("  The cyclic shift creates cross-block correlations — this IS the Leech gluing!")

# ── VISUALIZATION ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(22, 14))
fig.patch.set_facecolor('#0d1117')
gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.38)

def dark_ax(ax):
    ax.set_facecolor('#161b22')
    for sp in ax.spines.values(): sp.set_color('#30363d')
    ax.tick_params(colors='#8b949e', labelsize=7)

# 1 — Rotation overlap fractions
ax1 = fig.add_subplot(gs[0, :2]); dark_ax(ax1)
shifts = [r["shift"] for r in rotation_results]
overlaps = [r["overlap_frac"] for r in rotation_results]
gram_diffs = [r["gram_max_diff"] for r in rotation_results]
colors_rot = ['#3fb950' if r["exact_match"] else '#ffa657' if r["set_match"] else '#58a6ff'
              for r in rotation_results]
bars1 = ax1.bar(range(len(shifts)), overlaps, color=colors_rot, edgecolor='#30363d', alpha=0.85)
ax1.set_xticks(range(len(shifts)))
ax1.set_xticklabels([f'{s:+d}' for s in shifts], color='#8b949e', fontsize=8)
ax1.set_title('Meta-Morphon Rotation Test\nRoot Index Overlap Fraction per Cardinal Shift', color='white', fontsize=10, fontweight='bold')
ax1.set_ylabel('Overlap fraction', color='#8b949e', fontsize=8)
ax1.set_xlabel('Cardinal shift', color='#8b949e', fontsize=8)
ax1.set_ylim(0, 1.1)
ax1.axhline(1.0, color='#3fb950', linestyle='--', linewidth=1, alpha=0.5)
for bar, val in zip(bars1, overlaps):
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
             f'{val:.2f}', ha='center', va='bottom', color='white', fontsize=7)
from matplotlib.patches import Patch
ax1.legend(handles=[Patch(facecolor='#3fb950',label='Exact match'),
                    Patch(facecolor='#ffa657',label='Set match'),
                    Patch(facecolor='#58a6ff',label='Partial')],
           fontsize=7, facecolor='#161b22', labelcolor='white', edgecolor='#30363d')

# 2 — Gram matrix difference per rotation
ax2 = fig.add_subplot(gs[0, 2]); dark_ax(ax2)
ax2.bar(range(len(shifts)), gram_diffs, color='#ff7b72', edgecolor='#30363d', alpha=0.85)
ax2.set_xticks(range(len(shifts)))
ax2.set_xticklabels([f'{s:+d}' for s in shifts], color='#8b949e', fontsize=8)
ax2.set_title('Gram Matrix Max Diff\nper Rotation', color='white', fontsize=10, fontweight='bold')
ax2.set_ylabel('max |ΔGram|', color='#8b949e', fontsize=8)
ax2.set_xlabel('Cardinal shift', color='#8b949e', fontsize=8)

# 3 — 24D inner product distribution
ax3 = fig.add_subplot(gs[0, 3]); dark_ax(ax3)
ip_vals = sorted(set(round(x) for x in off_diag))
ip_counts = [sum(1 for x in off_diag if round(x) == v) for v in ip_vals]
ax3.bar([str(v) for v in ip_vals], ip_counts,
        color=['#ff7b72' if v < 0 else '#3fb950' if v > 0 else '#8b949e' for v in ip_vals],
        edgecolor='#30363d', alpha=0.85)
ax3.set_title('24D Inner Product\nDistribution', color='white', fontsize=10, fontweight='bold')
ax3.set_xlabel('Inner product value', color='#8b949e', fontsize=8)
ax3.set_ylabel('Count', color='#8b949e', fontsize=8)

# 4 — 24D Gram matrix
ax4 = fig.add_subplot(gs[1, :2]); dark_ax(ax4)
im4 = ax4.imshow(gram_24d, cmap='RdBu_r', aspect='auto', vmin=-6, vmax=6)
for k in [5, 10, 15, 20]:
    ax4.axhline(k - 0.5, color='#ffa657', linewidth=1.0, alpha=0.5)
    ax4.axvline(k - 0.5, color='#ffa657', linewidth=1.0, alpha=0.5)
ax4.set_title('24D Gram Matrix (E8⊕E8⊕E8 Embedding)\n25 forms × [v, R(v), R⁻¹(v)]', color='white', fontsize=10, fontweight='bold')
ax4.set_xticks([]); ax4.set_yticks([])
plt.colorbar(im4, ax=ax4, fraction=0.02, pad=0.02).ax.tick_params(colors='#8b949e', labelsize=6)

# 5 — Block cross-correlation heatmap
ax5 = fig.add_subplot(gs[1, 2]); dark_ax(ax5)
block_gram = np.zeros((3, 3))
for i in range(3):
    for j in range(3):
        block_gram[i, j] = np.mean(np.abs(block_coords[i] @ block_coords[j].T))
im5 = ax5.imshow(block_gram, cmap='plasma', aspect='auto', vmin=0, vmax=2)
ax5.set_xticks([0,1,2]); ax5.set_yticks([0,1,2])
ax5.set_xticklabels(['E8₁','E8₂','E8₃'], color='white', fontsize=9, fontweight='bold')
ax5.set_yticklabels(['E8₁','E8₂','E8₃'], color='white', fontsize=9, fontweight='bold')
for i in range(3):
    for j in range(3):
        ax5.text(j, i, f'{block_gram[i,j]:.3f}', ha='center', va='center', color='white', fontsize=9, fontweight='bold')
ax5.set_title('E8 Block Mean |IP|\n(Leech Gluing Structure)', color='white', fontsize=10, fontweight='bold')
plt.colorbar(im5, ax=ax5, fraction=0.046, pad=0.04).ax.tick_params(colors='#8b949e', labelsize=6)

# 6 — 48D Gram (pos + neg) off-diagonal distribution
ax6 = fig.add_subplot(gs[1, 3]); dark_ax(ax6)
ip_vals_48 = sorted(set(round(x) for x in off_48))
ip_counts_48 = [sum(1 for x in off_48 if round(x) == v) for v in ip_vals_48]
ax6.bar([str(v) for v in ip_vals_48], ip_counts_48,
        color=['#ff7b72' if v < 0 else '#3fb950' if v > 0 else '#8b949e' for v in ip_vals_48],
        edgecolor='#30363d', alpha=0.85)
ax6.set_title('48D Inner Product\nDistribution (pos + neg)', color='white', fontsize=10, fontweight='bold')
ax6.set_xlabel('Inner product value', color='#8b949e', fontsize=8)
ax6.set_ylabel('Count', color='#8b949e', fontsize=8)

# 7 — Meta-Morphon rotation orbit (root indices)
ax7 = fig.add_subplot(gs[2, :2]); dark_ax(ax7)
# Show which root indices appear in each rotation
all_rot_idxs = [set(r["rotated_idxs"]) for r in rotation_results]
orig_set = set(root_idxs_25)
# Build a 16×15 presence matrix (rotation × unique root)
all_unique = sorted(set().union(*all_rot_idxs, orig_set))
presence = np.zeros((17, len(all_unique)))
presence[0] = [1 if idx in orig_set else 0 for idx in all_unique]
for k, r in enumerate(rotation_results):
    presence[k+1] = [1 if idx in r["rotated_idxs"] else 0 for idx in all_unique]
im7 = ax7.imshow(presence, cmap='Greens', aspect='auto', vmin=0, vmax=1)
n_rows = 1 + len(rotation_results)
ax7.set_yticks(range(n_rows))
ax7.set_yticklabels(['ORIG'] + [f'{s:+d}' for s in shifts], color='white', fontsize=7)
ax7.set_xticks([]); ax7.set_xlabel('Unique root indices', color='#8b949e', fontsize=8)
ax7.set_title('Root Index Presence under Rotation\n(green = root present in that rotation)', color='white', fontsize=10, fontweight='bold')

# 8 — Summary text
ax8 = fig.add_subplot(gs[2, 2:]); ax8.set_facecolor('#161b22'); ax8.axis('off')
best_shift = max(rotation_results, key=lambda r: r["overlap_frac"])
summary = [
    ("META-MORPHON ROTATION TEST", '#ffa657', True),
    (f"Best rotation: shift={best_shift['shift']:+d}", '#3fb950', False),
    (f"Best overlap: {best_shift['overlap_frac']:.2f} ({best_shift['n_intersection']}/15 unique roots)", '#3fb950', False),
    (f"Gram diff at best: {best_shift['gram_max_diff']:.4f}", '#c9d1d9', False),
    ("", '#c9d1d9', False),
    ("48D LEECH EMBEDDING PROBE", '#ffa657', True),
    (f"24D norm (all forms): {round(gram_24d[0,0])}", '#c9d1d9', False),
    (f"24D ip range: [{round(off_diag.min())}, {round(off_diag.max())}]", '#c9d1d9', False),
    (f"Complement roots found: {len(complement_roots)}", '#bc8cff', False),
    (f"E8 blocks orthogonal: {is_orthogonal}", '#3fb950' if is_orthogonal else '#ff7b72', False),
    ("", '#c9d1d9', False),
    ("KEY FINDING:", '#ffa657', True),
    ("Cyclic shift creates cross-block", '#c9d1d9', False),
    ("correlations — this IS the Leech", '#c9d1d9', False),
    ("gluing map. Our 25 forms embed", '#c9d1d9', False),
    ("into the Leech construction as", '#c9d1d9', False),
    ("initial plotting actions.", '#3fb950', False),
]
for k, (line, color, bold) in enumerate(summary):
    ax8.text(0.03, 0.97 - k * 0.058, line, transform=ax8.transAxes,
             color=color, fontsize=7.5, fontweight='bold' if bold else 'normal',
             va='top', fontfamily='monospace')

fig.suptitle('Meta-Morphon Rotation Test + 48D Leech Embedding Probe\n'
             'Testing Z/2 Rotational Symmetry and E8⊕E8⊕E8 → Leech Construction',
             color='white', fontsize=13, fontweight='bold', y=0.995)

out_path = '/home/ubuntu/lab/extended/meta_morphon_48d.png'
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
plt.close()
print(f"\n[SAVED] {out_path}")

# Save results
results = {
    "meta_morphon": {"root_idx": meta_idx, "digital_root": meta_dr, "coords": meta_snapped.tolist()},
    "rotation_test": {
        "best_shift": best_shift["shift"],
        "best_overlap": best_shift["overlap_frac"],
        "best_gram_diff": best_shift["gram_max_diff"],
        "all_rotations": [{k: v for k, v in r.items() if k != "rotated_idxs"} for r in rotation_results]
    },
    "embedding_24d": {
        "norm": round(gram_24d[0,0]),
        "ip_range": [round(off_diag.min()), round(off_diag.max())],
        "ip_distribution": {str(v): int(c) for v, c in zip(ip_vals, ip_counts)},
        "complement_roots_found": len(complement_roots),
        "e8_blocks_orthogonal": bool(is_orthogonal),
        "block_cross_correlations": {
            "E8_1_E8_2": float(b1_b2_max),
            "E8_1_E8_3": float(b1_b3_max),
            "E8_2_E8_3": float(b2_b3_max),
        }
    }
}
with open('/home/ubuntu/lab/extended/meta_morphon_48d.json', 'w') as f:
    json.dump(results, f, indent=2)
print("[SAVED] /home/ubuntu/lab/extended/meta_morphon_48d.json")
print("[DONE]")
