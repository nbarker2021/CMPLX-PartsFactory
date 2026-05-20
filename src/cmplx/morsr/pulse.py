"""
MORSREngine — the recursive ripple-pulse diagnostic engine.

The core MORSR cycle, from the canonical
`CQE_MORSR_NewBest_v1/cqe_plus/morsr.py:pulse()`:

```
for stage in 0..N:
    1. build shell (radial or BFS, scaled by factor^stage)
    2. Ring 0 = the current overlay (identity)
    3. Ring 1 = apply each operator to the current overlay
       for each candidate:
         - shell containment check
         - compute NSL sectors (v_before → v_after)
         - gate decision (GOVERN / AMORTIZE / SIGNAL)
         - emit handshake
       if any accepted → current = best accepted
    4. compute return metric (accept_rate / novelty / strict_gain)
    5. EMA-smooth return
    6. stop if return + ema below threshold OR factors exhausted
```

The "Reader" half is `HandshakeLog`; the "Shaper" half is the
operator set. Together: full diagnostic trace of everything the
wave touched plus what interfered.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from cmplx.nsl import (
    GateMode,
    NSLProvider,
    NSLSectors,
    delta_phi,
    potential,
)

from .handshake import Handshake, HandshakeLog
from .operators import OperatorRegistry
from .overlay import Overlay
from .shell import ShellMode, build_shell, in_shell


# ---------------------------------------------------------------------------
# Stop metrics
# ---------------------------------------------------------------------------

class StopMetric(str, Enum):
    ACCEPT_RATE = "accept_rate"   # fraction of candidates accepted
    NOVELTY = "novelty"           # raw count of accepted candidates
    STRICT_GAIN = "strict_gain"   # cumulative |negative ΔΦ|


# ---------------------------------------------------------------------------
# Policy + Region + StageMetrics
# ---------------------------------------------------------------------------

@dataclass
class MORSRPolicy:
    """All knobs the pulse cycle reads from."""
    # Acceptance tolerance (epsilon for ΔΦ ≤ -ε)
    eps_phi: float = 1e-6
    # Allow plateau acceptances (ΔΦ ≈ 0) up to this many times
    plateau_cap: int = 0
    # Shell
    shell_mode: ShellMode = ShellMode.RADIAL
    shell_base: float = 0.25
    shell_factors: tuple[int, ...] = (1, 2, 3, 5, 8)  # Fibonacci-ish growth
    # Stop conditions
    stop_metric: StopMetric = StopMetric.STRICT_GAIN
    stop_threshold: float = 1e-4
    ema_alpha: float = 0.5
    max_stages: Optional[int] = None
    # Gate
    gate_mode: GateMode = GateMode.GOVERN
    stage_budget: float = 0.0


@dataclass
class StageMetrics:
    stage: int = 0
    attempts: int = 0
    accepts: int = 0
    delta_phi: float = 0.0       # cumulative ΔΦ at this stage
    return_value: float = 0.0
    return_ema: float = 0.0
    shell_meta: dict = field(default_factory=dict)


@dataclass
class Region:
    """The accepted-overlay graph from one pulse run."""
    seed_id: str = ""
    overlay_store: dict[str, Overlay] = field(default_factory=dict)
    stages: list[StageMetrics] = field(default_factory=list)
    final_overlay_id: str = ""
    status: str = "running"  # "terminated_threshold" / "terminated_factor_exhausted" / "max_stages"

    def add_overlay(self, overlay: Overlay) -> None:
        self.overlay_store[overlay.overlay_id] = overlay

    def summary(self) -> dict:
        total_attempts = sum(s.attempts for s in self.stages)
        total_accepts = sum(s.accepts for s in self.stages)
        cumulative_dphi = sum(s.delta_phi for s in self.stages)
        return {
            "seed_id": self.seed_id,
            "final_overlay_id": self.final_overlay_id,
            "status": self.status,
            "stage_count": len(self.stages),
            "total_attempts": total_attempts,
            "total_accepts": total_accepts,
            "overlays_accepted": len(self.overlay_store),
            "cumulative_delta_phi": cumulative_dphi,
        }


# ---------------------------------------------------------------------------
# MORSREngine — the pulse executor
# ---------------------------------------------------------------------------

class MORSREngine:
    """The pulse-cycle executor.

    Bundles an OperatorRegistry + a Policy + an NSLProvider + a
    HandshakeLog. Register a fresh engine per pulse run (or call
    `reset()` between runs).
    """

    name: str = "morsr_engine"

    def __init__(
        self,
        policy: Optional[MORSRPolicy] = None,
        operators: Optional[OperatorRegistry] = None,
        nsl: Optional[NSLProvider] = None,
    ) -> None:
        self.policy = policy or MORSRPolicy()
        self.operators = operators or OperatorRegistry()
        self.nsl = nsl or NSLProvider()
        self.log = HandshakeLog()
        self._plateau_remaining = self.policy.plateau_cap

    # ── Pulse cycle ───────────────────────────────────────────────────

    def pulse(self, seed: Overlay) -> Region:
        """Run the full MORSR pulse cycle on `seed`. Returns a Region."""
        region = Region(seed_id=seed.overlay_id)
        region.add_overlay(seed)
        current = seed
        self._plateau_remaining = self.policy.plateau_cap
        ret_ema: Optional[float] = None

        max_stages = self.policy.max_stages
        if max_stages is None:
            max_stages = len(self.policy.shell_factors)

        for stage in range(max_stages):
            factor = self.policy.shell_factors[
                min(stage, len(self.policy.shell_factors) - 1)
            ]
            active = current.active_indices()
            allowed, shell_meta = build_shell(
                mode=self.policy.shell_mode,
                mask_len=len(current.activations),
                base=self.policy.shell_base,
                factor=factor,
                stage=stage,
                active_idxs=active,
            )

            # Run Ring 1: apply each operator
            stage_metrics = StageMetrics(stage=stage, shell_meta=shell_meta)
            best_candidate: Optional[Overlay] = None
            best_delta: float = 0.0

            for op_name, op_fn in self.operators.items():
                candidate = self._apply_operator(op_fn, current)
                hs = self._evaluate_candidate(
                    op_name=op_name,
                    current=current,
                    candidate=candidate,
                    allowed=allowed,
                    stage=stage,
                )
                self.log.append(hs)
                stage_metrics.attempts += 1
                if hs.accepted:
                    stage_metrics.accepts += 1
                    stage_metrics.delta_phi += hs.delta
                    region.add_overlay(candidate)
                    # Keep the candidate with the most negative ΔΦ
                    if best_candidate is None or hs.delta < best_delta:
                        best_candidate = candidate
                        best_delta = hs.delta

            # Re-center if we improved
            if best_candidate is not None:
                current = best_candidate

            # Stop metric + EMA
            ret = self._compute_return(stage_metrics)
            stage_metrics.return_value = ret
            ret_ema = (
                ret if ret_ema is None
                else self.policy.ema_alpha * ret
                     + (1 - self.policy.ema_alpha) * ret_ema
            )
            stage_metrics.return_ema = ret_ema
            region.stages.append(stage_metrics)

            # Stop conditions
            if ret < self.policy.stop_threshold and ret_ema < self.policy.stop_threshold:
                region.status = "terminated_threshold"
                break
        else:
            region.status = "max_stages"

        if region.status == "running" and stage >= len(self.policy.shell_factors) - 1:
            region.status = "terminated_factor_exhausted"

        region.final_overlay_id = current.overlay_id
        return region

    # ── Per-candidate evaluation ─────────────────────────────────────

    def _evaluate_candidate(
        self,
        op_name: str,
        current: Overlay,
        candidate: Overlay,
        allowed: set[int],
        stage: int,
    ) -> Handshake:
        cand_actives = candidate.active_indices()
        phi_before = potential(current.position)
        phi_after = potential(candidate.position)
        delta = phi_after - phi_before
        sectors = self.nsl.compute_sectors(current.position, candidate.position)

        # Shell containment
        if cand_actives and not in_shell(cand_actives, allowed):
            return Handshake(
                overlay_id=candidate.overlay_id,
                op=op_name,
                phi_before=phi_before,
                phi_after=phi_after,
                delta=delta,
                sectors=sectors,
                accepted=False,
                reason="out_of_shell",
                stage=stage,
                ring=1,
            )

        # NSL gate decision
        decision = self.nsl.gate(
            sectors,
            mode=self.policy.gate_mode,
            budget=self.policy.stage_budget,
        )

        accepted = decision.accepted
        reason = decision.reason

        # Strict-decrease shortcut: prefer this label when delta < -eps
        if accepted and delta <= -self.policy.eps_phi:
            reason = "strict_decrease"
        elif accepted and abs(delta) <= self.policy.eps_phi:
            # Plateau handling
            if self._plateau_remaining > 0:
                self._plateau_remaining -= 1
                reason = "plateau"
            else:
                accepted = False
                reason = "plateau_exhausted"

        return Handshake(
            overlay_id=candidate.overlay_id,
            op=op_name,
            phi_before=phi_before,
            phi_after=phi_after,
            delta=delta,
            sectors=sectors,
            accepted=accepted,
            reason=reason,
            stage=stage,
            ring=1,
        )

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _apply_operator(op_fn, overlay: Overlay) -> Overlay:
        """Apply an operator with sensible defaults if it takes extra args."""
        try:
            return op_fn(overlay)
        except TypeError:
            # Operator expected extra args; call with empty kwargs to get
            # the operator's own defaults.
            return op_fn(overlay)

    def _compute_return(self, stage: StageMetrics) -> float:
        if self.policy.stop_metric == StopMetric.ACCEPT_RATE:
            return stage.accepts / max(stage.attempts, 1)
        if self.policy.stop_metric == StopMetric.NOVELTY:
            return float(stage.accepts)
        # STRICT_GAIN: cumulative magnitude of negative ΔΦ
        return max(0.0, -stage.delta_phi)

    def reset(self) -> None:
        """Clear the handshake log and plateau counter."""
        self.log.clear()
        self._plateau_remaining = self.policy.plateau_cap

    def __repr__(self) -> str:
        return (
            f"<MORSREngine ops={len(self.operators)} "
            f"handshakes={len(self.log)}>"
        )
