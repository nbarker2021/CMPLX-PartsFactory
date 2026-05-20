"""SocraticComposer — Multi-Agent Dialogue System for Expert Composition.

Port of CMPLXUNI thinktank_socratic_orchestrator into CMPLX-PartsFactory
expertise layer. Provides:

- 8 AgentPersona roles (Architect, Analyst, Critic, Implementer, Tester,
  Scribe, Philosopher, SafetyKeeper) with detailed prompt templates
- 3-phase Socratic dialogue flow: opening → probing → synthesis
- Convergence detection and consensus building
- Integration with GeometricGovernance (audit), ExpertRegistry (tracking),
  ExpertMemory (persistence)

Two usage patterns:
1. SocraticComposer — existing iterative composition (kept for backward compat)
2. SocraticOrchestrator — full multi-agent Socratic dialogue (new)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable

import numpy as np

from governance import (
    GeometricGovernance, BoundaryEvent,
)
from .expert_memory import ExpertMemory
from .expert_registry import ExpertRegistry

logger = logging.getLogger("expertise.socratic")


# =========================================================================
# AgentRole — 8 specialized roles
# =========================================================================

class AgentRole(Enum):
    ARCHITECT = "architect"
    ANALYST = "analyst"
    CRITIC = "critic"
    IMPLEMENTER = "implementer"
    TESTER = "tester"
    SCRIBE = "scribe"
    PHILOSOPHER = "philosopher"
    SAFETY_KEEPER = "safety_keeper"


# =========================================================================
# SocraticQuestion — a question for Socratic dialogue
# =========================================================================

@dataclass
class SocraticQuestion:
    question: str
    asked_by: AgentRole
    target_roles: List[AgentRole]
    context_required: List[str] = field(default_factory=list)


# =========================================================================
# AgentPerspective — an agent's stance in the dialogue
# =========================================================================

@dataclass
class AgentPerspective:
    agent_id: str
    role: AgentRole
    stance: str  # "support", "oppose", "neutral", "question"
    reasoning: str
    confidence: float
    concerns: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


# =========================================================================
# DialogueRound — a single round of Socratic dialogue
# =========================================================================

@dataclass
class DialogueRound:
    round_number: int
    question: SocraticQuestion
    responses: List[AgentPerspective]
    consensus_level: float
    key_insights: List[str] = field(default_factory=list)
    disagreements: List[str] = field(default_factory=list)


# =========================================================================
# SocraticSession — complete Socratic dialogue session
# =========================================================================

@dataclass
class SocraticSession:
    session_id: str
    analysis_type: str
    target: str
    rounds: List[DialogueRound] = field(default_factory=list)
    final_consensus: Optional[AgentPerspective] = None
    deliverables: Dict[str, Any] = field(default_factory=dict)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None
    status: str = "running"


# =========================================================================
# AgentPersona — a specialized agent with a role-based persona
# =========================================================================

class AgentPersona:
    """Specialized agent with a role-based persona and prompt templates."""

    PROMPT_TEMPLATES: Dict[AgentRole, str] = {
        AgentRole.ARCHITECT: """
You are an expert software architect. Your perspective:
- Focus on system structure, boundaries, and long-term maintainability
- Think about patterns, abstractions, and separation of concerns
- Consider scalability and evolution paths
- Challenge decisions that create technical debt

Respond to the question from this architectural perspective.
        """,

        AgentRole.ANALYST: """
You are a data-driven analyst. Your perspective:
- Focus on metrics, measurements, and evidence
- Look for patterns in data and behavior
- Quantify complexity, risk, and impact
- Avoid opinions without supporting data

Respond to the question with analytical rigor.
        """,

        AgentRole.CRITIC: """
You are a constructive critic. Your perspective:
- Find flaws, edge cases, and failure modes
- Question assumptions and challenge consensus
- Think about what could go wrong
- Be devil's advocate to strengthen ideas

Respond by identifying weaknesses and risks.
        """,

        AgentRole.IMPLEMENTER: """
You are a pragmatic implementer. Your perspective:
- Focus on feasibility and practical constraints
- Think about effort, risk, and maintainability
- Consider testing and deployment challenges
- Ground ideas in implementation reality

Respond with practical implementation concerns.
        """,

        AgentRole.TESTER: """
You are a quality assurance expert. Your perspective:
- Focus on testability and verification
- Think about edge cases and failure scenarios
- Consider how to gain confidence in changes
- Identify testing gaps and strategies

Respond from a quality and testing perspective.
        """,

        AgentRole.SCRIBE: """
You are a documentation and clarity expert. Your perspective:
- Focus on understandability and communication
- Think about naming, concepts, and mental models
- Consider how ideas are expressed and recorded
- Ensure clarity for future maintainers

