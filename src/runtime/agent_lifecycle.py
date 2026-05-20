"""AgentLifecycle — TMN2-native agent lifecycle integrated with CMPLX-PartsFactory runtime.

Ports the TMN2 Agent class (agent.py) into the existing Runtime ecosystem:
  - AgentState dataclass with 5 epoch tiers, specialist tracking, wallet merit/snap
  - process()  — file through tmn2-pipeline, tracks epoch + specialist progression
  - search()   — label-directed search via PG
  - mirror()   — dihedral review (forward + mirror search + synthesis)
  - preflight() — 8-step task assessment via pipeline + PG coverage
  - birth()    — spawn child agent via tmn2-spawn
  - status()   — full agent report with live PG stats + service health

Integrates with: AgentMemory (state persistence), HealthChecker (service probes),
StateManager (snapshots), RuntimeOrchestrator (idea pipeline).
"""

from __future__ import annotations
import json
import logging
import math
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .memory import AgentMemory
from .health import HealthChecker
from .snapshots import StateManager
from .orchestrator import RuntimeOrchestrator

logger = logging.getLogger("runtime.lifecycle")

# ── TMN2 Service URLs (via host.docker.internal for Docker bridge) ──────────

PIPELINE_URL  = os.environ.get("TMN2_PIPELINE_URL",  "http://host.docker.internal:8825")
BOARD_URL     = os.environ.get("TMN2_BOARD_URL",     "http://host.docker.internal:8825")
BRAIN_URL     = os.environ.get("TMN2_BRAIN_URL",     "http://host.docker.internal:8824")
RECEIPT_URL   = os.environ.get("TMN2_RECEIPT_URL",   "http://host.docker.internal:8844")
MINT_URL      = os.environ.get("TMN2_MINT_URL",      "http://host.docker.internal:8870")
GATE_URL      = os.environ.get("TMN2_GATE_URL",      "http://host.docker.internal:8823")
SPAWN_URL     = os.environ.get("TMN2_SPAWN_URL",     "http://host.docker.internal:8815")
IDENTITY_URL  = os.environ.get("TMN2_IDENTITY_URL",  "http://host.docker.internal:3000")

PG_DSN = os.environ.get(
    "TMN2_PG_DSN",
    "postgresql://tmn2:tmn2_dev@host.docker.internal:5432/unification_hub",
)


def _http(url: str, data: dict | None = None, method: str = "POST") -> dict:
    """Thin HTTP JSON helper (same signature as TMN2 agent.py _http)."""
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


def _pg_query(sql: str, params: tuple | list | None = None) -> list[dict]:
    """Query PostgreSQL via psycopg2 (same signature as TMN2 agent.py _pg_query)."""
    try:
        import psycopg2
        conn = psycopg2.connect(PG_DSN)
        cur = conn.cursor()
        cur.execute(sql, params or ())
        if cur.description:
            cols = [d[0] for d in cur.description]
            results = [dict(zip(cols, row)) for row in cur.fetchall()]
        else:
            results = []
        conn.close()
        return results
    except Exception as e:
        return [{"error": str(e)[:120]}]


# ── AgentState ─────────────────────────────────────────────────────────────

EPOCH_TIERS = ["nascent", "apprentice", "journeyman", "master", "architect"]
TIER_THRESHOLDS = [0, 50, 150, 300, 600]  # epoch gates


@dataclass
class AgentState:
    agent_id: str = "opencmplx-agent-v1"
    brain_dim: int = 24
    epoch: int = 0
    epoch_tier: str = "nascent"
    total_atoms: int = 0
    total_dphi: float = 0.0
    total_novel: int = 0
    total_labels: int = 0
    wallet_merit: float = 0.0
    wallet_snap: float = 0.0
    specialist: Dict[str, float] = field(default_factory=lambda: {
        "geometry": 0.0, "orchestration": 0.0, "validation": 0.0,
        "logging": 0.0, "hashing": 0.0, "morphonic": 0.0,
        "network": 0.0, "database": 0.0, "caching": 0.0,
    })
    last_action: str = ""

    SPECIALIST_TOUCH_MAP: Dict[str, str] = field(default_factory=lambda: {
        "SNAPtouch_geometry": "geometry", "SNAPtouch_orchestration": "orchestration",
        "SNAPtouch_validation": "validation", "SNAPtouch_logging": "logging",
        "SNAPtouch_hashing": "hashing", "SNAPtouch_morphonic": "morphonic",
        "SNAPtouch_network": "network", "SNAPtouch_database": "database",
        "SNAPtouch_caching": "caching",
    }, init=False, repr=False)

    def update_specialist(self, labels: List[str]) -> None:
        for label in labels:
            key = self.SPECIALIST_TOUCH_MAP.get(label)
            if key:
                self.specialist[key] = min(
                    1.0, self.specialist.get(key, 0) + 0.01 * (1.0 - self.specialist.get(key, 0))
                )

    def update_tier(self) -> None:
        if self.epoch >= 600:
            self.epoch_tier = "architect"
        elif self.epoch >= 300:
            self.epoch_tier = "master"
        elif self.epoch >= 150:
            self.epoch_tier = "journeyman"
        elif self.epoch >= 50:
            self.epoch_tier = "apprentice"
        else:
            self.epoch_tier = "nascent"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> AgentState:
        state = cls()
        for k, v in d.items():
            if hasattr(state, k):
                setattr(state, k, v)
        return state


