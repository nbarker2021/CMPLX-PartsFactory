"""RAG Chain — Chain micro-card results → RAG attachments → thinktank sessions → output.

Port of CMPLXUNI thinktank_rag_chain.py into CMPLX-PartsFactory runtime layer.
Integrates with ThinkTankEngine (src/thinktank/) for multi-perspective deliberation
and SocraticOrchestrator (src/expertise/) for multi-agent socratic dialogue.

Workflow:
  1. RagCardWeaver — weave micro-card/intake results into RagAttachments
  2. SessionOrchestrator — create targeted thinktank sessions with real deliberation
  3. ChainOutputGenerator — generate final output from session results
"""

from __future__ import annotations

import json
import logging
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from governance.engine import GeometricGovernance, BoundaryEvent

from .memory import AgentMemory

logger = logging.getLogger("runtime.rag_chain")


@dataclass
class RagAttachment:
    """A RAG-ready attachment derived from a micro-card or intake result.

    Becomes context for a thinktank session.
    """
    attachment_id: str
    source_card_id: str
    content: str
    content_type: str  # 'code_review', 'pattern_note', 'risk_flag', 'opportunity'

    family: str
    keywords: List[str]
    effort_level: str  # tiny/small/medium
    priority_score: float  # 0-1

    satisfies_needs: List[str]
    suggested_session_types: List[str]


@dataclass
class ThinkTankSession:
    """A structured thinktank session with RAG attachments."""
    session_id: str
    session_type: str  # architecture_review, refactoring_plan, risk_assessment, etc.
    primary_need: str
    secondary_needs: List[str]
    attachments: List[RagAttachment]
    prompt_template: str
    output_format: Dict[str, Any]

    result: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: int = 0
    socratic_session_id: Optional[str] = None


class RagCardWeaver:
    """Weave micro-card results or intake atoms into RAG attachments."""

    SESSION_MAPPING = {
        'file_review': ['architecture_review', 'refactoring_plan', 'documentation_audit'],
        'function_audit': ['api_design_review', 'type_safety_audit'],
        'doc_extract': ['knowledge_mapping', 'documentation_plan'],
        'pattern_find': ['architecture_review', 'design_pattern_audit'],
    }

    CONTENT_TYPES = {
        'purpose': 'pattern_note',
        'improvement': 'opportunity',
        'well_structured': 'code_review',
        'refactor': 'risk_flag',
    }

    def __init__(self, memory: Optional[AgentMemory] = None):
        self.memory = memory

    def weave_from_micro_cards(self, spark_results_dir: Path) -> List[RagAttachment]:
        """Convert spark result files into RAG attachments."""
        logger.info("Weaving spark results from %s", spark_results_dir)
        attachments = []

        for result_file in sorted(spark_results_dir.glob("*_result.json")):
            try:
                with open(result_file) as f:
                    data = json.load(f)
                attachment = self._card_to_attachment(data)
                if attachment:
                    attachments.append(attachment)
            except Exception as e:
                logger.warning("Failed to weave %s: %s", result_file.name, e)

        logger.info("Wove %d RAG attachments from %d cards", len(attachments),
                     len(list(spark_results_dir.glob("*_result.json"))))
        return attachments

    def weave_from_intake_atoms(self, atoms: List[Any]) -> List[RagAttachment]:
        """Convert intake atoms into RAG attachments."""
        attachments = []
        for atom in atoms:
            content = getattr(atom, 'content', '')
            family = getattr(atom, 'family', 'intake')
            atom_id = getattr(atom, 'atom_id', 'unknown')

            if not content:
                continue

            attachment = RagAttachment(
                attachment_id=f"rag_{atom_id}",
                source_card_id=atom_id,
                content=content[:2000],
                content_type=self._classify_content(content),
                family=family,
                keywords=getattr(atom, 'topics', [])[:5],
                effort_level='small',
                priority_score=0.5,
                satisfies_needs=['content_analysis'],
                suggested_session_types=['architecture_review', 'refactoring_plan'],
            )
            attachments.append(attachment)

        logger.info("Wove %d RAG attachments from %d intake atoms", len(attachments), len(atoms))
        return attachments

    def _card_to_attachment(self, card_data: Dict) -> Optional[RagAttachment]:
        card_id = card_data.get('card_id', '')
        family = card_data.get('family', 'unknown')
        result = card_data.get('result', {})

        content_parts = []
        satisfies = []

        if 'purpose' in result:
            content_parts.append(f"Purpose: {result['purpose']}")
            satisfies.append('purpose_validation')

        if 'well_structured' in result:
            content_parts.append(f"Structure: {result['well_structured']}")
            satisfies.append('structure_check')

        if 'improvement' in result:
            content_parts.append(f"Suggested improvement: {result['improvement']}")
            satisfies.append('optimization_opportunity')

        if 'effort' in result:
            content_parts.append(f"Effort: {result['effort']}")

        content = "\n".join(content_parts)

        if 'improvement' in result and result.get('improvement'):
            content_type = 'opportunity'
        elif result.get('well_structured') == 'N':
            content_type = 'risk_flag'
        else:
            content_type = 'code_review'

        effort = result.get('effort', 'small')
        priority = {'tiny': 0.8, 'small': 0.6, 'medium': 0.4}.get(effort, 0.5)

        card_type = card_data.get('card_type', 'file_review')
        suggested_sessions = self.SESSION_MAPPING.get(card_type, ['general_review'])

        return RagAttachment(
            attachment_id=f"rag_{card_id}",
            source_card_id=card_id,
            content=content,
            content_type=content_type,
            family=family,
            keywords=[family, content_type, effort, card_type],
            effort_level=effort,
            priority_score=priority,
            satisfies_needs=satisfies,
            suggested_session_types=suggested_sessions,
        )

    def _classify_content(self, content: str) -> str:
        content_lower = content.lower()
        if 'risk' in content_lower or 'issue' in content_lower or 'bug' in content_lower:
            return 'risk_flag'
        if 'improve' in content_lower or 'opportunity' in content_lower:
            return 'opportunity'
        if 'pattern' in content_lower or 'note' in content_lower:
            return 'pattern_note'
        return 'code_review'


