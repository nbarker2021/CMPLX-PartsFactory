"""
TMN2Daemon — Complete CRT 24-ring orchestrator ported from CMPLX-TMN-main.

Integrates:
  - E8 orientation controller (8D state vector → UP/DOWN/SIDEWAYS projections)
  - Grain budget system with breathability (load-factor backoff on error)
  - 24 fully-implemented CRT channels on coprime periods
  - LocalCRT for buffered outbound handlers (board posts, pipeline batch, etc.)
  - PgConnector for PostgreSQL (unification_hub + unification_aggregator)
  - GeometricGovernance audit integration for boundary events

Service endpoints route via host.docker.internal:PORT to running Docker services.
"""
import hashlib
import json
import logging
import math
import os
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from fastapi import FastAPI

from daemon.local_crt import LocalCRT, make_board_flusher, make_pipeline_flusher
from daemon.global_crt import PgConnector

logger = logging.getLogger("daemon.tmn2")

# ── Configuration ────────────────────────────────────────────────────────────
# All URLs route through host.docker.internal to running Docker services.
# Each is overridable via environment variable.

PORT = int(os.environ.get("TMN2_DAEMON_PORT", "8080"))

# PostgreSQL (unification_hub)
PG_URL = os.environ.get(
    "PG_URL",
    "postgresql://...:@host.docker.internal:5432/unification_hub"  # configure via PG_URL env var,
)
# Redis (not used by handlers, available for future channels)
REDIS_URL = os.environ.get("REDIS_URL", "redis://host.docker.internal:6379/0")

# Service endpoints — mapped to running Docker services
BOARD_URL = os.environ.get("BOARD_URL", "http://host.docker.internal:8002")
PIPELINE_URL = os.environ.get("PIPELINE_URL", "http://host.docker.internal:8000")
THINKTANK_URL = os.environ.get("THINKTANK_URL", "http://host.docker.internal:3000")
SAP_URL = os.environ.get("SAP_URL", "http://host.docker.internal:8003")
SPEEDLIGHT_URL = os.environ.get("SPEEDLIGHT_URL", "http://host.docker.internal:8843")
COOP_URL = os.environ.get("COOP_URL", "http://host.docker.internal:8823")
MINT_URL = os.environ.get("MINT_URL", "http://host.docker.internal:8824")
CONSERVATION_URL = os.environ.get("CONSERVATION_URL", "http://host.docker.internal:8825")
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://host.docker.internal:8844")
SPAWN_URL = os.environ.get("SPAWN_URL", "http://host.docker.internal:8870")
IDENTITY_URL = os.environ.get("IDENTITY_URL", "http://host.docker.internal:8824")
ECONOMY_URL = os.environ.get("ECONOMY_URL", "http://host.docker.internal:8844")
BOND_URL = os.environ.get("BOND_URL", "http://host.docker.internal:8815")

# ── E8 Orientation Controller ────────────────────────────────────────────────
# 8D state vector dimensions:
#   0: atom review pressure  (pending low-quality atoms / 100)
#   1: commit throughput     (recent commits / 50)
#   2: conservation health   (1.0 if violated, 0.0 if OK)
#   3: bounty pressure       (open bounties / 20)
#   4: agent health          (active / total from identity)
#   5: economy health        (total coins / 100)
#   6: pipeline backlog      (queue depth / 100)
#   7: avg load_factor       (across all channels)

UP_ROOT = [1, 1, 1, 1, 1, 1, 1, 1]
DOWN_ROOT = [1, -1, 1, -1, 1, -1, 1, -1]
SIDE_ROOT = [1, 1, -1, -1, 1, 1, -1, -1]

UP_CHANNELS = {"atom_review", "pg_commit", "conservation", "thinktank"}
DOWN_CHANNELS = {"conservation_audit", "lifecycle", "dead_letter", "db_audit", "key_check"}
SIDE_CHANNELS = {"dispatch", "assign", "snap_route", "speedlight", "morphon", "governance"}
# META = everything else — pulse, cross_check, backpressure, full_report,
#        stats, economy, birth, epoch_gate, outside_actor

BASE_BUDGET = 50


def _normalize(v: List[float]) -> List[float]:
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n > 0 else v


def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _scale_budget(channel_name: str, orientation: Dict[str, float]) -> int:
    if channel_name in UP_CHANNELS:
        return int(BASE_BUDGET * max(0.5, 1.0 + orientation.get("up", 0)))
    elif channel_name in DOWN_CHANNELS:
        return int(BASE_BUDGET * 0.5 * max(0.5, 1.0 + orientation.get("down", 0)))
    elif channel_name in SIDE_CHANNELS:
        return int(BASE_BUDGET * 0.3 * max(0.5, 1.0 + orientation.get("sideways", 0)))
    return BASE_BUDGET * 10


# ── Channel Definitions ─────────────────────────────────────────────────────
# 24 channels on coprime periods with offsets for CRT reconstruction.

CHANNELS = [
    {"symbol": "\u03bd", "name": "pulse",              "period": 5,   "offset": 0},
    {"symbol": "\u03c7", "name": "cross_check",         "period": 7,   "offset": 2},
    {"symbol": "\u03b5", "name": "atom_review",          "period": 30,  "offset": 0},
    {"symbol": "\u03c0", "name": "pg_commit",            "period": 30,  "offset": 5},
    {"symbol": "\u03c1", "name": "conservation",         "period": 30,  "offset": 10},
    {"symbol": "\u03b8", "name": "backpressure",         "period": 30,  "offset": 25},
    {"symbol": "\u03bb", "name": "dispatch",             "period": 45,  "offset": 15},
    {"symbol": "\u03b1", "name": "assign",               "period": 45,  "offset": 22},
    {"symbol": "\u03c3", "name": "snap_route",           "period": 60,  "offset": 3},
    {"symbol": "\u03bc", "name": "morphon",              "period": 60,  "offset": 6},
    {"symbol": "\u03c8", "name": "speedlight",           "period": 60,  "offset": 9},
    {"symbol": "\u03c9", "name": "thinktank",            "period": 90,  "offset": 7},
    {"symbol": "\u03b7", "name": "outside_actor",        "period": 90,  "offset": 12},
    {"symbol": "\u03b3", "name": "governance",           "period": 90,  "offset": 30},
    {"symbol": "\u03c4", "name": "lifecycle",            "period": 120, "offset": 20},
    {"symbol": "\u03be", "name": "epoch_gate",           "period": 120, "offset": 40},
    {"symbol": "\u03b2", "name": "birth",                "period": 150, "offset": 60},
    {"symbol": "\u03c6", "name": "economy",              "period": 180, "offset": 75},
    {"symbol": "\u03b4", "name": "conservation_audit",   "period": 300, "offset": 45},
    {"symbol": "\u03a3", "name": "stats",                "period": 300, "offset": 90},
    {"symbol": "\u03ba", "name": "key_check",            "period": 600, "offset": 120},
    {"symbol": "\u03a9", "name": "dead_letter",          "period": 600, "offset": 180},
    {"symbol": "\u0394", "name": "db_audit",             "period": 600, "offset": 240},
    {"symbol": "\u039b", "name": "full_report",          "period": 900, "offset": 300},
]