# ── AgentLifecycle ──────────────────────────────────────────────────────────

class AgentLifecycle:
    """TMN2 agent lifecycle wrapped for CMPLX-PartsFactory Runtime.

    Every method updates AgentState, persists via AgentMemory,
    and hits TMN2 services via host.docker.internal URLs.
    """

    def __init__(self, memory: AgentMemory | None = None,
                 health: HealthChecker | None = None,
                 snapshots: StateManager | None = None,
                 orchestrator: RuntimeOrchestrator | None = None,
                 state_key: str = "agent_lifecycle_state"):
        self.memory = memory
        self.health = health
        self.snapshots = snapshots
        self.orchestrator = orchestrator
        self.state_key = state_key
        self.state = self._load_state()

    # ── State Persistence ──────────────────────────────────────

    def _load_state(self) -> AgentState:
        if self.memory is not None:
            raw = self.memory.get_state(self.state_key)
            if raw is not None and isinstance(raw, dict):
                return AgentState.from_dict(raw)
        return AgentState()

    def _save_state(self) -> None:
        if self.memory is not None:
            self.memory.set_state(self.state_key, self.state.to_dict())

    # ── Lifecycle Methods ──────────────────────────────────────

    def process(self, filepath: str, source_tag: str = "") -> Dict[str, Any]:
        """Process a file through tmn2-pipeline. Increments epoch on new atoms."""
        self.state.last_action = f"process:{filepath}"
        p = Path(filepath)
        if not p.exists():
            return {"error": "File not found"}
        text = p.read_text(encoding="utf-8", errors="replace")
        if len(text.strip()) < 10:
            return {"error": "Too short"}

        result = _http(f"{PIPELINE_URL}/process", {
            "content": text[:4000],
            "source": source_tag or p.name,
            "agent_id": self.state.agent_id,
            "epoch": self.state.epoch,
        })

        if result.get("atom_id") and not result.get("dedup"):
            labels = result.get("snap_labels", [])
            self.state.total_atoms += 1
            self.state.total_dphi += result.get("delta_phi", 0)
            self.state.total_labels += len(labels)
            self.state.epoch += 1
            self.state.update_specialist(labels)
            self.state.update_tier()

            if self.state.epoch > 0 and self.state.epoch % 300 == 0:
                _http(f"{GATE_URL}/check", {
                    "agent_id": self.state.agent_id,
                    "epoch": self.state.epoch,
                    "dims": self.state.brain_dim,
                    "tier": self.state.epoch_tier,
                    "capacity_score": 0.5,
                })

        self._save_state()
        return result

    def search(self, query: str) -> Dict[str, Any]:
        """Label-directed search in PG. Builds candidate labels from query terms."""
        self.state.last_action = f"search:{query}"
        terms = query.strip().split()
        candidates = []
        for t in terms:
            candidates.extend([
                f"SNAPkeyword_{t}", f"SNAPlit_{t}", f"SNAPformal_{t}",
                f"SNAPmeta_{t}", f"SNAPdomain_{t}",
            ])

        rows = _pg_query(
            "SELECT label, count(*) as atoms FROM snap_labels "
            "WHERE label = ANY(%s) GROUP BY label ORDER BY count(*) DESC",
            (candidates,),
        )
        labels = {r["label"]: r["atoms"] for r in rows if "label" in r}

        sources = []
        found_list = list(labels.keys())
        if len(found_list) >= 2:
            sources = _pg_query(
                "SELECT a.source_file, count(DISTINCT sl.label) as matching "
                "FROM atoms a JOIN snap_labels sl ON a.atom_id = sl.atom_id "
                "WHERE sl.label = ANY(%s) AND a.source_file != '' AND a.source_file IS NOT NULL "
                "GROUP BY a.source_file "
                "HAVING count(DISTINCT sl.label) >= 2 "
                "ORDER BY count(DISTINCT sl.label) DESC LIMIT 10",
                (found_list,),
            )

        self._save_state()
        return {"found": len(labels), "labels": labels, "sources": sources, "query": terms}

    def mirror(self) -> Dict[str, Any]:
        """Dihedral review — forward own state through pipeline, then search mirror, then synthesize."""
        self.state.last_action = "mirror"
        state_text = json.dumps(self.state.to_dict(), indent=2)

        forward = _http(f"{PIPELINE_URL}/process", {
            "content": state_text,
            "source": "mirror::self_state",
            "agent_id": self.state.agent_id,
            "epoch": self.state.epoch,
        })

        top_spec = sorted(self.state.specialist.items(), key=lambda x: -x[1])[:3]
        mirror_query = " ".join(s[0] for s in top_spec)
        mirror_result = self.search(mirror_query)

        self._save_state()
        return {
            "forward_labels": len(forward.get("snap_labels", [])),
            "forward_dphi": forward.get("delta_phi", 0),
            "mirror_found": mirror_result.get("found", 0),
            "mirror_sources": len(mirror_result.get("sources", [])),
            "top_specialists": top_spec,
        }

    def preflight(self, task: str) -> Dict[str, Any]:
        """8-step task assessment: label task, check PG coverage, identify gaps."""
        self.state.last_action = f"preflight:{task[:30]}"

        import urllib.request
        result = _http(
            f"{PIPELINE_URL}/label?content={urllib.request.quote(task[:2000])}"
        )
        task_labels = result.get("labels", []) if result else []

        meaningful = [
            l for l in task_labels
            if l.startswith(("SNAPtouch_", "SNAPdomain_", "SNAPformal_", "SNAPmeta_"))
        ]
        inventory = {}
        for label in meaningful:
            rows = _pg_query(
                "SELECT count(*) as c FROM snap_labels WHERE label = %s", (label,)
            )
            inventory[label] = rows[0]["c"] if rows and "c" in rows[0] else 0

        gaps = {l: c for l, c in inventory.items() if c < 5}
        can_close = len(gaps) == 0
        atoms_needed = sum(max(0, 5 - c) for c in gaps.values())
        energy_cost = abs(-0.81) * atoms_needed

        self._save_state()
        return {
            "task": task[:100],
            "labels": len(task_labels),
            "meaningful": len(meaningful),
            "inventory": inventory,
            "gaps": gaps,
            "can_close": can_close,
            "atoms_needed": atoms_needed,
            "energy_cost": round(energy_cost, 2),
            "recommendation": "EXECUTE" if can_close else "FILL_GAPS",
        }

    def birth(self, domain: str = "", boost: str = "") -> Dict[str, Any]:
        """Spawn a child agent via tmn2-spawn."""
        self.state.last_action = f"birth:{domain}"
        result = _http(f"{SPAWN_URL}/birth", {
            "parent_id": self.state.agent_id,
            "domain": domain,
            "domain_boost": boost,
            "snapdna": list(self.state.specialist.keys()),
            "escrow_merit": self.state.wallet_merit * 0.2,
        })
        self._save_state()
        return result

    def status(self) -> Dict[str, Any]:
        """Full agent status with live PG stats and service health."""
        s = self.state.to_dict()

        rows = _pg_query("SELECT count(*) as c FROM atoms")
        s["pg_atoms"] = rows[0]["c"] if rows and "c" in rows[0] else 0
        rows = _pg_query("SELECT count(DISTINCT label) as c FROM snap_labels")
        s["pg_labels"] = rows[0]["c"] if rows and "c" in rows[0] else 0
        rows = _pg_query(
            "SELECT COALESCE(sum(morphon_delta_phi),0)::numeric(10,2) as c FROM atoms"
        )
        s["pg_dphi"] = float(rows[0]["c"]) if rows and "c" in rows[0] else 0

        s["services"] = {}
        for name, url in [
            ("pipeline", PIPELINE_URL), ("board", BOARD_URL),
            ("receipt", RECEIPT_URL), ("mint", MINT_URL),
            ("brain", BRAIN_URL), ("gate", GATE_URL),
        ]:
            h = _http(f"{url}/health", method="GET")
            s["services"][name] = h.get("ok", False) if isinstance(h, dict) else False

        s["dominant"] = (
            max(self.state.specialist.items(), key=lambda x: x[1])[0]
            if self.state.specialist else "none"
        )
        return s

    # ── Integration helpers ────────────────────────────────────

    def to_task_handler(self) -> Dict[str, Any]:
        """Return a handler map for AgentProcess._dispatch integration.

        Usage:
            agent_process._dispatch = {
                **agent_process._dispatch,
                **lifecycle.to_task_handler(),
            }
        """
        return {
            "lifecycle_process": lambda d: self.process(
                d.get("filepath", ""), d.get("source", "")
            ),
            "lifecycle_search": lambda d: self.search(d.get("query", "")),
            "lifecycle_mirror": lambda d: self.mirror(),
            "lifecycle_preflight": lambda d: self.preflight(d.get("task", "")),
            "lifecycle_birth": lambda d: self.birth(
                d.get("domain", ""), d.get("boost", "")
            ),
            "lifecycle_status": lambda d: self.status(),
        }