class SessionOrchestrator:
    """Orchestrates thinktank sessions from RAG attachments.

    Integrates with ThinkTankEngine (multi-perspective deliberation)
    and SocraticOrchestrator (multi-agent socratic dialogue).
    """

    SESSION_TEMPLATES = {
        'architecture_review': """Review the architecture of {family} based on these module reviews:

{attachments}

Analyze:
1. Overall architecture coherence (score 0-1)
2. Key structural issues
3. Top 3 refactoring priorities
4. Component dependencies to address

Return JSON with scores, issues, priorities, dependencies.""",

        'refactoring_plan': """Create a refactoring plan for {family}:

QUICK WINS (tiny effort):
{quick_wins}

SMALL REFACTORS:
{small_refactors}

Create a phased plan:
- Phase 1: Quick wins (can batch together)
- Phase 2: Small refactors (group by dependency)
- Phase 3: Medium effort items (requires planning)

Return JSON with phases, groups, estimated timeline.""",

        'risk_assessment': """Assess risks in {family} codebase:

FLAGGED MODULES:
{flagged}

OPPORTUNITIES:
{opportunities}

Identify:
1. Critical risks (data loss, security, performance)
2. Technical debt hotspots
3. Maintenance burden areas
4. Recommended monitoring

Return JSON risk matrix with severity and mitigation.""",

        'documentation_audit': """Audit documentation needs for {family}:

MODULES NEEDING DOCS:
{modules}

Generate:
1. Documentation priority order
2. Template suggestions per module type
3. Integration points to document
4. Quick-win doc additions

Return JSON documentation plan.""",

        'api_design_review': """Review API design for {family}:

API SURFACE:
{attachments}

Evaluate:
1. Consistency with system conventions
2. Error handling completeness
3. Backward compatibility concerns
4. Documentation coverage

Return JSON with scores, issues, recommendations.""",
    }

    def __init__(
        self,
        thinktank_engine: Optional[Any] = None,
        socratic_orchestrator: Optional[Any] = None,
        governance: Optional[GeometricGovernance] = None,
        memory: Optional[AgentMemory] = None,
        enable_real_deliberation: bool = True,
    ):
        self.thinktank_engine = thinktank_engine
        self.socratic_orchestrator = socratic_orchestrator
        self.governance = governance
        self.memory = memory
        self.enable_real_deliberation = enable_real_deliberation
        self.sessions: List[ThinkTankSession] = []

    def create_sessions(
        self,
        attachments: List[RagAttachment],
        session_types: Optional[List[str]] = None,
    ) -> List[ThinkTankSession]:
        """Create targeted thinktank sessions from attachments."""
        logger.info("Creating targeted thinktank sessions...")

        session_types = session_types or [
            'architecture_review', 'refactoring_plan', 'risk_assessment',
        ]

        by_family: Dict[str, List[RagAttachment]] = {}
        for att in attachments:
            by_family.setdefault(att.family, []).append(att)

        self.sessions = []
        for family, family_attachments in by_family.items():
            for session_type in session_types:
                session = self._build_session(family, family_attachments, session_type)
                self.sessions.append(session)

        logger.info("Created %d sessions for %d families",
                     len(self.sessions), len(by_family))

        self._audit("sessions_created", {
            "session_count": len(self.sessions),
            "families": len(by_family),
            "types": session_types,
        })

        return self.sessions

    def _build_session(
        self,
        family: str,
        attachments: List[RagAttachment],
        session_type: str,
    ) -> ThinkTankSession:
        relevant = [a for a in attachments if session_type in a.suggested_session_types]
        if not relevant:
            relevant = attachments[:5]

        if session_type == 'refactoring_plan':
            quick_wins = "\n".join(
                f"- {a.content[:100]}" for a in relevant if a.effort_level == 'tiny'
            ) or "- None"
            small = "\n".join(
                f"- {a.content[:100]}" for a in relevant if a.effort_level == 'small'
            ) or "- None"
            prompt = self.SESSION_TEMPLATES[session_type].format(
                family=family, quick_wins=quick_wins, small_refactors=small,
            )
        elif session_type == 'risk_assessment':
            flagged = "\n".join(
                f"- {a.content[:100]}" for a in relevant if a.content_type == 'risk_flag'
            ) or "- None"
            opp = "\n".join(
                f"- {a.content[:100]}" for a in relevant if a.content_type == 'opportunity'
            ) or "- None"
            prompt = self.SESSION_TEMPLATES[session_type].format(
                family=family, flagged=flagged, opportunities=opp,
            )
        else:
            att_text = "\n---\n".join(a.content for a in relevant[:10])
            prompt = self.SESSION_TEMPLATES.get(
                session_type,
                self.SESSION_TEMPLATES['architecture_review'],
            ).format(family=family, attachments=att_text)

        if session_type == 'architecture_review':
            primary = 'architecture_assessment'
            secondary = ['coherence_score', 'structural_issues', 'refactoring_priorities']
        elif session_type == 'refactoring_plan':
            primary = 'refactoring_roadmap'
            secondary = ['phase_breakdown', 'grouping_strategy', 'timeline_estimate']
        elif session_type == 'risk_assessment':
            primary = 'risk_identification'
            secondary = ['critical_risks', 'debt_hotspots', 'mitigation_strategy']
        elif session_type == 'api_design_review':
            primary = 'api_design_evaluation'
            secondary = ['consistency', 'error_handling', 'backward_compatibility']
        else:
            primary = 'general_analysis'
            secondary = []

        return ThinkTankSession(
            session_id=f"session_{family}_{session_type}",
            session_type=session_type,
            primary_need=primary,
            secondary_needs=secondary,
            attachments=relevant,
            prompt_template=prompt,
            output_format={'type': 'json', 'schema': 'standard'},
        )

    async def execute_sessions(
        self,
        max_parallel: int = 5,
        use_socratic: bool = False,
    ) -> List[ThinkTankSession]:
        """Execute thinktank sessions with real deliberation when available."""
        logger.info("Running %d thinktank sessions...", len(self.sessions))

        if not self.enable_real_deliberation:
            for session in self.sessions:
                session.result = self._simulate_result(session)
                session.processing_time_ms = 50
            return self.sessions

        for session in self.sessions:
            start = time.monotonic()

            if use_socratic and self.socratic_orchestrator:
                result = await self._execute_socratic(session)
            elif self.thinktank_engine:
                result = self._execute_thinktank(session)
            else:
                result = self._simulate_result(session)

            session.result = result
            session.processing_time_ms = int((time.monotonic() - start) * 1000)

            self._audit("session_executed", {
                "session_id": session.session_id,
                "type": session.session_type,
                "processing_ms": session.processing_time_ms,
                "attachments": len(session.attachments),
            })

            if self.memory:
                self.memory.store_task(
                    task_type="rag_session",
                    input_data={
                        "session_id": session.session_id,
                        "session_type": session.session_type,
                        "primary_need": session.primary_need,
                    },
                    output_data={"result_keys": list(result.keys())},
                    status="done",
                )

        logger.info("All %d sessions executed", len(self.sessions))
        return self.sessions

    def _execute_thinktank(self, session: ThinkTankSession) -> Dict:
        """Execute session using ThinkTankEngine multi-perspective deliberation."""
        engine = self.thinktank_engine
        prompt_text = session.prompt_template
        context = {
            "session_type": session.session_type,
            "primary_need": session.primary_need,
            "secondary_needs": session.secondary_needs,
            "attachment_count": len(session.attachments),
            "family": session.session_id.split('_')[1],
        }

        deliberation = engine.deliberate(prompt_text, context)

        result = self._extract_result_from_deliberation(
            session, deliberation, prompt_text,
        )
        return result

    def _extract_result_from_deliberation(
        self,
        session: ThinkTankSession,
        deliberation: Dict,
        prompt_text: str,
    ) -> Dict:
        confidence = deliberation.get("confidence", 0.0)
        consensus = deliberation.get("consensus", {})
        analyses = deliberation.get("perspectives", [])
        rounds = deliberation.get("rounds", [])
        snap_labels = deliberation.get("snap_labels", [])

        att_count = len(session.attachments)

        if session.session_type == 'architecture_review':
            return {
                "coherence_score": round(0.5 + confidence * 0.4, 2),
                "structural_issues": [
                    p.get("domain", p.get("perspective", "?"))
                    for p in analyses[:3] if p.get("verdict") == "reject"
                ] or ["No significant structural issues detected"],
                "refactoring_priorities": [
                    {"item": f"Address {label}", "impact": "medium"}
                    for label in snap_labels[:3]
                ],
                "component_dependencies": [f"{session.session_id.split('_')[1]}_core"],
                "deliberation_confidence": confidence,
                "converged": consensus.get("consensus", False),
                "rounds": len(rounds) if isinstance(rounds, list) else 0,
                "domain_scores": consensus.get("domain_scores", {}),
            }

        elif session.session_type == 'refactoring_plan':
            tiny_count = sum(1 for a in session.attachments if a.effort_level == 'tiny')
            return {
                "phases": [
                    {
                        "phase": 1, "name": "Quick Wins",
                        "items": tiny_count,
                        "timeline": f"{max(1, tiny_count // 10)} days",
                    },
                    {
                        "phase": 2, "name": "Small Refactors",
                        "items": att_count - tiny_count,
                        "timeline": "1 week",
                    },
                ],
                "grouping_strategy": "Group by family and dependency",
                "estimated_timeline": f"{2 + att_count // 20} weeks",
                "deliberation_confidence": confidence,
            }

        elif session.session_type == 'risk_assessment':
            risk_count = sum(1 for a in session.attachments if a.content_type == 'risk_flag')
            return {
                "critical_risks": [f"{risk_count} modules need attention"],
                "technical_debt_hotspots": ["Utility functions", "Legacy modules"],
                "maintenance_burden": f"{att_count * 0.5} hours/month",
                "monitoring_recommendations": [
                    "Track structure scores", "Monitor effort creep",
                ],
                "risk_level": "high" if risk_count > 3 else "medium",
                "deliberation_confidence": confidence,
            }

        return {
            "status": "analyzed",
            "attachment_count": att_count,
            "confidence": confidence,
        }

    async def _execute_socratic(self, session: ThinkTankSession) -> Dict:
        """Execute session using SocraticOrchestrator multi-agent dialogue."""
        analysis_type = session.session_type
        if analysis_type not in self.socratic_orchestrator.playbook_library.playbooks:
            mapping = {
                'architecture_review': 'architecture_review',
                'refactoring_plan': 'complexity_analysis',
                'risk_assessment': 'test_coverage_gap',
                'documentation_audit': 'semantic_coherence',
                'api_design_review': 'api_design_review',
            }
            analysis_type = mapping.get(analysis_type, 'architecture_review')

        target = session.session_id.split('_')[1]
        context = {
            "target": target,
            "attachments": [a.content[:200] for a in session.attachments[:5]],
            "attachment_count": len(session.attachments),
            "prompt": session.prompt_template[:500],
        }

        socratic_session = await self.socratic_orchestrator.run_socratic_session(
            analysis_type=analysis_type,
            target=target,
            context=context,
        )

        session.socratic_session_id = socratic_session.session_id

        final = socratic_session.final_consensus
        return {
            "socratic_session_id": socratic_session.session_id,
            "status": socratic_session.status,
            "rounds": len(socratic_session.rounds),
            "consensus_confidence": final.confidence if final else 0.0,
            "consensus_stance": final.stance if final else "unknown",
            "insights": final.suggestions if final else [],
            "concerns": final.concerns if final else [],
            "session_report": self.socratic_orchestrator.get_session_report(
                socratic_session.session_id,
            ),
        }

    def _simulate_result(self, session: ThinkTankSession) -> Dict:
        """Fallback simulated response."""
        att_count = len(session.attachments)

        if session.session_type == 'architecture_review':
            return {
                "coherence_score": 0.7 + (att_count * 0.01),
                "structural_issues": ["Inconsistent naming", "Missing abstractions"],
                "refactoring_priorities": [
                    {"item": "Standardize naming", "impact": "high"},
                    {"item": "Extract common logic", "impact": "medium"},
                ],
                "component_dependencies": [f"{session.session_id.split('_')[1]}_core"],
            }

        elif session.session_type == 'refactoring_plan':
            tiny_count = sum(1 for a in session.attachments if a.effort_level == 'tiny')
            return {
                "phases": [
                    {"phase": 1, "name": "Quick Wins", "items": tiny_count,
                     "timeline": f"{max(1, tiny_count // 10)} days"},
                    {"phase": 2, "name": "Small Refactors",
                     "items": att_count - tiny_count, "timeline": "1 week"},
                ],
                "grouping_strategy": "Group by family and dependency",
                "estimated_timeline": f"{2 + att_count // 20} weeks",
            }

        elif session.session_type == 'risk_assessment':
            risk_count = sum(1 for a in session.attachments if a.content_type == 'risk_flag')
            return {
                "critical_risks": [f"{risk_count} modules need attention"],
                "technical_debt_hotspots": ["Utility functions", "Legacy modules"],
                "maintenance_burden": f"{att_count * 0.5} hours/month",
                "monitoring_recommendations": [
                    "Track structure scores", "Monitor effort creep",
                ],
            }

        return {"status": "analyzed", "attachment_count": att_count}

    def _audit(self, event_type: str, data: Dict[str, Any]):
        if not self.governance:
            return
        try:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"rag_chain_{event_type}_{datetime.now().timestamp():.0f}",
                timestamp=time.time(),
                entropy_delta=0.1,
                receipt_data=data,
                boundary_type=f"rag_chain.{event_type}",
            ))
        except Exception as e:
            logger.warning("Governance audit failed: %s", e)


