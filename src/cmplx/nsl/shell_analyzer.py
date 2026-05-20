"""Shell analysis for AGRM legality (escrow stub)."""
from __future__ import annotations

from typing import Any

import numpy as np


class ShellAnalyzer:
    def compute(self, points: np.ndarray, cx: float, cy: float) -> dict[str, Any]:
        r = np.sqrt((points[:, 0] - cx) ** 2 + (points[:, 1] - cy) ** 2)
        theta = np.arctan2(points[:, 1] - cy, points[:, 0] - cx)
        return {"r": r, "theta": theta, "shells": np.digitize(r, np.quantile(r, [0.2, 0.4, 0.6, 0.8]))}
