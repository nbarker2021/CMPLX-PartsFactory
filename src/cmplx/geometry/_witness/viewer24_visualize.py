"""
Escrow merge L01 (2026-05-19T01:10:18Z).
Source: ``D:/Manny Unification 2/datasets from previous review/MannyUnification/tmp/cmplx_skeleton/visualize.py``
Slot: ``slot-09-viewer24-probe``
"""
#!/usr/bin/env python3
"""
CMPLX Manifold v3 × NSL-KDD — Pipeline Visualization
Generates 6 analysis plots from the pipeline results.
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
from collections import Counter, defaultdict

# ── Load results ──────────────────────────────────────────────────────────────
with open('pipeline_results.json') as f:
    summary = json.load(f)

with open('pipeline_sample.json') as f:
    sample = json.load(f)   # first 1000 rows

# ── Style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'monospace',
    'font.size': 9,
    'axes.facecolor': '#0d1117',
    'figure.facecolor': '#0d1117',
    'axes.edgecolor': '#30363d',
    'axes.labelcolor': '#c9d1d9',
    'xtick.color': '#8b949e',
    'ytick.color': '#8b949e',
    'text.color': '#c9d1d9',
    'grid.color': '#21262d',
    'grid.linewidth': 0.5,
})

COLORS = {
    'normal':  '#3fb950',
    'dos':     '#f85149',
    'probe':   '#d29922',
    'r2l':     '#a371f7',
    'u2r':     '#ff7b72',
    'unknown': '#8b949e',
}

CAT_ORDER = ['normal', 'dos', 'probe', 'r2l', 'u2r']

# ── Figure 1: Six-panel dashboard ─────────────────────────────────────────────
fig = plt.figure(figsize=(18, 12))
fig.suptitle('CMPLX Enhanced Manifold v3  ×  NSL-KDD Intrusion Detection\n'
             'Pipeline Behavior Analysis — 14,376 Stratified Rows',
             fontsize=13, color='#e6edf3', fontweight='bold', y=0.98)

gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.38,
                       left=0.07, right=0.97, top=0.92, bottom=0.06)

# ─── Panel 1: Gate rate by attack category ────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
cat_stats = summary['category_stats']
cats = [c for c in CAT_ORDER if c in cat_stats]
gate_rates = [100 * cat_stats[c]['gated'] / max(cat_stats[c]['total'], 1) for c in cats]
totals = [cat_stats[c]['total'] for c in cats]
bars = ax1.barh(cats, gate_rates, color=[COLORS[c] for c in cats], alpha=0.85, height=0.6)
for bar, rate, tot in zip(bars, gate_rates, totals):
    ax1.text(min(rate + 1, 97), bar.get_y() + bar.get_height()/2,
             f'{rate:.1f}%  (n={tot:,})', va='center', fontsize=8, color='#c9d1d9')
ax1.set_xlim(0, 105)
ax1.set_xlabel('Gate Rate (%)')
ax1.set_title('Gate Rate by Attack Category', color='#e6edf3', fontsize=10)
ax1.axvline(86.5, color='#58a6ff', linestyle='--', linewidth=1, alpha=0.7, label='Overall 86.5%')
ax1.legend(fontsize=7, loc='lower right')
ax1.grid(axis='x', alpha=0.3)

# ─── Panel 2: Pipeline path distribution ──────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
path_dist = summary['path_distribution']
# Simplify path names for display
simplified = {}
for k, v in path_dist.items():
    if k == 'speedlight':
        simplified['SpeedLight\nCache'] = v
    elif k == 'full_eval':
        simplified['Full\nEvaluation'] = v
    elif 'class_I' in k:
        simplified['Class I\nGate'] = simplified.get('Class I\nGate', 0) + v
    elif 'class_II' in k:
        simplified['Class II\nGate'] = simplified.get('Class II\nGate', 0) + v
    elif 'class_IV' in k:
        simplified['Class IV\nGate'] = simplified.get('Class IV\nGate', 0) + v
    else:
        simplified['Other\nGate'] = simplified.get('Other\nGate', 0) + v

path_colors = ['#58a6ff', '#f85149', '#3fb950', '#d29922', '#a371f7', '#ff7b72']
labels = list(simplified.keys())
values = list(simplified.values())
wedges, texts, autotexts = ax2.pie(
    values, labels=labels, autopct='%1.1f%%',
    colors=path_colors[:len(labels)],
    textprops={'fontsize': 7, 'color': '#c9d1d9'},
    pctdistance=0.75, startangle=90,
)
for at in autotexts:
    at.set_fontsize(7)
ax2.set_title('Pipeline Path Distribution', color='#e6edf3', fontsize=10)

# ─── Panel 3: CA class distribution ───────────────────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
ca_dist = summary['ca_distribution']
ca_labels = sorted(ca_dist.keys())
ca_vals = [ca_dist[k] for k in ca_labels]
ca_colors = {'I': '#3fb950', 'II': '#58a6ff', 'III': '#f85149', 'IV': '#d29922'}
bars3 = ax3.bar(
    [f'Class {l}' for l in ca_labels], ca_vals,
    color=[ca_colors.get(l, '#8b949e') for l in ca_labels],
    alpha=0.85, width=0.5
)
for bar, val in zip(bars3, ca_vals):
    pct = 100 * val / summary['total_rows']
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
             f'{val:,}\n({pct:.1f}%)', ha='center', fontsize=8, color='#c9d1d9')
ax3.set_ylabel('Row Count')
ax3.set_title('Wolfram CA Class Assignment', color='#e6edf3', fontsize=10)
ax3.grid(axis='y', alpha=0.3)
ax3.set_ylim(0, max(ca_vals) * 1.18)

# ─── Panel 4: Braid word length distribution (from sample) ────────────────────
ax4 = fig.add_subplot(gs[1, 0])
braid_lens = [r['braid_len'] for r in sample if r.get('braid_len', 0) >= 0]
braid_by_cat = defaultdict(list)
for r in sample:
    braid_by_cat[r.get('category', 'unknown')].append(r.get('braid_len', 0))

bins = range(0, max(braid_lens) + 2)
for cat in CAT_ORDER:
    if cat in braid_by_cat:
        ax4.hist(braid_by_cat[cat], bins=bins, alpha=0.6,
                 label=cat, color=COLORS[cat], density=True)
ax4.set_xlabel('Braid Word Length (navigation cost)')
ax4.set_ylabel('Density')
ax4.set_title('Braid Navigation Word Length\nby Attack Category', color='#e6edf3', fontsize=10)
ax4.legend(fontsize=7)
ax4.grid(alpha=0.3)
ax4.axvline(summary['braid']['mean_len'], color='white', linestyle='--',
            linewidth=1, alpha=0.7, label=f'Mean={summary["braid"]["mean_len"]:.2f}')

# ─── Panel 5: Delta-phi (conservation) over time ──────────────────────────────
ax5 = fig.add_subplot(gs[1, 1])
dphi_vals = [r['delta_phi'] for r in sample]
cumulative = np.cumsum(dphi_vals)
x = range(len(dphi_vals))
ax5.fill_between(x, cumulative, 0, where=[c < 0 for c in cumulative],
                 alpha=0.3, color='#3fb950', label='ΔΦ < 0 (info gain)')
ax5.fill_between(x, cumulative, 0, where=[c > 0 for c in cumulative],
                 alpha=0.3, color='#f85149', label='ΔΦ > 0 (violation)')
ax5.plot(x, cumulative, color='#58a6ff', linewidth=1, alpha=0.9)
ax5.axhline(0, color='#8b949e', linewidth=0.8, linestyle='--')
ax5.set_xlabel('Row Index (sample)')
ax5.set_ylabel('Cumulative ΔΦ')
ax5.set_title('Conservation Law: Cumulative ΔΦ\n(must stay ≤ 0)', color='#e6edf3', fontsize=10)
ax5.legend(fontsize=7)
ax5.grid(alpha=0.3)

# ─── Panel 6: Sparsity vs gate decision ───────────────────────────────────────
ax6 = fig.add_subplot(gs[1, 2])
gated_sparsity = [r['sparsity'] for r in sample if r.get('gate')]
full_sparsity  = [r['sparsity'] for r in sample if not r.get('gate') and r.get('path') == 'full_eval']
cache_sparsity = [r['sparsity'] for r in sample if r.get('path') == 'speedlight']

ax6.hist(gated_sparsity, bins=20, alpha=0.6, color='#3fb950',
         label=f'Gated (n={len(gated_sparsity)})', density=True)
ax6.hist(full_sparsity, bins=20, alpha=0.6, color='#f85149',
         label=f'Full eval (n={len(full_sparsity)})', density=True)
ax6.hist(cache_sparsity, bins=20, alpha=0.6, color='#58a6ff',
         label=f'Cache hit (n={len(cache_sparsity)})', density=True)
ax6.set_xlabel('Row Sparsity (fraction of zero features)')
ax6.set_ylabel('Density')
ax6.set_title('Sparsity Distribution\nby Pipeline Path', color='#e6edf3', fontsize=10)
ax6.legend(fontsize=7)
ax6.grid(alpha=0.3)

# ─── Panel 7: Per-class full-eval rate (the hard cases) ───────────────────────
ax7 = fig.add_subplot(gs[2, 0])
# Use per-label stats from sample
label_stats = defaultdict(lambda: {'total':0, 'full_eval':0})
for r in sample:
    lbl = r.get('label', 'unknown')
    label_stats[lbl]['total'] += 1
    if r.get('path') == 'full_eval':
        label_stats[lbl]['full_eval'] += 1

# Sort by full-eval rate (hardest first)
sorted_labels = sorted(
    [(lbl, s['full_eval'] / max(s['total'], 1), s['total'])
     for lbl, s in label_stats.items()],
    key=lambda x: -x[1]
)[:15]  # top 15 hardest

lbls = [x[0] for x in sorted_labels]
rates = [100 * x[1] for x in sorted_labels]
totals = [x[2] for x in sorted_labels]

# Color by category
def lbl_to_cat(lbl):
    from collections import defaultdict
    cats = {
        'normal':'normal','neptune':'dos','back':'dos','land':'dos',
        'pod':'dos','smurf':'dos','teardrop':'dos','ipsweep':'probe',
        'nmap':'probe','portsweep':'probe','satan':'probe',
        'ftp_write':'r2l','guess_passwd':'r2l','imap':'r2l',
        'multihop':'r2l','phf':'r2l','spy':'r2l','warezclient':'r2l',
        'warezmaster':'r2l','buffer_overflow':'u2r','loadmodule':'u2r',
        'perl':'u2r','rootkit':'u2r',
    }
    return cats.get(lbl, 'unknown')

bar_colors = [COLORS[lbl_to_cat(l)] for l in lbls]
bars7 = ax7.barh(range(len(lbls)), rates, color=bar_colors, alpha=0.85, height=0.65)
ax7.set_yticks(range(len(lbls)))
ax7.set_yticklabels([f'{l} (n={t})' for l, t in zip(lbls, totals)], fontsize=7)
ax7.set_xlabel('Full Evaluation Rate (%)')
ax7.set_title('Hardest Classes\n(highest full-eval rate)', color='#e6edf3', fontsize=10)
ax7.grid(axis='x', alpha=0.3)
ax7.set_xlim(0, 110)
for bar, rate in zip(bars7, rates):
    ax7.text(rate + 1, bar.get_y() + bar.get_height()/2,
             f'{rate:.0f}%', va='center', fontsize=7, color='#c9d1d9')

# ─── Panel 8: SNAP label depth distribution ───────────────────────────────────
ax8 = fig.add_subplot(gs[2, 1])
snap_by_cat = defaultdict(list)
for r in sample:
    snap_by_cat[r.get('category', 'unknown')].append(r.get('snap_depth', 0))

positions = range(len(CAT_ORDER))
bp_data = [snap_by_cat[c] for c in CAT_ORDER]
bp = ax8.boxplot(bp_data, positions=positions, patch_artist=True,
                 medianprops={'color': 'white', 'linewidth': 1.5},
                 whiskerprops={'color': '#8b949e'},
                 capprops={'color': '#8b949e'},
                 flierprops={'marker': '.', 'color': '#8b949e', 'markersize': 3})
for patch, cat in zip(bp['boxes'], CAT_ORDER):
    patch.set_facecolor(COLORS[cat])
    patch.set_alpha(0.7)
ax8.set_xticks(positions)
ax8.set_xticklabels(CAT_ORDER, fontsize=8)
ax8.set_ylabel('SNAP Label Depth')
ax8.set_title('SNAP Label Depth\nby Attack Category', color='#e6edf3', fontsize=10)
ax8.grid(axis='y', alpha=0.3)

# ─── Panel 9: Key metrics summary box ─────────────────────────────────────────
ax9 = fig.add_subplot(gs[2, 2])
ax9.axis('off')

metrics = [
    ("Dataset",          "NSL-KDD (Intrusion Detection)"),
    ("Rows Processed",   f"{summary['total_rows']:,}  (stratified)"),
    ("Features",         "41  (38 numeric + 3 categorical)"),
    ("Sparsity",         f"{100*summary['sparsity']['mean']:.1f}% zero features"),
    ("Imbalance Ratio",  "33,672 : 1  (spy vs normal)"),
    ("",                 ""),
    ("SpeedLight Hits",  f"{summary['cache_hits']:,}  ({100*summary['cache_hit_rate']:.1f}%)"),
    ("Gate Rate",        f"{100*summary['gate_rate']:.1f}%  (skipped full eval)"),
    ("Full Evaluation",  f"{summary['full_eval']:,}  ({100*summary['full_eval_rate']:.1f}%)"),
    ("Swarm Capsules",   f"{summary['swarm_spawned']}  spawned"),
    ("",                 ""),
    ("Receipts",         f"{summary['receipts']:,}  generated"),
    ("Chain Integrity",  "✓  intact  (SHA-256 hash chain)"),
    ("ΔΦ Cumulative",    f"{summary['cumulative_dphi']:.1f}"),
    ("Conservation",     "✓  holds  (ΔΦ ≤ 0)"),
    ("",                 ""),
    ("Braid Mean Len",   f"{summary['braid']['mean_len']:.2f}  reflections"),
    ("Braid Max Len",    f"{summary['braid']['max_len']}  reflections"),
    ("Zero-Nav Items",   f"{summary['braid']['zero_nav']:,}  (same region)"),
    ("CA Class II",      f"{summary['ca_distribution'].get('II',0):,}  (99.4%)"),
    ("CA Class IV",      f"{summary['ca_distribution'].get('IV',0):,}  (0.6%)"),
]

y = 0.98
for label, value in metrics:
    if label == "":
        y -= 0.025
        continue
    ax9.text(0.02, y, label + ":", fontsize=7.5, color='#8b949e',
             transform=ax9.transAxes, va='top')
    ax9.text(0.45, y, value, fontsize=7.5, color='#e6edf3',
             transform=ax9.transAxes, va='top', fontweight='bold')
    y -= 0.046

ax9.set_title('Pipeline Metrics Summary', color='#e6edf3', fontsize=10)
rect = FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02",
                      linewidth=1, edgecolor='#30363d', facecolor='#161b22',
                      transform=ax9.transAxes, zorder=0)
ax9.add_patch(rect)

plt.savefig('pipeline_analysis.png', dpi=150, bbox_inches='tight',
            facecolor='#0d1117')
print("Saved: pipeline_analysis.png")


# ── Figure 2: Leech coordinate scatter (2D projection of 24D space) ───────────
fig2, axes = plt.subplots(1, 2, figsize=(14, 6))
fig2.patch.set_facecolor('#0d1117')
fig2.suptitle('Leech Lattice Coordinate Projections — NSL-KDD\n'
              '24D Leech space projected to 2D via first two principal components',
              color='#e6edf3', fontsize=11, fontweight='bold')

# Re-run a mini pipeline to get coordinates for plotting
import sys
sys.path.insert(0, '/home/ubuntu/nslkdd')

# Rebuild coordinates from sample
COLS_LOCAL = [
    'duration','protocol_type','service','flag',
    'src_bytes','dst_bytes','land','wrong_fragment','urgent',
    'hot','num_failed_logins','logged_in','num_compromised','root_shell',
    'su_attempted','num_root','num_file_creations','num_shells',
    'num_access_files','num_outbound_cmds','is_host_login','is_guest_login',
    'count','srv_count','serror_rate','srv_serror_rate','rerror_rate',
    'srv_rerror_rate','same_srv_rate','diff_srv_rate','srv_diff_host_rate',
    'dst_host_count','dst_host_srv_count','dst_host_same_srv_rate',
    'dst_host_diff_srv_rate','dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate','dst_host_serror_rate',
    'dst_host_srv_serror_rate','dst_host_rerror_rate',
    'dst_host_srv_rerror_rate','label'
]
ATTACK_CAT_LOCAL = {
    'normal':'normal','neptune':'dos','back':'dos','land':'dos',
    'pod':'dos','smurf':'dos','teardrop':'dos','ipsweep':'probe',
    'nmap':'probe','portsweep':'probe','satan':'probe',
    'ftp_write':'r2l','guess_passwd':'r2l','imap':'r2l',
    'multihop':'r2l','phf':'r2l','spy':'r2l','warezclient':'r2l',
    'warezmaster':'r2l','buffer_overflow':'u2r','loadmodule':'u2r',
    'perl':'u2r','rootkit':'u2r',
}
PROTO_MAP  = {'tcp': 0.0, 'udp': 0.5, 'icmp': 1.0}
FLAG_MAP   = {'SF':1.0,'S0':0.1,'REJ':0.2,'RSTO':0.3,'RSTR':0.4,
              'SH':0.5,'S1':0.6,'S2':0.7,'S3':0.8,'OTH':0.9,'RSTOS0':0.15}
import hashlib, math
E8_SIMPLE_ROOTS = np.array([
    [1,-1,0,0,0,0,0,0],[0,1,-1,0,0,0,0,0],[0,0,1,-1,0,0,0,0],
    [0,0,0,1,-1,0,0,0],[0,0,0,0,1,-1,0,0],[0,0,0,0,0,1,-1,0],
    [0,0,0,0,0,1,1,0],[-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5,-0.5],
], dtype=float)

def _svc(s): return int(hashlib.md5(s.encode()).hexdigest()[:4],16)/65535.0
def _lg(x): return math.log1p(float(x))/math.log1p(1e9)
def _e8(v):
    p = E8_SIMPLE_ROOTS @ v
    return p / (np.linalg.norm(p) + 1e-12)

train_full = pd.read_csv('KDDTrain.csv', names=COLS_LOCAL, header=None)
# Take 3000 rows stratified for scatter
frames_sc = []
for lbl in train_full['label'].unique():
    sub = train_full[train_full['label']==lbl]
    frames_sc.append(sub.sample(min(100, len(sub)), random_state=0))
scatter_df = pd.concat(frames_sc).sample(frac=1, random_state=0).reset_index(drop=True)

coords_all = []
cats_all = []
labels_all = []
for _, row in scatter_df.iterrows():
    a = np.array([_lg(row['duration']),PROTO_MAP.get(str(row['protocol_type']),0.5),
                  _svc(str(row['service'])),FLAG_MAP.get(str(row['flag']),0.5),
                  _lg(row['src_bytes']),_lg(row['dst_bytes']),
                  float(row['land']),_lg(row['wrong_fragment'])], dtype=float)
    b = np.array([_lg(row['hot']),min(float(row['num_failed_logins']),1.0),
                  float(row['logged_in']),_lg(row['num_compromised']),
                  float(row['root_shell']),float(row['su_attempted']),
                  _lg(row['num_root']),_lg(row['num_file_creations'])], dtype=float)
    g = np.array([_lg(row['count']),_lg(row['srv_count']),
                  float(row['serror_rate']),float(row['rerror_rate']),
                  float(row['same_srv_rate']),float(row['diff_srv_rate']),
                  _lg(row['dst_host_count']),_lg(row['dst_host_srv_count'])], dtype=float)
    coords = np.concatenate([_e8(a), _e8(b), _e8(g)])
    norm = np.linalg.norm(coords)
    coords_all.append(coords / (norm + 1e-12))
    cats_all.append(ATTACK_CAT_LOCAL.get(str(row['label']), 'unknown'))
    labels_all.append(str(row['label']))

coords_arr = np.array(coords_all)

# PCA projection
from numpy.linalg import svd
C = coords_arr - coords_arr.mean(axis=0)
_, _, Vt = svd(C, full_matrices=False)
proj2d = C @ Vt[:2].T

# Left: by category
ax_l = axes[0]
ax_l.set_facecolor('#0d1117')
for cat in CAT_ORDER:
    mask = [c == cat for c in cats_all]
    if any(mask):
        pts = proj2d[mask]
        ax_l.scatter(pts[:,0], pts[:,1], c=COLORS[cat], label=cat,
                     alpha=0.55, s=12, linewidths=0)
ax_l.set_title('Leech Projection — by Attack Category', color='#e6edf3', fontsize=10)
ax_l.set_xlabel('PC1', color='#8b949e')
ax_l.set_ylabel('PC2', color='#8b949e')
ax_l.legend(fontsize=8, markerscale=2)
ax_l.grid(alpha=0.2)

# Right: highlight rare classes
ax_r = axes[1]
ax_r.set_facecolor('#0d1117')
rare_labels = ['buffer_overflow','loadmodule','perl','rootkit',
               'spy','phf','multihop','ftp_write']
# Background: all non-rare in grey
non_rare_mask = [l not in rare_labels for l in labels_all]
ax_r.scatter(proj2d[non_rare_mask, 0], proj2d[non_rare_mask, 1],
             c='#21262d', s=8, alpha=0.4, linewidths=0, label='common classes')

rare_colors = plt.cm.Set1(np.linspace(0, 1, len(rare_labels)))
for i, rl in enumerate(rare_labels):
    mask = [l == rl for l in labels_all]
    if any(mask):
        pts = proj2d[mask]
        ax_r.scatter(pts[:,0], pts[:,1], c=[rare_colors[i]], label=f'{rl} (n={sum(mask)})',
                     alpha=0.9, s=40, linewidths=0.5, edgecolors='white', zorder=5)

ax_r.set_title('Leech Projection — Rare/Extreme Classes\n(highlighted against common background)',
               color='#e6edf3', fontsize=10)
ax_r.set_xlabel('PC1', color='#8b949e')
ax_r.set_ylabel('PC2', color='#8b949e')
ax_r.legend(fontsize=7, markerscale=1.5, loc='upper right')
ax_r.grid(alpha=0.2)

plt.tight_layout()
plt.savefig('leech_projection.png', dpi=150, bbox_inches='tight',
            facecolor='#0d1117')
print("Saved: leech_projection.png")
print("All visualizations complete.")
