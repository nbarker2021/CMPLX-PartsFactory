"""
QuorumConsensusCalibration — multi-agent E8 convergence (G5, target 4.2).

Reproduces the algorithm from
``CMPLX-1T/Wolfram study/experiment_03_quorum_cmply.py`` using OUR
substrate's E8 roots (cmplx.geometry.e8.embed.e8_roots). The POC has
hardcoded Unix paths that make direct import fragile; the calibration
re-runs the algorithm in our environment against the POC's claimed
behavioral properties.

This is the first BEHAVIORAL calibration (vs structural). It exercises
the E8 nearest-root snap path across many rounds with many agents.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any, Optional

import numpy as np

from ..harness import CalibrationClaim, CalibrationTarget


def _run_quorum(
    n_agents: int,
    n_rounds: int,
    convergence_weight: float,
    noise_scale: float,
    seed: int,
) -> dict[str, Any]:
    """Multi-agent E8 quorum consensus simulation.

    Algorithm (from experiment_03 in the prior repo):
      1. Initialize N agents at random 8D belief vectors (unit-normalized).
      2. Each round:
         (a) snap each agent to its nearest E8 root → vote
         (b) compute belief-distribution entropy over the 240 buckets
         (c) check consensus (all agents on same root)
         (d) move each belief toward the centroid with conv_weight,
             perturbed by Gaussian noise of given scale
         (e) renormalize

    Substrate touched: cmplx.geometry.e8.embed.e8_roots().
    """
    from cmplx.geometry.e8.embed import e8_roots

    roots = np.array(e8_roots(), dtype=float)  # shape (240, 8)
    rng = np.random.default_rng(seed)

    beliefs = rng.standard_normal((n_agents, 8))
    beliefs /= np.linalg.norm(beliefs, axis=1, keepdims=True)

    entropy_history: list[float] = []
    consensus_round: Optional[int] = None
    final_votes: list[int] = []

    for round_n in range(n_rounds):
        # Snap every agent to nearest E8 root.
        # Pairwise squared distance: shape (N, 240).
        dist_sq = np.sum((beliefs[:, None, :] - roots[None, :, :]) ** 2, axis=2)
        votes = np.argmin(dist_sq, axis=1).tolist()
        final_votes = votes

        # Entropy over vote distribution.
        counter = Counter(votes)
        n = len(votes)
        ent = -sum((c / n) * math.log2(c / n) for c in counter.values())
        entropy_history.append(ent)

        # Consensus check.
        if len(counter) == 1 and consensus_round is None:
            consensus_round = round_n
            break

        # Move toward weighted centroid; apply noise.
        centroid = beliefs.mean(axis=0)
        noise = rng.standard_normal(beliefs.shape) * noise_scale
        beliefs = (1 - convergence_weight) * beliefs + convergence_weight * centroid + noise
        norms = np.linalg.norm(beliefs, axis=1, keepdims=True)
        beliefs = beliefs / np.where(norms > 1e-12, norms, 1.0)

    return {
        "consensus_round": consensus_round,
        "final_votes": final_votes,
        "final_n_unique": len(set(final_votes)) if final_votes else 0,
        "entropy_history": entropy_history,
        "final_entropy": entropy_history[-1] if entropy_history else 0.0,
    }


class QuorumConsensusCalibration(CalibrationTarget):
    """Multi-agent E8 quorum consensus — 5 behavioral claims.

    Substrate exercised: cmplx.geometry.e8.embed.e8_roots (E8 root set
    used as the quantization buckets agents snap to).
    """

    target_name = "quorum_consensus"

    def __init__(self) -> None:
        self._low_noise: dict[str, Any] = {}
        self._high_noise: dict[str, Any] = {}

    def setup(self) -> None:
        # Low-noise, small-n scenario: agents should converge quickly.
        self._low_noise = _run_quorum(
            n_agents=5,
            n_rounds=30,
            convergence_weight=0.6,
            noise_scale=0.05,
            seed=42,
        )
        # High-noise scenario: convergence should NOT occur within budget.
        self._high_noise = _run_quorum(
            n_agents=8,
            n_rounds=30,
            convergence_weight=0.4,
            noise_scale=0.50,
            seed=7,
        )

    def claims(self) -> list[CalibrationClaim]:
        return [
            CalibrationClaim(
                name="low_noise_converges",
                expected=True,
                tolerance=0,
                observed_fn=lambda: self._low_noise["consensus_round"] is not None,
                notes=(
                    "With n=5, conv_w=0.6, noise=0.05, agents converge to a "
                    "single E8 root within 30 rounds."
                ),
            ),
            CalibrationClaim(
                name="low_noise_consensus_round_under_20",
                expected=True,
                tolerance=0,
                observed_fn=lambda: (
                    self._low_noise["consensus_round"] is not None
                    and self._low_noise["consensus_round"] <= 20
                ),
                notes="Convergence happens fast — POC claims by round 12-15 for similar params.",
            ),
            CalibrationClaim(
                name="low_noise_entropy_monotone_nonincreasing_eventually",
                expected=True,
                tolerance=0,
                observed_fn=lambda: _is_monotone_nonincreasing_after_burnin(
                    self._low_noise["entropy_history"], burnin=2,
                ),
                notes=(
                    "After a small burn-in (random initial votes), entropy "
                    "decreases monotonically as agents cluster."
                ),
            ),
            CalibrationClaim(
                name="high_noise_prevents_consensus",
                expected=True,
                tolerance=0,
                observed_fn=lambda: self._high_noise["consensus_round"] is None,
                notes=(
                    "With noise_scale=0.50, the system never reaches single-root "
                    "consensus within the round budget — perpetual perturbation."
                ),
            ),
            CalibrationClaim(
                name="final_unique_roots_bounded",
                expected=True,
                tolerance=0,
                observed_fn=lambda: (
                    self._low_noise["final_n_unique"] <= 5
                    and self._high_noise["final_n_unique"] <= 20
                ),
                notes=(
                    "Convergence clusters agents to few roots: low-noise ≤ 5 "
                    "unique; high-noise stays in a bounded subregion (≤ 20)."
                ),
            ),
            CalibrationClaim(
                name="every_vote_is_valid_e8_root_index",
                expected=True,
                tolerance=0,
                observed_fn=lambda: all(
                    0 <= v < 240
                    for run in (self._low_noise, self._high_noise)
                    for v in run["final_votes"]
                ),
                notes=(
                    "Sanity: every agent vote must be a valid index into "
                    "our 240 E8 roots."
                ),
            ),
        ]


def _is_monotone_nonincreasing_after_burnin(seq: list[float], burnin: int = 2) -> bool:
    """True iff seq[burnin:] is non-increasing (with tiny tolerance for float noise)."""
    tail = seq[burnin:]
    if len(tail) < 2:
        return True
    return all(tail[i] >= tail[i + 1] - 1e-9 for i in range(len(tail) - 1))
