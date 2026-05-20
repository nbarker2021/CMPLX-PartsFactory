"""
CQEProvider — the `engine` port provider.

Bundles `CQERunner` + `CQEGovernance` + `CQEObjectiveFunction` +
`DomainAdapter` + (optional) `MORSRProvider`. Register on the
`engine` port:

    MorphonController.get().register("engine", CQEProvider())
"""
from __future__ import annotations

from typing import Any, Optional

from cmplx.nsl import NSLProvider
from cmplx.receipt import ReceiptProvider

from .atom import CQEAtom
from .cqe import CQEConfig, CQERunner, ProblemSolution, TextResult
from .domain import DomainAdapter
from .governance import CQEGovernance
from .modes import OperationMode
from .objective import CQEObjectiveFunction


class CQEProvider:
    """Composite CQE provider: orchestrator + governance + objective."""

    name: str = "cqe_provider"

    def __init__(
        self,
        config: Optional[CQEConfig] = None,
        nsl: Optional[NSLProvider] = None,
        receipts: Optional[ReceiptProvider] = None,
        morsr: Optional[Any] = None,
    ) -> None:
        self.config = config or CQEConfig()
        self.nsl = nsl or NSLProvider()
        self.receipts = receipts or ReceiptProvider()
        self.governance = CQEGovernance(nsl=self.nsl)
        self.governance.set_active_policy(self.config.governance_policy)
        self.domain_adapter = DomainAdapter()
        self.objective = CQEObjectiveFunction(nsl=self.nsl)
        self.runner = CQERunner(
            config=self.config,
            nsl=self.nsl,
            receipts=self.receipts,
            governance=self.governance,
            domain_adapter=self.domain_adapter,
            objective=self.objective,
            morsr=morsr,
        )

    # ── Main entry points ────────────────────────────────────────────

    def process_text(
        self,
        text: str,
        mode: Optional[OperationMode] = None,
    ) -> TextResult:
        return self.runner.process_text(text, mode=mode)

    def solve_problem(
        self,
        problem: dict,
        domain_type: str = "computational",
        mode: Optional[OperationMode] = None,
    ) -> ProblemSolution:
        return self.runner.solve_problem(problem, domain_type, mode=mode)

    def forge_atom(self, payload: Any, **kwargs) -> CQEAtom:
        return self.runner.forge_atom(payload, **kwargs)

    # ── Configuration ────────────────────────────────────────────────

    def set_mode(self, mode: OperationMode) -> None:
        self.runner.config.operation_mode = mode

    def set_governance_policy(self, name: str) -> bool:
        return self.governance.set_active_policy(name)

    def attach_morsr(self, morsr_provider: Any) -> None:
        """Wire in a MORSR provider so `solve_problem` can use its
        pulse cycle in Phase 3."""
        self.runner.morsr = morsr_provider

    # ── Reporting ────────────────────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": "cqe_provider",
            "runner": self.runner.health,
            "governance": self.governance.health,
            "config": {
                "mode": self.config.operation_mode.value,
                "policy": self.config.governance_policy,
                "seed": self.config.seed,
            },
        }

    def __repr__(self) -> str:
        return (
            f"<CQEProvider mode={self.config.operation_mode.value} "
            f"policy={self.governance.active_policy().name if self.governance.active_policy() else 'none'}>"
        )
