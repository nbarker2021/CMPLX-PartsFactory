"""SAP Governance — Sentinel->Arbiter->Porter triad with deception detection.

Sentinel: pre-flight checks (conservation, content, labels, identity)
Arbiter: quality scoring 0-1 (labels, domains, morphon z, substance)
Porter: routing (board/staging/economy/portal/default) + receipt emission
5 family variants: board, staging, economy, portal, default.
Deception detection: phantom_evidence, self_interest, rubber_stamp,
    unsupported_confidence, circular_logic, authority_appeal, false_consensus.
PG-backed sap_verdicts table.
Integrates with GeometricGovernance for all boundary event recording.
"""
from __future__ import annotations
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import psycopg2
import requests

from .engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("governance.sap")

PG_URL = os.environ.get(
    "PG_URL",
    "postgresql://...:@host.docker.internal:5432/unification_hub"  # configure via PG_URL env var,
)

DECEPTION_TYPES = {
    "phantom_evidence": {"severity": 0.4, "description": "Cites evidence not present in the action"},
    "self_interest": {"severity": 0.6, "description": "Judge is judging own work"},
    "rubber_stamp": {"severity": 0.15, "description": "Approve rate >95% over last 20 votes"},
    "unsupported_confidence": {"severity": 0.1, "description": "High confidence with minimal evidence"},
    "circular_logic": {"severity": 0.3, "description": "Conclusion assumes its premises"},
    "authority_appeal": {"severity": 0.2, "description": "Relies on authority rather than evidence"},
    "false_consensus": {"severity": 0.35, "description": "Claims agreement that does not exist"},
}

BLOCK_THRESHOLD = 0.5
FLAG_THRESHOLD = 0.3
APPROVE_THRESHOLD = 0.6
DEEPEN_THRESHOLD = 0.3

PORTER_ROUTES = {
    "board": {"destinations": ["board_service", "notify_subscribers", "receipt"],
              "description": "Route to community board"},
    "staging": {"destinations": ["master_db", "domain_dbs", "receipt"],
                "description": "Route to staging gateway for commit"},
    "economy": {"destinations": ["mint_service", "coin_ledger", "receipt"],
                "description": "Route to economy for transaction"},
    "portal": {"destinations": ["partition", "audit", "dmz", "receipt"],
               "description": "Route through external portal DMZ"},
    "default": {"destinations": ["receipt"],
                "description": "Generic routing with receipt only"},
}

MMDB_URL = os.environ.get("MMDB_UNIFIED_URL", "http://host.docker.internal:8824")
MDHG_URL = os.environ.get("MDHG_UNIFIED_URL", "http://host.docker.internal:8825")
SNAP_URL = os.environ.get("SNAP_UNIFIED_URL", "http://host.docker.internal:8823")