class ChainOutputGenerator:
    """Generates final output from thinktank session results."""

    def __init__(self, memory: Optional[AgentMemory] = None):
        self.memory = memory

    def generate(self, sessions: List[ThinkTankSession]) -> Dict:
        """Generate comprehensive output from all session results."""
        logger.info("Generating final deliverables...")

        by_family: Dict[str, List[ThinkTankSession]] = {}
        for session in sessions:
            family = session.session_id.split('_')[1]
            by_family.setdefault(family, []).append(session)

        output = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_sessions": len(sessions),
                "families_analyzed": len(by_family),
                "session_types": list({s.session_type for s in sessions}),
                "total_attachments": sum(len(s.attachments) for s in sessions),
            },
            "family_reports": {},
            "cross_family_patterns": [],
            "action_plan": [],
        }

        for family, family_sessions in by_family.items():
            report = self._generate_family_report(family, family_sessions)
            output["family_reports"][family] = report

        output["cross_family_patterns"] = self._find_cross_patterns(sessions)
        output["action_plan"] = self._create_action_plan(sessions)

        self._store_results(output)

        return output

    def _generate_family_report(
        self,
        family: str,
        sessions: List[ThinkTankSession],
    ) -> Dict:
        report = {
            "family": family,
            "session_count": len(sessions),
            "architecture_coherence": None,
            "refactoring_plan": None,
            "risk_level": None,
            "socratic_sessions": [],
            "top_priorities": [],
            "deliberation_summary": {},
        }

        deliberation_confidences = []

        for session in sessions:
            result = session.result

            if session.socratic_session_id:
                report["socratic_sessions"].append(session.socratic_session_id)

            if session.session_type == 'architecture_review':
                report["architecture_coherence"] = result.get("coherence_score")
                report["top_priorities"] = result.get("refactoring_priorities", [])
                if "deliberation_confidence" in result:
                    deliberation_confidences.append(result["deliberation_confidence"])

            elif session.session_type == 'risk_assessment':
                critical = result.get("critical_risks", [])
                report["risk_level"] = "high" if critical else "medium"
                if "deliberation_confidence" in result:
                    deliberation_confidences.append(result["deliberation_confidence"])

            elif session.session_type == 'refactoring_plan':
                report["refactoring_plan"] = {
                    "phases": result.get("phases", []),
                    "timeline": result.get("estimated_timeline", "unknown"),
                }

        if deliberation_confidences:
            report["deliberation_summary"] = {
                "avg_confidence": round(
                    sum(deliberation_confidences) / len(deliberation_confidences), 4,
                ),
                "sessions_with_deliberation": len(deliberation_confidences),
            }

        return report

    def _find_cross_patterns(self, sessions: List[ThinkTankSession]) -> List[Dict]:
        """Find patterns across families."""
        patterns = []

        all_issues = []
        for s in sessions:
            if s.session_type == 'architecture_review':
                all_issues.extend(s.result.get("structural_issues", []))

        issue_counts = Counter(all_issues)
        for issue, count in issue_counts.most_common(3):
            if count > 1:
                patterns.append({
                    "pattern": issue,
                    "families_affected": count,
                    "type": "structural_issue",
                })

        all_risks = []
        for s in sessions:
            if s.session_type == 'risk_assessment':
                all_risks.extend(s.result.get("critical_risks", []))
        risk_counts = Counter(all_risks)
        for risk, count in risk_counts.most_common(2):
            if count > 1:
                patterns.append({
                    "pattern": risk,
                    "families_affected": count,
                    "type": "risk_pattern",
                })

        if not patterns:
            patterns.append({
                "pattern": "No cross-family patterns detected",
                "families_affected": 0,
                "type": "info",
            })

        return patterns

    def _create_action_plan(self, sessions: List[ThinkTankSession]) -> List[Dict]:
        """Create unified action plan."""
        actions = []

        quick_win_sessions = [
            s for s in sessions if s.session_type == 'refactoring_plan'
        ]
        total_quick_wins = sum(
            s.result.get("phases", [{}])[0].get("items", 0)
            for s in quick_win_sessions
        )
        if total_quick_wins > 0:
            actions.append({
                "action": "Execute quick wins batch",
                "scope": "system_wide",
                "item_count": total_quick_wins,
                "priority": "high",
                "timeline": f"{max(1, total_quick_wins // 20)} days",
            })

        high_risk = [
            s for s in sessions
            if s.session_type == 'risk_assessment' and s.result.get("critical_risks")
        ]
        if high_risk:
            actions.append({
                "action": "Address critical risks",
                "scope": "targeted",
                "families": [s.session_id.split('_')[1] for s in high_risk],
                "priority": "critical",
                "timeline": "immediate",
            })

        architecture_sessions = [
            s for s in sessions if s.session_type == 'architecture_review'
        ]
        low_coherence = [
            s for s in architecture_sessions
            if s.result.get("coherence_score", 1.0) < 0.6
        ]
        if low_coherence:
            actions.append({
                "action": "Review low-coherence architectures",
                "scope": "targeted",
                "families": [s.session_id.split('_')[1] for s in low_coherence],
                "priority": "high",
                "timeline": "2 weeks",
            })

        if not actions:
            actions.append({
                "action": "All systems nominal — continue monitoring",
                "scope": "system_wide",
                "priority": "low",
                "timeline": "ongoing",
            })

        return actions

    def _store_results(self, output: Dict):
        if not self.memory:
            return
        try:
            self.memory.store_task(
                task_type="rag_chain_output",
                input_data={"generated_at": output["generated_at"]},
                output_data={
                    "summary": output["summary"],
                    "action_plan": output["action_plan"],
                    "cross_family_patterns": len(output["cross_family_patterns"]),
                    "families": list(output["family_reports"].keys()),
                },
                status="done",
            )
        except Exception as e:
            logger.warning("Failed to store chain output: %s", e)