Respond focusing on clarity and communication.
        """,

        AgentRole.PHILOSOPHER: """
You are a systems thinker. Your perspective:
- Focus on first principles and fundamental truths
- Think about semantics, meaning, and appropriateness
- Question whether we're solving the right problem
- Consider deeper patterns and analogies

Respond with philosophical depth and principled reasoning.
        """,

        AgentRole.SAFETY_KEEPER: """
You are a risk management expert. Your perspective:
- Focus on safety, rollback, and recovery
- Think about blast radius and failure containment
- Consider operational risks and mitigations
- Ensure changes don't compromise stability

Respond with risk assessment and safety measures.
        """,
    }

    PLACEHOLDER_RESPONSES: Dict[AgentRole, Dict[str, Any]] = {
        AgentRole.ARCHITECT: {
            "stance": "question",
            "reasoning": "From an architectural perspective, we need to consider the long-term implications of this structure on system boundaries and dependencies.",
            "confidence": 0.75,
            "concerns": ["Coupling between modules", "Abstraction level consistency"],
            "suggestions": ["Consider extracting interfaces", "Review dependency directions"],
        },
        AgentRole.ANALYST: {
            "stance": "support",
            "reasoning": "The data suggests this approach addresses the complexity metrics we identified. Measurements show clear improvement potential.",
            "confidence": 0.85,
            "concerns": ["Need baseline metrics"],
            "suggestions": ["Quantify improvement", "Measure before and after"],
        },
        AgentRole.CRITIC: {
            "stance": "oppose",
            "reasoning": "I see several risks with this approach that haven't been addressed. The edge cases around error handling could cause significant issues.",
            "confidence": 0.70,
            "concerns": ["Error handling gaps", "Edge case coverage", "Rollback strategy"],
            "suggestions": ["Add comprehensive error tests", "Consider failure modes"],
        },
        AgentRole.IMPLEMENTER: {
            "stance": "neutral",
            "reasoning": "This is feasible to implement, but will require careful refactoring to maintain backward compatibility. The effort is moderate.",
            "confidence": 0.80,
            "concerns": ["Implementation effort", "Breaking changes"],
            "suggestions": ["Incremental migration", "Feature flags"],
        },
        AgentRole.TESTER: {
            "stance": "support",
            "reasoning": "The test strategy is sound. We can verify behavior preservation through comprehensive test coverage.",
            "confidence": 0.85,
            "concerns": ["Test data setup", "Integration test coverage"],
            "suggestions": ["Add property-based tests", "Increase integration coverage"],
        },
        AgentRole.SCRIBE: {
            "stance": "neutral",
            "reasoning": "The concepts are mostly clear, but some naming could be improved for better understanding.",
            "confidence": 0.75,
            "concerns": ["Naming consistency", "Documentation gaps"],
            "suggestions": ["Clarify naming conventions", "Add usage examples"],
        },
        AgentRole.PHILOSOPHER: {
            "stance": "question",
            "reasoning": "Are we solving the fundamental problem, or treating symptoms? The abstraction level suggests we might be missing a deeper pattern.",
            "confidence": 0.65,
            "concerns": ["Problem framing", "Fundamental vs symptomatic"],
            "suggestions": ["Re-examine first principles", "Consider alternative problem definitions"],
        },
        AgentRole.SAFETY_KEEPER: {
            "stance": "neutral",
            "reasoning": "The risks appear manageable with proper safeguards. We need rollback plans and staged rollout.",
            "confidence": 0.80,
            "concerns": ["Blast radius", "Rollback complexity"],
            "suggestions": ["Staged rollout", "Monitoring alerts", "Rollback automation"],
        },
    }

    def __init__(self, agent_id: str, role: AgentRole, llm_backend=None):
        self.agent_id = agent_id
        self.role = role
        self.llm_backend = llm_backend

    @property
    def persona_prompt(self) -> str:
        return self.PROMPT_TEMPLATES.get(self.role, "Respond thoughtfully.")

    async def respond_to_question(
        self,
        question: SocraticQuestion,
        context: Dict[str, Any],
        previous_rounds: List[DialogueRound],
    ) -> AgentPerspective:
        context_str = self._build_context(context, previous_rounds)
        response = self._generate_placeholder_response(question, context_str)
        return AgentPerspective(
            agent_id=self.agent_id,
            role=self.role,
            stance=response["stance"],
            reasoning=response["reasoning"],
            confidence=response["confidence"],
            concerns=response.get("concerns", []),
            suggestions=response.get("suggestions", []),
        )

    def _build_context(self, context: Dict[str, Any], previous_rounds: List[DialogueRound]) -> str:
        lines = []
        if "target" in context:
            lines.append(f"Analyzing: {context['target']}")
        if previous_rounds:
            lines.append("\nPrevious discussion:")
            for rd in previous_rounds[-2:]:
                lines.append(f"Round {rd.round_number}: {rd.question.question}")
                lines.append(f"Consensus: {rd.consensus_level:.0%}")
        return "\n".join(lines)

    def _generate_placeholder_response(self, question: SocraticQuestion, context: str) -> Dict[str, Any]:
        return self.PLACEHOLDER_RESPONSES.get(self.role, {
            "stance": "neutral",
            "reasoning": "Considering the question from multiple perspectives...",
            "confidence": 0.70,
            "concerns": [],
            "suggestions": [],
        })


# =========================================================================
# PlaybookLibrary — embedded playbooks for each analysis type
# =========================================================================

class PlaybookLibrary:
    """Embedded library of Socratic playbooks (no external dependency)."""

    def __init__(self):
        self.playbooks: Dict[str, Dict[str, Any]] = {}
        self._initialize()

    def _initialize(self):
        self.playbooks["architecture_review"] = {
            "name": "Comprehensive Architecture Review",
            "required_roles": [
                AgentRole.ARCHITECT, AgentRole.CRITIC,
                AgentRole.PHILOSOPHER, AgentRole.ANALYST,
            ],
            "opening_questions": [
                SocraticQuestion("What is the fundamental purpose of this system?", AgentRole.PHILOSOPHER, [AgentRole.ARCHITECT, AgentRole.CRITIC]),
                SocraticQuestion("What are the boundaries between layers, and are they respected?", AgentRole.ARCHITECT, [AgentRole.CRITIC, AgentRole.ANALYST]),
                SocraticQuestion("If we needed to replace this component, what would break?", AgentRole.CRITIC, [AgentRole.ARCHITECT, AgentRole.IMPLEMENTER]),
            ],
            "probing_questions": [
                SocraticQuestion("Why was this abstraction chosen over alternatives?", AgentRole.PHILOSOPHER, [AgentRole.ARCHITECT]),
                SocraticQuestion("Where are the hidden dependencies that aren't explicit in imports?", AgentRole.CRITIC, [AgentRole.ANALYST, AgentRole.ARCHITECT]),
                SocraticQuestion("How would we scale this if usage increased 100x?", AgentRole.ANALYST, [AgentRole.ARCHITECT, AgentRole.CRITIC]),
                SocraticQuestion("Is this pattern solving a problem we actually have?", AgentRole.PHILOSOPHER, [AgentRole.ARCHITECT, AgentRole.CRITIC]),
                SocraticQuestion("Where are we violating our own architectural principles?", AgentRole.CRITIC, [AgentRole.ARCHITECT, AgentRole.PHILOSOPHER]),
            ],
            "synthesis_questions": [
                SocraticQuestion("What single change would most improve the architecture?", AgentRole.ARCHITECT, [AgentRole.ARCHITECT, AgentRole.CRITIC, AgentRole.PHILOSOPHER]),
                SocraticQuestion("Do we have consensus on the priority of these architectural debts?", AgentRole.SCRIBE, [AgentRole.ARCHITECT, AgentRole.CRITIC, AgentRole.ANALYST]),
            ],
            "max_rounds": 5,
            "convergence_threshold": 0.8,
        }
        self.playbooks["complexity_analysis"] = {
            "name": "Deep Complexity Analysis",
            "required_roles": [
                AgentRole.ANALYST, AgentRole.IMPLEMENTER,
                AgentRole.CRITIC, AgentRole.TESTER,
            ],
            "opening_questions": [
                SocraticQuestion("What makes this code complex - branches, state, or concepts?", AgentRole.ANALYST, [AgentRole.CRITIC, AgentRole.IMPLEMENTER]),
                SocraticQuestion("If we extracted this into a separate module, what would the interface be?", AgentRole.IMPLEMENTER, [AgentRole.ANALYST, AgentRole.CRITIC]),
            ],
            "probing_questions": [
                SocraticQuestion("Is this complexity inherent to the problem or accidental?", AgentRole.CRITIC, [AgentRole.ANALYST, AgentRole.PHILOSOPHER]),
                SocraticQuestion("How many mental variables must one track to understand this function?", AgentRole.ANALYST, [AgentRole.CRITIC, AgentRole.IMPLEMENTER]),
                SocraticQuestion("Can we replace conditional logic with polymorphism or table-driven design?", AgentRole.IMPLEMENTER, [AgentRole.ARCHITECT, AgentRole.CRITIC]),
                SocraticQuestion("What tests would give us confidence to refactor this?", AgentRole.TESTER, [AgentRole.IMPLEMENTER, AgentRole.CRITIC]),
            ],
            "synthesis_questions": [
                SocraticQuestion("Which refactoring gives the best complexity reduction for effort?", AgentRole.ANALYST, [AgentRole.IMPLEMENTER, AgentRole.CRITIC]),
                SocraticQuestion("Can we verify this refactor is behavior-preserving?", AgentRole.TESTER, [AgentRole.IMPLEMENTER, AgentRole.SAFETY_KEEPER]),
            ],
            "max_rounds": 4,
            "convergence_threshold": 0.85,
        }
        self.playbooks["test_coverage_gap"] = {
            "name": "Test Strategy and Coverage Analysis",
            "required_roles": [
                AgentRole.TESTER, AgentRole.CRITIC,
                AgentRole.ANALYST, AgentRole.SAFETY_KEEPER,
            ],
            "opening_questions": [
                SocraticQuestion("What behaviors are we testing, and what are we assuming?", AgentRole.TESTER, [AgentRole.CRITIC, AgentRole.ANALYST]),
                SocraticQuestion("What would cause this to fail in production that tests wouldn't catch?", AgentRole.CRITIC, [AgentRole.TESTER, AgentRole.SAFETY_KEEPER]),
            ],
            "probing_questions": [
                SocraticQuestion("Are we testing implementation or behavior?", AgentRole.CRITIC, [AgentRole.TESTER, AgentRole.PHILOSOPHER]),
                SocraticQuestion("What invariants should always hold that we never test?", AgentRole.ANALYST, [AgentRole.TESTER, AgentRole.CRITIC]),
                SocraticQuestion("How would we test this with generated/random inputs?", AgentRole.TESTER, [AgentRole.ANALYST, AgentRole.CRITIC]),
                SocraticQuestion("What happens at the boundaries of valid input?", AgentRole.CRITIC, [AgentRole.TESTER, AgentRole.SAFETY_KEEPER]),
            ],
            "synthesis_questions": [
                SocraticQuestion("What tests give us the most confidence per effort?", AgentRole.ANALYST, [AgentRole.TESTER, AgentRole.IMPLEMENTER]),
                SocraticQuestion("Do we have enough safety to refactor the implementation?", AgentRole.SAFETY_KEEPER, [AgentRole.TESTER, AgentRole.CRITIC]),
            ],
            "max_rounds": 4,
            "convergence_threshold": 0.85,
        }
        self.playbooks["semantic_coherence"] = {
            "name": "Semantic Coherence and Naming Analysis",
            "required_roles": [
                AgentRole.PHILOSOPHER, AgentRole.SCRIBE,
                AgentRole.CRITIC, AgentRole.ANALYST,
            ],
            "opening_questions": [
                SocraticQuestion("What domain concepts are we modeling, and do our names match?", AgentRole.PHILOSOPHER, [AgentRole.SCRIBE, AgentRole.ANALYST]),
                SocraticQuestion("If a new developer saw this name, what would they assume?", AgentRole.CRITIC, [AgentRole.SCRIBE, AgentRole.PHILOSOPHER]),
            ],
            "probing_questions": [
                SocraticQuestion("Where do we use the same word to mean different things?", AgentRole.PHILOSOPHER, [AgentRole.SCRIBE, AgentRole.ANALYST]),
                SocraticQuestion("What metaphors are we using, and do they hold?", AgentRole.PHILOSOPHER, [AgentRole.CRITIC, AgentRole.SCRIBE]),
                SocraticQuestion("Are our abstractions at consistent levels, or do we mix high and low?", AgentRole.CRITIC, [AgentRole.PHILOSOPHER, AgentRole.ARCHITECT]),
                SocraticQuestion("What concepts are missing names that we refer to awkwardly?", AgentRole.SCRIBE, [AgentRole.PHILOSOPHER, AgentRole.CRITIC]),
            ],
            "synthesis_questions": [
                SocraticQuestion("What naming convention would make this code self-describing?", AgentRole.SCRIBE, [AgentRole.PHILOSOPHER, AgentRole.CRITIC]),
                SocraticQuestion("Do we have consensus on the core metaphors this code uses?", AgentRole.PHILOSOPHER, [AgentRole.SCRIBE, AgentRole.ANALYST, AgentRole.CRITIC]),
            ],
            "max_rounds": 4,
            "convergence_threshold": 0.85,
        }
        self.playbooks["api_design_review"] = {
            "name": "Public API Design Review",
            "required_roles": [
                AgentRole.ARCHITECT, AgentRole.CRITIC,
                AgentRole.SCRIBE, AgentRole.ANALYST,
            ],
            "opening_questions": [
                SocraticQuestion("What is the core promise of this API?", AgentRole.ARCHITECT, [AgentRole.CRITIC, AgentRole.PHILOSOPHER]),
                SocraticQuestion("How would a new user discover how to use this correctly?", AgentRole.SCRIBE, [AgentRole.CRITIC, AgentRole.ANALYST]),
            ],
            "probing_questions": [
                SocraticQuestion("Where does this API surprise users with unexpected behavior?", AgentRole.CRITIC, [AgentRole.ARCHITECT, AgentRole.ANALYST]),
                SocraticQuestion("What errors do users make, and how does the API respond?", AgentRole.CRITIC, [AgentRole.ARCHITECT, AgentRole.SAFETY_KEEPER]),
                SocraticQuestion("Is this API consistent with others in the same system?", AgentRole.ARCHITECT, [AgentRole.CRITIC, AgentRole.ANALYST]),
                SocraticQuestion("What would we need to change to make this API v2?", AgentRole.ARCHITECT, [AgentRole.CRITIC, AgentRole.IMPLEMENTER]),
            ],
            "synthesis_questions": [
                SocraticQuestion("What API changes give the most usability improvement?", AgentRole.ARCHITECT, [AgentRole.CRITIC, AgentRole.ANALYST]),
                SocraticQuestion("Can we make these changes without breaking existing users?", AgentRole.SAFETY_KEEPER, [AgentRole.ARCHITECT, AgentRole.IMPLEMENTER]),
            ],
            "max_rounds": 5,
            "convergence_threshold": 0.85,
        }

    def get_playbook(self, analysis_type: str) -> Optional[Dict[str, Any]]:
        return self.playbooks.get(analysis_type)

    def list_playbooks(self) -> List[str]:
        return list(self.playbooks.keys())


# =========================================================================
# SocraticOrchestrator — multi-agent Socratic dialogue
# =========================================================================

class SocraticOrchestrator:
    """Orchestrates multi-agent Socratic dialogue with convergence detection.

    Manages the 3-phase flow (opening → probing → synthesis), collects
    responses, detects convergence, and builds consensus. Integrates with
    GeometricGovernance (audit), ExpertRegistry (tracking), and ExpertMemory
    (persistence).
    """

    def __init__(
        self,
        playbook_library: Optional[PlaybookLibrary] = None,
        governance: Optional[GeometricGovernance] = None,
        registry: Optional[ExpertRegistry] = None,
    ):
        self.playbook_library = playbook_library or PlaybookLibrary()
        self.governance = governance
        self.registry = registry
        self.agents: Dict[str, AgentPersona] = {}
        self.sessions: Dict[str, SocraticSession] = {}

    def create_agent(self, role: AgentRole, agent_id: Optional[str] = None) -> str:
        if agent_id is None:
            agent_id = f"{role.value}_{len(self.agents):03d}"
        self.agents[agent_id] = AgentPersona(agent_id, role)
        logger.info("Created agent %s with role %s", agent_id, role.value)
        return agent_id

    async def run_socratic_session(
        self,
        analysis_type: str,
        target: str,
        context: Dict[str, Any],
        max_rounds: Optional[int] = None,
    ) -> SocraticSession:
        playbook = self.playbook_library.get_playbook(analysis_type)
        if not playbook:
            raise ValueError(f"No playbook found for {analysis_type}")

        session_id = uuid.uuid4().hex[:8]
        session = SocraticSession(
            session_id=session_id,
            analysis_type=analysis_type,
            target=target,
        )
        self.sessions[session_id] = session

        self._audit_boundary("socratic_start", {
            "session_id": session_id,
            "analysis_type": analysis_type,
            "target": target,
            "playbook": playbook["name"],
        })

        logger.info("Starting Socratic session %s: %s", session_id, playbook["name"])
        logger.info("Required roles: %s", [r.value for r in playbook["required_roles"]])

        self._ensure_agents(playbook["required_roles"])
        pb_max = max_rounds or playbook["max_rounds"]
        threshold = playbook["convergence_threshold"]

        # Phase 1: Opening questions
        for question in playbook["opening_questions"]:
            round_data = await self._run_round(session, question, context)
            session.rounds.append(round_data)
            if self._check_convergence(round_data, threshold):
                session.status = "converged"
                break

        # Phase 2: Probing questions (if not converged)
        if session.status != "converged":
            for question in playbook["probing_questions"]:
                if len(session.rounds) >= pb_max:
                    session.status = "timeout"
                    break
                round_data = await self._run_round(session, question, context)
                session.rounds.append(round_data)
                if self._check_convergence(round_data, threshold):
                    session.status = "converged"
                    break

        # Phase 3: Synthesis questions
        if session.status in ("converged",) or len(session.rounds) > 2:
            for question in playbook["synthesis_questions"]:
                if len(session.rounds) >= pb_max:
                    break
                round_data = await self._run_round(session, question, context)
                session.rounds.append(round_data)

        session.ended_at = datetime.now().isoformat()
        if session.status == "running":
            session.status = "completed"

        session.final_consensus = self._synthesize_consensus(session)

        self._audit_boundary("socratic_end", {
            "session_id": session_id,
            "status": session.status,
            "rounds": len(session.rounds),
            "consensus": session.final_consensus.confidence if session.final_consensus else 0,
        })

        self._persist_to_registry(session)
        self._persist_to_memory(session)

        logger.info("Session %s completed: %s (%d rounds)", session_id, session.status, len(session.rounds))
        return session

    async def _run_round(
        self,
        session: SocraticSession,
        question: SocraticQuestion,
        context: Dict[str, Any],
    ) -> DialogueRound:
        round_num = len(session.rounds) + 1
        logger.debug("Round %d: %s...", round_num, question.question[:50])

        agents = self._get_agents_for_roles(question.target_roles) if question.target_roles else list(self.agents.values())

        responses = []
        for agent in agents:
            response = await agent.respond_to_question(question, context, session.rounds)
            responses.append(response)

        consensus_level = self._calculate_consensus(responses)
        insights = self._extract_insights(responses)
        disagreements = self._extract_disagreements(responses)

        round_data = DialogueRound(
            round_number=round_num,
            question=question,
            responses=responses,
            consensus_level=consensus_level,
            key_insights=insights,
            disagreements=disagreements,
        )

        self._audit_boundary("socratic_round", {
            "session_id": session.session_id,
            "round": round_num,
            "consensus": consensus_level,
            "responses": len(responses),
        })

        logger.debug("Round %d complete. Consensus: %.0f%%", round_num, consensus_level * 100)
        return round_data

    def _ensure_agents(self, required_roles: List[AgentRole]):
        existing = {a.role for a in self.agents.values()}
        for role in required_roles:
            if role not in existing:
                self.create_agent(role)
                existing.add(role)

    def _get_agents_for_roles(self, roles: List[AgentRole]) -> List[AgentPersona]:
        agents = []
        covered = set()
        for agent in self.agents.values():
            if agent.role in roles and agent.role not in covered:
                agents.append(agent)
                covered.add(agent.role)
        return agents

    def _check_convergence(self, round_data: DialogueRound, threshold: float) -> bool:
        return round_data.consensus_level >= threshold

    def _calculate_consensus(self, responses: List[AgentPerspective]) -> float:
        if not responses:
            return 0.0
        stances = [r.stance for r in responses]
        counts = {}
        for s in stances:
            counts[s] = counts.get(s, 0) + 1
        max_agreement = max(counts.values()) if counts else 0
        consensus = max_agreement / len(responses)
        avg_conf = sum(r.confidence for r in responses) / len(responses)
        return (consensus + avg_conf) / 2

    def _extract_insights(self, responses: List[AgentPerspective]) -> List[str]:
        insights = []
        for r in responses:
            insights.extend(r.suggestions)
        return insights[:5]

    def _extract_disagreements(self, responses: List[AgentPerspective]) -> List[str]:
        disagreements = []
        for r in responses:
            disagreements.extend(r.concerns)
        return disagreements[:5]

    def _synthesize_consensus(self, session: SocraticSession) -> Optional[AgentPerspective]:
        if not session.rounds:
            return None
        all_insights = []
        all_concerns = []
        avg = 0.0
        for rd in session.rounds:
            all_insights.extend(rd.key_insights)
            all_concerns.extend(rd.disagreements)
            avg += rd.consensus_level
        avg /= len(session.rounds)
        return AgentPerspective(
            agent_id="consensus",
            role=AgentRole.SCRIBE,
            stance="support" if avg > 0.7 else "neutral",
            reasoning=f"Synthesized from {len(session.rounds)} rounds of Socratic dialogue. Average consensus: {avg:.0%}",
            confidence=avg,
            concerns=list(set(all_concerns))[:5],
            suggestions=list(set(all_insights))[:5],
        )

    def get_session_report(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        return {
            "session_id": session.session_id,
            "analysis_type": session.analysis_type,
            "target": session.target,
            "status": session.status,
            "rounds_count": len(session.rounds),
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "final_consensus": {
                "stance": session.final_consensus.stance if session.final_consensus else None,
                "confidence": session.final_consensus.confidence if session.final_consensus else 0,
                "suggestions": session.final_consensus.suggestions if session.final_consensus else [],
            },
            "rounds_summary": [
                {
                    "round": r.round_number,
                    "question": r.question.question[:100],
                    "consensus": r.consensus_level,
                    "responses": len(r.responses),
                }
                for r in session.rounds
            ],
        }

    def _audit_boundary(self, boundary_type: str, data: Dict[str, Any]):
        if self.governance:
            try:
                self.governance.record_boundary_event(BoundaryEvent(
                    event_id=f"socratic_{boundary_type}_{uuid.uuid4().hex[:8]}",
                    timestamp=time.time(),
                    entropy_delta=0.1,
                    receipt_data=data,
                    boundary_type=f"socratic_{boundary_type}",
                ))
            except Exception as e:
                logger.warning("Governance audit failed: %s", e)

    def _persist_to_registry(self, session: SocraticSession):
        if not self.registry:
            return
        try:
            self.registry.connect()
            for rd in session.rounds:
                for resp in rd.responses:
                    expert_data = self.registry.get_expert(resp.agent_id)
                    if expert_data:
                        self.registry.update_performance(
                            resp.agent_id,
                            success=(resp.stance in ("support", "neutral")),
                            latency_ms=50.0,
                        )
            self.registry.close()
        except Exception as e:
            logger.warning("Registry persistence failed: %s", e)

    def _persist_to_memory(self, session: SocraticSession):
        for rd in session.rounds:
            for resp in rd.responses:
                try:
                    mem = ExpertMemory(resp.agent_id)
                    mem.connect()
                    mem.store_entry(
                        entry_type="socratic_response",
                        content={
                            "session_id": session.session_id,
                            "round": rd.round_number,
                            "question": rd.question.question,
                            "stance": resp.stance,
                            "reasoning": resp.reasoning,
                            "confidence": resp.confidence,
                            "consensus": rd.consensus_level,
                        },
                        relevance_score=resp.confidence,
                    )
                    mem.close()
                except Exception as e:
                    logger.warning("Memory persistence failed for %s: %s", resp.agent_id, e)


# =========================================================================
# Existing SocraticComposer — kept for backward compatibility
# =========================================================================

@dataclass
class SocraticRound:
    round_number: int
    expert_outputs: Dict[str, Dict[str, Any]]
    critiques: Dict[str, List[str]] = field(default_factory=dict)
    refinements: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    convergence_signature: str = ""
    convergence_score: float = 0.0
    timestamp: float = 0.0


class SocraticComposer:
    """Iterative socratic composition engine (legacy interface).

    Runs experts through critique → refine → converge cycles until
    the system reaches consensus or max rounds.
    """

    def __init__(self, governance: GeometricGovernance,
                 registry: ExpertRegistry,
                 service_fn: Callable = None):
        self.governance = governance
        self.registry = registry
        self.service_fn = service_fn
        self.rounds: List[SocraticRound] = []
        self.convergence_history: List[float] = []
        self.max_rounds = 7
        self.convergence_threshold = 0.92

    def compose(self, expert_ids: List[str], problem: str,
                context: Dict[str, Any] = None) -> Dict[str, Any]:
        ctx = context or {}
        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"socratic_start_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            entropy_delta=0.2,
            receipt_data={
                "experts": expert_ids,
                "problem": problem[:200],
            },
            boundary_type="socratic_start",
        ))

        round_0_outputs = self._dispatch_experts(expert_ids, problem, ctx, round_num=0)
        round_0 = SocraticRound(
            round_number=0,
            expert_outputs=round_0_outputs,
            timestamp=time.time(),
        )
        self.rounds.append(round_0)

        for round_num in range(1, self.max_rounds + 1):
            prev_round = self.rounds[-1]
            critiques = self._generate_critiques(expert_ids, prev_round.expert_outputs)
            refinements = self._generate_refinements(expert_ids, critiques, problem, ctx, round_num)
            new_outputs = self._dispatch_experts(expert_ids, problem, ctx, round_num, refinements)

            signature = self._compute_convergence_signature(new_outputs)
            score = self._compute_convergence_score(prev_round.expert_outputs, new_outputs)

            current_round = SocraticRound(
                round_number=round_num,
                expert_outputs=new_outputs,
                critiques=critiques,
                refinements=refinements,
                convergence_signature=signature,
                convergence_score=score,
                timestamp=time.time(),
            )
            self.rounds.append(current_round)
            self.convergence_history.append(score)

            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"socratic_round_{round_num}_{uuid.uuid4().hex[:8]}",
                timestamp=time.time(),
                entropy_delta=0.1,
                receipt_data={
                    "round": round_num,
                    "convergence_score": score,
                    "signature": signature,
                },
                boundary_type="socratic_round",
            ))

            logger.info("Socratic round %d/%d — convergence=%.4f",
                         round_num, self.max_rounds, score)

            if score >= self.convergence_threshold:
                logger.info("Socratic convergence reached at round %d (score=%.4f)",
                             round_num, score)
                break

        final_round = self.rounds[-1]
        result = {
            "rounds": len(self.rounds),
            "convergence_score": final_round.convergence_score,
            "convergence_history": self.convergence_history,
            "final_outputs": final_round.expert_outputs,
            "all_rounds": [
                {
                    "round": r.round_number,
                    "score": r.convergence_score,
                    "timestamp": r.timestamp,
                }
                for r in self.rounds
            ],
        }

        self.governance.record_boundary_event(BoundaryEvent(
            event_id=f"socratic_end_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            entropy_delta=0.1,
            receipt_data={
                "total_rounds": len(self.rounds),
                "final_convergence": final_round.convergence_score,
            },
            boundary_type="socratic_end",
        ))

        return result

    def _dispatch_experts(self, expert_ids: List[str], problem: str,
                          context: Dict[str, Any], round_num: int = 0,
                          refinements: Dict[str, Any] = None) -> Dict[str, Dict[str, Any]]:
        outputs = {}
        for expert_id in expert_ids:
            expert = self.registry.get_expert(expert_id)
            if not expert:
                outputs[expert_id] = {"error": f"Expert {expert_id} not found"}
                continue

            memory = ExpertMemory(expert_id)
            memory.connect()
            similar = memory.recall(problem, top_k=3)
            memory.close()

            if self.service_fn:
                try:
                    service_result = self.service_fn(expert_id, {
                        "problem": problem,
                        "context": context,
                        "round": round_num,
                        "refinements": refinements,
                        "similar_experiences": similar,
                    })
                    outputs[expert_id] = service_result
                except Exception as e:
                    outputs[expert_id] = {
                        "status": "simulated",
                        "expert_id": expert_id,
                        "domain": expert.get("domain", "unknown"),
                        "archetype": expert.get("archetype", "unknown"),
                        "round": round_num,
                        "similar_experiences": similar,
                    }
            else:
                outputs[expert_id] = {
                    "status": "simulated",
                    "expert_id": expert_id,
                    "domain": expert.get("domain", "unknown"),
                    "archetype": expert.get("archetype", "unknown"),
                    "capabilities": expert.get("capabilities", []),
                    "round": round_num,
                    "similar_experiences": similar,
                    "refinements_applied": refinements.get(expert_id) if refinements else None,
                }
        return outputs

    def _generate_critiques(self, expert_ids: List[str],
                            outputs: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        critiques: Dict[str, List[str]] = {}
        for expert_id in expert_ids:
            my_critiques = []
            for other_id in expert_ids:
                if other_id == expert_id:
                    continue
                other_output = outputs.get(other_id, {})
                my_critiques.append(
                    f"Cross-critique from {expert_id} on {other_id}: "
                    f"round={other_output.get('round', 0)}, "
                    f"status={other_output.get('status', 'unknown')}"
                )
            critiques[expert_id] = my_critiques
        return critiques

    def _generate_refinements(self, expert_ids: List[str],
                               critiques: Dict[str, List[str]],
                               problem: str, context: Dict[str, Any],
                               round_num: int) -> Dict[str, Dict[str, Any]]:
        refinements = {}
        for expert_id in expert_ids:
            refinements[expert_id] = {
                "received_critiques": critiques.get(expert_id, []),
                "round": round_num,
                "adjustment": "incorporate_cross_expert_feedback",
            }
        return refinements

    def _compute_convergence_signature(self,
                                        outputs: Dict[str, Dict[str, Any]]) -> str:
        serialized = json.dumps(outputs, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def _compute_convergence_score(self,
                                    prev: Dict[str, Dict[str, Any]],
                                    curr: Dict[str, Dict[str, Any]]) -> float:
        prev_str = json.dumps(prev, sort_keys=True, default=str)
        curr_str = json.dumps(curr, sort_keys=True, default=str)
        prev_vec = self._text_to_vector(prev_str)
        curr_vec = self._text_to_vector(curr_str)
        dot = float(np.dot(prev_vec, curr_vec))
        norm = float(np.linalg.norm(prev_vec) * np.linalg.norm(curr_vec))
        if norm < 1e-10:
            return 0.0
        return dot / norm

    def _text_to_vector(self, text: str) -> np.ndarray:
        words = text.lower().split()
        vec = np.zeros(128, dtype=np.float64)
        for i, word in enumerate(words[:128]):
            vec[i % 128] += hash(word) % 10000 / 10000.0
        norm = np.linalg.norm(vec)
        return vec / (norm + 1e-10)