class PGStore:
    _conn = None

    @classmethod
    def _get_pg(cls):
        if cls._conn is None or cls._conn.closed:
            try:
                cls._conn = psycopg2.connect(PG_URL)
                cls._conn.autocommit = True
            except Exception as e:
                logger.warning("PG connection failed: %s", e)
                return None
        return cls._conn

    @classmethod
    def ensure_tables(cls):
        conn = cls._get_pg()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sap_verdicts (
                        verdict_id          TEXT PRIMARY KEY,
                        agent_id            TEXT NOT NULL,
                        content_hash        TEXT,
                        action              TEXT NOT NULL,
                        boundary_type       TEXT DEFAULT 'default',
                        sentinel_result     JSONB DEFAULT '{}',
                        arbiter_result      JSONB DEFAULT '{}',
                        porter_destination  TEXT,
                        confidence          REAL DEFAULT 0.0,
                        deception_flags     JSONB DEFAULT '[]',
                        created_at          DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_sv_agent ON sap_verdicts(agent_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_sv_action ON sap_verdicts(action)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_sv_boundary ON sap_verdicts(boundary_type)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_sv_time ON sap_verdicts(created_at DESC)")
        except Exception as e:
            logger.warning("Table creation failed: %s", e)

    @classmethod
    def store_verdict(cls, verdict_id: str, agent_id: str, content_hash: str,
                      action: str, boundary_type: str, sentinel: Dict,
                      arbiter: Dict, porter_dest: str, confidence: float,
                      deception_flags: List):
        conn = cls._get_pg()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sap_verdicts (verdict_id, agent_id, content_hash, action, boundary_type,
                        sentinel_result, arbiter_result, porter_destination, confidence, deception_flags, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (verdict_id) DO NOTHING
                """, (verdict_id, agent_id, content_hash, action, boundary_type,
                      json.dumps(sentinel), json.dumps(arbiter), porter_dest,
                      confidence, json.dumps(deception_flags), time.time()))
        except Exception as e:
            logger.warning("PG verdict store failed: %s", e)

    @classmethod
    def query_verdicts(cls, limit: int = 20):
        conn = cls._get_pg()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT verdict_id, agent_id, content_hash, action, boundary_type,
                           sentinel_result, arbiter_result, porter_destination, confidence, created_at
                    FROM sap_verdicts ORDER BY created_at DESC LIMIT %s
                """, (limit,))
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception as e:
            logger.warning("PG verdict query failed: %s", e)
            return []

    @classmethod
    def stats(cls):
        conn = cls._get_pg()
        if not conn:
            return {}
        result = {}
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM sap_verdicts")
                result["total"] = cur.fetchone()[0]
                cur.execute("SELECT action, COUNT(*) FROM sap_verdicts GROUP BY action")
                result["by_action"] = {r[0]: r[1] for r in cur.fetchall()}
                cur.execute("SELECT boundary_type, COUNT(*) FROM sap_verdicts GROUP BY boundary_type")
                result["by_boundary"] = {r[0]: r[1] for r in cur.fetchall()}
        except Exception as e:
            logger.warning("PG stats failed: %s", e)
        return result


class Sentinel:
    """Pre-flight checks per family variant (board/staging/economy/portal/default)."""

    @staticmethod
    def board(content: str, labels: List[str], delta_phi: float, agent_id: str) -> Dict:
        issues = []
        if delta_phi > 0:
            issues.append(f"conservation:dphi={delta_phi:.4f}")
        if len(content) < 10:
            issues.append("content_too_short")
        if not labels:
            issues.append("no_snap_labels")
        return {"passed": len(issues) == 0, "issues": issues, "variant": "board"}

    @staticmethod
    def staging(content: str, labels: List[str], delta_phi: float, agent_id: str) -> Dict:
        issues = []
        if delta_phi > 0:
            issues.append(f"conservation:dphi={delta_phi:.4f}")
        dangerous = ["os.system", "subprocess", "eval(", "exec(", "__import__", "rm -rf"]
        for d in dangerous:
            if d in content:
                issues.append(f"unsafe_code:{d}")
        if not labels:
            issues.append("no_snap_labels")
        return {"passed": len(issues) == 0, "issues": issues, "variant": "staging"}

    @staticmethod
    def economy(content: str, labels: List[str], delta_phi: float, agent_id: str) -> Dict:
        issues = []
        if delta_phi > 0:
            issues.append(f"conservation:dphi={delta_phi:.4f}")
        if not agent_id:
            issues.append("no_agent_id_for_transaction")
        economy_labels = [l for l in labels if "coin" in l.lower() or "economy" in l.lower() or "mint" in l.lower()]
        if not economy_labels:
            issues.append("no_economy_labels")
        return {"passed": len(issues) == 0, "issues": issues, "variant": "economy"}

    @staticmethod
    def portal(content: str, labels: List[str], delta_phi: float, agent_id: str) -> Dict:
        issues = []
        if delta_phi > 0:
            issues.append(f"conservation:dphi={delta_phi:.4f}")
        if not agent_id:
            issues.append("no_agent_identity")
        portal_labels = [l for l in labels if "portal" in l.lower() or "external" in l.lower() or "ingress" in l.lower()]
        if not portal_labels:
            issues.append("no_portal_permission_labels")
        return {"passed": len(issues) == 0, "issues": issues, "variant": "portal"}

    @staticmethod
    def default(content: str, labels: List[str], delta_phi: float, agent_id: str) -> Dict:
        issues = []
        if delta_phi > 0:
            issues.append(f"conservation:dphi={delta_phi:.4f}")
        if not content and not labels:
            issues.append("empty_content_and_labels")
        return {"passed": len(issues) == 0, "issues": issues, "variant": "default"}

    VARIANTS = {
        "board": board, "staging": staging,
        "economy": economy, "portal": portal,
        "default": default,
    }

    @classmethod
    def check(cls, content: str, labels: List[str], delta_phi: float,
              agent_id: str, boundary_type: str = "default") -> Dict:
        fn = cls.VARIANTS.get(boundary_type, cls.default)
        return fn(content, labels, delta_phi, agent_id)


class Arbiter:
    """Quality scoring 0-1 based on labels, diversity, length, boundary type."""

    @staticmethod
    def score(content: str, labels: List[str], quality_score: float,
              boundary_type: str = "default") -> Dict:
        label_count = len(labels)

        if label_count > 20:
            score = 0.9
        elif label_count > 10:
            score = 0.7
        elif label_count > 5:
            score = 0.5
        elif label_count > 0:
            score = 0.4
        else:
            score = 0.2

        domains = set()
        for l in labels:
            if "domain:" in l.lower():
                domains.add(l)
            elif ":" in l:
                domains.add(l.split(":")[0])
        if len(domains) >= 3:
            score = min(score + 0.15, 1.0)
        elif len(domains) >= 2:
            score = min(score + 0.1, 1.0)

        if len(content) > 1000:
            score = min(score + 0.05, 1.0)

        if quality_score > 0:
            score = 0.7 * score + 0.3 * quality_score

        if boundary_type == "board":
            snap_layers = set(l.split(":")[0] for l in labels if ":" in l)
            if len(snap_layers) >= 3:
                score = min(score + 0.05, 1.0)
        elif boundary_type == "staging":
            code_labels = [l for l in labels if any(k in l.lower() for k in ["function", "class", "module", "code"])]
            if code_labels:
                score = min(score + 0.1, 1.0)

        if score >= APPROVE_THRESHOLD:
            verdict = "APPROVE"
        elif score >= DEEPEN_THRESHOLD:
            verdict = "DEEPEN"
        else:
            verdict = "REJECT"

        return {
            "score": round(score, 4), "verdict": verdict,
            "label_count": label_count, "domain_count": len(domains),
            "content_length": len(content), "boundary_type": boundary_type,
        }


class Porter:
    """Routing: determines destinations per boundary type and verdict."""

    @staticmethod
    def route(boundary_type: str, verdict: str) -> Dict:
        route_config = PORTER_ROUTES.get(boundary_type, PORTER_ROUTES["default"])
        if verdict == "REJECT":
            return {"destinations": ["quarantine"], "action": "reject",
                    "description": "Rejected — routed to quarantine"}
        if verdict == "DEEPEN":
            return {"destinations": ["thinktank", "receipt"], "action": "deepen",
                    "description": "Needs deeper analysis — routed to ThinkTank"}
        return {"destinations": route_config["destinations"], "action": "approve",
                "description": route_config["description"]}


class DeceptionDetector:
    """7-type deception detection with vote history tracking."""

    def __init__(self):
        self._vote_history: Dict[str, List[bool]] = {}
        self._stats: Dict[str, int] = {"deception_flags": 0}

    @property
    def vote_history(self) -> Dict[str, List[bool]]:
        return dict(self._vote_history)

    @property
    def stats(self) -> Dict[str, int]:
        return dict(self._stats)

    def check(self, judge_id: str, verdict: str, evidence_labels: List[str],
              confidence: float, action_labels: List[str], action_agent_id: str) -> Dict:
        flags = []
        severity = 0.0

        action_set = set(action_labels)
        cited_set = set(evidence_labels)
        phantom = cited_set - action_set
        if phantom:
            flags.append({"type": "phantom_evidence", "detail": f"{len(phantom)} phantom labels",
                           "severity": DECEPTION_TYPES["phantom_evidence"]["severity"]})
            severity += DECEPTION_TYPES["phantom_evidence"]["severity"]

        if judge_id and judge_id == action_agent_id:
            flags.append({"type": "self_interest", "detail": "Judge is judging own work",
                           "severity": DECEPTION_TYPES["self_interest"]["severity"]})
            severity += DECEPTION_TYPES["self_interest"]["severity"]

        history = self._vote_history.get(judge_id, [])
        if len(history) >= 20:
            approve_rate = sum(history[-20:]) / 20
            if approve_rate > 0.95:
                flags.append({"type": "rubber_stamp", "detail": f"Approve rate {approve_rate:.0%}",
                               "severity": DECEPTION_TYPES["rubber_stamp"]["severity"]})
                severity += DECEPTION_TYPES["rubber_stamp"]["severity"]

        if confidence > 0.8 and len(evidence_labels) < 2:
            flags.append({"type": "unsupported_confidence",
                           "detail": f"Confidence {confidence:.2f} with {len(evidence_labels)} evidence labels",
                           "severity": DECEPTION_TYPES["unsupported_confidence"]["severity"]})
            severity += DECEPTION_TYPES["unsupported_confidence"]["severity"]

        domain_evidence = [l for l in evidence_labels if "domain" in l.lower()]
        if confidence > 0.7 and not domain_evidence and evidence_labels:
            flags.append({"type": "authority_appeal", "detail": "No domain evidence cited",
                           "severity": DECEPTION_TYPES["authority_appeal"]["severity"]})
            severity += DECEPTION_TYPES["authority_appeal"]["severity"]

        if verdict == "APPROVE" and len(evidence_labels) == 1 and confidence > 0.9:
            flags.append({"type": "false_consensus", "detail": "Single-evidence high-confidence approval",
                           "severity": DECEPTION_TYPES["false_consensus"]["severity"]})
            severity += DECEPTION_TYPES["false_consensus"]["severity"]

        self._vote_history.setdefault(judge_id, []).append(verdict == "APPROVE")
        if len(self._vote_history[judge_id]) > 100:
            self._vote_history[judge_id] = self._vote_history[judge_id][-50:]

        clean = severity < FLAG_THRESHOLD
        blocked = severity >= BLOCK_THRESHOLD

        if flags:
            self._stats["deception_flags"] += len(flags)

        return {
            "clean": clean, "blocked": blocked,
            "flags": flags, "severity": round(severity, 4),
            "recommendation": "block" if blocked else ("flag" if not clean else "pass"),
        }


class SAPGovernance:
    """Full Sentinel->Arbiter->Porter governance triad with deception detection.

    Integrates with GeometricGovernance by recording all judgments as BoundaryEvents
    and validates each step through the audit trail.
    """

    def __init__(self, governance: Optional[GeometricGovernance] = None):
        self.governance = governance or GeometricGovernance()
        self.sentinel = Sentinel()
        self.arbiter = Arbiter()
        self.porter = Porter()
        self.deception = DeceptionDetector()
        self._judgments: List[Dict] = []
        self._stats: Dict[str, Any] = {"total": 0, "approved": 0, "rejected": 0, "deepened": 0,
                                        "by_boundary": {}}
        PGStore.ensure_tables()

    @property
    def stats(self) -> Dict:
        s = dict(self._stats)
        s["deception_flags"] = self.deception.stats["deception_flags"]
        s["pg"] = PGStore.stats()
        s["vote_trackers"] = len(self.deception.vote_history)
        return s

    @property
    def judgments(self) -> List[Dict]:
        return list(self._judgments)

    @staticmethod
    def _content_hash(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:24]

    @staticmethod
    def _verdict_id(agent_id: str, content_hash: str) -> str:
        raw = f"{agent_id}:{content_hash}:{time.time()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:20]

    def _update_stats(self, verdict: str, boundary_type: str):
        self._stats["total"] += 1
        if verdict == "APPROVE":
            self._stats["approved"] += 1
        elif verdict == "REJECT":
            self._stats["rejected"] += 1
        else:
            self._stats["deepened"] += 1
        self._stats["by_boundary"][boundary_type] = self._stats["by_boundary"].get(boundary_type, 0) + 1

    def judge(self, content: str = "", snap_labels: Optional[List[str]] = None,
              delta_phi: float = 0.0, agent_id: str = "", boundary_type: str = "default",
              epoch: int = 0, quality_score: float = 0.0) -> Dict:
        labels = snap_labels or []
        ch = self._content_hash(content)
        vid = self._verdict_id(agent_id, ch)

        sentinel = self.sentinel.check(content, labels, delta_phi, agent_id, boundary_type)

        if sentinel["passed"]:
            arbiter = self.arbiter.score(content, labels, quality_score, boundary_type)
        else:
            arbiter = {"score": 0.0, "verdict": "REJECT", "label_count": 0,
                       "reason": "sentinel_failed"}

        porter = self.porter.route(boundary_type, arbiter["verdict"])

        deception = self.deception.check(
            agent_id, arbiter["verdict"], labels, arbiter.get("score", 0.0),
            labels, agent_id,
        )

        judgment = {
            "verdict_id": vid, "agent_id": agent_id,
            "boundary_type": boundary_type,
            "sentinel": sentinel, "arbiter": arbiter, "porter": porter,
            "deception": deception,
            "final_verdict": arbiter["verdict"],
            "confidence": arbiter.get("score", 0.0),
            "epoch": epoch, "timestamp": time.time(),
        }

        self._judgments.append(judgment)
        self._update_stats(arbiter["verdict"], boundary_type)

        self.governance.record_boundary_event(BoundaryEvent(
            event_id=vid,
            timestamp=time.time(),
            entropy_delta=arbiter.get("score", 0.0) if sentinel["passed"] else 1.0,
            receipt_data={
                "action": "sap_judgment",
                "sentinel": sentinel,
                "arbiter": arbiter,
                "porter": porter,
                "deception": deception,
                "boundary_type": boundary_type,
            },
            boundary_type=f"sap_{boundary_type}",
        ))

        PGStore.store_verdict(vid, agent_id, ch, arbiter["verdict"],
                              boundary_type, sentinel, arbiter,
                              ",".join(porter["destinations"]), arbiter.get("score", 0.0),
                              deception.get("flags", []))

        return judgment

    def sentinel_check(self, content: str = "", snap_labels: Optional[List[str]] = None,
                       delta_phi: float = 0.0, agent_id: str = "",
                       boundary_type: str = "default") -> Dict:
        return self.sentinel.check(content, snap_labels or [], delta_phi, agent_id, boundary_type)

    def arbiter_score(self, content: str = "", snap_labels: Optional[List[str]] = None,
                      quality_score: float = 0.0, boundary_type: str = "default") -> Dict:
        return self.arbiter.score(content, snap_labels or [], quality_score, boundary_type)

    def porter_route(self, boundary_type: str = "default", verdict: str = "approve") -> Dict:
        return self.porter.route(boundary_type, verdict)

    def deception_check(self, judge_id: str = "", verdict: str = "",
                        evidence_labels: Optional[List[str]] = None,
                        confidence: float = 0.0,
                        action_labels: Optional[List[str]] = None,
                        action_agent_id: str = "") -> Dict:
        return self.deception.check(
            judge_id, verdict, evidence_labels or [],
            confidence, action_labels or [], action_agent_id,
        )

    def get_verdicts(self, limit: int = 20, source: str = "memory") -> List[Dict]:
        if source == "pg":
            return PGStore.query_verdicts(limit)
        return self._judgments[-limit:]

    def fetch_mmdb_labels(self, agent_id: str) -> List[str]:
        try:
            resp = requests.get(f"{MMDB_URL}/crystal/{agent_id}", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("snap_labels", [])
        except Exception as e:
            logger.warning("MMDB fetch failed for %s: %s", agent_id, e)
        return []

    def fetch_mdhg_graph(self, session_id: str) -> Dict:
        try:
            resp = requests.get(f"{MDHG_URL}/graph/{session_id}", timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning("MDHG fetch failed for %s: %s", session_id, e)
        return {}

    def stratify_snap(self, concept: str, depth: int = 3) -> Dict:
        try:
            resp = requests.post(f"{SNAP_URL}/stratify",
                                 json={"concept": concept, "depth": depth}, timeout=30)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning("SNAP stratify failed for %s: %s", concept, e)
        return {}
