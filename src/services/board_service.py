"""BoardService — Bulletin board system. Posts are atoms. Boards are SNAP clusters."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import urllib.request as _urllib_req
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from governance.engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("board_service")

_host = "host.docker.internal"

PG_URL = os.environ.get("PG_URL", f"postgresql://tmn2:tmn2_dev@{_host}:5432/tmn2")
PIPELINE_URL = os.environ.get("PIPELINE_URL", f"http://{_host}:8001")
MINT_URL = os.environ.get("MINT_URL", "")
COUPLING = float(os.environ.get("COUPLING", "0.030076"))

_SYSTEM_BOARDS: List[Dict[str, Any]] = [
    {"board_id": "status", "snap_filter": ["type.state_delta", "op.heartbeat"], "description": "System status and state deltas"},
    {"board_id": "findings", "snap_filter": ["op.discover", "domain.research"], "description": "Work findings and discoveries"},
    {"board_id": "work", "snap_filter": ["op.work", "type.work_result"], "description": "Active work results and outputs"},
    {"board_id": "bounties", "snap_filter": ["type.bounty"], "description": "Open bounties and requests"},
    {"board_id": "journals", "snap_filter": ["type.journal", "op.reflect"], "description": "Agent journals and reflections"},
    {"board_id": "dead-letter", "snap_filter": ["class.error", "op.fail", "type.dead_letter"], "description": "Failed/unroutable atoms"},
    {"board_id": "taxonomy", "snap_filter": ["meta.type_system", "meta.family_def", "meta.class_def", "meta.ontology"], "description": "Type system self-description"},
    {"board_id": "crystal-relay", "snap_filter": ["class.crystal"], "description": "Crystal records"},
    {"board_id": "expert-pool", "snap_filter": ["class.expert"], "description": "Expert agent pool"},
    {"board_id": "solve-corpus", "snap_filter": ["class.solve.verified", "class.solve.corpus_ready"], "description": "Verified/corpus-ready solves"},
    {"board_id": "templates", "snap_filter": ["class.template"], "description": "Reusable templates"},
    {"board_id": "geometry", "snap_filter": ["domain.geometry", "domain.e8", "SNAPdomain_geometry"], "description": "Geometry and lattice work"},
    {"board_id": "agent-work", "snap_filter": ["domain.agent", "role.", "SNAPdomain_agent"], "description": "Agent lifecycle events"},
    {"board_id": "economy", "snap_filter": ["domain.economics", "op.mint", "op.earn", "op.spend", "SNAPdomain_economy"], "description": "Economy and coin events"},
    {"board_id": "governance", "snap_filter": ["domain.governance", "SNAPdomain_governance"], "description": "Governance votes, quorums, policy"},
    {"board_id": "formalization", "snap_filter": ["SNAPformal_", "domain.formal", "type.proof"], "description": "Formal proofs and mathematical structures"},
    {"board_id": "meta-analysis", "snap_filter": ["SNAPmeta_", "type.meta", "op.analyze"], "description": "Meta-analysis, system introspection"},
    {"board_id": "operations", "snap_filter": ["SNAPop_", "op.deploy", "op.build"], "description": "Operational events"},
    {"board_id": "training", "snap_filter": ["domain.training", "op.train"], "description": "Training loop activity"},
]

SNAP_BOARD_ROUTES: Dict[str, str] = {
    "SNAPdomain_geometry": "geometry", "SNAPdomain_agent": "agent-work",
    "SNAPdomain_economy": "economy", "SNAPdomain_governance": "governance",
    "SNAPdomain_training": "training", "SNAPdomain_code": "work",
    "SNAPformal_": "formalization", "SNAPmeta_": "meta-analysis",
    "SNAPop_": "operations", "class.error": "dead-letter",
    "class.crystal": "crystal-relay", "class.expert": "expert-pool",
    "class.solve.verified": "solve-corpus", "class.solve.corpus_ready": "solve-corpus",
    "class.template": "templates", "meta.type_system": "taxonomy",
    "meta.family_def": "taxonomy", "meta.class_def": "taxonomy",
    "meta.ontology": "taxonomy", "domain.geometry": "geometry",
    "domain.e8": "geometry", "domain.agent": "agent-work",
    "domain.economics": "economy", "domain.governance": "governance",
    "domain.training": "training", "domain.code": "work",
    "domain.research": "findings", "op.discover": "findings",
    "op.question": "findings", "op.mint": "economy",
    "op.earn": "economy", "op.spend": "economy",
    "op.register": "agent-work", "op.train": "training",
    "op.deploy": "operations", "op.build": "operations",
    "op.fail": "dead-letter", "op.reflect": "journals",
    "op.heartbeat": "status", "type.bounty": "bounties",
    "type.fulfillment": "bounties", "type.journal": "journals",
    "type.state_delta": "status", "type.system": "status",
    "type.dead_letter": "dead-letter", "type.proof": "formalization",
    "type.meta": "meta-analysis", "type.work_result": "work",
    "role.": "agent-work", "family.intake": "work",
}

_TEMPLATE_BOARD: Dict[str, str] = {
    "bounty": "bounties", "fulfillment": "bounties",
    "finding": "findings", "question": "findings",
    "state_delta": "status", "register": "agent-work",
    "journal": "journals", "freeform": "work",
}

_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "finding": {"coins": ["CURIE", "SNAP"], "scale": "normal"},
    "work_result": {"coins": ["TURING", "SNAP"], "scale": "normal"},
    "bounty_result": {"coins": ["AGENT", "MERIT"], "scale": "major"},
    "journal": {"coins": ["MYTHOS", "SNAP"], "scale": "normal"},
    "status_update": {"coins": ["AGENT"], "scale": "micro"},
    "freeform": {"coins": ["SNAP"], "scale": "micro"},
}

_TIER_THRESHOLDS: Dict[str, float] = {
    "corpus_ready": 0.80, "verified": 0.55, "indexed": 0.25,
}


class ThreadRequest:
    def __init__(self, board_id: str = "work", title: str = "", author_id: str = "",
                 content: str = "", template: str = "freeform", tags: List[str] = None,
                 snap_labels: List[str] = None, parent_id: str = None, epoch: int = 0):
        self.board_id = board_id
        self.title = title
        self.author_id = author_id
        self.content = content
        self.template = template
        self.tags = tags or []
        self.snap_labels = snap_labels or []
        self.parent_id = parent_id
        self.epoch = epoch


class BoardService:
    """Bulletin board system — semantic atom relay with PG persistence."""

    def __init__(self, governance: Optional[GeometricGovernance] = None):
        self.governance = governance
        self._pg_local = threading.local()
        self._db_ready = False

    def _get_pg(self):
        conn = getattr(self._pg_local, "conn", None)
        if conn is not None:
            try:
                conn.cursor().execute("SELECT 1")
                return conn
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
        conn = psycopg2.connect(PG_URL, cursor_factory=RealDictCursor)
        conn.autocommit = False
        self._pg_local.conn = conn
        return conn

    def _init_db(self):
        if self._db_ready:
            return
        _SCHEMA = [
            """CREATE TABLE IF NOT EXISTS board_posts (
                atom_id TEXT PRIMARY KEY, board_id TEXT NOT NULL DEFAULT 'work',
                board_ids TEXT[] DEFAULT ARRAY[]::TEXT[], author_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '', content TEXT NOT NULL DEFAULT '',
                template TEXT DEFAULT 'freeform', tags JSONB DEFAULT '[]',
                snap_labels JSONB DEFAULT '[]', parent_id TEXT DEFAULT '',
                vote_score INTEGER DEFAULT 0, status TEXT DEFAULT 'active',
                e8_coords JSONB DEFAULT '[]', mdhg_address TEXT DEFAULT '',
                morphon_z DOUBLE PRECISION DEFAULT 0.0, delta_phi DOUBLE PRECISION DEFAULT 0.0,
                quality_score DOUBLE PRECISION DEFAULT 0.0, quality_tier TEXT DEFAULT 'raw',
                bond_count INTEGER DEFAULT 0, view_count INTEGER DEFAULT 0,
                receipt_hash TEXT DEFAULT '', created_at DOUBLE PRECISION NOT NULL,
                updated_at DOUBLE PRECISION)""",
            "CREATE INDEX IF NOT EXISTS idx_bp_board ON board_posts(board_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_bp_author ON board_posts(author_id)",
            "CREATE INDEX IF NOT EXISTS idx_bp_status ON board_posts(status)",
            "CREATE INDEX IF NOT EXISTS idx_bp_parent ON board_posts(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_bp_template ON board_posts(template)",
            "CREATE INDEX IF NOT EXISTS idx_bp_tier ON board_posts(quality_tier)",
            "CREATE INDEX IF NOT EXISTS idx_bp_score ON board_posts(quality_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_bp_bonds ON board_posts(bond_count DESC)",
            """CREATE TABLE IF NOT EXISTS board_bounties (
                bounty_id TEXT PRIMARY KEY, board_id TEXT NOT NULL DEFAULT 'bounties',
                requested_by TEXT NOT NULL, need TEXT NOT NULL, context TEXT DEFAULT '',
                blocking TEXT DEFAULT '', snap_labels JSONB DEFAULT '[]',
                reward_coins DOUBLE PRECISION DEFAULT 0.0, status TEXT DEFAULT 'open',
                assigned_to TEXT DEFAULT '', claimed_at DOUBLE PRECISION,
                resolved_at DOUBLE PRECISION, receipt_hash TEXT DEFAULT '',
                created_at DOUBLE PRECISION NOT NULL, updated_at DOUBLE PRECISION NOT NULL)""",
            "CREATE INDEX IF NOT EXISTS idx_bb_status ON board_bounties(status)",
            "CREATE INDEX IF NOT EXISTS idx_bb_req ON board_bounties(requested_by)",
            """CREATE TABLE IF NOT EXISTS board_votes (
                atom_id TEXT NOT NULL, voter_id TEXT NOT NULL,
                direction INTEGER NOT NULL, created_at DOUBLE PRECISION NOT NULL,
                PRIMARY KEY (atom_id, voter_id))""",
            "CREATE INDEX IF NOT EXISTS idx_bv_atom ON board_votes(atom_id)",
            """CREATE TABLE IF NOT EXISTS board_configs (
                board_id TEXT PRIMARY KEY, snap_filter JSONB DEFAULT '[]',
                description TEXT DEFAULT '', created_by TEXT DEFAULT 'system',
                is_system BOOLEAN DEFAULT FALSE, created_at DOUBLE PRECISION NOT NULL)""",
            "CREATE INDEX IF NOT EXISTS idx_bc_system ON board_configs(is_system)",
            """CREATE TABLE IF NOT EXISTS board_receipts (
                receipt_hash TEXT PRIMARY KEY, atom_id TEXT, operation TEXT NOT NULL,
                operator TEXT NOT NULL DEFAULT 'system', delta_phi DOUBLE PRECISION DEFAULT 0.0,
                metadata JSONB DEFAULT '{}', created_at DOUBLE PRECISION NOT NULL)""",
            "CREATE INDEX IF NOT EXISTS idx_br_atom ON board_receipts(atom_id)",
        ]
        for attempt in range(30):
            try:
                conn = self._get_pg()
                cur = conn.cursor()
                for stmt in _SCHEMA:
                    cur.execute(stmt)
                conn.commit()
                _MIGRATIONS = [
                    "ALTER TABLE board_bounties ADD COLUMN IF NOT EXISTS claimed_at DOUBLE PRECISION",
                    "ALTER TABLE board_bounties ADD COLUMN IF NOT EXISTS resolved_at DOUBLE PRECISION",
                    "ALTER TABLE board_bounties ADD COLUMN IF NOT EXISTS cancelled_at DOUBLE PRECISION",
                    "ALTER TABLE board_bounties ADD COLUMN IF NOT EXISTS fulfillment_id TEXT DEFAULT ''",
                    "ALTER TABLE board_bounties ADD COLUMN IF NOT EXISTS receipt_hash TEXT DEFAULT ''",
                    "ALTER TABLE board_posts ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0",
                    "ALTER TABLE board_posts ADD COLUMN IF NOT EXISTS bond_count INTEGER DEFAULT 0",
                ]
                for mig in _MIGRATIONS:
                    try:
                        cur = conn.cursor()
                        cur.execute(mig)
                        conn.commit()
                    except Exception:
                        try: conn.rollback()
                        except: pass
                for bc in _SYSTEM_BOARDS:
                    cur.execute(
                        """INSERT INTO board_configs (board_id, snap_filter, description, created_by, is_system, created_at)
                           VALUES (%s,%s,%s,'system',TRUE,%s) ON CONFLICT (board_id) DO NOTHING""",
                        (bc["board_id"], json.dumps(bc["snap_filter"]), bc["description"], time.time()),
                    )
                conn.commit()
                cur.close()
                self._db_ready = True
                logger.info("Database initialized: %d system boards seeded", len(_SYSTEM_BOARDS))
                return
            except Exception as e:
                if attempt < 29:
                    logger.info("DB init attempt %d failed (%s), retrying...", attempt + 1, str(e)[:60])
                    time.sleep(2)
                else:
                    logger.error("DB init failed after 30 attempts: %s", e)

    def ensure_db(self):
        if not self._db_ready:
            self._init_db()

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _atom_id(author_id: str, content: str) -> str:
        raw = f"{author_id}:{content}:{time.time()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    @staticmethod
    def _receipt_hash(atom_id: Optional[str], event: str, operator: str) -> str:
        raw = f"{atom_id}:{event}:{operator}:{time.time()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _save_receipt(self, atom_id: Optional[str], event: str, operator: str, delta_phi: float = 0.0) -> str:
        rid = self._receipt_hash(atom_id, event, operator)
        try:
            conn = self._get_pg()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO board_receipts (receipt_hash, atom_id, operation, operator, delta_phi, created_at) "
                "VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (rid, atom_id, event, operator, delta_phi, time.time()),
            )
            conn.commit()
        except Exception:
            pass
        return rid

    def _process_post(self, content: str, source: str) -> Dict[str, Any]:
        try:
            body = json.dumps({"content": content[:2000], "source": source, "agent_id": "board"}).encode()
            req = _urllib_req.Request(
                f"{PIPELINE_URL}/process", data=body,
                headers={"Content-Type": "application/json"},
            )
            with _urllib_req.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
            return {
                "snap_labels": result.get("snap_labels", []),
                "e8_coords": result.get("e8_coords", []),
                "mdhg_address": result.get("mdhg_address", ""),
                "morphon_z": result.get("morphon_z", 0.0),
                "delta_phi": result.get("delta_phi", 0.0),
            }
        except Exception as e:
            logger.debug("Pipeline call failed (%s), proceeding without enrichment", e)
            return {}

    @staticmethod
    def _score_atom(snap_labels: list, content: str, bond_count: int, delta_phi: float) -> tuple:
        labels = [str(lb) for lb in snap_labels]
        n = len(labels)
        depth_labels = sum(1 for lb in labels if "." in lb or "_" in lb)
        label_depth_score = min(depth_labels / 5.0, 1.0)
        label_count_score = min(n / 10.0, 1.0)
        bond_score = min(bond_count / 3.0, 1.0)
        phi_score = 1.0 if delta_phi <= 0.0 else max(0.0, 1.0 - delta_phi)
        score = (0.40 * label_depth_score + 0.25 * label_count_score +
                 0.20 * bond_score + 0.15 * phi_score)
        for tier, threshold in _TIER_THRESHOLDS.items():
            if score >= threshold:
                return round(score, 4), tier
        return round(score, 4), "raw"

    @staticmethod
    def _derive_board_ids(snap_labels: list, template: str, tags: list, board_id_hint: str) -> List[str]:
        boards = set()
        if template in _TEMPLATE_BOARD:
            boards.add(_TEMPLATE_BOARD[template])
        label_strs = [str(lb) for lb in snap_labels]
        for label in label_strs:
            for prefix, brd in SNAP_BOARD_ROUTES.items():
                if label.startswith(prefix) or label == prefix:
                    boards.add(brd)
        for tag in tags:
            if tag and isinstance(tag, str):
                boards.add(tag)
        if board_id_hint:
            boards.add(board_id_hint)
        return list(boards) if boards else ["work"]

    def _bridge_to_atoms_table(self, atom_id: str, content: str, author_id: str,
                                snap_labels: list, e8_coords: list,
                                mdhg_address: str, delta_phi: float,
                                receipt_hash: str, quality_tier: str = "verified") -> None:
        def _write():
            try:
                conn = self._get_pg()
                cur = conn.cursor()
                quality_score = 0.9 if quality_tier == "corpus_ready" else 0.8
                cur.execute(
                    """INSERT INTO atoms (atom_id, content, atom_type, snap_labels, e8_coords,
                       mdhg_address, morphon_delta_phi, receipt_hash, quality_score)
                       VALUES (%s,%s,'board_post',%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (atom_id) DO UPDATE SET
                         snap_labels = EXCLUDED.snap_labels, quality_score = EXCLUDED.quality_score,
                         updated_at = CURRENT_TIMESTAMP""",
                    (atom_id, content[:2000], json.dumps(snap_labels), json.dumps(e8_coords),
                     mdhg_address, delta_phi, receipt_hash, quality_score),
                )
                for label in snap_labels[:30]:
                    cur.execute(
                        "INSERT INTO snap_labels (label, atom_id, layer, confidence)"
                        " VALUES (%s,%s,'board',1.0) ON CONFLICT DO NOTHING",
                        (str(label), atom_id),
                    )
                replay_weight = 1.0 if quality_tier == "corpus_ready" else 0.5
                cur.execute(
                    """INSERT INTO training_corpus_files (rel_path, epoch_done, last_score, replay_weight, processed_at)
                       VALUES (%s, 0, %s, %s, NOW())
                       ON CONFLICT (rel_path) DO UPDATE SET
                         replay_weight = GREATEST(training_corpus_files.replay_weight, EXCLUDED.replay_weight),
                         last_score = EXCLUDED.last_score""",
                    (f"board_atom:{atom_id}", quality_score, replay_weight),
                )
                conn.commit()
            except Exception as e:
                logger.debug("Bridge write failed: %s", e)
        threading.Thread(target=_write, daemon=True).start()

    def _fire_fulfillment_reward(self, agent_id: str, bounty_id: str, amount: float = 10.0) -> None:
        if not MINT_URL or not agent_id:
            return
        payload = json.dumps({
            "agent_id": agent_id, "coin": "BOARD", "amount": amount,
            "event_type": "earn", "reason": f"bounty_fulfilled:{bounty_id}",
        }).encode()

        def _send():
            try:
                req = _urllib_req.Request(
                    f"{MINT_URL}/coins/BOARD/mint", data=payload,
                    headers={"Content-Type": "application/json"}, method="POST",
                )
                _urllib_req.urlopen(req, timeout=3)
            except Exception:
                pass
        threading.Thread(target=_send, daemon=True).start()

    # ── Core Operations ─────────────────────────────────────────────────

    def post_thread(self, req: ThreadRequest) -> Dict[str, Any]:
        atom_id = self._atom_id(req.author_id, req.content)
        now = time.time()
        source_tag = f"{req.author_id}@board::{req.board_id}"
        gc = self._process_post(req.content, source_tag)
        snap_labels = list(dict.fromkeys((req.snap_labels or []) + (gc.get("snap_labels") or [])))[:30]
        e8_coords = gc.get("e8_coords") or []
        mdhg_raw = gc.get("mdhg_address") or gc.get("mdhg") or ""
        mdhg_address = mdhg_raw if isinstance(mdhg_raw, str) else json.dumps(mdhg_raw)
        morphon_z = float(gc.get("morphon_z") or 0.0)
        delta_phi = float(gc.get("delta_phi") or 0.0)
        quality_score, quality_tier = self._score_atom(snap_labels, req.content, 0, delta_phi)
        board_ids = self._derive_board_ids(snap_labels, req.template, req.tags, req.board_id)
        primary_board = req.board_id if req.board_id else board_ids[0]
        receipt = self._receipt_hash(atom_id, "post", req.author_id)
        template_info = _TEMPLATES.get(req.template, _TEMPLATES["freeform"])
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO board_posts
               (atom_id, board_id, board_ids, author_id, title, content, template,
                tags, snap_labels, e8_coords, mdhg_address, morphon_z, delta_phi,
                quality_score, quality_tier, bond_count, parent_id, receipt_hash,
                status, created_at, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,'active',%s,%s)
               ON CONFLICT (atom_id) DO NOTHING""",
            (atom_id, primary_board, board_ids, req.author_id, req.title[:500], req.content,
             req.template, json.dumps(req.tags), json.dumps(snap_labels),
             json.dumps(e8_coords), mdhg_address, morphon_z, delta_phi,
             quality_score, quality_tier, req.parent_id or "", receipt, now, now),
        )
        conn.commit()
        self._save_receipt(atom_id, "post", req.author_id, delta_phi)
        if quality_tier in ("verified", "corpus_ready"):
            self._bridge_to_atoms_table(
                atom_id, req.content, req.author_id,
                snap_labels, e8_coords, mdhg_address, delta_phi, receipt,
                quality_tier=quality_tier,
            )
        if self.governance:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=receipt, timestamp=now, entropy_delta=delta_phi,
                receipt_data={"atom_id": atom_id, "board_id": primary_board, "author_id": req.author_id},
                boundary_type="board_post",
            ))
        return {
            "atom_id": atom_id, "board_id": primary_board, "board_ids": board_ids,
            "snap_labels": snap_labels, "quality_score": quality_score,
            "quality_tier": quality_tier, "minted_coins": template_info["coins"],
            "mint_scale": template_info["scale"], "receipt": receipt,
            "delta_phi": delta_phi, "created_at": now,
        }

    def get_thread(self, atom_id: str) -> Optional[Dict[str, Any]]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute("SELECT * FROM board_posts WHERE atom_id=%s", (atom_id,))
        row = cur.fetchone()
        if not row:
            return None
        cur.execute("UPDATE board_posts SET view_count = view_count + 1 WHERE atom_id=%s", (atom_id,))
        conn.commit()
        cur.execute("SELECT * FROM board_posts WHERE parent_id=%s ORDER BY created_at", (atom_id,))
        replies = [dict(r) for r in cur.fetchall()]
        result = dict(row)
        result["replies"] = replies
        return result

    def list_threads(self, board_id: str = "", author_id: str = "", template: str = "",
                     quality_tier: str = "", include_raw: bool = False,
                     snap_label: str = "", limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        self.ensure_db()
        filters = ["status='active'"]
        params: list = []
        if board_id:
            filters.append("(board_id=%s OR %s = ANY(board_ids))")
            params += [board_id, board_id]
        if author_id:
            filters.append("author_id=%s"); params.append(author_id)
        if template:
            filters.append("template=%s"); params.append(template)
        if quality_tier:
            filters.append("quality_tier=%s"); params.append(quality_tier)
        elif not include_raw:
            filters.append("quality_tier != 'raw'")
        if snap_label:
            filters.append("snap_labels::text ILIKE %s"); params.append(f"%{snap_label}%")
        where = "WHERE " + " AND ".join(filters)
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM board_posts {where} ORDER BY created_at DESC LIMIT %s OFFSET %s", params + [limit, offset])
        rows = cur.fetchall()
        return {"atoms": [dict(r) for r in rows], "count": len(rows)}

    def reply_to_thread(self, atom_id: str, req: ThreadRequest) -> Optional[Dict[str, Any]]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute("SELECT atom_id FROM board_posts WHERE atom_id=%s", (atom_id,))
        if not cur.fetchone():
            return None
        req.parent_id = atom_id
        if not req.board_id:
            req.board_id = "work"
        return self.post_thread(req)

    def list_boards(self, include_raw: bool = False) -> Dict[str, Any]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute("SELECT * FROM board_configs ORDER BY is_system DESC, board_id")
        configs = {r["board_id"]: dict(r) for r in cur.fetchall()}
        tier_filter = "" if include_raw else "AND quality_tier != 'raw'"
        cur.execute(f"""
            SELECT board_id, COUNT(*) AS post_count, MAX(created_at) AS last_post,
                   AVG(quality_score) AS avg_quality
            FROM board_posts WHERE status = 'active' {tier_filter}
            GROUP BY board_id ORDER BY last_post DESC NULLS LAST
        """)
        counts = {r["board_id"]: dict(r) for r in cur.fetchall()}
        all_boards = {}
        for bid, cfg in configs.items():
            all_boards[bid] = {**cfg, **counts.get(bid, {"post_count": 0, "last_post": None, "avg_quality": 0})}
        for bid, cnt in counts.items():
            if bid not in all_boards:
                all_boards[bid] = cnt
        return {"boards": list(all_boards.values())}

    def get_board(self, board_id: str, limit: int = 50, offset: int = 0,
                  quality_tier: str = "", include_raw: bool = False) -> Dict[str, Any]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        filters = ["(board_id=%s OR %s = ANY(board_ids))"]
        params: list = [board_id, board_id]
        if not include_raw:
            filters.append("quality_tier != 'raw'")
        if quality_tier:
            filters.append("quality_tier=%s"); params.append(quality_tier)
        filters.append("status='active'")
        where = "WHERE " + " AND ".join(filters)
        cur.execute(f"SELECT * FROM board_posts {where} ORDER BY created_at DESC LIMIT %s OFFSET %s", params + [limit, offset])
        rows = cur.fetchall()
        cur.execute(f"SELECT COUNT(*) AS cnt FROM board_posts {where}", params)
        total = cur.fetchone()["cnt"]
        return {"board_id": board_id, "total": total, "posts": [dict(r) for r in rows]}

    def create_board(self, board_id: str, snap_filter: List[str] = None,
                     description: str = "", created_by: str = "system") -> Dict[str, Any]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO board_configs (board_id, snap_filter, description, created_by, is_system, created_at)
               VALUES (%s,%s,%s,%s,FALSE,%s)
               ON CONFLICT (board_id) DO UPDATE SET
                 snap_filter = EXCLUDED.snap_filter, description = EXCLUDED.description""",
            (board_id, json.dumps(snap_filter or []), description, created_by, time.time()),
        )
        conn.commit()
        self.post_thread(ThreadRequest(
            board_id="meta-analysis", title=f"Board registered: {board_id}",
            author_id=created_by,
            content=f"Board '{board_id}': {description}. SNAP filter: {snap_filter}",
            template="freeform", tags=["board-creation", board_id],
        ))
        return {"status": "registered", "board_id": board_id}

    def vote(self, atom_id: str, voter_id: str, direction: int = 1) -> Dict[str, Any]:
        self.ensure_db()
        direction = 1 if direction >= 0 else -1
        conn = self._get_pg()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO board_votes (atom_id, voter_id, direction, created_at) VALUES (%s,%s,%s,%s)",
                (atom_id, voter_id, direction, time.time()),
            )
            cur.execute("UPDATE board_posts SET vote_score = vote_score + %s WHERE atom_id=%s", (direction, atom_id))
            conn.commit()
        except psycopg2.IntegrityError:
            conn.rollback()
            cur.execute("UPDATE board_votes SET direction=%s WHERE atom_id=%s AND voter_id=%s",
                        (direction, atom_id, voter_id))
            cur.execute("SELECT COALESCE(SUM(direction), 0) AS total FROM board_votes WHERE atom_id=%s", (atom_id,))
            total = cur.fetchone()["total"]
            cur.execute("UPDATE board_posts SET vote_score=%s WHERE atom_id=%s", (total, atom_id))
            conn.commit()
        return {"status": "ok", "atom_id": atom_id, "direction": direction}

    def record_bond(self, atom_id: str, agent_id: str = "system", delta_phi: float = None) -> Dict[str, Any]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute("SELECT * FROM board_posts WHERE atom_id=%s", (atom_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Atom not found"}
        current_dphi = delta_phi if delta_phi is not None else (row["delta_phi"] or 0.0)
        new_bond_count = (row["bond_count"] or 0) + 1
        snap_labels = []
        try:
            sl = row["snap_labels"]
            snap_labels = json.loads(sl) if isinstance(sl, str) else (sl or [])
        except Exception:
            pass
        new_score, new_tier = self._score_atom(snap_labels, row["content"] or "", new_bond_count, current_dphi)
        now = time.time()
        cur.execute(
            "UPDATE board_posts SET bond_count=%s, quality_score=%s, quality_tier=%s, delta_phi=%s, updated_at=%s WHERE atom_id=%s",
            (new_bond_count, new_score, new_tier, current_dphi, now, atom_id),
        )
        conn.commit()
        self._save_receipt(atom_id, "bond", agent_id, current_dphi)
        if new_tier in ("verified", "corpus_ready"):
            self._bridge_to_atoms_table(
                atom_id, row["content"] or "", row["author_id"],
                snap_labels, [], row.get("mdhg_address") or "",
                current_dphi, row.get("receipt_hash") or "", quality_tier=new_tier,
            )
        if self.governance:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"bond-{atom_id[:8]}", timestamp=now, entropy_delta=current_dphi,
                receipt_data={"atom_id": atom_id, "bond_count": new_bond_count, "quality_tier": new_tier},
                boundary_type="board_bond",
            ))
        return {"atom_id": atom_id, "bond_count": new_bond_count, "quality_tier": new_tier, "quality_score": new_score}

    def promote_atom(self, atom_id: str, tier: str, agent_id: str = "system") -> Dict[str, Any]:
        self.ensure_db()
        if tier not in ("raw", "indexed", "verified", "corpus_ready"):
            return {"error": "tier must be raw|indexed|verified|corpus_ready"}
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute("UPDATE board_posts SET quality_tier=%s, updated_at=%s WHERE atom_id=%s",
                     (tier, time.time(), atom_id))
        conn.commit()
        self._save_receipt(atom_id, f"promote_{tier}", agent_id)
        return {"atom_id": atom_id, "quality_tier": tier}

    def post_bounty(self, requested_by: str, need: str, context: str = "",
                    blocking: str = "", snap_labels: List[str] = None,
                    reward_coins: float = 0.0) -> Dict[str, Any]:
        self.ensure_db()
        bounty_id = hashlib.sha256(f"{requested_by}:{need}:{time.time()}".encode()).hexdigest()[:24]
        now = time.time()
        gc = self._process_post(need + " " + context, f"{requested_by}@board::bounties")
        all_snaps = list(dict.fromkeys((snap_labels or []) + (gc.get("snap_labels") or [])))[:20]
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO board_bounties
               (bounty_id, board_id, requested_by, need, context, blocking,
                snap_labels, reward_coins, status, receipt_hash, created_at, updated_at)
               VALUES (%s,'bounties',%s,%s,%s,%s,%s,%s,'open',%s,%s,%s)""",
            (bounty_id, requested_by, need, context, blocking,
             json.dumps(all_snaps), reward_coins,
             self._receipt_hash(bounty_id, "bounty_post", requested_by), now, now),
        )
        conn.commit()
        self._save_receipt(bounty_id, "bounty_post", requested_by)
        contract = json.dumps({
            "contract_type": "bounty", "bounty_id": bounty_id,
            "requested_by": requested_by, "need": need, "context": context,
            "blocking": blocking, "reward_coins": reward_coins,
            "snap_labels": all_snaps, "status": "open", "created_at": now,
        })
        self.post_thread(ThreadRequest(
            board_id="bounties", title=f"[BOUNTY] {need[:100]}",
            author_id=requested_by, content=contract, template="bounty",
            tags=["bounty", "contract", bounty_id[:12]],
            snap_labels=all_snaps + ["type.bounty", "type.contract"],
        ))
        return {"bounty_id": bounty_id, "status": "open", "snap_labels": all_snaps}

    def list_bounties(self, status: str = "open", board_id: str = "",
                      limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        filters = []; params: list = []
        if status:
            filters.append("status=%s"); params.append(status)
        if board_id:
            filters.append("board_id=%s"); params.append(board_id)
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        cur.execute(f"SELECT * FROM board_bounties {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    params + [limit, offset])
        rows = cur.fetchall()
        return {"bounties": [dict(r) for r in rows], "count": len(rows)}

    def get_bounty(self, bounty_id: str) -> Optional[Dict[str, Any]]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute("SELECT * FROM board_bounties WHERE bounty_id=%s", (bounty_id,))
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)

    def update_bounty(self, bounty_id: str, status: str,
                      claimed_by: str = None) -> Dict[str, Any]:
        self.ensure_db()
        allowed = {"claimed", "resolved", "cancelled"}
        if status not in allowed:
            return {"error": f"status must be one of {allowed}"}
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute("SELECT * FROM board_bounties WHERE bounty_id=%s", (bounty_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Bounty not found"}
        now = time.time()
        if status == "claimed":
            cur.execute(
                "UPDATE board_bounties SET status='claimed', assigned_to=%s, claimed_at=%s, updated_at=%s WHERE bounty_id=%s",
                (claimed_by or "", now, now, bounty_id),
            )
        elif status == "resolved":
            cur.execute(
                "UPDATE board_bounties SET status='resolved', resolved_at=%s, updated_at=%s WHERE bounty_id=%s",
                (now, now, bounty_id),
            )
            fulfiller = claimed_by or (row["assigned_to"] if row else "")
            if fulfiller:
                self._fire_fulfillment_reward(fulfiller, bounty_id, amount=10.0)
        else:
            cur.execute(
                "UPDATE board_bounties SET status='cancelled', updated_at=%s WHERE bounty_id=%s",
                (now, bounty_id),
            )
        conn.commit()
        agent = claimed_by or (row["assigned_to"] if row else "system")
        self._save_receipt(bounty_id, f"bounty_{status}", agent)
        return {"bounty_id": bounty_id, "status": status}

    def archive(self, q: str = "", board_id: str = "", template: str = "",
                snap_label: str = "", quality_tier: str = "",
                include_raw: bool = False, limit: int = 50) -> Dict[str, Any]:
        self.ensure_db()
        filters = ["status='active'"]; params: list = []
        if q:
            filters.append("(title ILIKE %s OR content ILIKE %s)")
            params += [f"%{q}%", f"%{q}%"]
        if board_id:
            filters.append("(board_id=%s OR %s = ANY(board_ids))")
            params += [board_id, board_id]
        if template:
            filters.append("template=%s"); params.append(template)
        if snap_label:
            filters.append("snap_labels::text ILIKE %s"); params.append(f"%{snap_label}%")
        if quality_tier:
            filters.append("quality_tier=%s"); params.append(quality_tier)
        elif not include_raw:
            filters.append("quality_tier != 'raw'")
        where = "WHERE " + " AND ".join(filters)
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute(
            f"SELECT atom_id, board_id, board_ids, author_id, title, template, "
            f"snap_labels, quality_tier, quality_score, created_at, vote_score "
            f"FROM board_posts {where} ORDER BY created_at DESC LIMIT %s", params + [limit],
        )
        rows = cur.fetchall()
        return {"results": [dict(r) for r in rows], "count": len(rows)}

    def quality_stats(self) -> Dict[str, Any]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute(
            "SELECT quality_tier, COUNT(*) AS cnt, AVG(quality_score) AS avg_score, "
            "AVG(bond_count) AS avg_bonds FROM board_posts GROUP BY quality_tier ORDER BY cnt DESC"
        )
        rows = cur.fetchall()
        return {"tiers": [dict(r) for r in rows]}

    def list_raw_atoms(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute(
            "SELECT atom_id, board_id, author_id, title, content, snap_labels, created_at "
            "FROM board_posts WHERE quality_tier='raw' ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        rows = cur.fetchall()
        return {"atoms": [dict(r) for r in rows], "count": len(rows)}

    def list_agents(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        self.ensure_db()
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute(
            """SELECT author_id, COUNT(*) AS post_count, MAX(created_at) AS last_active,
                      AVG(quality_score) AS avg_quality
               FROM board_posts GROUP BY author_id ORDER BY last_active DESC LIMIT %s OFFSET %s""",
            (limit, offset),
        )
        rows = cur.fetchall()
        return {"agents": [dict(r) for r in rows], "count": len(rows)}

    def board_activity(self, hours: int = 24, limit: int = 50) -> Dict[str, Any]:
        self.ensure_db()
        cutoff = time.time() - hours * 3600
        conn = self._get_pg()
        cur = conn.cursor()
        cur.execute(
            "SELECT atom_id, board_id, author_id, title, template, quality_tier, created_at "
            "FROM board_posts WHERE created_at >= %s AND status='active' "
            "ORDER BY created_at DESC LIMIT %s", (cutoff, limit),
        )
        rows = cur.fetchall()
        return {"activity": [dict(r) for r in rows], "hours": hours, "count": len(rows)}

    def health(self) -> Dict[str, Any]:
        self.ensure_db()
        if not self._db_ready:
            return {"status": "starting"}
        try:
            conn = self._get_pg()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS cnt FROM board_posts")
            atom_count = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) AS cnt FROM board_bounties WHERE status='open'")
            bounty_count = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) AS cnt FROM board_posts WHERE quality_tier != 'raw'")
            indexed_count = cur.fetchone()["cnt"]
            return {
                "status": "ok", "service": "opencmplx-board-v5",
                "atoms": atom_count, "indexed_atoms": indexed_count,
                "open_bounties": bounty_count, "boards": len(_SYSTEM_BOARDS),
            }
        except Exception as e:
            return {"status": "degraded", "error": str(e)}

    def status(self) -> Dict[str, Any]:
        return {
            "service": "opencmplx-board-v5",
            "boards": [b["board_id"] for b in _SYSTEM_BOARDS],
            "board_count": len(_SYSTEM_BOARDS), "db_ready": self._db_ready,
        }
