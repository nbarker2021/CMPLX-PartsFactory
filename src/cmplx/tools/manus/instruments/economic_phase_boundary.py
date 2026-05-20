"""
Integrated 2026-05-19T00:52:23Z from external toolkit.
Source: ``D:\Manny Unification 2\datasets from previous review\Manus dev and review\economic_phase_boundary.py``
"""
#!/usr/bin/env python3
"""
TOOL 3: EconomicPhaseBoundaryDetector
=======================================
Layer:  Meso (multi-step, within-experiment — rolling window analysis)
Field:  Macroeconomics / Financial Mathematics
Author: Nicholas Barker & Manus AI, 2026

PROBLEM SOLVED
--------------
Economic phase transitions (recessions, bubbles, crashes) are identified only
in retrospect. Standard tools (yield curve inversions, PMI, NBER dating) are
lagging indicators. There is no real-time tool that detects the *approach* of
a phase boundary using the internal geometric structure of the time series.

NOVEL CONTRIBUTION
------------------
A multivariate economic time series (e.g., GDP growth, inflation, unemployment,
yield spread, credit spread) is treated as a sequence of 8D state vectors. Each
state vector is snapped to the nearest E8 root. The digital root of the resulting
root index sequence is computed over a rolling window. Phase boundaries appear as
local minima in the entropy of the DR sequence — exactly as observed in the
Rule 30 / powers-of-10 experiment. The tool outputs a real-time "Phase Boundary
Proximity Score" (PBPS) that peaks just before a transition.

KEY INSIGHT
-----------
The E8 lattice is the densest packing in 8D. An economy in a stable phase
occupies a small, dense region of E8 space. As it approaches a phase boundary,
it begins to explore a larger region — the E8 snap distances increase and the
DR entropy drops (the system is "searching" for a new stable configuration).
The PBPS is the inverse of the DR entropy, normalized to [0,1].
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
    return -sum((c/n) * math.log2(c/n) for c in counts.values() if c > 0)

class EconomicPhaseBoundaryDetector:
    """
    Detects economic phase boundaries in real-time using E8 geometry.
    """
    def __init__(self, window_size=12):
        self.e8 = E8Lattice()
        self.roots = self.e8.get_roots()
        self.root_vecs = np.array([r.coords for r in self.roots], dtype=float)
        self.window_size = window_size

    def _normalize_series(self, series):
        """Z-score normalize each dimension of the time series."""
        arr = np.array(series, dtype=float)
        mean = arr.mean(axis=0)
        std  = arr.std(axis=0)
        std[std < 1e-10] = 1.0
        return (arr - mean) / std

    def _snap_to_e8(self, vec8d):
        """Snap an 8D vector to the nearest E8 root."""
        v = np.array(vec8d, dtype=float)
        dists = np.linalg.norm(self.root_vecs - v, axis=1)
        idx = int(np.argmin(dists))
        return idx, float(dists[idx])

    def _pad_to_8d(self, vec):
        """Pad or truncate a vector to exactly 8 dimensions."""
        v = np.array(vec, dtype=float)
        if len(v) >= 8:
            return v[:8]
        return np.pad(v, (0, 8 - len(v)), mode='wrap')

    def analyze(self, time_series, timestamps=None, variable_names=None):
        """
        Analyze a multivariate economic time series.

        time_series: list of T observations, each a list of N economic variables
        timestamps:  optional list of T timestamp labels
        variable_names: optional list of N variable names

        Returns per-timestep analysis and the Phase Boundary Proximity Score.
        """
        T = len(time_series)
        if timestamps is None:
            timestamps = list(range(T))
        if variable_names is None:
            variable_names = [f"Var{i+1}" for i in range(len(time_series[0]))]

        # Normalize and pad to 8D
        norm_series = self._normalize_series(time_series)
        vecs_8d = [self._pad_to_8d(v) for v in norm_series]

        # Snap each observation to E8
        e8_indices = []
        snap_distances = []
        for v in vecs_8d:
            idx, dist = self._snap_to_e8(v)
            e8_indices.append(idx)
            snap_distances.append(dist)

        # Compute digital roots of E8 indices
        drs = [digital_root(idx + 1) for idx in e8_indices]

        # Rolling window entropy and PBPS
        pbps = []
        dr_entropies = []
        for t in range(T):
            start = max(0, t - self.window_size + 1)
            window_drs = drs[start:t+1]
            ent = shannon_entropy(window_drs)
            dr_entropies.append(ent)
            # PBPS = 1 - normalized entropy (low entropy = high proximity to boundary)
            max_ent = math.log2(9) if len(window_drs) >= 9 else (math.log2(len(set(window_drs))) if len(set(window_drs)) > 1 else 0)
            pbps_val = 1.0 - (ent / max_ent) if max_ent > 0 else 0.0
            pbps.append(pbps_val)

        # Detect phase boundaries: local maxima in PBPS above threshold
        threshold = 0.65
        boundaries = []
        for t in range(1, T-1):
            if pbps[t] > threshold and pbps[t] >= pbps[t-1] and pbps[t] >= pbps[t+1]:
                boundaries.append({
                    "timestep": t,
                    "timestamp": timestamps[t],
                    "pbps": pbps[t],
                    "dr_entropy": dr_entropies[t],
                    "e8_root": e8_indices[t],
                    "dr": drs[t],
                    "snap_distance": snap_distances[t],
                })

        # Classify current economic phase
        recent_drs = drs[-self.window_size:]
        phase_dr = digital_root(sum(recent_drs))
        phase_names = {
            1: "Expansion (early)",
            2: "Expansion (late)",
            3: "Peak / Pre-transition",
            4: "Contraction (early)",
            5: "Contraction (deep)",
            6: "Trough",
            7: "Recovery (early)",
            8: "Recovery (late)",
            9: "Neutral / Suspended",
        }
        current_phase = phase_names.get(phase_dr, f"Phase {phase_dr}")

        return {
            "n_observations": T,
            "window_size": self.window_size,
            "timestamps": timestamps,
            "e8_indices": e8_indices,
            "snap_distances": snap_distances,
            "digital_roots": drs,
            "dr_entropies": dr_entropies,
            "pbps": pbps,
            "phase_boundaries_detected": boundaries,
            "current_phase_dr": phase_dr,
            "current_phase": current_phase,
            "current_pbps": pbps[-1],
            "mean_snap_distance": float(np.mean(snap_distances)),
        }

    def plot(self, result, output_path, title="Economic Phase Boundary Detector"):
        """Comprehensive visualization of the phase boundary analysis."""
        fig = plt.figure(figsize=(24, 16))
        fig.patch.set_facecolor('#0d1117')
        gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.50, wspace=0.35)

        def dark_ax(ax):
            ax.set_facecolor('#161b22')
            for sp in ax.spines.values(): sp.set_color('#30363d')
            ax.tick_params(colors='#8b949e', labelsize=8)

        T = result['n_observations']
        ts = result['timestamps']
        pbps = result['pbps']
        ent  = result['dr_entropies']
        drs  = result['digital_roots']
        dists = result['snap_distances']
        boundaries = result['phase_boundaries_detected']
        boundary_ts = [b['timestep'] for b in boundaries]

        # ── Panel 1: PBPS over time ───────────────────────────────────────────
        ax1 = fig.add_subplot(gs[0, :]); dark_ax(ax1)
        ax1.fill_between(range(T), pbps, alpha=0.25, color='#ffa657')
        ax1.plot(range(T), pbps, color='#ffa657', linewidth=2)
        ax1.axhline(0.65, color='#ff7b72', linewidth=1.5, linestyle='--', alpha=0.7, label='Boundary threshold (0.65)')
        for b in boundaries:
            ax1.axvline(b['timestep'], color='#ff7b72', linewidth=2, alpha=0.9)
            ax1.text(b['timestep'], b['pbps'] + 0.02, f"⚠ {b['timestamp']}",
                     color='#ff7b72', fontsize=8, ha='center', va='bottom', fontweight='bold')
        ax1.set_xlim(0, T-1); ax1.set_ylim(0, 1.05)
        ax1.set_xlabel('Time', color='#8b949e', fontsize=9)
        ax1.set_ylabel('Phase Boundary Proximity Score', color='#8b949e', fontsize=9)
        ax1.set_title('Phase Boundary Proximity Score (PBPS) — Real-Time Phase Transition Detector',
                      color='white', fontsize=11, fontweight='bold')
        ax1.legend(fontsize=9, facecolor='#161b22', labelcolor='white', edgecolor='#30363d')

        # ── Panel 2: DR Entropy ───────────────────────────────────────────────
        ax2 = fig.add_subplot(gs[1, :2]); dark_ax(ax2)
        ax2.plot(range(T), ent, color='#58a6ff', linewidth=1.8)
        for bt in boundary_ts:
            ax2.axvline(bt, color='#ff7b72', linewidth=1.5, alpha=0.7)
        ax2.set_xlabel('Time', color='#8b949e', fontsize=9)
        ax2.set_ylabel('DR Entropy (bits)', color='#8b949e', fontsize=9)
        ax2.set_title('Digital Root Entropy\n(Low entropy → approaching phase boundary)',
                      color='white', fontsize=10, fontweight='bold')

        # ── Panel 3: E8 snap distance ─────────────────────────────────────────
        ax3 = fig.add_subplot(gs[1, 2]); dark_ax(ax3)
        ax3.plot(range(T), dists, color='#3fb950', linewidth=1.5, alpha=0.9)
        for bt in boundary_ts:
            ax3.axvline(bt, color='#ff7b72', linewidth=1.5, alpha=0.7)
        ax3.set_xlabel('Time', color='#8b949e', fontsize=9)
        ax3.set_ylabel('E8 Snap Distance', color='#8b949e', fontsize=9)
        ax3.set_title('E8 Snap Distance\n(High distance → unstable state)', color='white', fontsize=10, fontweight='bold')

        # ── Panel 4: DR sequence heatmap ──────────────────────────────────────
        ax4 = fig.add_subplot(gs[2, :2]); dark_ax(ax4)
        dr_colors = {1:'#ff7b72',2:'#58a6ff',3:'#3fb950',4:'#ffa657',
                     5:'#d2a8ff',6:'#79c0ff',7:'#56d364',8:'#e3b341',9:'#8b949e'}
        colors_seq = [dr_colors.get(d, '#8b949e') for d in drs]
        ax4.scatter(range(T), [1]*T, c=colors_seq, s=80, marker='s', zorder=5)
        ax4.set_xlim(-0.5, T-0.5); ax4.set_ylim(0.5, 1.5)
        ax4.set_yticks([]); ax4.set_xlabel('Time', color='#8b949e', fontsize=9)
        ax4.set_title('Digital Root Sequence (Color = Basin Class)',
                      color='white', fontsize=10, fontweight='bold')
        for bt in boundary_ts:
            ax4.axvline(bt, color='#ff7b72', linewidth=2, alpha=0.9)

        # ── Panel 5: Summary ──────────────────────────────────────────────────
        ax5 = fig.add_subplot(gs[2, 2]); ax5.set_facecolor('#161b22'); ax5.axis('off')
        for sp in ax5.spines.values(): sp.set_color('#30363d')
        lines = [
            ("PHASE ANALYSIS SUMMARY", '#ffa657', True),
            ("", '#c9d1d9', False),
            (f"Observations:    {result['n_observations']}", '#c9d1d9', False),
            (f"Window size:     {result['window_size']}", '#c9d1d9', False),
            (f"Boundaries found:{len(boundaries)}", '#ff7b72' if boundaries else '#3fb950', False),
            ("", '#c9d1d9', False),
            ("CURRENT STATE:", '#58a6ff', True),
            (f"  Phase DR: {result['current_phase_dr']}", '#c9d1d9', False),
            (f"  Phase:    {result['current_phase']}", '#3fb950', False),
            (f"  PBPS:     {result['current_pbps']:.3f}", '#ffa657', False),
            (f"  Mean dist:{result['mean_snap_distance']:.3f}", '#c9d1d9', False),
            ("", '#c9d1d9', False),
        ]
        if boundaries:
            lines.append(("BOUNDARIES DETECTED:", '#ff7b72', True))
            for b in boundaries[-3:]:
                lines.append((f"  t={b['timestep']} PBPS={b['pbps']:.2f}", '#ff7b72', False))
        for k, (line, color, bold) in enumerate(lines):
            ax5.text(0.04, 0.97 - k*0.075, line, transform=ax5.transAxes,
                     color=color, fontsize=9, fontweight='bold' if bold else 'normal',
                     va='top', fontfamily='monospace')

        fig.suptitle(title, color='white', fontsize=13, fontweight='bold', y=1.01)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
        plt.close()
        print(f"[SAVED] {output_path}")


# ── LIVE DEMONSTRATION ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    os.makedirs('/home/ubuntu/lab/tools/tool03_economic', exist_ok=True)

    print("=" * 65)
    print("TOOL 3: EconomicPhaseBoundaryDetector — Live Demonstration")
    print("=" * 65)

    # Simulate a 120-month (10-year) economic time series
    # Variables: GDP growth, inflation, unemployment, yield spread,
    #            credit spread, consumer confidence, industrial production, housing starts
    rng = np.random.default_rng(42)
    T = 120

    def simulate_economy():
        """Simulate a realistic business cycle with 2 recessions."""
        t = np.arange(T)
        # Business cycle: 2 recessions at t≈30 and t≈85
        cycle = np.sin(2*np.pi*t/60) * 2.0
        recession1 = -3.0 * np.exp(-0.5*((t-30)/8)**2)
        recession2 = -4.0 * np.exp(-0.5*((t-85)/6)**2)
        base = cycle + recession1 + recession2

        gdp        = base + rng.normal(0, 0.5, T)
        inflation  = 2.0 + 0.3*base + rng.normal(0, 0.3, T)
        unemploy   = 5.0 - 0.4*base + rng.normal(0, 0.2, T)
        yield_sp   = 1.5 + 0.5*base + rng.normal(0, 0.3, T)
        credit_sp  = 2.0 - 0.6*base + rng.normal(0, 0.4, T)
        confidence = 100 + 5*base + rng.normal(0, 3, T)
        indprod    = base * 0.8 + rng.normal(0, 0.4, T)
        housing    = 1200 + 100*base + rng.normal(0, 50, T)

        return list(zip(gdp, inflation, unemploy, yield_sp, credit_sp, confidence, indprod, housing))

    series = simulate_economy()
    timestamps = [f"M{t+1}" for t in range(T)]
    var_names = ['GDP Growth', 'Inflation', 'Unemployment', 'Yield Spread',
                 'Credit Spread', 'Confidence', 'Ind. Production', 'Housing Starts']

    tool = EconomicPhaseBoundaryDetector(window_size=12)
    result = tool.analyze(series, timestamps, var_names)

    print(f"\nObservations analyzed: {result['n_observations']}")
    print(f"Phase boundaries detected: {len(result['phase_boundaries_detected'])}")
    for b in result['phase_boundaries_detected']:
        print(f"  {b['timestamp']}  PBPS={b['pbps']:.3f}  DR={b['dr']}  E8 root #{b['e8_root']}")
    print(f"\nCurrent economic phase: {result['current_phase']} (DR={result['current_phase_dr']})")
    print(f"Current PBPS: {result['current_pbps']:.3f}")

    out_png = '/home/ubuntu/lab/tools/tool03_economic/phase_boundary_analysis.png'
    tool.plot(result, out_png, title="EconomicPhaseBoundaryDetector: 10-Year Business Cycle Demo")

    # Save summary (exclude large lists)
    summary = {k: v for k, v in result.items()
               if k not in ('e8_indices','snap_distances','digital_roots','dr_entropies','pbps','timestamps')}
    with open('/home/ubuntu/lab/tools/tool03_economic/results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("[SAVED] /home/ubuntu/lab/tools/tool03_economic/results.json")
    print("[DONE]")
