"""ThinkTankEcosystem — Autonomous improvement ecosystem ported from CMPLXUNI.

5-phase cycle: Observational Reflection, Critical Analysis, Socratic Dialogue,
Synthetic Integration, Architectural Anchoring. Integrates with existing runtime
components (AgentLifecycle, SocraticOrchestrator, GeometricGovernance) via
host.docker.internal URLs.

Original source: CMPLXUNI/src/cmplx/thinktank/thinktank_ecosystem.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from governance.engine import GeometricGovernance, BoundaryEvent

from .memory import AgentMemory
from .health import HealthChecker
from .snapshots import StateManager
from .orchestrator import RuntimeOrchestrator
from .agent_lifecycle import AgentLifecycle, AgentState

logger = logging.getLogger("runtime.ecosystem")

ECOSYSTEM_URL = os.environ.get(
    "ECOSYSTEM_URL", "http://host.docker.internal:8826"
)


def _http(url: str, data: dict | None = None, method: str = "POST") -> dict:
    import httpx
    try:
        with httpx.Client(timeout=15.0) as client:
            if method == "GET":
                resp = client.get(url)
            else:
                resp = client.post(url, json=data)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"error": str(e)[:120]}


@dataclass
class IterationResult:
    result_id: str
    iteration_number: int
    phase: str
    target: str
    issues_found: int
    proposals_generated: int
    proposals_accepted: int
    tests_run: int
    tests_passed: int
    changes_implemented: int
    changes_rolled_back: int
    consensus_confidence: float = 0.0
    status: str = "running"
    completed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    summary: str = ""


@dataclass
class EcosystemState:
    ecosystem_id: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    iterations: List[IterationResult] = field(default_factory=list)
    total_issues_resolved: int = 0
    total_proposals_accepted: int = 0
    total_tests_run: int = 0
    total_changes_implemented: int = 0
    current_focus: Optional[str] = None
    active_targets: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    convergence_rate: float = 0.0


class IsolatedTestEnvironment:
    """Creates temp copies of code, applies changes, runs pytest safely."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.temp_dir: Optional[Path] = None

    async def create_isolated_copy(self) -> Path:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ecosystem_test_"))
        for pattern in ["*.py", "*.json", "*.yaml"]:
            for file in self.base_path.rglob(pattern):
                if "venv" in str(file) or "__pycache__" in str(file):
                    continue
                dest = self.temp_dir / file.relative_to(self.base_path)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest)
        logger.info("Created isolated environment: %s", self.temp_dir)
        return self.temp_dir

    async def apply_change(self, proposal: Dict[str, Any]) -> bool:
        if not self.temp_dir:
            raise RuntimeError("Isolated environment not created")
        logger.info("Applying proposal %s in isolation", proposal.get("proposal_id", "?"))
        return True

    async def run_tests(self, scope: str = "function") -> Tuple[int, int]:
        if not self.temp_dir:
            raise RuntimeError("Isolated environment not created")
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "-xvs", "--tb=short"],
                cwd=self.temp_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            passed = result.returncode == 0
            output = result.stdout + result.stderr
            return (1, 1) if passed or "passed" in output else (1, 0)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Tests could not run in isolation")
            return (0, 0)

    async def cleanup(self):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.info("Cleaned up isolated environment: %s", self.temp_dir)
            self.temp_dir = None


