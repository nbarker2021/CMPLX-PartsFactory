"""
CQERunner / CQESystem — the CQE orchestrator (both flavors).

Merges the two canonical entry points:

  - `process_text(text, mode=...)` — Flavor 1 (Unified Runtime).
    8-stage pipeline: ingest → e8_embed → fractal → toroidal → phi →
    semantics → governance → validation. Receipt per stage. Emits a
    banded result.

  - `solve_problem(problem, domain_type, mode=...)` — Flavor 2 (Modular
    Orchestrator). 5-phase pipeline: domain adapt → channel extract →
    MORSR explore → analyze → recommend.

Both flavors share the same CQEAtom population, governance gate,
NSL conservation tracking, and receipt minting. `OperationMode`
selects which stages are active.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from cmplx.morphon import Morphon
from cmplx.nsl import NSLProvider, NSLSectors
from cmplx.receipt import ReceiptProvider, ReceiptType

from .atom import CQEAtom
from .banding import band_for, compute_v_total
from .domain import DomainAdapter
from .governance import CQEGovernance
from .mandelbrot import analyze_string
from .modes import OperationMode, profile_for
from .objective import CQEObjectiveFunction, ObjectiveScores
from .toroidal import generate_toroidal_shell, pattern_distribution


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class TextResult:
    """Output of `process_text`."""
    text: str
    mode: str
    e8: dict = field(default_factory=dict)
    fractal: dict = field(default_factory=dict)
    toroidal_patterns: dict = field(default_factory=dict)
    toroidal_n: int = 0
    phi_scores: Optional[ObjectiveScores] = None
    nsl_sectors: NSLSectors = field(default_factory=NSLSectors)
    governance_valid: bool = True
    governance_violations: int = 0
    v_total: float = 0.0
    band: str = "EXPLORATORY"
    receipt_ids: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "mode": self.mode,
            "e8": self.e8,
            "fractal": self.fractal,
            "toroidal_patterns": self.toroidal_patterns,
            "toroidal_n": self.toroidal_n,
            "phi_scores": self.phi_scores.to_dict() if self.phi_scores else None,
            "nsl_sectors": self.nsl_sectors.to_dict(),
            "governance_valid": self.governance_valid,
            "governance_violations": self.governance_violations,
            "v_total": self.v_total,
            "band": self.band,
            "receipt_count": len(self.receipt_ids),
            "elapsed_seconds": self.elapsed_seconds,
        }


@dataclass
class ProblemSolution:
    """Output of `solve_problem`."""
    problem: dict
    domain_type: str
    mode: str
    initial_vector: tuple[float, ...] = ()
    optimal_vector: tuple[float, ...] = ()
    reference_channels: tuple[float, ...] = ()
    optimal_channels: tuple[float, ...] = ()
    objective_score: float = 0.0
    phi_scores: Optional[ObjectiveScores] = None
    recommendations: list[str] = field(default_factory=list)
    receipt_ids: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "problem": self.problem,
            "domain_type": self.domain_type,
            "mode": self.mode,
            "initial_vector": list(self.initial_vector),
            "optimal_vector": list(self.optimal_vector),
            "objective_score": self.objective_score,
            "phi_scores": self.phi_scores.to_dict() if self.phi_scores else None,
            "recommendations": self.recommendations,
            "receipt_count": len(self.receipt_ids),
            "elapsed_seconds": self.elapsed_seconds,
        }


# ---------------------------------------------------------------------------
# CQEConfig — the small config knob bundle
# ---------------------------------------------------------------------------

@dataclass
class CQEConfig:
    operation_mode: OperationMode = OperationMode.ENHANCED
    governance_policy: str = "standard"
    seed: int = 42
    toroidal_n_points: int = 64
    mandelbrot_max_iter: int = 50
    agent_id: str = "cqe"


# ---------------------------------------------------------------------------
# CQERunner / CQESystem — unified orchestrator
# ---------------------------------------------------------------------------

class CQERunner:
    """The CQE orchestrator. Two main entry points:

      - `process_text(text)` — text → 8-stage pipeline → TextResult
      - `solve_problem(problem, domain_type)` → 5-phase pipeline →
        ProblemSolution

    Subsystems registered at construction; can be passed in or built
    with defaults. The active `OperationMode` selects which stages run.
    """

    name: str = "cqe_runner"

    def __init__(
        self,
        config: Optional[CQEConfig] = None,
        nsl: Optional[NSLProvider] = None,
        receipts: Optional[ReceiptProvider] = None,
        governance: Optional[CQEGovernance] = None,
        domain_adapter: Optional[DomainAdapter] = None,
        objective: Optional[CQEObjectiveFunction] = None,
        morsr: Optional[Any] = None,  # MORSRProvider (avoid hard import cycle)
    ) -> None:
        self.config = config or CQEConfig()
        self.nsl = nsl or NSLProvider()
        self.receipts = receipts or ReceiptProvider()
        self.governance = governance or CQEGovernance(nsl=self.nsl)
        self.governance.set_active_policy(self.config.governance_policy)
        self.domain_adapter = domain_adapter or DomainAdapter()
        self.objective = objective or CQEObjectiveFunction(nsl=self.nsl)
        self.morsr = morsr  # Optional — `solve_problem` requires it

    # ── Flavor 1: process_text ───────────────────────────────────────

    def process_text(
        self,
        text: str,
        mode: Optional[OperationMode] = None,
    ) -> TextResult:
        """Run the 8-stage unified pipeline on `text`."""
        mode = mode or self.config.operation_mode
        profile = profile_for(mode)
        start = time.time()

        result = TextResult(text=text, mode=mode.value)

        # Stage 1: ingest (always)
        ingest_receipt = self.receipts.mint(
            receipt_type=ReceiptType.PROCESS.value,
            agent_id=self.config.agent_id,
            operation="cqe.ingest",
            payload={"text_len": len(text), "mode": mode.value},
        )
        result.receipt_ids.append(ingest_receipt.receipt_id)

        # Stage 2: E8 embed (Flavor 1 style)
        if profile.e8_embed:
            e8_vec = self.domain_adapter.embed_text(text)
            result.e8 = {
                "vector": list(e8_vec),
                "norm": sum(x * x for x in e8_vec) ** 0.5,
            }
            r = self.receipts.mint(
                receipt_type=ReceiptType.PROCESS.value,
                agent_id=self.config.agent_id,
                operation="cqe.e8_embed",
                payload=result.e8,
            )
            result.receipt_ids.append(r.receipt_id)

        # Stage 3: Mandelbrot fractal
        if profile.fractal_mandelbrot:
            result.fractal = analyze_string(
                text, max_iter=self.config.mandelbrot_max_iter
            )
            r = self.receipts.mint(
                receipt_type=ReceiptType.PROCESS.value,
                agent_id=self.config.agent_id,
                operation="cqe.fractal",
                payload={"behavior": result.fractal["behavior"]},
            )
            result.receipt_ids.append(r.receipt_id)

        # Stage 4: Toroidal shell
        if profile.toroidal_shell:
            shell = generate_toroidal_shell(
                n_points=self.config.toroidal_n_points,
                seed=self.config.seed,
            )
            result.toroidal_n = len(shell)
            result.toroidal_patterns = pattern_distribution(shell)
            r = self.receipts.mint(
                receipt_type=ReceiptType.PROCESS.value,
                agent_id=self.config.agent_id,
                operation="cqe.toroidal",
                payload={"n_points": result.toroidal_n,
                         "patterns": result.toroidal_patterns},
            )
            result.receipt_ids.append(r.receipt_id)

        # Stage 5: Phi (objective) computation
        if profile.phi_computation and result.e8:
            vec = tuple(result.e8["vector"])
            # Use the vector itself as reference channels for the first pass
            ref_channels = tuple(c / max(1.0, abs(c)) for c in vec)
            result.phi_scores = self.objective.evaluate(
                vector=vec, reference_channels=ref_channels,
                v_before=tuple(0.0 for _ in vec),
            )
            result.nsl_sectors = result.phi_scores.nsl_sectors
            r = self.receipts.mint(
                receipt_type=ReceiptType.GATE.value,
                agent_id=self.config.agent_id,
                operation="cqe.phi",
                delta_phi=result.nsl_sectors.total,
                payload={"phi_total": result.phi_scores.phi_total},
            )
            result.receipt_ids.append(r.receipt_id)

        # Stage 6: Governance
        if profile.governance and result.e8:
            ctx = {
                "e8_coordinates": tuple(result.e8["vector"]),
                "sectors": result.nsl_sectors,
                "timestamp": time.time(),
            }
            gov_check = self.governance.validate(item=None, ctx=ctx)
            result.governance_valid = gov_check["valid"]
            result.governance_violations = len(gov_check["violations"])
            r = self.receipts.mint(
                receipt_type=ReceiptType.GATE.value,
                agent_id=self.config.agent_id,
                operation="cqe.governance",
                payload={"valid": result.governance_valid,
                         "violations": result.governance_violations,
                         "policy": gov_check.get("policy")},
            )
            result.receipt_ids.append(r.receipt_id)

        # Stage 7: Validation banding
        if profile.validation and result.phi_scores:
            score_dict = {
                "phi_total": result.phi_scores.phi_total,
                "parity_consistency": result.phi_scores.parity_consistency,
                "chamber_stability": result.phi_scores.chamber_stability,
                "geometric_separation": result.phi_scores.geometric_separation,
            }
            weights = {"phi_total": 0.4, "parity_consistency": 0.2,
                       "chamber_stability": 0.2, "geometric_separation": 0.2}
            result.v_total = compute_v_total(score_dict, weights)
            result.band = band_for(result.v_total)
            r = self.receipts.mint(
                receipt_type=ReceiptType.PROCESS.value,
                agent_id=self.config.agent_id,
                operation="cqe.validate",
                payload={"v_total": result.v_total, "band": result.band},
            )
            result.receipt_ids.append(r.receipt_id)

        result.elapsed_seconds = time.time() - start
        return result

    # ── Flavor 2: solve_problem ──────────────────────────────────────

    def solve_problem(
        self,
        problem: dict,
        domain_type: str = "computational",
        mode: Optional[OperationMode] = None,
    ) -> ProblemSolution:
        """Run the 5-phase modular pipeline on a structured problem."""
        mode = mode or self.config.operation_mode
        start = time.time()

        solution = ProblemSolution(
            problem=dict(problem),
            domain_type=domain_type,
            mode=mode.value,
        )

        # Phase 1: Domain adaptation
        initial = self.domain_adapter.adapt(problem, domain_type)
        solution.initial_vector = initial
        r = self.receipts.mint(
            receipt_type=ReceiptType.PROCESS.value,
            agent_id=self.config.agent_id,
            operation="cqe.adapt",
            payload={"domain_type": domain_type,
                     "initial_norm": sum(x * x for x in initial) ** 0.5},
        )
        solution.receipt_ids.append(r.receipt_id)

        # Phase 2: Reference channels
        # Simple form: normalize the vector to unit magnitude per component
        norm = max(1e-9, sum(x * x for x in initial) ** 0.5)
        ref_channels = tuple(x / norm for x in initial)
        solution.reference_channels = ref_channels

        # Phase 3: MORSR exploration (if MORSR provider available)
        optimal = initial
        if self.morsr is not None and profile_for(mode).morsr_exploration:
            # Build an Overlay from initial and pulse
            from cmplx.morsr import Overlay
            seed = Overlay(position=initial)
            region = self.morsr.pulse(seed)
            # Use final overlay's position as optimal
            final = region.overlay_store.get(region.final_overlay_id)
            if final is not None:
                optimal = final.position
            r = self.receipts.mint(
                receipt_type=ReceiptType.PROCESS.value,
                agent_id=self.config.agent_id,
                operation="cqe.morsr_explore",
                payload={"stages": len(region.stages),
                         "status": region.status},
            )
            solution.receipt_ids.append(r.receipt_id)
        solution.optimal_vector = optimal
        solution.optimal_channels = ref_channels  # carry forward

        # Phase 4: Analysis (objective score breakdown)
        solution.phi_scores = self.objective.evaluate(
            vector=optimal, reference_channels=ref_channels,
            domain_context={"domain_type": domain_type, **problem},
            v_before=initial,
        )
        solution.objective_score = solution.phi_scores.phi_total
        r = self.receipts.mint(
            receipt_type=ReceiptType.GATE.value,
            agent_id=self.config.agent_id,
            operation="cqe.analyze",
            delta_phi=solution.phi_scores.nsl_sectors.total,
            payload={"phi_total": solution.objective_score},
        )
        solution.receipt_ids.append(r.receipt_id)

        # Phase 5: Recommendations
        solution.recommendations = self._generate_recommendations(
            solution.phi_scores, domain_type, problem
        )

        solution.elapsed_seconds = time.time() - start
        return solution

    def _generate_recommendations(
        self,
        scores: ObjectiveScores,
        domain_type: str,
        problem: dict,
    ) -> list[str]:
        recs: list[str] = []
        if scores.phi_total < 0.5:
            recs.append("Phi_total below 0.5 — increase MORSR iterations or "
                        "adjust exploration parameters.")
        if scores.parity_consistency < 0.5:
            recs.append("Improve parity channel consistency via repair iterations.")
        if scores.chamber_stability < 0.6:
            recs.append("Enhance chamber stability — consider alternative "
                        "projection methods.")
        if scores.geometric_separation < 0.3:
            recs.append("Geometric separation low; problem may be too close "
                        "to origin to discriminate.")
        if domain_type == "computational":
            cclass = problem.get("complexity_class")
            if cclass in ("P", "NP") and scores.geometric_separation < 0.5:
                recs.append(f"Geometric separation suggests potential "
                            f"misclassification of {cclass} problem.")
        if not recs:
            recs.append("Solution quality excellent — no specific "
                        "improvements needed.")
        return recs

    # ── Atom-aware forging ───────────────────────────────────────────

    def forge_atom(
        self,
        payload: Any,
        *,
        parent: Optional[str] = None,
        source_text: Optional[str] = None,
    ) -> CQEAtom:
        """Mint a fresh CQE atom (Morphon with all CQE fields populated)
        and emit a MINT receipt."""
        atom = CQEAtom.forge(payload, source_text=source_text, parent=parent)
        r = self.receipts.mint(
            receipt_type=ReceiptType.MINT.value,
            agent_id=self.config.agent_id,
            atom_id=atom.id,
            operation="cqe.forge_atom",
            payload={
                "quad": list(atom.quad_encoding),
                "dr": atom.digital_root,
            },
        )
        return atom

    # ── Reporting ────────────────────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": "cqe_runner",
            "mode": self.config.operation_mode.value,
            "governance_policy": (
                self.governance.active_policy().name
                if self.governance.active_policy() else None
            ),
            "nsl_cumulative": self.nsl.ledger.cumulative,
            "receipts_minted": self.receipts.length,
            "morsr_available": self.morsr is not None,
        }

    def __repr__(self) -> str:
        return (
            f"<CQERunner mode={self.config.operation_mode.value} "
            f"policy={self.governance.active_policy().name if self.governance.active_policy() else 'none'}>"
        )


# Backward-compat alias — CQESystem is just CQERunner.
CQESystem = CQERunner
