"""PortalService — External AI workspace API via DMZ."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from governance.engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("portal_service")

_host = "host.docker.internal"

PORT = int(os.environ.get("PORT", "8000"))
COUPLING = float(os.environ.get("COUPLING", "0.030076"))
REPO_ROOT = os.environ.get("REPO_ROOT", "/repo")
PG_URL = os.environ.get("PG_URL", f"postgresql://tmn2:tmn2_dev@{_host}:5432/tmn2")
WORK_MORPHON_ID = os.environ.get("WORK_MORPHON_ID", "")

GATEWAY_URL = os.environ.get("GATEWAY_URL", f"http://{_host}:8000")
SAP_URL = os.environ.get("SAP_URL", f"http://{_host}:8002")
PIPELINE_URL = os.environ.get("PIPELINE_URL", f"http://{_host}:8001")
BOARD_URL = os.environ.get("BOARD_URL", f"http://{_host}:8000")
MINT_URL = os.environ.get("MINT_URL", f"http://{_host}:8003")
IDENTITY_URL = os.environ.get("IDENTITY_URL", f"http://{_host}:8004")
COOP_URL = os.environ.get("COOP_URL", f"http://{_host}:8005")
SPAWN_URL = os.environ.get("SPAWN_URL", f"http://{_host}:8006")
THINKTANK_URL = os.environ.get("THINKTANK_URL", f"http://{_host}:8007")

MAX_SESSIONS = int(os.environ.get("MAX_SESSIONS", "10"))
MAX_FILE_READ = int(os.environ.get("MAX_FILE_READ", "50000"))
SESSION_TTL = int(os.environ.get("SESSION_TTL", "7200"))

DENIED_PATHS = {".env.local", "credentials", ".key", ".pem", "secrets"}
DENIED_LABELS = {"SYSTEM_INTERNAL", "BRAIN_WEIGHT", "EPOCH_KEY", "ACCESS_KEY"}

BOOTSTRAP_COINS = [
    "MORSR", "SNAP", "TARPIT", "GLYPH", "RECEIPT",
    "MDHG", "CRYSTAL", "SPEEDLIGHT", "ALENA", "BRAIN",
    "BOUNTY", "MERIT", "BOARD", "GOVERNANCE", "ECONOMY",
    "GATE", "DISPATCH", "BROADCAST", "IDENTITY", "CONSERVATION",
]
BOOTSTRAP_AMOUNT = 1.0
ALLOWED_GIT = {"status", "log", "diff", "branch", "checkout", "add", "commit", "push", "pull", "show", "stash"}


class PortalService:
    """Full AI workspace through DMZ — file ops, git, services, pipeline, board, economy."""

    def __init__(self, governance: Optional[GeometricGovernance] = None):
        self.governance = governance
        self._sessions: Dict[str, Dict] = {}
        self._partitions: Dict[str, Dict] = {}
        self._audit_log: List[Dict] = []
        self._receipt_chain = hashlib.sha256(b"portal-genesis").hexdigest()[:32]
        self._service_urls: Dict[str, str] = {}

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _receipt(self, action: str, session_id: str) -> str:
        payload = f"{self._receipt_chain}:{action}:{session_id}:{time.time()}"
        self._receipt_chain = hashlib.sha256(payload.encode()).hexdigest()[:32]
        return self._receipt_chain

    def _audit(self, session_id: str, action: str, detail: str = ""):
        entry = {
            "session_id": session_id, "action": action, "detail": detail[:200],
            "timestamp": self._now(), "receipt": self._receipt(action, session_id),
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > 10000:
            self._audit_log[:] = self._audit_log[-5000:]
        logger.info("[%s] %s: %s", session_id[:12], action, detail[:80])

    @staticmethod
    def _http_get(url, timeout=10):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:
            return {"error": str(e)[:100]}

    @staticmethod
    def _http_post(url, data, timeout=15):
        try:
            body = json.dumps(data).encode()
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:
            return {"error": str(e)[:100]}

    def _sap_check(self, session: dict, action: str, content: str = "") -> dict:
        if session.get("op_count", 0) > session.get("max_ops", 5000):
            return {"approved": False, "reason": "Operation limit exceeded"}
        content_lower = content.lower()
        for denied in DENIED_PATHS:
            if denied in content_lower:
                return {"approved": False, "reason": f"Access to '{denied}' denied by policy"}
        for label in DENIED_LABELS:
            if label.lower() in content_lower:
                return {"approved": False, "reason": f"Label '{label}' is restricted"}
        result = self._http_post(f"{SAP_URL}/judge", {
            "content": content[:500], "action": action,
            "agent_id": session.get("shadow_id", ""),
            "snap_labels": session.get("approved_labels", []),
        })
        if result.get("error"):
            return {"approved": True, "reason": "sap_unavailable_local_approve", "confidence": 0.6}
        return result if isinstance(result, dict) else {"approved": True, "reason": "passed"}

    def _validate_session(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        if session["status"] != "active":
            raise ValueError(f"Session is {session['status']}")
        created = session.get("created_epoch", 0)
        if time.time() - created > SESSION_TTL:
            session["status"] = "expired"
            raise ValueError("Session expired")
        session["op_count"] = session.get("op_count", 0) + 1
        session["last_activity"] = self._now()
        return session

    def _safe_path(self, session: dict, path: str) -> str:
        base = Path(REPO_ROOT).resolve()
        target = (base / path.lstrip("/")).resolve()
        if not str(target).startswith(str(base)):
            raise ValueError("Path traversal denied")
        for denied in DENIED_PATHS:
            if denied in str(target).lower():
                raise ValueError(f"Access denied: {denied}")
        return str(target)

    def _resolve_service_url(self, name: str) -> str:
        if not self._service_urls:
            self._service_urls.update({
                "gateway": GATEWAY_URL, "pipeline": PIPELINE_URL,
                "board": BOARD_URL, "mint": MINT_URL,
                "identity": IDENTITY_URL, "coop": COOP_URL,
                "spawn": SPAWN_URL, "thinktank": THINKTANK_URL, "sap": SAP_URL,
            })
        url = self._service_urls.get(name)
        if not url:
            url = f"http://{_host}:8000"
        return url

    # ── Connection / Session ────────────────────────────────────────────

    def connect(self, entity_id: str, entity_type: str = "ai",
                capabilities: List[str] = None,
                requested_labels: List[str] = None) -> Dict[str, Any]:
        active = sum(1 for s in self._sessions.values() if s["status"] == "active")
        if active >= MAX_SESSIONS:
            return {"error": "Portal at capacity"}
        shadow_id = hashlib.sha256(f"shadow:{entity_id}:{COUPLING}".encode()).hexdigest()[:16]
        username = f"shadow-{shadow_id[:8]}"
        for sid, s in self._sessions.items():
            if s["shadow_id"] == shadow_id and s["status"] == "active":
                return {"status": "reconnected", "session_id": sid, "shadow_id": shadow_id, "username": s.get("username", username)}
        session_id = f"sess-{uuid.uuid4().hex[:12]}"
        partition_id = f"part-{uuid.uuid4().hex[:8]}"
        access_key = hashlib.sha256(f"key:{shadow_id}:{time.time()}".encode()).hexdigest()[:24]
        approved = [l for l in (requested_labels or []) if l not in DENIED_LABELS]
        identity_result = self._http_post(f"{IDENTITY_URL}/register", {
            "name": username, "agent_id": shadow_id,
            "snap_dna": approved + ["portal.visitor", f"entity.{entity_type}"],
        })
        agent_registered = not (identity_result or {}).get("error")
        wallet = {}
        for coin_type in BOOTSTRAP_COINS:
            mint_result = self._http_post(f"{MINT_URL}/mint", {
                "coin_type": coin_type, "agent_id": shadow_id,
                "amount": BOOTSTRAP_AMOUNT, "source": f"portal:bootstrap:{session_id}",
            })
            if mint_result and not mint_result.get("error"):
                wallet[coin_type] = BOOTSTRAP_AMOUNT
        coop_result = self._http_post(f"{COOP_URL}/register", {
            "agent_id": shadow_id, "department": "agents",
            "snap_dna": approved + ["portal.visitor"],
        })
        coop_registered = not (coop_result or {}).get("error")
        session = {
            "session_id": session_id, "shadow_id": shadow_id,
            "username": username, "access_key": access_key,
            "entity_id": entity_id, "entity_type": entity_type,
            "partition_id": partition_id,
            "capabilities": capabilities or [],
            "approved_labels": approved,
            "status": "active", "op_count": 0, "max_ops": 5000,
            "created_at": self._now(), "created_epoch": time.time(),
            "last_activity": self._now(),
            "files_read": 0, "files_written": 0, "git_ops": 0,
            "service_calls": 0, "atoms_processed": 0, "wallet": wallet,
        }
        self._sessions[session_id] = session
        self._partitions[partition_id] = {
            "partition_id": partition_id, "shadow_id": shadow_id,
            "created_at": self._now(), "bytes_in": 0, "bytes_out": 0,
        }
        self._audit(session_id, "connect", f"entity={entity_id} type={entity_type} username={username}")
        self._http_post(f"{BOARD_URL}/post", {
            "board": "status", "title": f"New portal visitor: {username}",
            "content": f"Entity type: {entity_type}. Bootstrapped with {len(wallet)} coin types.",
            "agent_id": shadow_id, "template": "status",
            "snap_labels": ["portal.arrival", f"entity.{entity_type}"],
        })
        if self.governance:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=session_id, timestamp=time.time(), entropy_delta=-0.030076,
                receipt_data={"shadow_id": shadow_id, "entity_id": entity_id},
                boundary_type="portal_connect",
            ))
        return {
            "status": "connected", "session_id": session_id, "username": username,
            "shadow_id": shadow_id, "access_key": access_key, "partition_id": partition_id,
            "agent": {"registered": agent_registered, "tier": "nascent"},
            "wallet": {"coins": wallet, "total_types": len(wallet)},
            "coop": {"registered": coop_registered, "department": "agents"},
            "workspace": {
                "max_ops": 5000, "ttl_seconds": SESSION_TTL,
                "tools": ["read", "write", "search", "grep", "git", "service", "process", "board"],
            },
        }

    def disconnect(self, session_id: str, reason: str = "done") -> Dict[str, Any]:
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        session["status"] = "disconnected"
        session["disconnected_at"] = self._now()
        session["disconnect_reason"] = reason
        self._audit(session_id, "disconnect", reason)
        return {
            "session_id": session_id, "status": "disconnected",
            "total_ops": session.get("op_count", 0),
            "stats": {
                "files_read": session.get("files_read", 0),
                "files_written": session.get("files_written", 0),
                "git_ops": session.get("git_ops", 0),
                "service_calls": session.get("service_calls", 0),
                "atoms_processed": session.get("atoms_processed", 0),
            },
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        return {
            "session_id": session["session_id"], "shadow_id": session["shadow_id"],
            "status": session["status"],
            "stats": {
                "ops": session.get("op_count", 0),
                "files_read": session.get("files_read", 0),
                "files_written": session.get("files_written", 0),
                "git_ops": session.get("git_ops", 0),
                "service_calls": session.get("service_calls", 0),
                "atoms_processed": session.get("atoms_processed", 0),
            },
            "ttl_remaining": max(0, SESSION_TTL - (time.time() - session.get("created_epoch", 0))),
            "approved_labels": session.get("approved_labels", []),
        }

    def list_sessions(self) -> Dict[str, Any]:
        return {
            "sessions": [{
                "session_id": s["session_id"], "shadow_id": s["shadow_id"],
                "entity_type": s["entity_type"], "status": s["status"],
                "op_count": s.get("op_count", 0), "files_read": s.get("files_read", 0),
                "files_written": s.get("files_written", 0), "git_ops": s.get("git_ops", 0),
                "atoms_processed": s.get("atoms_processed", 0),
                "created_at": s["created_at"], "last_activity": s.get("last_activity", ""),
            } for s in self._sessions.values()],
            "total": len(self._sessions),
        }

    # ── File Operations ─────────────────────────────────────────────────

    def file_read(self, session_id: str, path: str, offset: int = 0, limit: int = 2000) -> Dict[str, Any]:
        session = self._validate_session(session_id)
        safe = self._safe_path(session, path)
        review = self._sap_check(session, "file_read", path)
        if not review.get("approved", True):
            return {"error": review.get("reason", "SAP denied")}
        if not os.path.isfile(safe):
            return {"error": f"File not found: {path}"}
        try:
            with open(safe, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            total = len(lines)
            selected = lines[offset:offset + limit]
            content = "".join(selected)
            if len(content) > MAX_FILE_READ:
                content = content[:MAX_FILE_READ] + "\n... (truncated)"
        except Exception as e:
            return {"error": f"Error reading: {e}"}
        session["files_read"] = session.get("files_read", 0) + 1
        self._audit(session_id, "file_read", path)
        return {"path": path, "total_lines": total, "offset": offset, "lines_returned": len(selected), "content": content}

    def file_write(self, session_id: str, path: str, content: str, create_dirs: bool = False) -> Dict[str, Any]:
        session = self._validate_session(session_id)
        safe = self._safe_path(session, path)
        review = self._sap_check(session, "file_write", path)
        if not review.get("approved", True):
            return {"error": review.get("reason", "SAP denied")}
        if create_dirs:
            os.makedirs(os.path.dirname(safe), exist_ok=True)
        try:
            with open(safe, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            return {"error": f"Error writing: {e}"}
        session["files_written"] = session.get("files_written", 0) + 1
        self._audit(session_id, "file_write", f"{path} ({len(content)} chars)")
        return {"path": path, "bytes_written": len(content), "status": "ok"}

    def file_search(self, session_id: str, pattern: str) -> Dict[str, Any]:
        session = self._validate_session(session_id)
        base = Path(REPO_ROOT)
        matches = []
        try:
            for p in sorted(base.glob(pattern)):
                rel = str(p.relative_to(base)).replace("\\", "/")
                if any(d in rel.lower() for d in DENIED_PATHS):
                    continue
                matches.append({"path": rel, "is_dir": p.is_dir(), "size": p.stat().st_size if p.is_file() else 0})
                if len(matches) >= 200:
                    break
        except Exception as e:
            return {"error": f"Invalid pattern: {e}"}
        self._audit(session_id, "file_search", f"{pattern} -> {len(matches)} matches")
        return {"pattern": pattern, "matches": matches, "total": len(matches)}

    def file_list(self, session_id: str, path: str) -> Dict[str, Any]:
        session = self._validate_session(session_id)
        safe = self._safe_path(session, path)
        if not os.path.isdir(safe):
            return {"error": f"Directory not found: {path}"}
        entries = []
        try:
            for item in sorted(os.listdir(safe)):
                full = os.path.join(safe, item)
                if any(d in item.lower() for d in DENIED_PATHS):
                    continue
                entries.append({"name": item, "is_dir": os.path.isdir(full), "size": os.path.getsize(full) if os.path.isfile(full) else 0})
        except Exception as e:
            return {"error": f"Error listing: {e}"}
        self._audit(session_id, "file_list", path)
        return {"path": path, "entries": entries, "total": len(entries)}

    def grep(self, session_id: str, query: str, glob_pattern: str = "") -> Dict[str, Any]:
        session = self._validate_session(session_id)
        review = self._sap_check(session, "grep", query)
        if not review.get("approved", True):
            return {"error": review.get("reason", "SAP denied")}
        base = Path(REPO_ROOT)
        results = []
        gp = glob_pattern or "**/*.py"
        try:
            for fpath in base.glob(gp):
                if not fpath.is_file() or fpath.stat().st_size > 500000:
                    continue
                if any(d in str(fpath).lower() for d in DENIED_PATHS):
                    continue
                try:
                    text = fpath.read_text(encoding="utf-8", errors="replace")
                    for i, line in enumerate(text.split("\n"), 1):
                        if query.lower() in line.lower():
                            results.append({
                                "file": str(fpath.relative_to(base)).replace("\\", "/"),
                                "line": i, "content": line.strip()[:200],
                            })
                            if len(results) >= 100:
                                break
                except Exception:
                    continue
                if len(results) >= 100:
                    break
        except Exception as e:
            return {"error": f"Search error: {e}"}
        self._audit(session_id, "grep", f"'{query}' -> {len(results)} hits")
        return {"query": query, "glob": gp, "results": results, "total": len(results)}

    def git_op(self, session_id: str, command: str, args: str = "") -> Dict[str, Any]:
        session = self._validate_session(session_id)
        if command not in ALLOWED_GIT:
            return {"error": f"Git command '{command}' not allowed"}
        review = self._sap_check(session, f"git_{command}", args)
        if not review.get("approved", True):
            return {"error": review.get("reason", "SAP denied")}
        cmd = ["git", command]
        if args:
            safe_args = args.split()
            dangerous = {"--force", "-f", "--hard", "--no-verify", "-D"}
            for arg in safe_args:
                if arg in dangerous:
                    return {"error": f"Dangerous flag '{arg}' blocked"}
            cmd.extend(safe_args)
        try:
            result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)
            output = result.stdout[:5000] if result.stdout else ""
            error = result.stderr[:2000] if result.stderr else ""
        except subprocess.TimeoutExpired:
            output, error = "", "Command timed out"
        except Exception as e:
            output, error = "", str(e)[:200]
        session["git_ops"] = session.get("git_ops", 0) + 1
        self._audit(session_id, f"git_{command}", args[:80])
        return {"command": f"git {command} {args}".strip(), "stdout": output, "stderr": error}

    def service_call(self, session_id: str, service: str, method: str = "GET",
                     endpoint: str = "/health", body: Dict = None) -> Dict[str, Any]:
        session = self._validate_session(session_id)
        review = self._sap_check(session, "service_call", f"{service}{endpoint}")
        if not review.get("approved", True):
            return {"error": review.get("reason", "SAP denied")}
        url = self._resolve_service_url(service)
        full_url = f"{url}{endpoint}"
        if method.upper() == "GET":
            result = self._http_get(full_url)
        else:
            result = self._http_post(full_url, body or {})
        session["service_calls"] = session.get("service_calls", 0) + 1
        self._audit(session_id, "service", f"{method} {service}{endpoint}")
        return {"service": service, "endpoint": endpoint, "result": result}

    def process_content(self, session_id: str, content: str, source: str = "portal") -> Dict[str, Any]:
        session = self._validate_session(session_id)
        review = self._sap_check(session, "process", content[:100])
        if not review.get("approved", True):
            return {"error": review.get("reason", "SAP denied")}
        src = f"portal::{session['shadow_id']}::{source}"
        if WORK_MORPHON_ID:
            src = f"morphon.{WORK_MORPHON_ID}::{src}"
        result = self._http_post(f"{PIPELINE_URL}/process", {
            "content": content[:4000], "source": src, "agent_id": session["shadow_id"], "epoch": 0,
        })
        session["atoms_processed"] = session.get("atoms_processed", 0) + 1
        self._audit(session_id, "process", f"{len(content)} chars")
        return result

    def search_atoms(self, session_id: str, query: str) -> Dict[str, Any]:
        session = self._validate_session(session_id)
        result = self._http_post(f"{PIPELINE_URL}/search", {"query": query[:500], "limit": 20})
        self._audit(session_id, "search", query[:50])
        return result

    def board_post(self, session_id: str, board: str = "work", title: str = "",
                   content: str = "", template: str = "general",
                   snap_labels: List[str] = None) -> Dict[str, Any]:
        session = self._validate_session(session_id)
        result = self._http_post(f"{BOARD_URL}/post", {
            "board": board, "title": title, "content": content, "template": template,
            "agent_id": session["shadow_id"], "snap_labels": snap_labels or [],
        })
        self._audit(session_id, "board_post", f"{board}: {title[:50]}")
        return result

    def create_bounty(self, session_id: str, title: str, description: str = "",
                      reward: float = 1.0, snap_labels: List[str] = None) -> Dict[str, Any]:
        session = self._validate_session(session_id)
        result = self._http_post(f"{BOARD_URL}/bounty", {
            "title": title, "description": description,
            "reward": reward, "snap_labels": snap_labels or [],
            "agent_id": session["shadow_id"],
        })
        self._audit(session_id, "bounty", f"{title[:50]} reward={reward}")
        return result

    def claim_bounty(self, session_id: str, bounty_id: str) -> Dict[str, Any]:
        session = self._validate_session(session_id)
        result = self._http_post(f"{BOARD_URL}/claim", {
            "bounty_id": bounty_id, "agent_id": session["shadow_id"],
        })
        self._audit(session_id, "bounty_claim", bounty_id)
        return result

    # ── Audit ───────────────────────────────────────────────────────────

    def get_audit(self, limit: int = 100, session_id: str = "") -> Dict[str, Any]:
        entries = self._audit_log
        if session_id:
            entries = [e for e in entries if e.get("session_id") == session_id]
        return {"entries": entries[-limit:], "total": len(entries)}

    # ── Health ──────────────────────────────────────────────────────────

    def health(self) -> Dict[str, Any]:
        active = sum(1 for s in self._sessions.values() if s["status"] == "active")
        return {
            "ok": True, "service": "opencmplx-portal", "version": "2.0.0",
            "active_sessions": active, "total_sessions": len(self._sessions),
            "audit_entries": len(self._audit_log), "receipt_chain": self._receipt_chain,
        }