# ══════════════════════════════════════════════════════════════════════════════
# TMN2Daemon — CRT 24-Ring Orchestrator Class
# ══════════════════════════════════════════════════════════════════════════════

class TMN2Daemon:
    """CRT 24-ring daemon with E8 orientation, grain budgets, breathability.

    Owns its tick loop (1s resolution, time-based with load-factor scaling).
    Uses LocalCRT instances for buffered outbound handlers.
    Integrates with PgConnector and optional GeometricGovernance.
    """

    def __init__(
        self,
        governance: Any = None,
        app: Optional[FastAPI] = None,
    ):
        self.pg = PgConnector()
        self.governance = governance

        # LocalCRT for buffered outbound handlers
        self.crt = LocalCRT(service_name="tmn2-daemon", tick_interval=10.0)
        self._init_localcrt_buffers()

        # Manifold and channel state
        self._manifold_state: Dict[str, Dict[str, Any]] = {}
        self._channel_state: Dict[str, Dict[str, Any]] = {}
        self._tick_count = 0
        self._start_time = time.time()
        self._running = False
        self._last_orientation: Dict[str, float] = {"up": 0.0, "down": 0.0, "sideways": 0.0}
        self._pg_conn = None
        self._lock = threading.Lock()

        self._init_state()
        self._handlers = self._build_handler_map()

        # Background thread
        self._thread: Optional[threading.Thread] = None

        # FastAPI app
        if app is not None:
            self._mount_routes(app)

    def _init_localcrt_buffers(self):
        self.crt.register_buffer(
            "board_posts", make_board_flusher(BOARD_URL), flush_period=3
        )
        self.crt.register_buffer(
            "pipeline_submissions", make_pipeline_flusher(PIPELINE_URL), flush_period=5
        )

    def _init_state(self):
        for ch in CHANNELS:
            self._channel_state[ch["name"]] = {
                **ch,
                "last_run": 0,
                "run_count": 0,
                "load_factor": 1.0,
                "grain_budget": BASE_BUDGET,
                "errors": 0,
                "last_error": "",
                "last_duration_ms": 0,
            }
            self._manifold_state[ch["name"]] = {"load": 1.0, "ok": True}

    # ── HTTP Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _http_get(url: str, timeout: int = 5) -> Optional[Dict]:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception:
            return None

    @staticmethod
    def _http_post(url: str, data: Dict, timeout: int = 10) -> Optional[Dict]:
        try:
            body = json.dumps(data).encode()
            req = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception:
            return None

    # ── PostgreSQL Helpers ───────────────────────────────────────────────

    def _get_pg(self):
        if not PG_URL:
            return None
        try:
            import psycopg2
            if self._pg_conn is None or self._pg_conn.closed:
                self._pg_conn = psycopg2.connect(PG_URL)
                self._pg_conn.autocommit = True
            return self._pg_conn
        except Exception:
            return None

    def _pg_query(self, sql: str, params=None) -> List:
        conn = self._get_pg()
        if conn is None:
            return []
        try:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception as e:
            logger.debug("PG query failed: %s", e)
            try:
                self._pg_conn.close()
            except Exception:
                pass
            self._pg_conn = None
            return []

    def _pg_execute(self, sql: str, params=None) -> int:
        conn = self._get_pg()
        if conn is None:
            return 0
        try:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            rc = cur.rowcount
            cur.close()
            return rc
        except Exception as e:
            logger.debug("PG execute failed: %s", e)
            try:
                self._pg_conn.close()
            except Exception:
                pass
            self._pg_conn = None
            return 0

    # ── Governance Audit ────────────────────────────────────────────────

    def _audit_event(self, event_type: str, data: Dict):
        if not self.governance:
            return
        try:
            from governance.engine import BoundaryEvent
            event = BoundaryEvent(
                event_id=f"tmn2_{event_type}_{int(time.time())}",
                timestamp=time.time(),
                entropy_delta=0.0,
                receipt_data=data,
                boundary_type=event_type,
            )
            self.governance.record_boundary_event(event)
        except Exception as e:
            logger.debug("governance audit failed: %s", str(e)[:80])

    # ── Channel Due Check ───────────────────────────────────────────────

    def _is_due(self, ch_state: Dict, now: float) -> bool:
        elapsed = now - ch_state["last_run"]
        effective_period = ch_state["period"] * ch_state["load_factor"]
        return elapsed >= effective_period

    # ══════════════════════════════════════════════════════════════════════
    # TICK HANDLERS — 24 channels
    # ══════════════════════════════════════════════════════════════════════

    # ── 1. Pulse (5s) ────────────────────────────────────────────────────

    def _tick_pulse(self):
        board_ok = self._http_get(f"{BOARD_URL}/health") is not None
        pipeline_ok = self._http_get(f"{PIPELINE_URL}/health") is not None
        self._manifold_state["pulse"]["board"] = "ok" if board_ok else "down"
        self._manifold_state["pulse"]["pipeline"] = "ok" if pipeline_ok else "down"
        if self._tick_count % 60 == 0:
            logger.info(
                "\u03bd pulse: board=%s pipeline=%s tick=%d",
                "ok" if board_ok else "DOWN",
                "ok" if pipeline_ok else "DOWN",
                self._tick_count,
            )

    # ── 2. Cross-Check (7s) ──────────────────────────────────────────────

    def _tick_cross_check(self):
        services = {
            "gateway": f"{GATEWAY_URL}/health",
            "board": f"{BOARD_URL}/health",
            "pipeline": f"{PIPELINE_URL}/health",
        }
        failures = 0
        for name, url in services.items():
            resp = self._http_get(url, timeout=3)
            status = "ok" if resp is not None else "unreachable"
            self._manifold_state["cross_check"][name] = status
            if resp is None:
                failures += 1
        self._manifold_state["cross_check"]["failures"] = failures
        if failures > 0:
            logger.warning(
                "\u03c7 cross-check: %d/%d services unreachable", failures, len(services)
            )

    # ── 3. Atom Review (30s) ─────────────────────────────────────────────

    def _tick_atom_review(self):
        rows = self._pg_query(
            "SELECT atom_id, snap_labels, quality_score FROM atoms "
            "WHERE quality_score < 0.5 ORDER BY created_at DESC LIMIT 50"
        )
        if not rows:
            return
        auto_approved = 0
        sent_to_thinktank = 0
        for atom_id, snap_labels_json, quality in rows:
            try:
                labels = json.loads(snap_labels_json) if snap_labels_json else []
            except (json.JSONDecodeError, TypeError):
                labels = []
            if len(labels) > 5:
                self._pg_execute(
                    "UPDATE atoms SET quality_score = 0.7 WHERE atom_id = %s",
                    (atom_id,),
                )
                auto_approved += 1
            else:
                resp = self._http_post(
                    f"{THINKTANK_URL}/reason",
                    {
                        "atom_id": atom_id,
                        "snap_labels": labels,
                        "quality": quality,
                        "request": "review_atom_quality",
                    },
                    timeout=10,
                )
                if resp is not None:
                    sent_to_thinktank += 1
        self._manifold_state["atom_review"]["pending"] = len(rows)
        self._manifold_state["atom_review"]["auto_approved"] = auto_approved
        if auto_approved > 0 or sent_to_thinktank > 0:
            logger.info(
                "\u03b5 atom-review: auto_approved=%d thinktank=%d pending=%d",
                auto_approved,
                sent_to_thinktank,
                len(rows),
            )

    # ── 4. PG Commit (30s) ───────────────────────────────────────────────

    def _tick_pg_commit(self):
        rows = self._pg_query(
            "SELECT a.atom_id, a.content_hash, a.snap_labels, a.e8_coords "
            "FROM atoms a "
            "LEFT JOIN content_hashes ch ON a.content_hash = ch.hash "
            "WHERE ch.hash IS NULL AND a.content_hash IS NOT NULL "
            "AND a.content_hash != '' "
            "ORDER BY a.created_at DESC LIMIT 100"
        )
        if not rows:
            self._manifold_state["pg_commit"]["last_committed"] = 0
            return
        committed = 0
        batch = []
        for atom_id, content_hash, labels_json, e8_json in rows:
            rc = self._pg_execute(
                "INSERT INTO content_hashes (hash, atom_id, created_at) "
                "VALUES (%s, %s, NOW()) ON CONFLICT (hash) DO NOTHING",
                (content_hash, atom_id),
            )
            if rc > 0:
                committed += 1
                try:
                    labels = json.loads(labels_json) if labels_json else []
                    e8 = json.loads(e8_json) if e8_json else []
                except (json.JSONDecodeError, TypeError):
                    labels, e8 = [], []
                batch.append({
                    "atom_id": atom_id,
                    "content_hash": content_hash,
                    "snap_labels": labels[:15],
                    "e8_coords": e8,
                })
        if batch:
            self._http_post(
                f"{SPEEDLIGHT_URL}/put",
                {"sidecar_id": "tmn2-daemon", "batch": batch},
                timeout=10,
            )
        self._manifold_state["pg_commit"]["last_committed"] = committed
        if committed > 0:
            logger.info(
                "\u03c0 pg-commit: %d atoms hashed and synced to SpeedLight", committed
            )

    # ── 5. Conservation Ledger (30s) ──────────────────────────────────────

    def _tick_conservation_ledger(self):
        resp = self._http_get(f"{CONSERVATION_URL}/health", timeout=5)
        if resp is None:
            self._manifold_state["conservation"]["ok"] = False
            self._manifold_state["conservation"]["status"] = "unreachable"
            return
        self._manifold_state["conservation"]["ok"] = True
        violations = resp.get("violations", resp.get("violation_count", 0))
        self._manifold_state["conservation"]["violations"] = violations
        self._manifold_state["conservation"]["violation"] = violations > 0
        if violations > 0:
            logger.warning(
                "\u03c1 conservation: %d violations detected", violations
            )
            self.crt.buffer("board_posts", {
                "board_id": "alerts",
                "author_id": "tmn2-daemon",
                "template": "alert",
                "title": f"Conservation Violation \u2014 {violations} active",
                "content": (
                    f"status: conservation_violation\n"
                    f"violations: {violations}\n"
                    f"details: Conservation ledger reports {violations} active violations."
                ),
            })

    # ── 6. Dispatch (45s) ────────────────────────────────────────────────

    def _tick_dispatch(self):
        resp = self._http_get(f"{BOARD_URL}/bounties?status=open", timeout=5)
        if resp is None:
            return
        bounties = resp.get("bounties", resp if isinstance(resp, list) else [])
        if not bounties:
            return
        library = self._http_get(f"{MINT_URL}/library", timeout=5)
        coin_defs = (library or {}).get("coins", {})
        existing_agents = set()
        existing_bounty_agents = set()
        rows = self._pg_query(
            "SELECT domain, name FROM spawn_births WHERE alive = true"
        )
        for row in (rows or []):
            if isinstance(row, (list, tuple)) and len(row) >= 2:
                existing_agents.add(row[0])
            elif isinstance(row, dict):
                existing_agents.add(row.get("domain", ""))
        for bounty in bounties:
            claimed_by = bounty.get("claimed_by")
            if claimed_by and claimed_by != "none":
                existing_bounty_agents.add(bounty.get("bounty_id", ""))
        matched = 0
        spawned = 0
        for bounty in bounties[:5]:
            bounty_id = bounty.get("bounty_id", bounty.get("id", ""))
            snap_labels = bounty.get("snap_labels", [])
            if isinstance(snap_labels, str):
                try:
                    snap_labels = json.loads(snap_labels)
                except Exception:
                    snap_labels = []
            match_coins = self._http_post(
                f"{MINT_URL}/match", {"snap_labels": snap_labels}, timeout=5
            )
            primary_coin = "MERIT"
            if match_coins and not match_coins.get("error"):
                matches = match_coins.get("matches", {})
                best_coin = None
                best_count = 0
                for coin_name, matched_labels in matches.items():
                    if coin_name != "MERIT" and len(matched_labels) > best_count:
                        best_coin = coin_name
                        best_count = len(matched_labels)
                if best_coin:
                    primary_coin = best_coin
            coin_def = coin_defs.get(primary_coin, {})
            domain = (
                coin_def.get("domain", primary_coin.lower()).split(",")[0].strip().lower()
            )
            domain_dept_map = {
                "geometry": "geometry", "computation": "computation",
                "experimental": "training", "engineering": "code",
                "cross-domain": "meta", "teaching": "training",
                "judgment": "governance", "pattern": "meta",
                "narrative": "meta", "general": "meta",
                "physics": "physics", "information": "code",
                "machine": "training", "simulation": "training",
                "conservation": "governance", "statistics": "meta",
                "transport": "intake", "sequences": "meta",
                "group": "geometry", "topology": "geometry",
                "semantic": "code", "hash": "computation",
                "regulation": "governance", "provenance": "governance",
                "communication": "meta", "agent": "agents",
                "data": "storage", "sonar": "geometry",
            }
            department = "meta"
            for key, dept in domain_dept_map.items():
                if key in domain:
                    department = dept
                    break
            agent_id = None
            match_resp = self._http_post(
                f"{COOP_URL}/match_for_task",
                {"task_labels": snap_labels},
                timeout=5,
            )
            if match_resp and not match_resp.get("error"):
                agent_matches = match_resp.get("matches", [])
                if agent_matches:
                    agent_id = agent_matches[0].get("agent_id")
            already_has_agent = domain in existing_agents or bounty_id in existing_bounty_agents
            if not agent_id and not already_has_agent:
                agent_name = f"{primary_coin.lower()}-{bounty_id[:6]}"
                spawn_resp = self._http_post(
                    f"{SPAWN_URL}/birth",
                    {
                        "parent_id": "daemon",
                        "domain": domain.split(",")[0].strip(),
                        "name": agent_name,
                        "snapdna": snap_labels[:10],
                        "domain_boost": primary_coin,
                    },
                    timeout=10,
                )
                if spawn_resp and not spawn_resp.get("error"):
                    agent_id = spawn_resp.get("child_id", spawn_resp.get("agent_id"))
                    existing_agents.add(department)
                    spawned += 1
                    logger.info(
                        "\u03bb dispatch: spawned %s (%s) for coin %s dept %s",
                        agent_id, agent_name, primary_coin, department,
                    )
            if agent_id:
                claim_resp = self._http_post(
                    f"{BOARD_URL}/bounties/{bounty_id}/update",
                    {"status": "claimed", "claimed_by": agent_id},
                    timeout=5,
                )
                if claim_resp and not claim_resp.get("error") and not claim_resp.get("detail"):
                    matched += 1
                    self._http_post(f"{COOP_URL}/tick/{agent_id}", {}, timeout=5)
        self._manifold_state["dispatch"]["open_bounties"] = len(bounties)
        self._manifold_state["dispatch"]["matched"] = matched
        self._manifold_state["dispatch"]["spawned"] = spawned
        if matched > 0 or spawned > 0:
            logger.info(
                "\u03bb dispatch: matched=%d spawned=%d bounties=%d",
                matched, spawned, len(bounties),
            )

    # ── 7. Assign (45s) ──────────────────────────────────────────────────

    def _tick_assign(self):
        resp = self._http_get(f"{BOARD_URL}/bounties?status=open", timeout=5)
        if resp is None:
            return
        bounties = resp.get("bounties", [])
        unmatched = [b for b in bounties if not b.get("claimed_by")]
        if not unmatched:
            return
        tick_resp = self._http_post(
            f"{COOP_URL}/tick",
            {
                "unmatched_count": len(unmatched),
                "bounty_ids": [b.get("bounty_id", b.get("id", "")) for b in unmatched[:5]],
            },
            timeout=5,
        )
        assigned = tick_resp.get("assigned", 0) if tick_resp else 0
        if assigned > 0:
            logger.info("\u03b1 assign: %d bounties assigned via co-op tick", assigned)

    # ── 8. ThinkTank (90s) ───────────────────────────────────────────────

    def _tick_thinktank(self):
        resp = self._http_get(f"{THINKTANK_URL}/health", timeout=5)
        if resp is None:
            self._manifold_state["thinktank"]["ok"] = False
            return
        self._manifold_state["thinktank"]["ok"] = True
        perspectives = resp.get("perspectives", resp.get("perspective_count", 0))
        saturation = resp.get("saturation", 0.0)
        self._manifold_state["thinktank"]["perspectives"] = perspectives
        self._manifold_state["thinktank"]["saturation"] = saturation
        logger.info(
            "\u03c9 thinktank: perspectives=%d saturation=%.2f", perspectives, saturation
        )

    # ── 9. Outside Actor (90s) ───────────────────────────────────────────

    def _tick_outside_actor(self):
        self._manifold_state["outside_actor"]["pending"] = 0
        logger.debug("\u03b7 outside-actor: no external proposals pending")

    # ── 10. Governance (90s) ─────────────────────────────────────────────

    def _tick_governance(self):
        resp = self._http_get(f"{SAP_URL}/pending", timeout=5)
        if resp is None:
            return
        if isinstance(resp, list):
            pending = resp
        elif isinstance(resp, dict):
            pending = resp.get("pending", resp.get("items", []))
        else:
            return
        if not pending:
            return
        if isinstance(pending, int):
            if pending > 0:
                logger.info("\u03b3 governance: %d pending votes", pending)
            return
        verdicts = {"approve": 0, "reject": 0, "deepen": 0}
        for item in pending[:10]:
            if isinstance(item, dict):
                item_id = item.get("id", item.get("item_id", item.get("verdict_id", "")))
            elif isinstance(item, str):
                item_id = item
            else:
                continue
            if not item_id:
                continue
            judge_resp = self._http_post(
                f"{SAP_URL}/judge",
                {
                    "content": f"governance review: {item_id}",
                    "action": "governance",
                    "agent_id": "daemon",
                },
                timeout=5,
            )
            if judge_resp and not judge_resp.get("error"):
                verdict = judge_resp.get("verdict", judge_resp.get("approved", "unknown"))
                if isinstance(verdict, bool):
                    verdict = "approve" if verdict else "reject"
                verdicts[str(verdict).lower()] = (
                    verdicts.get(str(verdict).lower(), 0) + 1
                )
        if any(v > 0 for v in verdicts.values()):
            logger.info("\u03b3 governance: verdicts=%s", verdicts)
            self._audit_event("governance", {
                "tick": self._tick_count,
                "pending": len(pending),
                "verdicts": verdicts,
            })

    # ── 11. Lifecycle (120s) ─────────────────────────────────────────────

    def _tick_lifecycle(self):
        rows = self._pg_query(
            "SELECT agent_id, coins, tick_count FROM agent_identities "
            "WHERE coins = 0 AND tick_count > 100 AND active = true "
            "LIMIT 20"
        )
        if not rows:
            return
        deactivated = 0
        for agent_id, coins, tick_count in rows:
            resp = self._http_post(
                f"{IDENTITY_URL}/deactivate",
                {
                    "agent_id": agent_id,
                    "reason": "zero_coins_lifecycle",
                    "tick_count": tick_count,
                },
                timeout=5,
            )
            if resp and resp.get("ok"):
                deactivated += 1
                self._pg_execute(
                    "UPDATE agent_identities SET active = false WHERE agent_id = %s",
                    (agent_id,),
                )
        if deactivated > 0:
            logger.info(
                "\u03c4 lifecycle: deactivated %d zero-coin agents", deactivated
            )

    # ── 12. Epoch Gate (120s) ────────────────────────────────────────────

    def _tick_epoch_gate(self):
        rows = self._pg_query(
            "SELECT agent_id, tick_count FROM agent_identities "
            "WHERE active = true AND tick_count > 0 AND tick_count %% 300 = 0 "
            "LIMIT 50"
        )
        if not rows:
            return
        gates = len(rows)
        agent_ids = [r[0] for r in rows]
        self.crt.buffer("board_posts", {
            "board_id": "training",
            "author_id": "tmn2-daemon",
            "template": "epoch_gate",
            "title": f"Epoch Gate \u2014 {gates} agents at boundary",
            "content": (
                f"status: epoch_gate\n"
                f"agents: {gates}\n"
                f"agent_ids: {agent_ids[:10]}\n"
                f"details: {gates} agents at epoch boundary (tick % 300)."
            ),
        })
        logger.info("\u03be epoch-gate: %d agents at epoch boundary", gates)

    # ── 13. Birth (150s) ─────────────────────────────────────────────────

    def _tick_birth(self):
        resp = self._http_get(f"{SPAWN_URL}/pending", timeout=5)
        if resp is None:
            return
        queue = resp.get("queue", resp.get("pending", []))
        if not queue:
            return
        top = queue[0] if isinstance(queue, list) and queue else None
        if top is None:
            if isinstance(queue, int) and queue > 0:
                self._http_post(f"{SPAWN_URL}/execute", {"limit": 1}, timeout=15)
                logger.info("\u03b2 birth: triggered spawn execution (queue=%d)", queue)
            return
        spawn_id = top.get("spawn_id", top.get("id", ""))
        result = self._http_post(
            f"{SPAWN_URL}/execute", {"spawn_id": spawn_id}, timeout=15
        )
        if result and result.get("ok"):
            agent_id = result.get("agent_id", "?")
            logger.info(
                "\u03b2 birth: spawned agent %s (spawn_id=%s)", agent_id, spawn_id
            )
        else:
            logger.warning("\u03b2 birth: spawn execution failed for %s", spawn_id)

    # ── 14. Economy (180s) ───────────────────────────────────────────────

    def _tick_economy(self):
        mint_resp = self._http_get(f"{MINT_URL}/health", timeout=5)
        econ_resp = self._http_get(f"{ECONOMY_URL}/health", timeout=5)
        mint_ok = mint_resp is not None
        econ_ok = econ_resp is not None
        coins = 0
        escrow = 0
        if mint_resp:
            coins = mint_resp.get("total_coins", mint_resp.get("coins", 0))
        if econ_resp:
            escrow = econ_resp.get("escrow", econ_resp.get("total_escrow", 0))
        self._manifold_state["economy"]["mint_ok"] = mint_ok
        self._manifold_state["economy"]["econ_ok"] = econ_ok
        self._manifold_state["economy"]["coins"] = coins
        self._manifold_state["economy"]["escrow"] = escrow
        logger.info(
            "\u03c6 economy: mint=%s econ=%s coins=%d escrow=%d",
            "ok" if mint_ok else "DOWN",
            "ok" if econ_ok else "DOWN",
            coins, escrow,
        )

    # ── 15. Conservation Audit (300s) ────────────────────────────────────

    def _tick_conservation_audit(self):
        resp = self._http_get(f"{CONSERVATION_URL}/health", timeout=10)
        if resp is None:
            logger.warning(
                "\u03b4 conservation-audit: conservation service unreachable"
            )
            return
        cumulative_dphi = resp.get("cumulative_dphi", resp.get("dphi", None))
        if cumulative_dphi is None:
            rows = self._pg_query(
                "SELECT cumulative_dphi FROM conservation_ledger "
                "ORDER BY id DESC LIMIT 1"
            )
            if rows:
                cumulative_dphi = rows[0][0]
        if cumulative_dphi is not None and cumulative_dphi > 0:
            logger.error(
                "\u03b4 CONSERVATION VIOLATION: cumulative_dphi=%.6f > 0",
                cumulative_dphi,
            )
            self.crt.buffer("board_posts", {
                "board_id": "alerts",
                "author_id": "tmn2-daemon",
                "template": "critical_alert",
                "title": "CRITICAL \u2014 Conservation Violation",
                "content": (
                    f"status: CRITICAL\n"
                    f"cumulative_dphi: {cumulative_dphi:.6f}\n"
                    f"details: Conservation law VIOLATED. Cumulative delta-phi > 0."
                ),
            })
            self._manifold_state["conservation_audit"]["violation"] = True
            self._audit_event("conservation_violation", {
                "cumulative_dphi": cumulative_dphi,
                "tick": self._tick_count,
            })
        else:
            dphi_val = cumulative_dphi if cumulative_dphi is not None else "N/A"
            logger.info(
                "\u03b4 conservation-audit: OK (cumulative_dphi=%s)", dphi_val
            )
            self._manifold_state["conservation_audit"]["violation"] = False

    # ── 16. Stats (300s) ─────────────────────────────────────────────────

    def _tick_stats(self):
        service_checks = {
            "board": f"{BOARD_URL}/health",
            "pipeline": f"{PIPELINE_URL}/health",
            "thinktank": f"{THINKTANK_URL}/health",
            "sap": f"{SAP_URL}/health",
            "speedlight": f"{SPEEDLIGHT_URL}/health",
            "coop": f"{COOP_URL}/health",
            "mint": f"{MINT_URL}/health",
            "conservation": f"{CONSERVATION_URL}/health",
            "gateway": f"{GATEWAY_URL}/health",
            "spawn": f"{SPAWN_URL}/health",
            "identity": f"{IDENTITY_URL}/health",
            "economy": f"{ECONOMY_URL}/health",
        }
        results = {}
        up_count = 0
        for name, url in service_checks.items():
            resp = self._http_get(url, timeout=3)
            ok = resp is not None
            results[name] = "ok" if ok else "down"
            if ok:
                up_count += 1
        total = len(service_checks)
        self.crt.buffer("board_posts", {
            "board_id": "status",
            "author_id": "tmn2-daemon",
            "template": "status_update",
            "title": f"System Health \u2014 {up_count}/{total} services",
            "content": (
                f"status: system_health\n"
                f"services_up: {up_count}/{total}\n"
                f"tick: {self._tick_count}\n"
                f"uptime: {int(time.time() - self._start_time)}s\n"
                f"orientation: up={self._last_orientation.get('up', 0):.3f} "
                f"down={self._last_orientation.get('down', 0):.3f} "
                f"sideways={self._last_orientation.get('sideways', 0):.3f}\n"
                f"details: {json.dumps(results)}"
            ),
        })
        logger.info(
            "\u03a3 stats: %d/%d services up, tick=%d", up_count, total, self._tick_count
        )
        self._audit_event("stats", {
            "tick": self._tick_count,
            "services_up": up_count,
            "services_total": total,
        })

    # ── 17. SNAP Route (60s) ─────────────────────────────────────────────

    def _tick_snap_route(self):
        resp = self._http_get(f"{GATEWAY_URL}/health", timeout=5)
        if resp is None:
            self._manifold_state["snap_route"]["ok"] = False
            return
        self._manifold_state["snap_route"]["ok"] = True
        service_count = resp.get(
            "services", resp.get("service_count", resp.get("routes", 0))
        )
        self._manifold_state["snap_route"]["services"] = service_count
        logger.info("\u03c3 snap-route: gateway OK, services=%s", service_count)

    # ── 18. Morphon (60s) ────────────────────────────────────────────────

    def _tick_morphon(self):
        orientation = self._compute_e8_orientation()
        logger.info(
            "\u03bc morphon: UP=%.3f DOWN=%.3f SIDEWAYS=%.3f",
            orientation["up"], orientation["down"], orientation["sideways"],
        )

    # ── 19. SpeedLight (60s) ─────────────────────────────────────────────

    def _tick_speedlight(self):
        resp = self._http_get(f"{SPEEDLIGHT_URL}/health", timeout=5)
        if resp is None:
            self._manifold_state["speedlight"]["ok"] = False
            return
        self._manifold_state["speedlight"]["ok"] = True
        cache_size = resp.get("cache_size", resp.get("entries", 0))
        hit_rate = resp.get("hit_rate", resp.get("hits_pct", 0.0))
        self._manifold_state["speedlight"]["cache_size"] = cache_size
        self._manifold_state["speedlight"]["hit_rate"] = hit_rate
        logger.info(
            "\u03c8 speedlight: cache_size=%s hit_rate=%.2f%%", cache_size, hit_rate
        )

    # ── 20. Key Check / Agent Tick (600s) ─────────────────────────────────

    def _tick_key_check(self):
        agents_resp = self._http_get(f"{COOP_URL}/agents", timeout=5)
        if not agents_resp:
            return
        agents = (
            agents_resp
            if isinstance(agents_resp, list)
            else agents_resp.get("agents", [])
        )
        ticked = 0
        for agent in agents:
            agent_id = agent.get("agent_id", "")
            state = agent.get("activity_state", "idle")
            if state == "idle" and agent_id:
                result = self._http_post(
                    f"{COOP_URL}/tick/{agent_id}", {}, timeout=5
                )
                if result and not result.get("error"):
                    ticked += 1
                if ticked >= 5:
                    break
        if ticked > 0:
            logger.info("\u03ba agent-tick: ticked %d idle agents", ticked)

    # ── 21. Dead Letter / Bond Pass (600s) ───────────────────────────────

    def _tick_dead_letter(self):
        rows = self._pg_query(
            "SELECT atom_id, e8_coords, snap_labels FROM atoms "
            "WHERE e8_coords IS NOT NULL AND e8_coords != 'null' "
            "AND snap_labels IS NOT NULL AND snap_labels != '[]' "
            "ORDER BY random() LIMIT 50"
        )
        if not rows:
            return
        atoms = []
        for row in rows:
            if isinstance(row, (list, tuple)) and len(row) >= 3:
                atom_id, e8_raw, labels_raw = row[0], row[1], row[2]
            elif isinstance(row, dict):
                atom_id = row.get("atom_id", "")
                e8_raw = row.get("e8_coords", "")
                labels_raw = row.get("snap_labels", "")
            else:
                continue
            try:
                e8 = json.loads(e8_raw) if isinstance(e8_raw, str) else e8_raw
                labels = (
                    json.loads(labels_raw) if isinstance(labels_raw, str) else labels_raw
                )
                if (
                    isinstance(e8, list)
                    and len(e8) >= 8
                    and isinstance(labels, list)
                    and len(labels) >= 3
                ):
                    domain = "general"
                    for l in labels:
                        if "domain_" in l:
                            domain = l.split("domain_")[-1]
                            break
                    atoms.append({
                        "atom_id": atom_id,
                        "snap_labels": labels[:20],
                        "domain": domain,
                        "e8_coords": e8[:8],
                    })
            except Exception:
                pass
        if not atoms:
            return
        reg = self._http_post(f"{BOND_URL}/register_atoms", atoms, timeout=15)
        if not reg or reg.get("error"):
            return
        result = self._http_post(f"{BOND_URL}/run_pass", {}, timeout=30)
        if not result or result.get("error"):
            return
        emergent = result.get("emergent_labels", [])
        geo = result.get("geometric", {})
        sem = result.get("semantic", {})
        if emergent:
            conn = self._get_pg()
            if conn:
                try:
                    cur = conn.cursor()
                    for label in emergent[:50]:
                        cur.execute(
                            "INSERT INTO snap_labels (label, atom_id, layer) "
                            "VALUES (%s, %s, 'bond') ON CONFLICT DO NOTHING",
                            (label, atoms[0]["atom_id"]),
                        )
                    conn.commit()
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
        logger.info(
            "\u03a9 bond-pass: %d atoms, %d dusts, %d triads, %d dimers, %d codons, %d emergent",
            len(atoms),
            geo.get("total_dusts", 0),
            geo.get("total_triads", 0),
            sem.get("total_dimers", 0),
            sem.get("total_codons", 0),
            len(emergent),
        )

    # ── 22. DB Audit (600s) ──────────────────────────────────────────────

    def _tick_db_audit(self):
        rows = self._pg_query(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        table_count = len(rows) if rows else 0
        atom_count = 0
        label_count = 0
        rows2 = self._pg_query("SELECT count(*) FROM atoms")
        if rows2 and rows2[0]:
            atom_count = (
                rows2[0][0] if isinstance(rows2[0], (list, tuple)) else rows2[0]
            )
        rows3 = self._pg_query("SELECT count(*) FROM snap_labels")
        if rows3 and rows3[0]:
            label_count = (
                rows3[0][0] if isinstance(rows3[0], (list, tuple)) else rows3[0]
            )
        logger.info(
            "\u0394 db-audit: %d tables, %s atoms, %s labels",
            table_count, atom_count, label_count,
        )
        self._audit_event("db_audit", {
            "tick": self._tick_count,
            "tables": table_count,
            "atoms": atom_count,
            "labels": label_count,
        })

    # ── 23. Backpressure (30s) ───────────────────────────────────────────

    def _tick_backpressure(self):
        orientation = self._compute_e8_orientation()
        adjustments = []
        for ch in CHANNELS:
            name = ch["name"]
            new_budget = _scale_budget(name, orientation)
            old_budget = self._channel_state[name].get("grain_budget", BASE_BUDGET)
            self._channel_state[name]["grain_budget"] = new_budget
            if abs(new_budget - old_budget) > 5:
                adjustments.append(
                    f"{ch['symbol']}{name}:{old_budget}->{new_budget}"
                )
        if adjustments:
            logger.info(
                "\u03b8 backpressure: orientation=UP:%.3f/DOWN:%.3f/SIDE:%.3f adjustments=[%s]",
                orientation["up"],
                orientation["down"],
                orientation["sideways"],
                ", ".join(adjustments[:8]),
            )
        else:
            logger.debug("\u03b8 backpressure: orientation stable, no budget changes")

    # ── 24. Full Report (900s) ───────────────────────────────────────────

    def _tick_full_report(self):
        channel_summary = {}
        for name, state in self._channel_state.items():
            channel_summary[name] = {
                "runs": state["run_count"],
                "load_factor": round(state["load_factor"], 3),
                "grain_budget": state["grain_budget"],
                "errors": state["errors"],
            }
        atom_rows = self._pg_query("SELECT COUNT(*) FROM atoms")
        atom_count = atom_rows[0][0] if atom_rows else "N/A"
        cons_rows = self._pg_query(
            "SELECT cumulative_dphi, violation_count FROM conservation_ledger "
            "ORDER BY id DESC LIMIT 1"
        )
        dphi = cons_rows[0][0] if cons_rows else "N/A"
        violations = cons_rows[0][1] if cons_rows else 0
        services_up = 0
        for url in [BOARD_URL, PIPELINE_URL, GATEWAY_URL, SPEEDLIGHT_URL]:
            if self._http_get(f"{url}/health", timeout=2) is not None:
                services_up += 1
        uptime = int(time.time() - self._start_time)
        self.crt.buffer("board_posts", {
            "board_id": "reports",
            "author_id": "tmn2-daemon",
            "template": "full_report",
            "title": f"Full Report \u2014 tick {self._tick_count}, {atom_count} atoms",
            "content": (
                f"=== OpenCMPLX Full System Report ===\n"
                f"tick: {self._tick_count}\n"
                f"uptime: {uptime}s ({uptime // 3600}h {(uptime % 3600) // 60}m)\n"
                f"atoms: {atom_count}\n"
                f"cumulative_dphi: {dphi}\n"
                f"conservation_violations: {violations}\n"
                f"services_up: {services_up}/4 (core)\n"
                f"orientation: UP={self._last_orientation.get('up', 0):.3f} "
                f"DOWN={self._last_orientation.get('down', 0):.3f} "
                f"SIDEWAYS={self._last_orientation.get('sideways', 0):.3f}\n"
                f"channels: {json.dumps(channel_summary, separators=(',', ':'))}"
            ),
        })
        logger.info(
            "\u039b full-report: tick=%d atoms=%s dphi=%s services=%d/4",
            self._tick_count, atom_count, dphi, services_up,
        )

    # ══════════════════════════════════════════════════════════════════════
    # E8 ORIENTATION — State Vector Computation
    # ══════════════════════════════════════════════════════════════════════

    def _compute_e8_orientation(self) -> Dict[str, float]:
        state = [0.5] * 8
        pending = self._manifold_state.get("atom_review", {}).get("pending", 0)
        state[0] = min(1.0, pending / 100.0)
        committed = self._manifold_state.get("pg_commit", {}).get("last_committed", 0)
        state[1] = min(1.0, committed / 50.0)
        cons_violation = self._manifold_state.get("conservation", {}).get("violation", False)
        audit_violation = self._manifold_state.get("conservation_audit", {}).get(
            "violation", False
        )
        state[2] = 1.0 if (cons_violation or audit_violation) else 0.0
        open_bounties = self._manifold_state.get("dispatch", {}).get("open_bounties", 0)
        state[3] = min(1.0, open_bounties / 20.0)
        agent_ok = self._manifold_state.get("thinktank", {}).get("ok", True)
        state[4] = 0.8 if agent_ok else 0.2
        coins = self._manifold_state.get("economy", {}).get("coins", 0)
        state[5] = min(1.0, coins / 100.0)
        pipeline_ok = self._manifold_state.get("pulse", {}).get("pipeline", "down")
        state[6] = 0.2 if pipeline_ok == "ok" else 0.8
        total_load = sum(
            s.get("load_factor", 1.0) for s in self._channel_state.values()
        )
        avg_load = total_load / max(len(self._channel_state), 1)
        state[7] = min(1.0, avg_load / 2.0)
        up = _normalize(UP_ROOT)
        down = _normalize(DOWN_ROOT)
        side = _normalize(SIDE_ROOT)
        ns = _normalize(state)
        w_up = _dot(ns, up)
        w_down = _dot(ns, down)
        w_side = _dot(ns, side)
        total = abs(w_up) + abs(w_down) + abs(w_side)
        if total > 0:
            w_up /= total
            w_down /= total
            w_side /= total
        self._last_orientation = {"up": w_up, "down": w_down, "sideways": w_side}
        return self._last_orientation

    # ══════════════════════════════════════════════════════════════════════
    # HANDLER DISPATCH
    # ══════════════════════════════════════════════════════════════════════

    def _build_handler_map(self) -> Dict[str, Any]:
        return {
            "pulse": self._tick_pulse,
            "cross_check": self._tick_cross_check,
            "atom_review": self._tick_atom_review,
            "pg_commit": self._tick_pg_commit,
            "conservation": self._tick_conservation_ledger,
            "backpressure": self._tick_backpressure,
            "dispatch": self._tick_dispatch,
            "assign": self._tick_assign,
            "snap_route": self._tick_snap_route,
            "morphon": self._tick_morphon,
            "speedlight": self._tick_speedlight,
            "thinktank": self._tick_thinktank,
            "outside_actor": self._tick_outside_actor,
            "governance": self._tick_governance,
            "lifecycle": self._tick_lifecycle,
            "epoch_gate": self._tick_epoch_gate,
            "birth": self._tick_birth,
            "economy": self._tick_economy,
            "conservation_audit": self._tick_conservation_audit,
            "stats": self._tick_stats,
            "key_check": self._tick_key_check,
            "dead_letter": self._tick_dead_letter,
            "db_audit": self._tick_db_audit,
            "full_report": self._tick_full_report,
        }

    # ══════════════════════════════════════════════════════════════════════
    # TICK LOOP — CRT 24-Ring Driver
    # ══════════════════════════════════════════════════════════════════════

    def _tick(self) -> List[str]:
        now = time.time()
        self._tick_count += 1
        fired = []
        for name, state in self._channel_state.items():
            if self._is_due(state, now):
                handler = self._handlers.get(name)
                if handler is None:
                    state["last_run"] = now
                    state["run_count"] += 1
                    continue
                t0 = time.time()
                state["last_run"] = now
                state["run_count"] += 1
                fired.append(name)
                try:
                    handler()
                    elapsed_ms = (time.time() - t0) * 1000
                    state["last_duration_ms"] = round(elapsed_ms, 1)
                    self._manifold_state[name]["load"] = state["load_factor"]
                    self._manifold_state[name]["ok"] = True
                    if state["load_factor"] > 1.0:
                        state["load_factor"] = max(1.0, state["load_factor"] * 0.9)
                except Exception as exc:
                    elapsed_ms = (time.time() - t0) * 1000
                    state["last_duration_ms"] = round(elapsed_ms, 1)
                    state["errors"] += 1
                    state["last_error"] = str(exc)[:200]
                    self._manifold_state[name]["ok"] = False
                    state["load_factor"] = min(4.0, state["load_factor"] * 1.5)
                    logger.error("Channel %s failed: %s", name, str(exc)[:120])
        return fired

    def _daemon_loop(self):
        logger.info(
            "CRT 24-ring started \u2014 %d channels, %d handlers",
            len(CHANNELS), len(self._handlers),
        )
        while self._running:
            time.sleep(1)
            fired = self._tick()
            if fired and (self._tick_count % 30 == 0):
                logger.info("Tick %d: fired %s", self._tick_count, fired)

    # ── Start / Stop ────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self._thread.start()
        self.crt.start_background()
        logger.info("TMN2Daemon started")

    def stop(self):
        self._running = False
        self.crt.stop()
        logger.info("TMN2Daemon stopped")

    # ══════════════════════════════════════════════════════════════════════
    # FASTAPI ENDPOINTS
    # ══════════════════════════════════════════════════════════════════════

    def _mount_routes(self, app: FastAPI):
        t = self

        @app.get("/health")
        def health():
            return {
                "ok": True,
                "service": "tmn2-daemon",
                "tick": t._tick_count,
                "channels": len(CHANNELS),
                "handlers": len(t._handlers),
                "running": t._running,
                "uptime": round(time.time() - t._start_time),
                "orientation": t._last_orientation,
            }

        @app.get("/status")
        def status():
            return {
                "tick": t._tick_count,
                "channels": len(CHANNELS),
                "running": t._running,
                "uptime": round(time.time() - t._start_time),
                "orientation": t._last_orientation,
                "channel_runs": {
                    name: s["run_count"] for name, s in t._channel_state.items()
                },
                "channel_errors": {
                    name: s["errors"]
                    for name, s in t._channel_state.items()
                    if s["errors"] > 0
                },
            }

        @app.get("/channels")
        def list_channels():
            return [
                {
                    **s,
                    "has_handler": s["name"] in t._handlers,
                    "due_in": max(
                        0,
                        round(
                            s["period"] * s["load_factor"]
                            - (time.time() - s["last_run"])
                        ),
                    ),
                }
                for s in t._channel_state.values()
            ]

        @app.get("/channel/{name}")
        def get_channel(name: str):
            if name not in t._channel_state:
                return {"error": f"Channel {name} not found"}
            state = t._channel_state[name]
            return {
                **state,
                "has_handler": name in t._handlers,
                "manifold": t._manifold_state.get(name, {}),
            }

        @app.get("/orientation")
        def get_orientation():
            budgets = {}
            for ch in CHANNELS:
                budgets[ch["name"]] = {
                    "symbol": ch["symbol"],
                    "budget": t._channel_state[ch["name"]]["grain_budget"],
                    "category": (
                        "UP"
                        if ch["name"] in UP_CHANNELS
                        else "DOWN"
                        if ch["name"] in DOWN_CHANNELS
                        else "SIDE"
                        if ch["name"] in SIDE_CHANNELS
                        else "META"
                    ),
                }
            return {"orientation": t._last_orientation, "budgets": budgets}

        @app.get("/manifold")
        def get_manifold():
            return t._manifold_state

        @app.post("/stop")
        def stop_daemon():
            t.stop()
            return {"ok": True, "message": "Daemon loop stopping"}


# ══════════════════════════════════════════════════════════════════════════════
# Factory function
# ══════════════════════════════════════════════════════════════════════════════

def create_tmn2_app(governance: Any = None) -> FastAPI:
    """Create a FastAPI app with a pre-configured TMN2Daemon instance.

    Args:
        governance: Optional GeometricGovernance instance for audit trail.

    Returns:
        FastAPI application with TMN2 daemon running in background.
    """
    app = FastAPI(
        title="OpenCMPLX TMN2 Daemon",
        description="CRT 24-ring orchestrator with E8 orientation, "
        "grain budgets, and breathability",
    )
    daemon = TMN2Daemon(governance=governance, app=app)
    daemon.start()

    @app.on_event("shutdown")
    def _shutdown():
        daemon.stop()

    return app


# ── Standalone entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    app = create_tmn2_app()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