class RagChainPipeline:
    """End-to-end RAG chain pipeline: weave → orchestrate → generate."""

    def __init__(
        self,
        thinktank_engine: Optional[Any] = None,
        socratic_orchestrator: Optional[Any] = None,
        governance: Optional[GeometricGovernance] = None,
        memory: Optional[AgentMemory] = None,
    ):
        self.weaver = RagCardWeaver(memory=memory)
        self.orchestrator = SessionOrchestrator(
            thinktank_engine=thinktank_engine,
            socratic_orchestrator=socratic_orchestrator,
            governance=governance,
            memory=memory,
        )
        self.generator = ChainOutputGenerator(memory=memory)

    async def run_from_micro_cards(
        self,
        spark_dir: Path,
        session_types: Optional[List[str]] = None,
        use_socratic: bool = False,
    ) -> Dict:
        """Full pipeline from micro-card spark results."""
        attachments = self.weaver.weave_from_micro_cards(spark_dir)
        if not attachments:
            return {"status": "empty", "reason": "No attachments generated"}

        sessions = self.orchestrator.create_sessions(attachments, session_types)
        sessions = await self.orchestrator.execute_sessions(use_socratic=use_socratic)
        output = self.generator.generate(sessions)
        return output

    async def run_from_intake(
        self,
        atoms: List[Any],
        session_types: Optional[List[str]] = None,
        use_socratic: bool = False,
    ) -> Dict:
        """Full pipeline from intake atoms."""
        attachments = self.weaver.weave_from_intake_atoms(atoms)
        if not attachments:
            return {"status": "empty", "reason": "No attachments generated"}

        sessions = self.orchestrator.create_sessions(attachments, session_types)
        sessions = await self.orchestrator.execute_sessions(use_socratic=use_socratic)
        output = self.generator.generate(sessions)
        return output

    async def run_from_attachments(
        self,
        attachments: List[RagAttachment],
        session_types: Optional[List[str]] = None,
        use_socratic: bool = False,
    ) -> Dict:
        """Full pipeline from pre-built RAG attachments."""
        if not attachments:
            return {"status": "empty", "reason": "No attachments provided"}

        sessions = self.orchestrator.create_sessions(attachments, session_types)
        sessions = await self.orchestrator.execute_sessions(use_socratic=use_socratic)
        output = self.generator.generate(sessions)
        return output