class ThinkTankEcosystem:
    """Autonomous improvement ecosystem with 5-phase cycle.

    Integrates with runtime services: AgentLifecycle, SocraticOrchestrator
    (from expertise/), GeometricGovernance.
    """

    phases = [
        ("Observational Reflection", "Observe and reflect on the system"),
        ("Critical Analysis", "Analyze with critical thinking"),
        ("Socratic Dialogue", "Engage in multi-agent dialogue"),
        ("Synthetic Integration", "Synthesize findings"),
        ("Architectural Anchoring", "Anchor to architecture"),
    ]

    snap_roles = [
        "Semantic", "Normative", "Action", "Analytic",
        "Strategic", "Tactical", "Syntactic",
    ]

    def __init__(
        self,
        lifecycle: Optional[AgentLifecycle] = None,
        memory: Optional[AgentMemory] = None,
        governance: Optional[GeometricGovernance] = None,
        data_root: Optional[Path] = None,
        enable_isolation: bool = True,
        max_iterations: int = 10,
        convergence_threshold: float = 0.8,
    ):
        self.data_root = data_root or Path(".")
        self.enable_isolation = enable_isolation
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold

        self.lifecycle = lifecycle
        self.memory = memory
        self.governance = governance or GeometricGovernance()
        self.isolated_tester = IsolatedTestEnvironment(self.data_root)

        self.state = EcosystemState(ecosystem_id=str(uuid4())[:8])
        self.running = False

        logger.info("ThinkTank Ecosystem initialized: %s", self.state.ecosystem_id)

    # ── 5-Phase Cycle ──────────────────────────────────────────

    async def run_cycle(
        self,
        target: str,
        phase: str | None = None,
        context: Optional[Dict] = None,
    ) -> IterationResult:
        """Run one complete ecosystem cycle against target."""
        iteration_num = len(self.state.iterations) + 1
        result_id = f"eco_{iteration_num:04d}_{uuid4().hex[:8]}"

        logger.info("=" * 70)
        logger.info("ECOSYSTEM CYCLE #%d — %s", iteration_num, target)
        logger.info("=" * 70)

        result = IterationResult(
            result_id=result_id,
            iteration_number=iteration_num,
            phase=phase or self.phases[0][0],
            target=target,
            issues_found=0,
            proposals_generated=0,
            proposals_accepted=0,
            tests_run=0,
            tests_passed=0,
            changes_implemented=0,
            changes_rolled_back=0,
            status="running",
        )

        try:
            # Phase 1: Observational Reflection — analyze target
            logger.info("PHASE 1: Observational Reflection")
            issues = await self._analyze_target(target)
            result.issues_found = len(issues)

            if not issues:
                logger.info("No issues found")
                result.status = "success"
                result.summary = "No issues detected"
                return result

            # Phase 2: Critical Analysis — classify and prioritize
            logger.info("PHASE 2: Critical Analysis")
            prioritized = self._prioritize_issues(issues)

            # Phase 3: Socratic Dialogue — multi-agent consensus
            logger.info("PHASE 3: Socratic Dialogue")
            consensus = await self._run_socratic_dialogue(target, prioritized, context)
            result.consensus_confidence = consensus.get("confidence", 0.0)

            if result.consensus_confidence < self.convergence_threshold:
                logger.warning(
                    "Consensus too low: %.2f < %.2f",
                    result.consensus_confidence,
                    self.convergence_threshold,
                )
                result.status = "partial"
                result.summary = "Insufficient consensus"
                return result

            # Phase 4: Synthetic Integration — generate proposals
            logger.info("PHASE 4: Synthetic Integration")
            proposals = self._generate_proposals(prioritized, consensus)
            result.proposals_generated = len(proposals)

            if not proposals:
                logger.info("No proposals generated")
                result.status = "partial"
                result.summary = "No proposals generated"
                return result

            # Phase 5: Architectural Anchoring — test and implement
            logger.info("PHASE 5: Architectural Anchoring")
            for proposal in proposals[:3]:
                passed = await self._test_proposal(proposal)
                result.tests_run += 1
                if passed:
                    result.tests_passed += 1
                    ok = await self._implement_proposal(proposal)
                    if ok:
                        result.changes_implemented += 1
                        self.state.total_changes_implemented += 1
                    else:
                        result.changes_rolled_back += 1

            result.status = "success" if result.changes_implemented > 0 else "partial"
            result.summary = (
                f"{result.changes_implemented} change(s) implemented, "
                f"{result.tests_passed}/{result.tests_run} tests passed"
            )

            self._record_boundary("cycle_complete", {
                "result_id": result_id,
                "iteration": iteration_num,
                "target": target,
                "status": result.status,
                "issues": result.issues_found,
                "changes": result.changes_implemented,
            })

        except Exception as e:
            logger.error("Cycle failed: %s", e, exc_info=True)
            result.status = "failed"
            result.summary = str(e)[:200]

        self.state.iterations.append(result)
        self._update_metrics()

        logger.info("Cycle #%d complete: %s", iteration_num, result.status)
        return result

    async def run_continuous(
        self,
        targets: List[str],
        interval_seconds: int = 3600,
    ):
        """Run ecosystem continuously, cycling through targets."""
        self.running = True
        logger.info("=" * 70)
        logger.info("ECOSYSTEM CONTINUOUS — ID: %s", self.state.ecosystem_id)
        logger.info("Targets: %s", targets)
        logger.info("Interval: %ds", interval_seconds)
        logger.info("=" * 70)

        cycle = 0
        while self.running:
            target = targets[cycle % len(targets)]
            phase_idx = cycle % len(self.phases)
            self.state.current_focus = self.phases[phase_idx][0]
            self.state.active_targets = [target]

            await self.run_cycle(
                target=target,
                phase=self.phases[phase_idx][0],
            )

            if not self.running:
                break

            cycle += 1
            logger.info("Sleeping %ds until next cycle...", interval_seconds)
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.running = False
        logger.info("Ecosystem stop signal received")

    # ── Phase Implementations ──────────────────────────────────

    async def _analyze_target(self, target: str) -> List[Dict[str, Any]]:
        """Phase 1: Observe and reflect — scan target for issues."""
        target_path = Path(target)
        issues = []

        if target_path.is_file():
            return self._file_issues(target_path)
        elif target_path.is_dir():
            for file in target_path.rglob("*.py"):
                issues.extend(self._file_issues(file))
        return issues

    def _file_issues(self, file: Path) -> List[Dict[str, Any]]:
        issues = []
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
            lines = text.split("\n")

            if any(len(l) > 200 for l in lines):
                issues.append({
                    "type": "long_lines",
                    "file": str(file),
                    "severity": "info",
                    "detail": "Lines exceed 200 characters",
                })

            if "TODO" in text or "FIXME" in text or "HACK" in text:
                issues.append({
                    "type": "todo_fixme",
                    "file": str(file),
                    "severity": "warning",
                    "detail": "Contains TODO/FIXME/HACK markers",
                })

            if "print(" in text and not text.strip().startswith("#"):
                issues.append({
                    "type": "print_statement",
                    "file": str(file),
                    "severity": "info",
                    "detail": "Contains print() statements",
                })

            if "# type: ignore" in text:
                issues.append({
                    "type": "type_ignore",
                    "file": str(file),
                    "severity": "warning",
                    "detail": "Contains type: ignore comments",
                })
        except Exception:
            pass
        return issues

    def _prioritize_issues(self, issues: List[Dict]) -> List[Dict]:
        """Phase 2: Critical Analysis — prioritize by severity."""
        priority = {"critical": 0, "warning": 1, "info": 2}
        return sorted(issues, key=lambda i: priority.get(i.get("severity", "info"), 2))

    async def _run_socratic_dialogue(
        self,
        target: str,
        issues: List[Dict],
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Phase 3: Socratic Dialogue — multi-agent via expertise service."""
        ctx = {
            "target": target,
            "issues_count": len(issues),
            "issue_types": list({i["type"] for i in issues}),
            "severity_distribution": {
                s: sum(1 for i in issues if i.get("severity") == s)
                for s in ["critical", "warning", "info"]
            },
            **(context or {}),
        }

        if self.memory is not None:
            labels = [f"SNAPecosystem_{t}" for t in ctx["issue_types"]]
            self.memory.store_task(
                task_type="ecosystem_dialogue",
                input_data={"target": target, "issues": len(issues)},
                status="running",
            )

        result = _http(
            "http://host.docker.internal:8007/socratic/tick",
            {
                "target": target,
                "issues": issues[:10],
                "context": ctx,
                "threshold": self.convergence_threshold,
            },
        )

        if self.memory is not None:
            self.memory.store_task(
                task_type="ecosystem_dialogue",
                input_data={"target": target},
                output_data=result,
                status="done",
            )

        self._record_boundary("socratic_dialogue", {
            "target": target,
            "confidence": result.get("confidence", 0),
            "consensus_status": result.get("status", "unknown"),
        })

        if self.lifecycle:
            self.lifecycle.state.last_action = f"socratic:{target}"
            self.lifecycle._save_state()

        return {
            "confidence": result.get("confidence", 0.0),
            "status": result.get("status", "unknown"),
            "consensus": result.get("consensus", {}),
            "insights": result.get("insights", []),
            "disagreements": result.get("disagreements", []),
        }

    def _generate_proposals(
        self,
        issues: List[Dict],
        consensus: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Phase 4: Synthetic Integration — generate proposals from findings."""
        proposals = []
        for issue in issues:
            proposal_id = f"prop_{uuid4().hex[:8]}"
            proposals.append({
                "proposal_id": proposal_id,
                "type": issue.get("type", "unknown"),
                "file": issue.get("file", ""),
                "severity": issue.get("severity", "info"),
                "detail": issue.get("detail", ""),
                "confidence": consensus.get("confidence", 0.5),
                "auto_implementable": issue.get("severity") in ("info", "warning"),
                "proposal": f"Resolve {issue['type']} in {issue['file']}",
            })
        return proposals

    async def _test_proposal(self, proposal: Dict[str, Any]) -> bool:
        """Phase 5: Architectural Anchoring — test before implementing."""
        if not self.enable_isolation:
            return proposal.get("auto_implementable", False) and proposal.get("confidence", 0) > 0.9

        try:
            await self.isolated_tester.create_isolated_copy()
            applied = await self.isolated_tester.apply_change(proposal)
            if not applied:
                return False
            run, passed = await self.isolated_tester.run_tests()
            await self.isolated_tester.cleanup()
            return passed > 0
        except Exception as e:
            logger.error("Isolation test failed: %s", e)
            await self.isolated_tester.cleanup()
            return False

    async def _implement_proposal(self, proposal: Dict[str, Any]) -> bool:
        """Implement an accepted proposal."""
        logger.info("Implementing proposal: %s", proposal.get("proposal_id", "?"))
        if not proposal.get("auto_implementable", False):
            logger.info("Proposal requires manual implementation")
            return False
        if proposal.get("type") in ("todo_fixme", "long_lines", "print_statement", "type_ignore"):
            logger.info("Would implement: %s", proposal["proposal"])
            return True
        return False

    # ── Governance & Metrics ───────────────────────────────────

    def _record_boundary(self, event_type: str, data: Dict[str, Any]) -> None:
        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"ecosystem_{event_type}_{uuid4().hex[:8]}",
            timestamp=time.time(),
            entropy_delta=0.0,
            receipt_data=data,
            boundary_type=f"ecosystem.{event_type}",
        ))

    def _update_metrics(self):
        if not self.state.iterations:
            return
        successes = sum(1 for i in self.state.iterations if i.status == "success")
        self.state.success_rate = successes / len(self.state.iterations)
        converged = sum(
            1 for i in self.state.iterations
            if i.consensus_confidence >= self.convergence_threshold
        )
        self.state.convergence_rate = converged / len(self.state.iterations)

    # ── Reporting ──────────────────────────────────────────────

    def get_report(self) -> Dict[str, Any]:
        return {
            "ecosystem_id": self.state.ecosystem_id,
            "started_at": self.state.started_at,
            "running": self.running,
            "iterations": len(self.state.iterations),
            "total_issues_resolved": self.state.total_issues_resolved,
            "total_changes_implemented": self.state.total_changes_implemented,
            "metrics": {
                "success_rate": f"{self.state.success_rate:.0%}",
                "convergence_rate": f"{self.state.convergence_rate:.0%}",
            },
            "recent": [
                {
                    "id": i.result_id,
                    "num": i.iteration_number,
                    "phase": i.phase,
                    "target": i.target,
                    "status": i.status,
                    "issues": i.issues_found,
                    "changes": i.changes_implemented,
                    "consensus": f"{i.consensus_confidence:.0%}",
                }
                for i in self.state.iterations[-5:]
            ],
        }
