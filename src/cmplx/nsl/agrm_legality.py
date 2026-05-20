"""
Escrow merge (2026-05-19T00:00:31Z).
Source: ``CMPLX-history/staging/by-family/agrm/mdhg_hierarchy/agrm_gates.py``
Slot: ``slot-02-nsl-phi``
"""

import numpy as np
from .shell_analyzer import ShellAnalyzer

class AGRMLegality:
    """
    Example AGRM-like legality gates:
    - max_edge: absolute distance cap
    - max_turn: curvature proxy using triangle inequality slack
    - shell_continuity_bias: prefer staying within +/-1 shell
    """
    def __init__(self, points: np.ndarray, max_edge: float=None, max_turn: float=1.5, shell_slack:int=1,
                 sector_bins:int=24, sparse_relief:float=0.15, phase_window:int=8,
                 unlock_sparse_after:int=200, unlock_midpoint_after:int=350, unlock_relief:float=0.25):
        self.points = points
        self.sector_bins = sector_bins
        self.sparse_relief = sparse_relief
        self.phase_window = phase_window
        self.unlock_sparse_after = unlock_sparse_after
        self.unlock_midpoint_after = unlock_midpoint_after
        self.unlock_relief = unlock_relief
        self.max_edge = max_edge
        self.max_turn = max_turn
        self.shell_slack = shell_slack
        self.an = ShellAnalyzer()
        self.center = (points[:,0].mean(), points[:,1].mean())
        self.meta = self.an.compute(points, self.center[0], self.center[1])  # expects dict with 'r' and 'shells' and 'theta'
        self.r = self.meta["r"]; self.theta = self.meta.get("theta")
        # quantize shells by percentiles
        q = np.quantile(self.r, [0.2,0.4,0.6,0.8])
        self.shell_idx = np.digitize(self.r, q)
        # sector indices
        if self.theta is None:
            # fallback compute
            self.theta = (np.arctan2(points[:,1]-self.center[1], points[:,0]-self.center[0]) + np.pi)%(2*np.pi)
        edges = np.linspace(0, 2*np.pi, self.sector_bins+1)
        self.sector_idx = np.digitize(self.theta, edges) % self.sector_bins
        # sparse zones (lower local density): allow longer edges within sparse_relief
        self.global_mean = float(np.mean(self.r))
        self.global_std  = float(np.std(self.r))

    def is_legal(self, a:int, b:int, prev:int=None, step:int=None) -> bool:
        pa = self.points[a]; pb = self.points[b]
        # edge length cap
        d = float(np.hypot(*(pa-pb)))
        # adjust edge cap for sparse zones (radially sparse regions get a relief factor)
        local_relief = 1.0
        if abs(self.r[a]-self.global_mean) > self.global_std:
            local_relief += self.sparse_relief
        max_edge = self.dynamic_edge_cap(a, self.max_edge, step=step)
        if (max_edge is not None) and d > max_edge:
            return False
        # sector continuity check
        if not self.sector_ok(a,b):
            return False
        # shell continuity (within +/- shell_slack)
        if abs(int(self.shell_idx[a]) - int(self.shell_idx[b])) > self.shell_slack:
            return False
        # curvature proxy if prev is given (phase timing window gate applies below)
        if prev is not None:
            pp = self.points[prev]
            ab = float(np.hypot(*(pp-pa)))
            bc = float(np.hypot(*(pa-pb)))
            ac = float(np.hypot(*(pp-pb)))
            turn = max(0.0, (ab+bc-ac))
            # allow slightly larger turns on phase windows
            turn_cap = self.max_turn * (1.15 if self.phase_ok(step) else 1.0)
            if turn > turn_cap:
                return False
        return True


    def sector_ok(self, a:int, b:int) -> bool:
        # prefer staying in same/adjacent sector
        da = abs(int(self.sector_idx[a]) - int(self.sector_idx[b]))
        da = min(da, self.sector_bins - da)
        return da <= 1

    def phase_ok(self, step:int) -> bool:
        # simplistic phase cycle: allow relaxed edges during every 'phase_window' steps boundary
        if step is None or self.phase_window <= 0:
            return True
        return (step % self.phase_window) in (0, 1)


    def dynamic_edge_cap(self, a:int, base_cap: float, step:int=None) -> float:
        if base_cap is None:
            return None
        cap = base_cap
        # periodic phase relief
        if self.phase_ok(step):
            cap *= (1.0 + 0.10)
        # sparse zone relief
        if abs(self.r[a]-self.global_mean) > self.global_std:
            cap *= (1.0 + self.sparse_relief)
        # global unlocks
        if step is not None:
            if step >= self.unlock_sparse_after:
                cap *= (1.0 + self.unlock_relief)
            if step >= self.unlock_midpoint_after:
                cap *= (1.0 + self.unlock_relief)
        return cap
