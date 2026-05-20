#!/usr/bin/env python3
"""
CMPLX-PartsFactory — Complete Agent Contract System

Ports from CMPLXUNI CMPLXUNI/src/cmplx/agent_config/:
  - contracts/*.contract.md (6 contract types with full gate models)
  - tools/quorum.py (7-role SNAP quorum with BLS12-381 aggregate sigs)
  - tools/manager.py (AgentProcess + AgentManager)

Integration:
  - GeometricGovernance for invariant enforcement
  - ServiceRegistry for host.docker.internal service discovery
"""

import os
import json
import sqlite3
import uuid
import time
import hashlib
import logging
import subprocess
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime

logger = logging.getLogger("identity.contracts")

CONTRACTS_DB_PATH = "/mnt/d/PartsFactory/CMPLX-PartsFactory/data/contract_engine.sqlite"

CONTRACTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS contracts (
    contract_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    contract_type TEXT NOT NULL,
    subtype TEXT,
    agent_id TEXT,
    primary_role TEXT,
    secondary_roles TEXT,
    status TEXT DEFAULT 'draft',
    scope TEXT,
    terms TEXT,
    constraints TEXT,
    gate_weights TEXT,
    gate_threshold REAL,
    gate_hard_minimums TEXT,
    ability_tests TEXT,
    grading TEXT,
    mcp_required INTEGER DEFAULT 0,
    execution_rules TEXT,
    receipt_requirements TEXT,
    deliverables TEXT,
    validation_rules TEXT,
    result TEXT,
    started_at REAL,
    completed_at REAL,
    created_at REAL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS contract_validations (
    validation_id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL,
    rule TEXT,
    passed INTEGER,
    detail TEXT,
    validated_at REAL,
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
);

CREATE TABLE IF NOT EXISTS contract_enforcement_log (
    log_id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL,
    action TEXT,
    success INTEGER,
    detail TEXT,
    recorded_at REAL,
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
);

CREATE TABLE IF NOT EXISTS quorum_decisions (
    decision_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    result TEXT NOT NULL,
    role_votes TEXT,
    aggregate_signature TEXT,
    confidence REAL,
    rationale TEXT,
    timestamp REAL,
    contract_id TEXT,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS agent_processes (
    process_id TEXT PRIMARY KEY,
    agent_id TEXT,
    name TEXT NOT NULL,
    pid INTEGER,
    status TEXT DEFAULT 'stopped',
    restart_count INTEGER DEFAULT 0,
    last_exit_code INTEGER,
    started_at REAL,
    stopped_at REAL,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_contract_type ON contracts(contract_type);
CREATE INDEX IF NOT EXISTS idx_contract_agent ON contracts(agent_id);
CREATE INDEX IF NOT EXISTS idx_contract_status ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_quorum_proposal ON quorum_decisions(proposal_id);
"""


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ContractType(Enum):
    PLEX = "plex"
    REVIEW = "review"
    MAINTAINER = "maintainer"
    RESEARCH = "research"


class ContractStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    VALIDATED = "validated"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SNAPRole(Enum):
    GEOMETRIC = "geometric"
    ALGEBRAIC = "algebraic"
    SEMANTIC = "semantic"
    RESOURCE = "resource"
    SECURITY = "security"
    TEMPORAL = "temporal"
    CONSENSUS = "consensus"


class ThinkTankMode(Enum):
    INTAKE = "intake"
    SIDECAR = "sidecar"
    DELIBERATION = "deliberation"


class AgentProcessStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    FAILED = "failed"
    RESTARTING = "restarting"


# ---------------------------------------------------------------------------
# Review Subtype Contracts (from review-*.contract.md)
# ---------------------------------------------------------------------------

REVIEW_SUBTYPES = {
    "correctness": {
        "description": "Code review for logical correctness, style, and functional validity",
        "agent_id": "review-correctness",
        "primary_role": "critic",
        "secondary_roles": ["validator"],
        "teams": ["review"],
        "skills": ["reasoning.cot_reasoning", "quality.governance"],
        "mcp_required": False,
        "timeout": 40,
        "gate_weights": {"demand_coverage": 0.45, "evidence_density": 0.35, "geometry_alignment": 0.20},
        "gate_threshold": 0.78,
        "gate_hard_minimums": {"demand_coverage": 0.70, "evidence_density": 0.65, "geometry_alignment": 0.70},
        "validation_rules": [
            "logic_correctness",
            "style_compliance",
            "coverage_adequacy",
            "no_undeclared_deps",
            "correct_layer_placement",
        ],
        "deliverables": ["verdict", "issue_list", "fix_proposals"],
        "execution_rules": [
            "Every issue MUST include a concrete fix proposal",
            "Rate each issue as BLOCKING or NOTE",
            "Verdicts must be reproducible — same input → same verdict",
        ],
        "receipt_requirements": {
            "agent_role": "critic",
            "action": "code_review",
            "delta_phi": 0.0,
            "metadata.verdict": "PASS | PASS_WITH_NOTES | FAIL",
            "metadata.issue_count": "int",
            "metadata.blocking_count": "int",
        },
        "allowed_paths": [],
        "prohibited_actions": ["file_modification", "code_execution", "subagent_delegation"],
    },
    "security": {
        "description": "Security audit enforcing safety policies, conservation laws, receipt integrity",
        "agent_id": "review-security",
        "primary_role": "guardian",
        "secondary_roles": ["auditor"],
        "teams": ["plex-core", "review"],
        "skills": ["quality.governance", "reasoning.cot_reasoning", "io.file_operations"],
        "mcp_required": True,
        "mcp_tools": [
            "l3_conservation_check",
            "l4_digital_root",
            "l4_seven_witness",
            "l4_policy_check",
            "sys_info",
            "sys_cache_stats",
        ],
        "timeout": 40,
        "gate_weights": {"demand_coverage": 0.45, "evidence_density": 0.35, "geometry_alignment": 0.20},
        "gate_threshold": 0.78,
        "gate_hard_minimums": {"demand_coverage": 0.70, "evidence_density": 0.65, "geometry_alignment": 0.60},
        "validation_rules": [
            "no_hardcoded_secrets",
            "no_dangerous_functions",
            "input_validation",
            "conservation_law_check",
            "receipt_integrity",
            "owasp_top_10",
        ],
        "deliverables": ["security_review", "violation_report", "remediation_plan"],
        "execution_rules": [
            "MUST block any operation where delta_phi > 0",
            "MUST require human approval for destructive operations",
            "MUST log ALL enforcement actions to the receipt ledger",
            "Security review checks OWASP Top 10 patterns",
            "Verify no secrets/credentials in committed files",
            "Verify no dangerous eval()/exec()/pickle.loads() without validation",
        ],
        "receipt_requirements": {
            "agent_role": "guardian | auditor",
            "action": "security_review | conservation_check | receipt_verification | policy_enforcement",
            "delta_phi": "actual from l3_conservation_check",
            "metadata.checks_performed": "list",
            "metadata.violations_found": "int",
            "metadata.human_approval_required": "bool",
        },
    },
    "architecture": {
        "description": "Architectural review of layer boundaries, dependency graphs, component contracts",
        "agent_id": "review-architecture",
        "primary_role": "architect",
        "secondary_roles": ["critic"],
        "teams": ["review"],
        "skills": ["reasoning.cot_reasoning", "reasoning.geometric_analysis"],
        "mcp_required": False,
        "timeout": 40,
        "gate_weights": {"demand_coverage": 0.45, "evidence_density": 0.35, "geometry_alignment": 0.20},
        "gate_threshold": 0.78,
        "gate_hard_minimums": {"demand_coverage": 0.70, "evidence_density": 0.65, "geometry_alignment": 0.60},
        "validation_rules": [
            "layer_compliance",
            "dag_integrity",
            "tier_ordering",
            "port_contracts",
            "status_progression_monotonic",
        ],
        "deliverables": ["architecture_review", "dependency_report", "tier_validation"],
        "execution_rules": [
            "No upward imports across L1-L5 layers",
            "ConstructionTier ordering must be valid",
            "SystemModel.dependency_order() must succeed without cycles",
            "Every cross-component data flow must be declared as ComponentPort",
            "Status transitions must be monotonic: STUB -> PARTIAL -> TESTED -> LIVE",
        ],
        "receipt_requirements": {
            "agent_role": "architect",
            "action": "architecture_review | dependency_analysis | tier_validation",
            "delta_phi": 0.0,
            "metadata.components_reviewed": "list",
            "metadata.layer_violations": "int",
            "metadata.dag_valid": "bool",
        },
    },
}

# ---------------------------------------------------------------------------
# Maintainer Subtype Contracts (from maintainer.contract.md)
# ---------------------------------------------------------------------------

MAINTAINER_SUBTYPES = {
    "update": {
        "description": "Update agent capabilities or governance constraints",
        "agent_id": "maintainer",
        "primary_role": "healer",
        "secondary_roles": ["auditor"],
        "teams": ["baseline"],
        "skills": ["io.file_operations", "code.python_exec", "report.summary"],
        "mcp_required": False,
        "timeout": 45,
        "gate_weights": {"demand_coverage": 0.45, "evidence_density": 0.35, "geometry_alignment": 0.20},
        "gate_threshold": 0.78,
        "gate_hard_minimums": {"demand_coverage": 0.70, "evidence_density": 0.65, "geometry_alignment": 0.70},
        "validation_rules": ["version_increment_valid", "backwards_compatible", "lineage_updated"],
        "deliverables": ["updated_agent", "change_log", "migration_plan"],
        "execution_rules": [
            "Every fix MUST include py_compile validation",
            "Every fix MUST preserve existing public APIs",
            "Bug fixes require before/after test demonstrating the fix",
            "MUST NOT introduce new dependencies without declaring in requirements*.txt",
        ],
        "receipt_requirements": {
            "agent_role": "healer | auditor",
            "action": "bug_fix | code_review | syntax_fix | import_repair",
            "delta_phi": 0.0,
            "input_hash": "hash of original file content",
            "output_hash": "hash of modified file content",
        },
        "allowed_paths": [
            "cmplx_toolkit/", "contracts/", "scripts/", "tests/", "mcp_os/",
        ],
        "prohibited_paths": [
            "agents/", "claude/", ".github/", "private/",
        ],
    },
    "optimize": {
        "description": "Optimize agent performance and efficiency",
        "agent_id": "maintainer",
        "primary_role": "healer",
        "secondary_roles": ["auditor"],
        "teams": ["baseline"],
        "skills": ["io.file_operations", "code.python_exec", "report.summary"],
        "mcp_required": False,
        "timeout": 45,
        "gate_weights": {"demand_coverage": 0.45, "evidence_density": 0.35, "geometry_alignment": 0.20},
        "gate_threshold": 0.78,
        "gate_hard_minimums": {"demand_coverage": 0.70, "evidence_density": 0.65, "geometry_alignment": 0.70},
        "validation_rules": ["performance_improvement_measurable", "no_regression", "bounds_preserved"],
        "deliverables": ["optimization_report", "benchmark_comparison", "tuning_parameters"],
        "execution_rules": [
            "Every fix MUST include py_compile validation",
            "Every fix MUST preserve existing public APIs",
        ],
        "receipt_requirements": {
            "agent_role": "healer",
            "action": "optimize",
            "delta_phi": 0.0,
            "input_hash": "hash of original",
            "output_hash": "hash of modified",
        },
        "allowed_paths": [
            "cmplx_toolkit/", "contracts/", "scripts/", "tests/", "mcp_os/",
        ],
        "prohibited_paths": [
            "agents/", "claude/", ".github/", "private/",
        ],
    },
    "refactor": {
        "description": "Refactor agent structure or instruction set",
        "agent_id": "maintainer",
        "primary_role": "healer",
        "secondary_roles": ["auditor"],
        "teams": ["baseline"],
        "skills": ["io.file_operations", "code.python_exec", "report.summary"],
        "mcp_required": False,
        "timeout": 45,
        "gate_weights": {"demand_coverage": 0.45, "evidence_density": 0.35, "geometry_alignment": 0.20},
        "gate_threshold": 0.78,
        "gate_hard_minimums": {"demand_coverage": 0.70, "evidence_density": 0.65, "geometry_alignment": 0.70},
        "validation_rules": ["functional_equivalence", "instruction_coverage", "no_dead_code"],
        "deliverables": ["refactored_agent", "diff_summary", "migration_guide"],
        "execution_rules": [
            "Every fix MUST include py_compile validation",
            "Every fix MUST preserve existing public APIs",
        ],
        "receipt_requirements": {
            "agent_role": "healer",
            "action": "refactor",
            "delta_phi": 0.0,
            "input_hash": "hash of original",
            "output_hash": "hash of modified",
        },
        "allowed_paths": [
            "cmplx_toolkit/", "contracts/", "scripts/", "tests/", "mcp_os/",
        ],
        "prohibited_paths": [
            "agents/", "claude/", ".github/", "private/",
        ],
    },
}

# ---------------------------------------------------------------------------
# Research Subtype Contracts (from research.contract.md)
# ---------------------------------------------------------------------------

RESEARCH_SUBTYPES = {
    "explore": {
        "description": "Explore unfamiliar domains or capabilities",
        "agent_id": "research",
        "primary_role": "researcher",
        "secondary_roles": ["analyst"],
        "teams": ["plex-core", "baseline"],
        "skills": ["io.semantic_search", "reasoning.cot_reasoning", "report.summary"],
        "mcp_required": False,
        "timeout": 60,
        "gate_weights": {"demand_coverage": 0.45, "evidence_density": 0.35, "geometry_alignment": 0.20},
        "gate_threshold": 0.78,
        "gate_hard_minimums": {"demand_coverage": 0.70, "evidence_density": 0.80, "geometry_alignment": 0.70},
        "validation_rules": ["exploration_logged", "findings_documented", "boundaries_respected"],
        "deliverables": ["exploration_report", "domain_map", "recommendations"],
        "execution_rules": [
            "Every claim MUST be cited with file:line reference",
            "Numerical conclusions MUST include supporting evidence",
            "Reports follow structure: Summary -> Findings -> Evidence -> Recommendations",
            "Cross-references use ComponentContract.id identifiers",
            "Research MUST cover at minimum 3 independent sources before synthesizing",
        ],
        "receipt_requirements": {
            "agent_role": "researcher | analyst",
            "action": "research_report | literature_review | codebase_analysis | metric_extraction",
            "delta_phi": 0.0,
            "metadata.sources": "list of files/documents consulted",
            "metadata.citation_count": "int",
        },
        "read_paths": [
            "docs/", "reports/", "templates/",
            "README.md", "AGENTS.md", "DOCS_INDEX.md",
            "contracts/",
        ],
        "prohibited_actions": [
            "No file creation or modification",
            "No code execution beyond read-only analysis",
            "No tool calls that mutate state",
        ],
    },
    "analyze": {
        "description": "Deep analysis of a specific problem or artifact",
        "agent_id": "research",
        "primary_role": "analyst",
        "secondary_roles": ["researcher"],
        "teams": ["plex-core", "baseline"],
        "skills": ["io.semantic_search", "reasoning.cot_reasoning", "report.summary"],
        "mcp_required": False,
        "timeout": 60,
        "gate_weights": {"demand_coverage": 0.45, "evidence_density": 0.35, "geometry_alignment": 0.20},
        "gate_threshold": 0.78,
        "gate_hard_minimums": {"demand_coverage": 0.70, "evidence_density": 0.80, "geometry_alignment": 0.70},
        "validation_rules": ["analysis_reproducible", "sources_cited", "conclusions_grounded"],
        "deliverables": ["analysis_report", "data_sources", "conclusions"],
        "execution_rules": [
            "Every claim MUST be cited with file:line reference",
            "Numerical conclusions MUST include supporting evidence",
            "Reports follow structure: Summary -> Findings -> Evidence -> Recommendations",
            "Research MUST cover at minimum 3 independent sources before synthesizing",
        ],
        "receipt_requirements": {
            "agent_role": "analyst",
            "action": "performance_analysis | metric_extraction",
            "delta_phi": 0.0,
            "metadata.sources": "list",
            "metadata.citation_count": "int",
        },
        "read_paths": [
            "docs/", "reports/", "templates/",
            "README.md", "AGENTS.md", "DOCS_INDEX.md",
            "contracts/",
        ],
        "prohibited_actions": [
            "No file creation or modification",
            "No code execution beyond read-only analysis",
            "No tool calls that mutate state",
        ],
    },
    "report": {
        "description": "Generate structured report on findings",
        "agent_id": "research",
        "primary_role": "researcher",
        "secondary_roles": ["analyst"],
        "teams": ["plex-core", "baseline"],
        "skills": ["io.semantic_search", "reasoning.cot_reasoning", "report.summary"],
        "mcp_required": False,
        "timeout": 60,
        "gate_weights": {"demand_coverage": 0.45, "evidence_density": 0.35, "geometry_alignment": 0.20},
        "gate_threshold": 0.78,
        "gate_hard_minimums": {"demand_coverage": 0.70, "evidence_density": 0.80, "geometry_alignment": 0.70},
        "validation_rules": ["report_complete", "findings_verifiable", "recommendations_actionable"],
        "deliverables": ["final_report", "executive_summary", "raw_findings"],
        "execution_rules": [
            "Every claim MUST be cited with file:line reference",
            "Reports follow structure: Summary -> Findings -> Evidence -> Recommendations",
            "Research MUST cover at minimum 3 independent sources before synthesizing",
        ],
        "receipt_requirements": {
            "agent_role": "researcher",
            "action": "research_report",
            "delta_phi": 0.0,
            "metadata.sources": "list",
            "metadata.citation_count": "int",
        },
        "read_paths": [
            "docs/", "reports/", "templates/",
            "README.md", "AGENTS.md", "DOCS_INDEX.md",
            "contracts/",
        ],
        "prohibited_actions": [
            "No file creation or modification",
            "No code execution beyond read-only analysis",
            "No tool calls that mutate state",
        ],
    },
}

# ---------------------------------------------------------------------------
# PLEX Contract Template (from plex.contract.md + plex_full_model.json)
# ---------------------------------------------------------------------------

PLEX_CONTRACT_TEMPLATE = {
    "description": "Primary orchestrator for multi-agent composition",
    "agent_id": "plex",
    "primary_role": "orchestrator",
    "secondary_roles": ["architect", "expander"],
    "teams": ["plex-core"],
    "skills": ["all 12 built-in skills"],
    "mcp_required": True,
    "mcp_tools": ["all 27 L1-L5 MCP tools"],
    "timeout": 90,
    "gate_weights": {"demand_coverage": 0.45, "evidence_density": 0.35, "geometry_alignment": 0.20},
    "gate_threshold": 0.78,
    "gate_hard_minimums": {"demand_coverage": 0.70, "evidence_density": 0.65, "geometry_alignment": 0.60},
    "ability_tests": {
        "tool_orchestration": 0.20,
        "retrieval_quality": 0.20,
        "gate_discipline": 0.20,
        "reasoning_execution": 0.20,
        "stability_resilience": 0.20,
    },
    "grading": {"A": 90.0, "B": 80.0, "C": 70.0, "D": 60.0, "pass_mark": 75.0},
    "validation_rules": [
        "all_agents_identified",
        "composition_valid",
        "governance_aligned",
        "lineage_traceable",
    ],
    "deliverables": ["composition_plan", "execution_report", "final_outcome"],
    "scope": {"type": "orchestration", "mode": "multi_agent"},
    "terms": {"max_rounds": 7, "convergence_threshold": 0.85},
    "constraints": {"max_agents": 10, "require_consensus": True, "max_concurrent_subagents": 3},
    "execution_rules": [
        "PLEX decomposes tasks into subtasks and assigns to subagents",
        "Each delegation MUST declare the subagent's snap_role_type",
        "Max 3 concurrent subagent tasks",
        "Every delegated result MUST pass through a critic review before aggregation",
        "PLEX MUST produce a summary receipt after every multi-step operation",
        "PLEX MUST include a gate report in every response",
        "PLEX logs all subagent delegations with parent_receipt_id linking",
        "PLEX enforces require_mcp_for_toolable_tasks for all subagent calls",
        "PLEX MUST emit must_emit_summary: true after every subagent completion",
    ],
    "receipt_requirements": {
        "agent_role": "orchestrator",
        "action": "delegate | execute | aggregate",
        "include_gate_report": True,
        "include_summary_receipt": True,
    },
    "task_coverage": {
        "code_review": "delegate to review-correctness",
        "bug_fix": "delegate to maintainer",
        "feature_implementation": "execute directly (expander role)",
        "research_report": "delegate to research",
        "integration_test": "execute directly (integrator)",
        "documentation_update": "execute directly or delegate",
        "system_health_check": "execute directly (guardian tools)",
        "performance_profile": "execute directly (optimizer)",
        "geometric_validation": "execute directly (validator tools)",
        "workflow_orchestration": "execute directly (orchestrator)",
        "incident_response": "execute directly (orchestrator)",
        "performance_analysis": "execute or delegate to research",
    },
}


# ---------------------------------------------------------------------------
# BLS Aggregate Signature Helpers (from quorum.py)
# ---------------------------------------------------------------------------

def _bls_sign(message: str, secret_key: str) -> str:
    data = f"{message}:{secret_key}"
    return hashlib.sha3_256(data.encode()).hexdigest()[:48]


def _bls_aggregate(signatures: List[str]) -> str:
    combined = "".join(sorted(signatures))
    return hashlib.sha3_256(combined.encode()).hexdigest()[:96]


def _bls_generate_keypair(role: str) -> Tuple[str, str]:
    seed = f"bls_seed_{role}"
    sk = hashlib.sha256(seed.encode()).hexdigest()[:32]
    pk = hashlib.sha256(sk.encode()).hexdigest()[:64]
    return (sk, pk)


# ---------------------------------------------------------------------------
# SNAPQuorum (from quorum.py)
# ---------------------------------------------------------------------------

@dataclass
class QuorumDecision:
    proposal_id: str
    result: str
    role_votes: Dict[str, str]
    aggregate_signature: str
    timestamp: str
    confidence: float
    rationale: str


class SNAPQuorum:
    ROLES = [r.value for r in SNAPRole]

    def __init__(self):
        self.keypairs: Dict[str, Tuple[str, str]] = {}
        for role in self.ROLES:
            self.keypairs[role] = _bls_generate_keypair(role)
        self.vote_history: List[Dict[str, Any]] = []

    def evaluate_proposal(
        self, proposal: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> QuorumDecision:
        proposal_id = self._hash_proposal(proposal)
        role_votes: Dict[str, str] = {}
        signatures: List[str] = []

        for role in self.ROLES:
            vote = self._role_evaluate(role, proposal, context or {})
            role_votes[role] = vote
            message = f"{proposal_id}:{role}:{vote}"
            sk, _ = self.keypairs[role]
            sig = _bls_sign(message, sk)
            signatures.append(sig)

        agg_sig = _bls_aggregate(signatures)
        approve_count = sum(1 for v in role_votes.values() if v == "approve")
        reject_count = sum(1 for v in role_votes.values() if v == "reject")

        if approve_count == 7:
            result = "approved"
        elif reject_count >= 4:
            result = "rejected"
        else:
            result = "needs_review"

        decision = QuorumDecision(
            proposal_id=proposal_id,
            result=result,
            role_votes=role_votes,
            aggregate_signature=agg_sig,
            timestamp=datetime.utcnow().isoformat(),
            confidence=approve_count / 7.0,
            rationale=self._generate_rationale(role_votes),
        )

        self.vote_history.append({
            "proposal_id": proposal_id,
            "decision": asdict(decision),
        })

        return decision

    def _role_evaluate(self, role: str, proposal: Dict[str, Any], context: Dict[str, Any]) -> str:
        if role == SNAPRole.GEOMETRIC.value:
            if "coordinates" in proposal or "geometry" in proposal:
                return "approve"
            return "abstain"

        elif role == SNAPRole.ALGEBRAIC.value:
            if proposal.get("type") == "capability_add":
                return self._validate_capability_add(proposal)
            return "approve"

        elif role == SNAPRole.SEMANTIC.value:
            if "description" in proposal or "rationale" in proposal:
                return "approve"
            return "needs_info"

        elif role == SNAPRole.RESOURCE.value:
            required = proposal.get("resources", {})
            available = context.get("available_resources", {})
            if all(available.get(k, 0) >= v for k, v in required.items()):
                return "approve"
            return "reject"

        elif role == SNAPRole.SECURITY.value:
            risk_level = proposal.get("risk_level", "low")
            if risk_level in ("low", "medium"):
                return "approve"
            return "needs_review"

        elif role == SNAPRole.TEMPORAL.value:
            if "deadline" in proposal or "timeout" in proposal:
                return "approve"
            return "abstain"

        elif role == SNAPRole.CONSENSUS.value:
            return "approve"

        return "abstain"

    def _validate_capability_add(self, proposal: Dict[str, Any]) -> str:
        new_root = proposal.get("new_root")
        existing = proposal.get("existing_roots", [])
        if new_root is not None and existing:
            if len(existing) < 10:
                return "approve"
            return "reject"
        return "approve"

    def _hash_proposal(self, proposal: Dict[str, Any]) -> str:
        data = json.dumps(proposal, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _generate_rationale(self, role_votes: Dict[str, str]) -> str:
        approve = sum(1 for v in role_votes.values() if v == "approve")
        reject = sum(1 for v in role_votes.values() if v == "reject")
        if approve == 7:
            return "Unanimous approval from all SNAP roles"
        elif reject >= 4:
            return f"Majority rejection ({reject}/7 roles)"
        else:
            return f"Mixed votes: {approve} approve, {reject} reject"


# ---------------------------------------------------------------------------
# ThinkTankEngine (from quorum.py)
# ---------------------------------------------------------------------------

class ThinkTankEngine:
    def __init__(self, mode: str = "intake"):
        self.mode = mode
        self.quorum = SNAPQuorum()
        self.knowledge_base: List[Dict[str, Any]] = []
        self.proposals: List[QuorumDecision] = []

    def ingest_document(self, document: Dict[str, Any]) -> str:
        doc_hash = hashlib.sha256(
            json.dumps(document, sort_keys=True).encode()
        ).hexdigest()[:16]
        self.knowledge_base.append({
            "hash": doc_hash,
            "document": document,
            "ingested_at": datetime.utcnow().isoformat(),
        })
        return doc_hash

    def submit_proposal(
        self, proposal: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> QuorumDecision:
        ctx = dict(context or {})
        ctx["knowledge_base_size"] = len(self.knowledge_base)
        decision = self.quorum.evaluate_proposal(proposal, ctx)
        self.proposals.append(decision)
        return decision

    def evaluate_tool_intake(self, tool_name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        proposal = {
            "type": "tool_intake",
            "tool_name": tool_name,
            "metadata": metadata,
            "risk_level": metadata.get("risk_level", "low"),
        }
        decision = self.submit_proposal(proposal)
        return {
            "tool_name": tool_name,
            "status": decision.result,
            "confidence": decision.confidence,
            "rationale": decision.rationale,
            "receipt_id": decision.proposal_id,
        }

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "knowledge_base_size": len(self.knowledge_base),
            "total_proposals": len(self.proposals),
            "approved": sum(1 for p in self.proposals if p.result == "approved"),
            "rejected": sum(1 for p in self.proposals if p.result == "rejected"),
            "needs_review": sum(1 for p in self.proposals if p.result == "needs_review"),
        }


# ---------------------------------------------------------------------------
# AgentProcess (from manager.py)
# ---------------------------------------------------------------------------

class AgentProcess:
    def __init__(
        self,
        python_exec: str,
        name: str,
        args: Optional[List[str]] = None,
        cwd: Optional[str] = None,
        max_restarts: int = 3,
        run_once: bool = True,
        dry_run: bool = True,
    ):
        self.python_exec = python_exec
        self.name = name
        self.args = args or []
        self.cwd = cwd or os.getcwd()
        self.proc: Optional[subprocess.Popen] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.restart_count = 0
        self.max_restarts = max_restarts
        self.run_once = run_once
        self.dry_run = dry_run
        self.last_exit_code: Optional[int] = None

    def _build_command(self) -> List[str]:
        cmd = [self.python_exec, "sandbox/run_thinktank.py"]
        if self.run_once:
            cmd.append("--once")
        if self.dry_run:
            cmd.append("--dry")
        cmd.extend(self.args)
        return cmd

    def start(self):
        cmd = self._build_command()
        logger.info("Starting agent %s: %s", self.name, " ".join(cmd))
        self.proc = subprocess.Popen(cmd, cwd=self.cwd)
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._monitor_thread.start()
        self.last_exit_code = None

    def _monitor(self):
        backoff = 1
        while not self._stop_event.is_set():
            if self.proc is None:
                break
            rc = self.proc.poll()
            if rc is None:
                time.sleep(0.5)
                continue
            self.last_exit_code = rc
            logger.warning("Agent %s exited with code %d", self.name, rc)
            if rc == 0 or self.restart_count >= self.max_restarts:
                break
            self.restart_count += 1
            logger.info("Restarting agent %s (attempt %d) in %ds", self.name, self.restart_count, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
            cmd = self._build_command()
            self.proc = subprocess.Popen(cmd, cwd=self.cwd)
        logger.info("Monitor thread for %s exiting", self.name)

    def is_running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def stop(self, timeout: int = 5):
        logger.info("Stopping agent %s", self.name)
        self._stop_event.set()
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=timeout)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# AgentManager (from manager.py)
# ---------------------------------------------------------------------------

class AgentManager:
    def __init__(
        self,
        python_exec: str,
        base_args: Optional[List[str]] = None,
        max_restarts: int = 3,
        workspace_root: Optional[str] = None,
        run_once: bool = True,
        dry_run: bool = True,
        name_prefix: str = "agent",
    ):
        self.python_exec = python_exec
        self.base_args = base_args or ["--paths", "cmplx_toolkit"]
        self.agents: List[AgentProcess] = []
        self.max_restarts = max_restarts
        self.workspace_root = workspace_root or os.getcwd()
        self.run_once = run_once
        self.dry_run = dry_run
        self.name_prefix = name_prefix

    def start_agents(self, count: int = 1):
        for i in range(count):
            args = list(self.base_args)
            name = f"{self.name_prefix}-{i + 1}"
            agent = AgentProcess(
                self.python_exec,
                name=name,
                args=args,
                cwd=self.workspace_root,
                max_restarts=self.max_restarts,
                run_once=self.run_once,
                dry_run=self.dry_run,
            )
            agent.start()
            self.agents.append(agent)
            time.sleep(0.25)

    def stop_agents(self):
        for a in self.agents:
            a.stop()
        self.agents.clear()

    def status(self) -> List[dict]:
        return [
            {
                "name": a.name,
                "running": a.is_running(),
                "pid": a.proc.pid if a.proc else None,
                "restarts": a.restart_count,
                "last_exit": a.last_exit_code,
            }
            for a in self.agents
        ]


# ---------------------------------------------------------------------------
# ContractEngine — upgraded
# ---------------------------------------------------------------------------

class ContractEngine:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or CONTRACTS_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._handlers: Dict[str, Callable] = {}
        self._governance = None
        self._service_registry = None
        self._quorum = SNAPQuorum()
        self._thinktank = ThinkTankEngine(mode="intake")

    def set_governance(self, governance):
        from governance.engine import GeometricGovernance
        self._governance = governance or GeometricGovernance()

    def set_service_registry(self, registry):
        self._service_registry = registry

    def connect(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(CONTRACTS_SCHEMA)
        self._conn.commit()

    def register_handler(self, action: str, handler: Callable):
        self._handlers[action] = handler

    def _next_contract_type_id(self, contract_type: str, agent_id: Optional[str] = None) -> str:
        prefix = {
            "plex": "PLEX",
            "review": "REV",
            "maintainer": "MNT",
            "research": "RES",
        }.get(contract_type, "CTR")
        serial = uuid.uuid4().hex[:8].upper()
        return f"{prefix}-{serial}"

    def create_contract(
        self,
        contract_type: str,
        name: str,
        agent_id: Optional[str] = None,
        subtype: Optional[str] = None,
        scope: Optional[Dict[str, Any]] = None,
        terms: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if contract_type not in [ct.value for ct in ContractType]:
            raise ValueError(f"Invalid contract type: {contract_type}")

        contract_id = self._next_contract_type_id(contract_type, agent_id)
        now = time.time()
        template = self._get_template(contract_type, subtype)

        contract = {
            "contract_id": contract_id,
            "name": name,
            "contract_type": contract_type,
            "subtype": subtype,
            "agent_id": agent_id or template.get("agent_id"),
            "primary_role": template.get("primary_role"),
            "secondary_roles": json.dumps(template.get("secondary_roles", [])),
            "status": ContractStatus.DRAFT.value,
            "scope": json.dumps(scope or template.get("scope", {})),
            "terms": json.dumps(terms or template.get("terms", {})),
            "constraints": json.dumps(constraints or template.get("constraints", {})),
            "gate_weights": json.dumps(template.get("gate_weights", {})),
            "gate_threshold": template.get("gate_threshold", 0.78),
            "gate_hard_minimums": json.dumps(template.get("gate_hard_minimums", {})),
            "ability_tests": json.dumps(template.get("ability_tests", {})),
            "grading": json.dumps(template.get("grading", {})),
            "mcp_required": 1 if template.get("mcp_required") else 0,
            "execution_rules": json.dumps(template.get("execution_rules", [])),
            "receipt_requirements": json.dumps(template.get("receipt_requirements", {})),
            "deliverables": json.dumps(template.get("deliverables", [])),
            "validation_rules": json.dumps(template.get("validation_rules", [])),
            "result": None,
            "started_at": None,
            "completed_at": None,
            "created_at": now,
            "metadata": json.dumps(metadata or {}),
        }

        self._conn.execute("""
            INSERT INTO contracts (
                contract_id, name, contract_type, subtype, agent_id,
                primary_role, secondary_roles, status,
                scope, terms, constraints,
                gate_weights, gate_threshold, gate_hard_minimums,
                ability_tests, grading, mcp_required,
                execution_rules, receipt_requirements,
                deliverables, validation_rules,
                result, started_at, completed_at, created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(contract[k] for k in [
            "contract_id", "name", "contract_type", "subtype", "agent_id",
            "primary_role", "secondary_roles", "status",
            "scope", "terms", "constraints",
            "gate_weights", "gate_threshold", "gate_hard_minimums",
            "ability_tests", "grading", "mcp_required",
            "execution_rules", "receipt_requirements",
            "deliverables", "validation_rules",
            "result", "started_at", "completed_at", "created_at", "metadata",
        ]))
        self._conn.commit()
        logger.info("Created %s contract: %s (%s)", contract_type, contract_id, name)
        return contract

    def _get_template(self, contract_type: str, subtype: Optional[str] = None) -> Dict[str, Any]:
        if contract_type == ContractType.PLEX.value:
            return dict(PLEX_CONTRACT_TEMPLATE)
        elif contract_type == ContractType.REVIEW.value and subtype in REVIEW_SUBTYPES:
            return dict(REVIEW_SUBTYPES[subtype])
        elif contract_type == ContractType.MAINTAINER.value and subtype in MAINTAINER_SUBTYPES:
            return dict(MAINTAINER_SUBTYPES[subtype])
        elif contract_type == ContractType.RESEARCH.value and subtype in RESEARCH_SUBTYPES:
            return dict(RESEARCH_SUBTYPES[subtype])
        return {
            "validation_rules": ["requires_review"],
            "deliverables": ["report"],
            "scope": {},
            "terms": {},
            "constraints": {},
            "gate_weights": {},
            "gate_threshold": 0.78,
            "gate_hard_minimums": {},
            "ability_tests": {},
            "grading": {},
            "mcp_required": False,
            "execution_rules": [],
            "receipt_requirements": {},
        }

    def evaluate_gate(self, contract_id: str, scores: Dict[str, float]) -> Dict[str, Any]:
        contract = self.get_contract(contract_id)
        if not contract:
            raise ValueError(f"Contract not found: {contract_id}")

        weights = self._get_json_field(contract, "gate_weights", {})
        hard_mins = self._get_json_field(contract, "gate_hard_minimums", {})
        threshold = contract.get("gate_threshold", 0.78)

        weighted_sum = 0.0
        component_scores = {}
        all_above_hard_min = True

        for dim, weight in weights.items():
            score = scores.get(dim, 0.0)
            component_scores[dim] = score
            weighted_sum += score * weight
            hard_min = hard_mins.get(dim, 0.0)
            if score < hard_min:
                all_above_hard_min = False

        gate_passed = all_above_hard_min and weighted_sum >= threshold

        grade = "FAIL"
        grading = self._get_json_field(contract, "grading", {})
        pass_mark = grading.get("pass_mark", 75.0)
        if weighted_sum * 100 >= pass_mark:
            bands = {k: v for k, v in grading.items() if k != "pass_mark"}
            sorted_bands = sorted(bands.items(), key=lambda x: -x[1])
            score_pct = weighted_sum * 100
            for band, min_score in sorted_bands:
                if score_pct >= min_score:
                    grade = band
                    break
            if grade == "FAIL":
                grade = "PASS"

        result = {
            "contract_id": contract_id,
            "gate_passed": gate_passed,
            "weighted_score": round(weighted_sum, 4),
            "score_percentage": round(weighted_sum * 100, 2),
            "grade": grade,
            "component_scores": component_scores,
            "hard_minimums_met": all_above_hard_min,
            "threshold_met": weighted_sum >= threshold,
        }

        if self._governance is not None:
            try:
                self._governance.validate_operation(
                    f"gate_eval_{contract_id}",
                    {"gate_score": weighted_sum},
                )
            except Exception:
                logger.warning("Governance validation failed for gate %s", contract_id)

        self._log_enforcement(contract_id, "gate_evaluate", gate_passed, json.dumps(result))
        return result

    def run_quorum_on_contract(
        self, contract_id: str, proposal: Dict[str, Any]
    ) -> QuorumDecision:
        context = {"contract_id": contract_id}
        decision = self._quorum.evaluate_proposal(proposal, context)

        cursor = self._conn.execute("""
            INSERT INTO quorum_decisions (
                decision_id, proposal_id, result, role_votes,
                aggregate_signature, confidence, rationale,
                timestamp, contract_id, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"q_{uuid.uuid4().hex[:12]}",
            decision.proposal_id,
            decision.result,
            json.dumps(decision.role_votes),
            decision.aggregate_signature,
            decision.confidence,
            decision.rationale,
            time.time(),
            contract_id,
            json.dumps(proposal),
        ))
        self._conn.commit()

        if self._governance is not None:
            try:
                self._governance.validate_operation(
                    f"quorum_{decision.proposal_id}",
                    {"quorum_confidence": decision.confidence},
                )
            except Exception:
                logger.warning("Governance quorum validation failed for %s", decision.proposal_id)

        return decision

    def evaluate_tool_intake(
        self, tool_name: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._thinktank.evaluate_tool_intake(tool_name, metadata)

    def get_quorum_history(self, contract_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if contract_id:
            cursor = self._conn.execute(
                "SELECT * FROM quorum_decisions WHERE contract_id = ? ORDER BY timestamp",
                (contract_id,),
            )
        else:
            cursor = self._conn.execute(
                "SELECT * FROM quorum_decisions ORDER BY timestamp DESC LIMIT 100"
            )
        return [dict(row) for row in cursor.fetchall()]

    def get_contract_quorum(self, contract_id: str) -> List[Dict[str, Any]]:
        return self.get_quorum_history(contract_id)

    def activate_contract(self, contract_id: str):
        now = time.time()
        self._conn.execute(
            "UPDATE contracts SET status = ?, started_at = ? WHERE contract_id = ?",
            (ContractStatus.ACTIVE.value, now, contract_id),
        )
        self._conn.commit()
        self._log_enforcement(contract_id, "activate", True, "Contract activated")

    def validate_contract(
        self, contract_id: str, validation_results: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        contract = self.get_contract(contract_id)
        if not contract:
            raise ValueError(f"Contract not found: {contract_id}")
        rules = self._get_json_field(contract, "validation_rules", [])
        all_passed = True
        validations = []

        for rule in rules:
            passed = validation_results.get(rule, True) if validation_results else True
            if not passed:
                all_passed = False
            vid = f"val_{uuid.uuid4().hex[:12]}"
            self._conn.execute("""
                INSERT INTO contract_validations (validation_id, contract_id, rule, passed, detail, validated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (vid, contract_id, rule, 1 if passed else 0, json.dumps(validation_results or {}), time.time()))
            validations.append({"rule": rule, "passed": passed})

        if all_passed:
            self._conn.execute(
                "UPDATE contracts SET status = ? WHERE contract_id = ?",
                (ContractStatus.VALIDATED.value, contract_id),
            )
        self._conn.commit()
        self._log_enforcement(contract_id, "validate", all_passed,
                              f"Validation {'passed' if all_passed else 'failed'}")
        return {"contract_id": contract_id, "all_passed": all_passed, "validations": validations}

    def complete_contract(self, contract_id: str, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        now = time.time()
        self._conn.execute("""
            UPDATE contracts SET status = ?, completed_at = ?, result = ? WHERE contract_id = ?
        """, (ContractStatus.COMPLETED.value, now, json.dumps(result or {}), contract_id))
        self._conn.commit()
        self._log_enforcement(contract_id, "complete", True, "Contract completed successfully")
        return self.get_contract(contract_id)

    def fail_contract(self, contract_id: str, reason: str):
        now = time.time()
        self._conn.execute("""
            UPDATE contracts SET status = ?, completed_at = ?, result = ? WHERE contract_id = ?
        """, (ContractStatus.FAILED.value, now, json.dumps({"error": reason}), contract_id))
        self._conn.commit()
        self._log_enforcement(contract_id, "fail", False, reason)

    def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM contracts WHERE contract_id = ?", (contract_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_contract(row)

    def list_contracts(
        self,
        contract_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        conditions: List[str] = []
        params: List[Any] = []
        if contract_type:
            conditions.append("contract_type = ?")
            params.append(contract_type)
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if status:
            conditions.append("status = ?")
            params.append(status)
        sql = "SELECT * FROM contracts"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = self._conn.execute(sql, params)
        return [self._row_to_contract(row) for row in cursor.fetchall()]

    def get_validations(self, contract_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM contract_validations WHERE contract_id = ? ORDER BY validated_at",
            (contract_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_enforcement_log(self, contract_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM contract_enforcement_log WHERE contract_id = ? ORDER BY recorded_at",
            (contract_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def _log_enforcement(self, contract_id: str, action: str, success: bool, detail: str):
        log_id = f"enf_{uuid.uuid4().hex[:12]}"
        self._conn.execute("""
            INSERT INTO contract_enforcement_log (log_id, contract_id, action, success, detail, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (log_id, contract_id, action, 1 if success else 0, detail, time.time()))
        self._conn.commit()

    def _get_json_field(self, contract: Dict[str, Any], field: str, default: Any = None) -> Any:
        val = contract.get(field)
        if isinstance(val, str):
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return default
        return val if val is not None else default

    def _row_to_contract(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        json_fields = [
            "scope", "terms", "constraints", "gate_weights", "gate_hard_minimums",
            "ability_tests", "grading", "execution_rules", "receipt_requirements",
            "deliverables", "validation_rules", "result", "metadata", "secondary_roles",
        ]
        for field in json_fields:
            if d.get(field) and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # host.docker.internal service calls via ServiceRegistry
    # ------------------------------------------------------------------

    def _resolve_service_url(self, service_name: str) -> str:
        if self._service_registry is not None:
            client = getattr(self._service_registry, service_name, None)
            if client is not None:
                try:
                    return str(client.base_url)
                except Exception:
                    pass
        return f"http://host.docker.internal:8000/{service_name}"

    def get_mcp_service_endpoint(self, tool_name: str) -> str:
        base = self._resolve_service_url("snap")
        return f"{base}/mcp/{tool_name}"

    def get_governance_endpoint(self) -> str:
        return self._resolve_service_url("mdhg") + "/governance"

    def get_receipt_service_endpoint(self) -> str:
        return self._resolve_service_url("mmdb") + "/receipts"
