import ast
import csv
import hashlib
import importlib.util
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field


KERNEL_ID = os.environ.get("REPO_KERNEL_ID", "cmplx-repo-kernel")
MANIFEST_PATH = Path(os.environ.get("REPO_KERNEL_MANIFEST", "/kernel/manifest/repos.json"))
REPOS_ROOT = Path(os.environ.get("REPO_KERNEL_REPOS", "/kernel/repos"))
HOST_REPOS_ROOT = os.environ.get("REPO_KERNEL_HOST_REPOS")
PROMOTION_LEDGER_PATH = Path(os.environ.get("REPO_KERNEL_PROMOTION_LEDGER", "/reports/repo_promotion_ledger_2026-05-13.json"))
SELF_STATE_PATH = Path(os.environ.get("REPO_KERNEL_SELF_STATE", "/kernel/state/self_state.sqlite"))
QUARANTINE_ROOT = Path(os.environ.get("REPO_KERNEL_QUARANTINE_ROOT", "/kernel/quarantine"))
PROTOTYPE_EVIDENCE_ROOT = Path(os.environ.get("REPO_KERNEL_PROTOTYPES_ROOT", "/sources/PartsFactory/Unification Prototypes"))
GITNEXUS_API_BASE = os.environ.get("GITNEXUS_API_BASE", "http://gitnexus-rebuild-server:4747")
GITNEXUS_AGGREGATE_DB = Path(os.environ.get("GITNEXUS_AGGREGATE_DB", "/sources/PartsFactory/CMPLX-PartsFactory/data/gitnexus_index.sqlite"))
GITNEXUS_META_PATH = Path(os.environ.get("GITNEXUS_META_PATH", "/sources/PartsFactory/CMPLX-PartsFactory/.gitnexus/meta.json"))
CMPLXMCP_RUNTIME_SHIM_AVAILABLE = os.environ.get("CMPLXMCP_RUNTIME_SHIM_AVAILABLE", "0") == "1"
ALLOW_MUTATION = os.environ.get("REPO_KERNEL_ALLOW_MUTATION", "0") == "1"
RUNTIME_GIT_STATUS = os.environ.get("REPO_KERNEL_RUNTIME_GIT_STATUS", "0") == "1"
MCP_NAME = os.environ.get("FASTMCP_INSTANCE", "cmplx-repo-kernel")


class SearchRequest(BaseModel):
    module: str
    query: str = Field(min_length=1)
    glob: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


class ComposePlanRequest(BaseModel):
    modules: list[str] | None = None
    goal: str = "unified master composition"


class ProbeRequest(BaseModel):
    mode: str = Field(default="static", pattern="^(static|light)$")
    include_search_examples: bool = True


class PromotionPlanRequest(BaseModel):
    target: str = "CMPLX-PartsFactory"
    include_probe: bool = True


class AdapterCallRequest(BaseModel):
    action: str = Field(pattern="^(probe|promotion_plan|surface_catalog|search|tree|read_file)$")
    args: dict[str, Any] = Field(default_factory=dict)


class RuntimeHealthRequest(BaseModel):
    modules: list[str] | None = None
    timeout_seconds: float = Field(default=1.5, ge=0.2, le=10.0)
    limit: int = Field(default=80, ge=1, le=500)


class RuntimeActivationPlanRequest(BaseModel):
    workflow: str = "memory"
    modules: list[str] | None = None
    include_infra: bool = True


class MemoryQueryRequest(BaseModel):
    family: str | None = None
    atom_id: str | None = None
    sql: str | None = None
    query: str | None = None
    dry_run: bool = True


class MCPToolCallPlanRequest(BaseModel):
    tool_name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    prefer_module: str | None = None
    dry_run: bool = True


class GlobalSystemCallPlanRequest(BaseModel):
    operation: str = Field(default="tool", pattern="^(tool|route|service|query|receipt|plan)$")
    name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    prefer_module: str | None = None
    dry_run: bool = True


class GlobalQueryRequest(BaseModel):
    q: str = Field(min_length=1)
    systems: list[str] = Field(default_factory=lambda: ["memory", "knowledge", "geometry", "operations"])
    limit: int = Field(default=20, ge=1, le=100)
    include_context: bool = True
    dry_run: bool = False


class PrototypeEvidenceReadRequest(BaseModel):
    path: str = Field(min_length=1)
    max_bytes: int = Field(default=120_000, ge=1, le=500_000)


class AgentOrchestrationPlanRequest(BaseModel):
    intent: str = Field(default="inspect agent orchestration capabilities", min_length=1)
    role: str | None = None
    prefer_module: str | None = None
    dry_run: bool = True


class KnowledgePlanRequest(BaseModel):
    task: str = Field(default="knowledge search and retrieval", min_length=1)
    query: str | None = None
    role: str | None = None
    prefer_module: str | None = None
    dry_run: bool = True


class RegisteredBundleRequest(BaseModel):
    modules: list[str] | None = None
    count: int | None = Field(default=None, ge=1, le=12)
    exclude: list[str] = Field(default_factory=lambda: ["CMPLX-PartsFactory", "scout-demo-service"])


class RegisteredBundleRunRequest(RegisteredBundleRequest):
    command: str = Field(default="status", pattern="^(status|probe|surface_catalog|tree|readme|native_verify)$")
    path: str = "."
    query: str | None = None
    execute_native: bool = False
    limit: int = Field(default=100, ge=1, le=1000)
    timeout_seconds: int = Field(default=45, ge=1, le=300)


class SourceInventoryRequest(BaseModel):
    source_id: str = "repo_kernel_repos"
    path: str = "."
    max_depth: int = Field(default=2, ge=0, le=6)
    limit: int = Field(default=500, ge=1, le=5000)


class SourceArchiveManifestRequest(BaseModel):
    source_id: str = "parts_factory"
    path: str = Field(min_length=1)
    limit: int = Field(default=500, ge=1, le=5000)


class SourceArchiveMemberReadRequest(BaseModel):
    source_id: str = "parts_factory"
    path: str = Field(min_length=1)
    member_path: str = Field(min_length=1)
    max_bytes: int = Field(default=200_000, ge=1, le=2_000_000)


class SourceArchiveCorpusSummaryRequest(BaseModel):
    source_id: str = "parts_factory"
    path: str = Field(min_length=1)
    max_bytes: int = Field(default=1_000_000, ge=1, le=5_000_000)


class ArchiveTriageRequest(BaseModel):
    source_ids: list[str] | None = None
    max_depth: int = Field(default=1, ge=0, le=4)
    limit_per_source: int = Field(default=500, ge=1, le=5000)
    result_limit: int = Field(default=100, ge=1, le=1000)


class ArchiveRef(BaseModel):
    source_id: str
    path: str = Field(min_length=1)


class ArchiveCompareRequest(BaseModel):
    archives: list[ArchiveRef] = Field(min_length=2)
    include_outer_hash: bool = False


class ArchiveDuplicateCandidateRequest(BaseModel):
    source_ids: list[str] | None = None
    max_depth: int = Field(default=1, ge=0, le=4)
    limit_per_source: int = Field(default=500, ge=1, le=5000)
    result_limit: int = Field(default=100, ge=1, le=1000)
    compare_limit: int = Field(default=25, ge=0, le=200)


class CleanupEvidenceRequest(BaseModel):
    source_ids: list[str] | None = None
    max_depth: int = Field(default=1, ge=0, le=4)
    limit_per_source: int = Field(default=500, ge=1, le=5000)
    result_limit: int = Field(default=100, ge=1, le=1000)
    corpus_archives: list[ArchiveRef] = Field(default_factory=list)


class FileHashSliceRequest(BaseModel):
    source_id: str = "parts_factory"
    path: str = "."
    max_depth: int = Field(default=1, ge=0, le=5)
    limit: int = Field(default=500, ge=1, le=5000)
    max_file_bytes: int = Field(default=50_000_000, ge=1, le=500_000_000)
    include_suffixes: list[str] | None = None


class ArchiveHashSliceRequest(BaseModel):
    source_id: str = "parts_factory"
    path: str = Field(min_length=1)
    limit: int = Field(default=500, ge=1, le=5000)
    max_member_bytes: int = Field(default=50_000_000, ge=1, le=500_000_000)
    include_suffixes: list[str] | None = None


class HashSliceBatchRequest(BaseModel):
    file_slices: list[FileHashSliceRequest] = Field(default_factory=list)
    archive_slices: list[ArchiveHashSliceRequest] = Field(default_factory=list)
    entry_limit: int = Field(default=5000, ge=1, le=20000)


class ArchiveSQLiteQuarantineProbeRequest(BaseModel):
    source_id: str = "parts_factory"
    archive: str = Field(min_length=1)
    member_path: str = Field(min_length=1)
    approved: bool = False
    max_member_bytes: int = Field(default=100_000_000, ge=1, le=500_000_000)
    replace_existing: bool = False
    table_limit: int = Field(default=50, ge=1, le=500)
    count_rows: bool = True


class FileBreakdownPlanRequest(BaseModel):
    source_id: str = "parts_factory"
    path: str = Field(min_length=1)
    archive_member_path: str | None = None
    target_chunk_bytes: int = Field(default=2_000_000, ge=64_000, le=100_000_000)
    max_chunks: int = Field(default=200, ge=1, le=5000)
    parsing_failure: str | None = None


class QuarantineSQLitePreviewRequest(BaseModel):
    path: str = Field(min_length=1)
    tables: list[str] | None = None
    table_limit: int = Field(default=10, ge=1, le=100)
    row_limit: int = Field(default=5, ge=1, le=100)
    row_offset: int = Field(default=0, ge=0, le=1_000_000)
    max_cell_chars: int = Field(default=240, ge=16, le=5000)
    include_schema: bool = True


class MMDBImportDryRunRequest(BaseModel):
    path: str = Field(min_length=1)
    tables: list[str] | None = None
    table_limit: int = Field(default=10, ge=1, le=100)
    sample_limit: int = Field(default=5, ge=1, le=100)
    row_offset: int = Field(default=0, ge=0, le=1_000_000)
    max_rows_per_table: int = Field(default=1000, ge=1, le=50_000)
    max_cell_chars: int = Field(default=240, ge=16, le=5000)
    include_samples: bool = True


class MMDBImportCompatibilityRequest(BaseModel):
    path: str = Field(min_length=1)
    tables: list[str] | None = None
    max_rows_per_table: int = Field(default=1000, ge=1, le=50_000)
    sample_limit: int = Field(default=2, ge=1, le=25)


class CleanupLedgerRecordRequest(BaseModel):
    kind: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: str = "candidate"
    source_id: str | None = None
    path: str | None = None
    sha256: str | None = None
    size: int | None = None
    detail: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class MemoryCorpusImportPlanRequest(BaseModel):
    source_id: str = "parts_factory"
    archive: str = "mmdb-corpus.zip"
    manifest_limit: int = Field(default=1000, ge=1, le=5000)
    max_db_member_bytes: int = Field(default=5_000_000, ge=1, le=500_000_000)


class SelfDecisionRequest(BaseModel):
    title: str = Field(min_length=1)
    status: str = "active"
    rationale: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class SelfIssueRequest(BaseModel):
    issue: str = Field(min_length=1)
    severity: str = "medium"
    area: str = "general"
    module: str | None = None
    status: str = "open"
    detail: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class SelfActionRequest(BaseModel):
    title: str = Field(min_length=1)
    priority: int = Field(default=50, ge=0, le=100)
    status: str = "open"
    area: str = "general"
    module: str | None = None
    detail: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class SelfWorkflowStatusRequest(BaseModel):
    workflow: str = Field(min_length=1)
    status: str = "unknown"
    summary: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class SelfWorklogRequest(BaseModel):
    message: str = Field(min_length=1)
    area: str = "general"
    data: dict[str, Any] = Field(default_factory=dict)


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            cmd,
            124,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=f"timeout after {timeout}s",
        )


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def safe_join(root: Path, rel: str | None) -> Path:
    rel = rel or "."
    if rel.startswith(("/", "\\")):
        raise HTTPException(400, "absolute paths are not allowed")
    candidate = (root / rel).resolve()
    root_resolved = root.resolve()
    if not is_relative_to(candidate, root_resolved):
        raise HTTPException(400, "path escapes module root")
    return candidate


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(prefix: str, text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]
    return f"{prefix}-{slug or 'item'}"


class RepoRegistry:
    def __init__(self, manifest_path: Path, repos_root: Path):
        self.manifest_path = manifest_path
        self.repos_root = repos_root

    def manifest(self) -> dict[str, Any]:
        if not self.manifest_path.is_file():
            return {"generated_at": None, "owner": None, "repo_root": str(self.repos_root), "modules": []}
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def modules(self) -> list[dict[str, Any]]:
        modules = []
        for module in self.manifest().get("modules", []):
            modules.append(self.enrich(module))
        return modules

    def module(self, name: str) -> dict[str, Any]:
        for module in self.manifest().get("modules", []):
            if module.get("name") == name:
                return self.enrich(module)
        raise HTTPException(404, f"unknown module: {name}")

    def module_root(self, name: str) -> Path:
        module = self.module(name)
        root = Path(module.get("container_path") or self.repos_root / name)
        root = root.resolve()
        repos_root = self.repos_root.resolve()
        if not is_relative_to(root, repos_root):
            raise HTTPException(500, f"module root escapes repo kernel root: {name}")
        return root

    def enrich(self, module: dict[str, Any]) -> dict[str, Any]:
        name = module["name"]
        root = self.repos_root / name
        cloned = root.is_dir() and (root / ".git").exists()
        data = dict(module)
        data["container_path"] = str(root)
        data["cloned"] = cloned
        data["api_base"] = f"/api/modules/{name}"
        data["mcp_tools"] = [
            "repo_kernel_list_modules",
            "repo_kernel_inspect_module",
            "repo_kernel_module_tree",
            "repo_kernel_read_file",
            "repo_kernel_search",
        ]
        if cloned:
            data["pinned_commit_runtime"] = git(root, "rev-parse", "HEAD")
            data["branch_runtime"] = git(root, "branch", "--show-current")
            if RUNTIME_GIT_STATUS:
                status = git(root, "status", "--porcelain", "-uno")
                data["dirty_state_runtime"] = "dirty" if status else "clean_or_unknown"
            else:
                data["dirty_state_runtime"] = module.get("dirty_state", "unknown")
        return data


def git(repo: Path, *args: str) -> str:
    proc = run(["git", "-C", str(repo), *args], timeout=20)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


class PromotionLedger:
    def __init__(self, path: Path):
        self.path = path

    def _candidate_paths(self) -> list[Path]:
        paths = [self.path]
        reports_root = Path("/reports")
        if reports_root.is_dir():
            paths.extend(sorted(reports_root.glob("repo_promotion_ledger_*.json"), reverse=True))
        return paths

    def read(self) -> dict[str, Any]:
        for path in self._candidate_paths():
            if path.is_file():
                return json.loads(path.read_text(encoding="utf-8"))
        return {"generated_at": None, "modules": [], "missing": str(self.path)}

    def module(self, name: str) -> dict[str, Any] | None:
        for module in self.read().get("modules", []):
            if module.get("name") == name:
                return module
        return None


class SourceUniverse:
    IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
    ARCHIVE_SUFFIXES = {".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".bz2", ".xz"}
    DB_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".duckdb"}
    MANIFEST_NAMES = {"pyproject.toml", "package.json", "requirements.txt", "setup.py", "Cargo.toml", "go.mod", "AGENTS.md", "README.md", "MANIFEST.md"}
    COMPOSE_NAMES = re.compile(r"^(docker-compose.*|compose.*)\.ya?ml$", re.IGNORECASE)

    def __init__(self, repos_root: Path):
        self.repos_root = repos_root

    def sources(self) -> list[dict[str, Any]]:
        defaults = [
            {
                "id": "repo_kernel_repos",
                "label": "Repo Kernel Clean Repos",
                "role": "active_module_substrate",
                "path": str(self.repos_root),
                "access": "rw",
                "priority": 100,
            },
            {
                "id": "parts_factory",
                "label": "PartsFactory",
                "role": "creative_yard",
                "path": "/sources/PartsFactory",
                "access": "ro",
                "priority": 90,
            },
            {
                "id": "manny_unification_2",
                "label": "Manny Unification 2",
                "role": "evidence_substrate",
                "path": "/sources/MannyUnification2",
                "access": "ro",
                "priority": 80,
            },
            {
                "id": "oc_build",
                "label": "OC build",
                "role": "design_doctrine",
                "path": "/sources/OCbuild",
                "access": "ro",
                "priority": 70,
            },
        ]
        extra = self._extra_sources()
        enriched = []
        for source in defaults + extra:
            path = Path(source["path"])
            item = dict(source)
            item["exists"] = path.exists()
            item["is_dir"] = path.is_dir()
            item["api_base"] = f"/api/sources/{item['id']}"
            enriched.append(item)
        return enriched

    def source(self, source_id: str) -> dict[str, Any]:
        for source in self.sources():
            if source["id"] == source_id:
                return source
        raise HTTPException(404, f"unknown source: {source_id}")

    def inventory(self, req: SourceInventoryRequest) -> dict[str, Any]:
        source = self.source(req.source_id)
        root = Path(source["path"])
        if not root.is_dir():
            raise HTTPException(404, f"source is not mounted as a directory: {req.source_id}")
        base = safe_join(root, req.path)
        if not base.is_dir():
            raise HTTPException(404, "inventory path is not a directory")

        entries: list[dict[str, Any]] = []
        markers = {"git_repos": 0, "compose_files": 0, "archives": 0, "databases": 0, "manifests": 0}
        base_depth = len(base.relative_to(root).parts)
        for current, dirs, files in os.walk(base):
            current_path = Path(current)
            rel_current = current_path.relative_to(root)
            depth = len(rel_current.parts) - base_depth
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            if depth >= req.max_depth:
                dirs[:] = []

            if current_path == base and (current_path / ".git").exists():
                markers["git_repos"] += 1
                entries.append(self._entry(root, current_path, "dir", marker="git_repo"))
            for dirname in dirs:
                path = current_path / dirname
                marker = "git_repo" if (path / ".git").exists() else None
                if marker:
                    markers["git_repos"] += 1
                entries.append(self._entry(root, path, "dir", marker=marker))
                if len(entries) >= req.limit:
                    return self._inventory_result(source, req, markers, entries, truncated=True)
            for filename in files:
                path = current_path / filename
                marker = self._file_marker(path)
                if marker == "compose_file":
                    markers["compose_files"] += 1
                elif marker == "archive":
                    markers["archives"] += 1
                elif marker == "database":
                    markers["databases"] += 1
                elif marker == "manifest":
                    markers["manifests"] += 1
                entries.append(self._entry(root, path, "file", marker=marker))
                if len(entries) >= req.limit:
                    return self._inventory_result(source, req, markers, entries, truncated=True)
        return self._inventory_result(source, req, markers, entries, truncated=False)

    def markers(self, req: SourceInventoryRequest) -> dict[str, Any]:
        inventory = self.inventory(req)
        interesting = [entry for entry in inventory["entries"] if entry.get("marker")]
        return {
            "source": inventory["source"],
            "request": inventory["request"],
            "summary": inventory["summary"],
            "markers": interesting[: req.limit],
            "truncated": inventory["truncated"] or len(interesting) > req.limit,
        }

    def archive_manifest(self, req: SourceArchiveManifestRequest) -> dict[str, Any]:
        source = self.source(req.source_id)
        root = Path(source["path"])
        if not root.is_dir():
            raise HTTPException(404, f"source is not mounted as a directory: {req.source_id}")
        path = safe_join(root, req.path)
        if not path.is_file():
            raise HTTPException(404, "archive path is not a file")
        if path.suffix.lower() != ".zip":
            raise HTTPException(400, "only zip archive manifests are currently supported")
        entries = []
        nested_archives = 0
        manifests = 0
        total_uncompressed = 0
        try:
            with zipfile.ZipFile(path) as archive:
                infos = archive.infolist()
                for info in infos[: req.limit]:
                    marker = self._archive_member_marker(info.filename)
                    if marker == "archive":
                        nested_archives += 1
                    elif marker == "manifest":
                        manifests += 1
                    total_uncompressed += info.file_size
                    entries.append({
                        "path": info.filename,
                        "type": "dir" if info.is_dir() else "file",
                        "size": info.file_size,
                        "compressed_size": info.compress_size,
                        "marker": marker,
                    })
                truncated = len(infos) > req.limit
                entry_count = len(infos)
        except zipfile.BadZipFile as exc:
            raise HTTPException(400, f"bad zip file: {exc}") from exc
        return {
            "source": source,
            "archive": req.path,
            "policy": "manifest only; archive contents were not extracted",
            "summary": {
                "entries": entry_count,
                "listed": len(entries),
                "nested_archives_listed": nested_archives,
                "manifests_listed": manifests,
                "uncompressed_bytes_listed": total_uncompressed,
                "truncated": truncated,
            },
            "entries": entries,
        }

    def archive_member_read(self, req: SourceArchiveMemberReadRequest) -> dict[str, Any]:
        source = self.source(req.source_id)
        root = Path(source["path"])
        if not root.is_dir():
            raise HTTPException(404, f"source is not mounted as a directory: {req.source_id}")
        path = safe_join(root, req.path)
        if not path.is_file():
            raise HTTPException(404, "archive path is not a file")
        if path.suffix.lower() != ".zip":
            raise HTTPException(400, "only zip member reads are currently supported")
        try:
            with zipfile.ZipFile(path) as archive:
                try:
                    info = archive.getinfo(req.member_path)
                except KeyError as exc:
                    raise HTTPException(404, f"member not found: {req.member_path}") from exc
                if info.is_dir():
                    raise HTTPException(400, "member is a directory")
                with archive.open(info) as handle:
                    data = handle.read(req.max_bytes + 1)
        except zipfile.BadZipFile as exc:
            raise HTTPException(400, f"bad zip file: {exc}") from exc
        truncated = len(data) > req.max_bytes
        data = data[: req.max_bytes]
        return {
            "source": source,
            "archive": req.path,
            "member_path": req.member_path,
            "policy": "read one zip member into memory; no archive extraction to disk",
            "bytes_read": len(data),
            "truncated": truncated,
            "marker": self._archive_member_marker(req.member_path),
            "content": data.decode("utf-8", errors="replace"),
        }

    def archive_corpus_summary(self, req: SourceArchiveCorpusSummaryRequest) -> dict[str, Any]:
        source = self.source(req.source_id)
        root = Path(source["path"])
        if not root.is_dir():
            raise HTTPException(404, f"source is not mounted as a directory: {req.source_id}")
        path = safe_join(root, req.path)
        if not path.is_file():
            raise HTTPException(404, "archive path is not a file")
        if path.suffix.lower() != ".zip":
            raise HTTPException(400, "only zip corpus summaries are currently supported")
        try:
            with zipfile.ZipFile(path) as archive:
                manifest_name = self._find_manifest_member(archive)
                if not manifest_name:
                    raise HTTPException(404, "no MANIFEST.md member found")
                with archive.open(manifest_name) as handle:
                    data = handle.read(req.max_bytes + 1)
        except zipfile.BadZipFile as exc:
            raise HTTPException(400, f"bad zip file: {exc}") from exc
        truncated = len(data) > req.max_bytes
        text = data[: req.max_bytes].decode("utf-8", errors="replace")
        parsed = self._parse_corpus_manifest(text)
        return {
            "source": source,
            "archive": req.path,
            "manifest_member": manifest_name,
            "policy": "parsed MANIFEST.md from zip without extracting archive contents",
            "truncated": truncated,
            "summary": parsed,
        }

    def archive_triage(self, req: ArchiveTriageRequest) -> dict[str, Any]:
        source_ids = req.source_ids or [
            source["id"]
            for source in self.sources()
            if source["id"] != "repo_kernel_repos" and source.get("exists")
        ]
        archives = []
        source_summaries = []
        for source_id in source_ids:
            markers = self.markers(SourceInventoryRequest(
                source_id=source_id,
                path=".",
                max_depth=req.max_depth,
                limit=req.limit_per_source,
            ))
            archive_entries = [entry for entry in markers.get("markers", []) if entry.get("marker") == "archive"]
            source_summaries.append({
                "source_id": source_id,
                "archives_seen": len(archive_entries),
                "truncated": markers.get("truncated", False),
            })
            for entry in archive_entries:
                archives.append({
                    "source_id": source_id,
                    "source_role": markers["source"].get("role"),
                    "path": entry["path"],
                    "name": entry["name"],
                    "size": entry.get("size") or 0,
                    "domain": self._archive_domain(entry["name"]),
                    "priority": self._archive_priority(entry["name"], entry.get("size") or 0),
                    "next_step": "inspect zip manifest without extraction" if entry["name"].lower().endswith(".zip") else "record only until extractor support is added",
                })
        archives.sort(key=lambda item: (-item["priority"], item["size"], item["path"]))
        return {
            "policy": "triage only; no archive extraction or deletion decisions",
            "request": req.model_dump(),
            "sources": source_summaries,
            "archive_count_seen": len(archives),
            "archives": archives[: req.result_limit],
            "truncated": len(archives) > req.result_limit or any(item["truncated"] for item in source_summaries),
        }

    def archive_compare(self, req: ArchiveCompareRequest) -> dict[str, Any]:
        compared = []
        signatures = []
        outer_hashes = []
        for ref in req.archives:
            source = self.source(ref.source_id)
            root = Path(source["path"])
            path = safe_join(root, ref.path)
            if not path.is_file():
                raise HTTPException(404, f"archive path is not a file: {ref.source_id}:{ref.path}")
            if path.suffix.lower() != ".zip":
                raise HTTPException(400, f"only zip comparison is currently supported: {ref.path}")
            signature = self._zip_member_signature(path)
            signatures.append(signature["signature_hash"])
            outer_hash = self._file_sha256(path) if req.include_outer_hash else None
            if outer_hash:
                outer_hashes.append(outer_hash)
            compared.append({
                "source_id": ref.source_id,
                "source_role": source.get("role"),
                "path": ref.path,
                "size": path.stat().st_size,
                "signature_hash": signature["signature_hash"],
                "entry_count": signature["entry_count"],
                "uncompressed_bytes": signature["uncompressed_bytes"],
                "outer_sha256": outer_hash,
            })
        return {
            "policy": "comparison only; archives were not extracted and no deletion is approved",
            "archives": compared,
            "same_member_signature": len(set(signatures)) == 1,
            "same_outer_hash": len(set(outer_hashes)) == 1 if req.include_outer_hash else None,
            "classification": self._archive_compare_classification(signatures, outer_hashes, req.include_outer_hash),
        }

    def archive_duplicate_candidates(self, req: ArchiveDuplicateCandidateRequest) -> dict[str, Any]:
        triage = self.archive_triage(ArchiveTriageRequest(
            source_ids=req.source_ids,
            max_depth=req.max_depth,
            limit_per_source=req.limit_per_source,
            result_limit=req.result_limit,
        ))
        groups: dict[tuple[str, int], list[dict[str, Any]]] = {}
        for archive in triage.get("archives", []):
            key = (archive["name"].lower(), int(archive.get("size") or 0))
            groups.setdefault(key, []).append(archive)

        candidates = []
        compared = 0
        for (name, size), archives in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0][0])):
            if len(archives) < 2:
                continue
            candidate = {
                "name": name,
                "size": size,
                "copies": len(archives),
                "archives": archives,
                "comparison": None,
            }
            if compared < req.compare_limit and all(item["name"].lower().endswith(".zip") for item in archives):
                comparison = self.archive_compare(ArchiveCompareRequest(
                    archives=[ArchiveRef(source_id=item["source_id"], path=item["path"]) for item in archives],
                    include_outer_hash=False,
                ))
                candidate["comparison"] = {
                    "same_member_signature": comparison["same_member_signature"],
                    "classification": comparison["classification"],
                }
                compared += 1
            candidates.append(candidate)
        return {
            "policy": "candidate duplicate report only; review before deletion or archival",
            "request": req.model_dump(),
            "triage_truncated": triage.get("truncated", False),
            "candidate_count": len(candidates),
            "compared_groups": compared,
            "candidates": candidates[: req.result_limit],
        }

    def cleanup_evidence(self, req: CleanupEvidenceRequest) -> dict[str, Any]:
        duplicate_report = self.archive_duplicate_candidates(ArchiveDuplicateCandidateRequest(
            source_ids=req.source_ids,
            max_depth=req.max_depth,
            limit_per_source=req.limit_per_source,
            result_limit=req.result_limit,
            compare_limit=50,
        ))
        duplicate_actions = []
        potential_reclaim = 0
        for candidate in duplicate_report.get("candidates", []):
            comparison = candidate.get("comparison") or {}
            if comparison.get("same_member_signature"):
                archives = candidate.get("archives", [])
                retain = self._preferred_archive_retention(archives)
                archive_candidates = [item for item in archives if item is not retain]
                potential_reclaim += sum(int(item.get("size") or 0) for item in archive_candidates)
                duplicate_actions.append({
                    "name": candidate["name"],
                    "classification": comparison.get("classification"),
                    "copies": candidate.get("copies"),
                    "retain_candidate": retain,
                    "archive_candidates": archive_candidates,
                    "status": "candidate_only_requires_user_approval",
                })

        corpus_refs = req.corpus_archives or [
            ArchiveRef(source_id="parts_factory", path="agenthub-corpus.zip"),
            ArchiveRef(source_id="parts_factory", path="mmdb-corpus.zip"),
            ArchiveRef(source_id="parts_factory", path="tmn-corpus.zip"),
        ]
        corpus_summaries = []
        for ref in corpus_refs:
            try:
                summary = self.archive_corpus_summary(SourceArchiveCorpusSummaryRequest(source_id=ref.source_id, path=ref.path))
                corpus_summaries.append({
                    "source_id": ref.source_id,
                    "path": ref.path,
                    "summary": summary["summary"],
                })
            except HTTPException as exc:
                corpus_summaries.append({
                    "source_id": ref.source_id,
                    "path": ref.path,
                    "error": exc.detail,
                })

        return {
            "policy": "non-destructive evidence ledger; no files are deleted, moved, extracted, or modified",
            "duplicate_evidence": {
                "candidate_groups": duplicate_report.get("candidate_count", 0),
                "compared_groups": duplicate_report.get("compared_groups", 0),
                "potential_reclaim_bytes_if_approved": potential_reclaim,
                "actions": duplicate_actions,
                "triage_truncated": duplicate_report.get("triage_truncated", False),
            },
            "corpus_evidence": corpus_summaries,
            "next_steps": [
                "review content-equivalent archive groups before any deletion or archival",
                "prefer archiving duplicate candidates to compressed cold storage before deletion",
                "feed MMDB and TMN corpus summaries into memory/runtime planning",
                "extend duplicate detection beyond archives with file-level hashes in bounded slices",
            ],
        }

    def file_hash_slice(self, req: FileHashSliceRequest) -> dict[str, Any]:
        source = self.source(req.source_id)
        root = Path(source["path"])
        if not root.is_dir():
            raise HTTPException(404, f"source is not mounted as a directory: {req.source_id}")
        base = safe_join(root, req.path)
        if not base.is_dir():
            raise HTTPException(404, "hash slice path is not a directory")
        suffixes = self._normalized_suffixes(req.include_suffixes)
        entries = []
        skipped = {"too_large": 0, "suffix": 0, "errors": 0}
        base_depth = len(base.relative_to(root).parts)
        for current, dirs, files in os.walk(base):
            current_path = Path(current)
            rel_current = current_path.relative_to(root)
            depth = len(rel_current.parts) - base_depth
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            if depth >= req.max_depth:
                dirs[:] = []
            for filename in files:
                path = current_path / filename
                if suffixes and path.suffix.lower() not in suffixes:
                    skipped["suffix"] += 1
                    continue
                try:
                    size = path.stat().st_size
                except OSError:
                    skipped["errors"] += 1
                    continue
                if size > req.max_file_bytes:
                    skipped["too_large"] += 1
                    continue
                try:
                    digest = self._file_sha256(path)
                except OSError:
                    skipped["errors"] += 1
                    continue
                entries.append({
                    "source_id": req.source_id,
                    "path": str(path.relative_to(root)).replace("\\", "/"),
                    "name": path.name,
                    "size": size,
                    "sha256": digest,
                    "marker": self._file_marker(path),
                })
                if len(entries) >= req.limit:
                    return self._hash_slice_result(source, req.model_dump(), entries, skipped, truncated=True)
        return self._hash_slice_result(source, req.model_dump(), entries, skipped, truncated=False)

    def archive_hash_slice(self, req: ArchiveHashSliceRequest) -> dict[str, Any]:
        source = self.source(req.source_id)
        root = Path(source["path"])
        if not root.is_dir():
            raise HTTPException(404, f"source is not mounted as a directory: {req.source_id}")
        path = safe_join(root, req.path)
        if not path.is_file():
            raise HTTPException(404, "archive path is not a file")
        if path.suffix.lower() != ".zip":
            raise HTTPException(400, "only zip member hash slices are currently supported")
        suffixes = self._normalized_suffixes(req.include_suffixes)
        entries = []
        skipped = {"too_large": 0, "suffix": 0, "errors": 0, "directories": 0}
        try:
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        skipped["directories"] += 1
                        continue
                    member_suffix = Path(info.filename).suffix.lower()
                    if suffixes and member_suffix not in suffixes:
                        skipped["suffix"] += 1
                        continue
                    if info.file_size > req.max_member_bytes:
                        skipped["too_large"] += 1
                        continue
                    try:
                        digest = self._zip_member_sha256(archive, info)
                    except OSError:
                        skipped["errors"] += 1
                        continue
                    entries.append({
                        "source_id": req.source_id,
                        "archive": req.path,
                        "member_path": info.filename,
                        "name": Path(info.filename).name,
                        "size": info.file_size,
                        "compressed_size": info.compress_size,
                        "sha256": digest,
                        "crc": info.CRC,
                        "marker": self._archive_member_marker(info.filename),
                    })
                    if len(entries) >= req.limit:
                        return self._hash_slice_result(source, req.model_dump(), entries, skipped, truncated=True)
        except zipfile.BadZipFile as exc:
            raise HTTPException(400, f"bad zip file: {exc}") from exc
        return self._hash_slice_result(source, req.model_dump(), entries, skipped, truncated=False)

    def hash_slice_batch(self, req: HashSliceBatchRequest) -> dict[str, Any]:
        slices = []
        entries = []
        truncated = False
        for file_req in req.file_slices:
            result = self.file_hash_slice(file_req)
            slices.append({"type": "file", "request": file_req.model_dump(), "summary": result["summary"]})
            for entry in result["entries"]:
                entries.append({**entry, "slice_type": "file"})
                if len(entries) >= req.entry_limit:
                    truncated = True
                    break
            if truncated:
                break
        if not truncated:
            for archive_req in req.archive_slices:
                result = self.archive_hash_slice(archive_req)
                slices.append({"type": "archive", "request": archive_req.model_dump(), "summary": result["summary"]})
                for entry in result["entries"]:
                    entries.append({**entry, "slice_type": "archive"})
                    if len(entries) >= req.entry_limit:
                        truncated = True
                        break
                if truncated:
                    break
        grouped = self._hash_slice_result(
            {"id": "batch", "label": "Hash Slice Batch", "role": "cross_source_evidence"},
            req.model_dump(),
            entries,
            {"too_large": 0, "suffix": 0, "errors": 0},
            truncated=truncated,
        )
        grouped["slices"] = slices
        grouped["policy"] = "bounded cross-source hash batch; no files are modified, moved, deleted, or extracted to disk"
        return grouped

    def archive_sqlite_quarantine_probe(self, req: ArchiveSQLiteQuarantineProbeRequest) -> dict[str, Any]:
        source = self.source(req.source_id)
        root = Path(source["path"])
        if not root.is_dir():
            raise HTTPException(404, f"source is not mounted as a directory: {req.source_id}")
        archive_path = safe_join(root, req.archive)
        if not archive_path.is_file():
            raise HTTPException(404, "archive path is not a file")
        if archive_path.suffix.lower() != ".zip":
            raise HTTPException(400, "only zip archive quarantine probes are currently supported")
        member_suffix = Path(req.member_path).suffix.lower()
        if member_suffix not in self.DB_SUFFIXES:
            raise HTTPException(400, "quarantine schema probe only accepts SQLite-like database members")

        try:
            with zipfile.ZipFile(archive_path) as archive:
                try:
                    info = archive.getinfo(req.member_path)
                except KeyError as exc:
                    raise HTTPException(404, f"member not found: {req.member_path}") from exc
                if info.is_dir():
                    raise HTTPException(400, "member is a directory")
                if info.file_size > req.max_member_bytes:
                    return {
                        "source": source,
                        "archive": req.archive,
                        "member_path": req.member_path,
                        "policy": "approval-gated quarantine extraction only; source archive is read-only",
                        "status": "too_large_for_current_gate",
                        "member": self._zip_member_record(req, info),
                        "next_step": "use file breakdown plan or raise max_member_bytes after review",
                    }
                member_digest = self._zip_member_sha256(archive, info)
                target = self._quarantine_target(req.source_id, req.archive, req.member_path, member_digest)
                if not req.approved:
                    return {
                        "source": source,
                        "archive": req.archive,
                        "member_path": req.member_path,
                        "policy": "plan only; set approved=true to extract this member into repo-kernel quarantine",
                        "status": "approval_required",
                        "member": self._zip_member_record(req, info, member_digest),
                        "quarantine_target": str(target),
                        "schema_probe": None,
                    }
                extracted = self._extract_zip_member_to_quarantine(archive, info, target, req.replace_existing)
        except zipfile.BadZipFile as exc:
            raise HTTPException(400, f"bad zip file: {exc}") from exc

        schema_probe = self._sqlite_schema_probe(target, table_limit=req.table_limit, count_rows=req.count_rows)
        return {
            "source": source,
            "archive": req.archive,
            "member_path": req.member_path,
            "policy": "source archive remained read-only; selected database member was copied to repo-kernel quarantine and opened SQLite read-only",
            "status": "probed",
            "member": {
                "size": extracted["size"],
                "sha256": extracted["sha256"],
                "quarantine_path": str(target),
                "extraction": extracted["status"],
            },
            "schema_probe": schema_probe,
            "next_gates": [
                "review table names, columns, and row counts",
                "map useful tables to unified memory contract",
                "write Postgres only after explicit approval and a backup/export receipt",
            ],
        }

    def file_breakdown_plan(self, req: FileBreakdownPlanRequest) -> dict[str, Any]:
        source = self.source(req.source_id)
        root = Path(source["path"])
        if not root.is_dir():
            raise HTTPException(404, f"source is not mounted as a directory: {req.source_id}")
        path = safe_join(root, req.path)
        if not path.is_file():
            raise HTTPException(404, "breakdown path is not a file")

        if req.archive_member_path:
            if path.suffix.lower() != ".zip":
                raise HTTPException(400, "archive_member_path can only be used with zip archives")
            try:
                with zipfile.ZipFile(path) as archive:
                    try:
                        info = archive.getinfo(req.archive_member_path)
                    except KeyError as exc:
                        raise HTTPException(404, f"member not found: {req.archive_member_path}") from exc
                    target_name = info.filename
                    target_size = info.file_size
                    target_suffix = Path(info.filename).suffix.lower()
                    marker = self._archive_member_marker(info.filename)
            except zipfile.BadZipFile as exc:
                raise HTTPException(400, f"bad zip file: {exc}") from exc
            subject = {
                "kind": "zip_member",
                "source_id": req.source_id,
                "archive": req.path,
                "member_path": req.archive_member_path,
                "name": Path(target_name).name,
            }
        else:
            target_name = path.name
            target_size = path.stat().st_size
            target_suffix = path.suffix.lower()
            marker = self._file_marker(path)
            subject = {
                "kind": "file",
                "source_id": req.source_id,
                "path": req.path,
                "name": target_name,
            }

        chunk_count = max(1, (target_size + req.target_chunk_bytes - 1) // req.target_chunk_bytes)
        truncated = chunk_count > req.max_chunks
        strategy = self._breakdown_strategy(target_suffix, marker, bool(req.archive_member_path))
        return {
            "policy": "plan only; no file is split, extracted, moved, deleted, or parsed",
            "request": req.model_dump(),
            "subject": {
                **subject,
                "size": target_size,
                "suffix": target_suffix,
                "marker": marker,
            },
            "strategy": strategy,
            "chunk_plan": {
                "target_chunk_bytes": req.target_chunk_bytes,
                "estimated_chunks": chunk_count,
                "listed_chunks": min(chunk_count, req.max_chunks),
                "truncated": truncated,
                "ranges": self._byte_ranges(target_size, req.target_chunk_bytes, req.max_chunks),
            },
            "fallback_gates": [
                "try normal manifest/hash/schema probe first",
                "materialize chunks only inside repo-kernel quarantine after approval",
                "keep chunk receipts with source path, byte range, size, and sha256",
                "merge/import only after a successful parser-specific validation pass",
            ],
            "parsing_failure": req.parsing_failure,
        }

    def quarantine_sqlite_preview(self, req: QuarantineSQLitePreviewRequest) -> dict[str, Any]:
        path = self._quarantine_path(req.path)
        if not path.is_file():
            raise HTTPException(404, "quarantined SQLite file not found")
        schema = self._sqlite_schema_probe(path, table_limit=500, count_rows=True)
        table_objects = [item for item in schema["objects"] if item["type"] == "table"]
        if req.tables:
            requested = set(req.tables)
            missing = sorted(requested - {item["name"] for item in table_objects})
            if missing:
                raise HTTPException(404, f"tables not found in quarantined SQLite file: {', '.join(missing)}")
            table_objects = [item for item in table_objects if item["name"] in requested]
        table_objects = sorted(
            table_objects,
            key=lambda item: (
                self._agentic_role_score(item["name"], item.get("columns", [])),
                item.get("row_count") if item.get("row_count") is not None else 0,
                item["name"],
            ),
            reverse=True,
        )[: req.table_limit]

        previews = []
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro&immutable=1", uri=True)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only=ON")
            for table in table_objects:
                table_name = table["name"]
                query = (
                    f"SELECT * FROM {self._sqlite_quote(table_name)} "
                    f"LIMIT {int(req.row_limit)} OFFSET {int(req.row_offset)}"
                )
                try:
                    rows = conn.execute(query).fetchall()
                    row_error = None
                except sqlite3.Error as exc:
                    rows = []
                    row_error = str(exc)
                sample_rows = [
                    {
                        key: self._sqlite_cell_preview(row[key], req.max_cell_chars)
                        for key in row.keys()
                    }
                    for row in rows
                ]
                previews.append({
                    "table": table_name,
                    "agentic_role": self._agentic_table_role(table_name, table.get("columns", [])),
                    "row_count": table.get("row_count"),
                    "sampled_rows": len(sample_rows),
                    "row_error": row_error,
                    "columns": table.get("columns", []),
                    "sample_rows": sample_rows,
                    "memory_mapping_hints": self._memory_mapping_hints(table_name, table.get("columns", [])),
                })
        except sqlite3.Error as exc:
            raise HTTPException(400, f"SQLite read-only preview failed: {exc}") from exc
        finally:
            if conn:
                conn.close()

        return {
            "policy": "read-only preview of a quarantined SQLite copy; no source evidence mutation and no Postgres writes",
            "request": req.model_dump(),
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": self._file_sha256(path),
            "schema": schema if req.include_schema else None,
            "agentic_summary": self._agentic_sqlite_summary(schema, previews),
            "previews": previews,
            "next_gates": [
                "select tables that carry durable agent memory or evidence provenance",
                "derive deterministic row identity hashes before any import",
                "map columns to atom/content/receipt/provenance/vector/lattice fields",
                "write Postgres only after explicit approval and export receipt",
            ],
        }

    def mmdb_import_dry_run(self, req: MMDBImportDryRunRequest) -> dict[str, Any]:
        path = self._quarantine_path(req.path)
        if not path.is_file():
            raise HTTPException(404, "quarantined SQLite file not found")
        db_sha = self._file_sha256(path)
        schema = self._sqlite_schema_probe(path, table_limit=500, count_rows=True)
        table_objects = [item for item in schema["objects"] if item["type"] == "table"]
        if req.tables:
            requested = set(req.tables)
            missing = sorted(requested - {item["name"] for item in table_objects})
            if missing:
                raise HTTPException(404, f"tables not found in quarantined SQLite file: {', '.join(missing)}")
            table_objects = [item for item in table_objects if item["name"] in requested]
        table_objects = sorted(
            table_objects,
            key=lambda item: (
                self._agentic_role_score(item["name"], item.get("columns", [])),
                item.get("row_count") if item.get("row_count") is not None else 0,
                item["name"],
            ),
            reverse=True,
        )[: req.table_limit]

        table_results = []
        total_candidate_rows = 0
        total_evaluated_rows = 0
        total_sample_records = 0
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro&immutable=1", uri=True)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only=ON")
            for table in table_objects:
                table_name = table["name"]
                row_count = int(table.get("row_count") or 0)
                total_candidate_rows += row_count
                evaluated_limit = min(req.max_rows_per_table, max(0, row_count - req.row_offset))
                rows = conn.execute(
                    (
                        f"SELECT * FROM {self._sqlite_quote(table_name)} "
                        f"LIMIT {int(evaluated_limit)} OFFSET {int(req.row_offset)}"
                    )
                ).fetchall() if evaluated_limit else []
                transformed = [
                    self._mmdb_transform_candidate(
                        path=path,
                        db_sha=db_sha,
                        table=table,
                        row=dict(row),
                        max_cell_chars=req.max_cell_chars,
                    )
                    for row in rows
                ]
                validation = self._mmdb_table_validation(table_name, table.get("columns", []), rows)
                samples = transformed[: req.sample_limit] if req.include_samples else []
                total_evaluated_rows += len(rows)
                total_sample_records += len(samples)
                table_results.append({
                    "table": table_name,
                    "mapping": self._mmdb_table_mapping(table_name, table.get("columns", [])),
                    "agentic_role": self._agentic_table_role(table_name, table.get("columns", [])),
                    "candidate_rows": row_count,
                    "evaluated_rows": len(rows),
                    "evaluation_truncated": row_count > req.row_offset + len(rows),
                    "validation": validation,
                    "sample_records": samples,
                })
        except sqlite3.Error as exc:
            raise HTTPException(400, f"SQLite read-only import dry-run failed: {exc}") from exc
        finally:
            if conn:
                conn.close()

        return {
            "workflow": "memory",
            "operation": "mmdb_import_dry_run",
            "policy": "read-only dry run against quarantined SQLite; no source evidence mutation and no Postgres writes",
            "request": req.model_dump(),
            "source": {
                "quarantine_path": str(path),
                "size": path.stat().st_size,
                "sha256": db_sha,
            },
            "unified_memory_contract": self._unified_memory_contract(),
            "summary": {
                "tables_considered": len(table_results),
                "candidate_rows": total_candidate_rows,
                "evaluated_rows": total_evaluated_rows,
                "sample_records": total_sample_records,
                "postgres_writes": 0,
                "requires_approval_for_write": True,
            },
            "tables": table_results,
            "recipe": {
                "identity": "row_hash = sha256(contract_version + db_sha + table + primary_key + canonical_row_json)",
                "dedupe": "skip or merge rows with identical source row_hash in the target memory ledger",
                "provenance": "preserve quarantine path, db sha256, table, primary key, row hash, and source member receipt",
                "write_gate": "explicit user approval plus backup/export receipt before any Postgres write",
            },
            "next_gates": [
                "review sample transformed records for semantic correctness",
                "persist this dry-run as an import recipe artifact",
                "compare target fields against live memory API surfaces",
                "request explicit approval before any write-capable importer is added",
            ],
        }

    def _extra_sources(self) -> list[dict[str, Any]]:
        raw = os.environ.get("REPO_KERNEL_SOURCE_ROOTS", "").strip()
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        sources = []
        for item in data:
            if isinstance(item, dict) and item.get("id") and item.get("path"):
                sources.append({
                    "id": item["id"],
                    "label": item.get("label", item["id"]),
                    "role": item.get("role", "external_evidence"),
                    "path": item["path"],
                    "access": item.get("access", "ro"),
                    "priority": int(item.get("priority", 50)),
                })
        return sources

    def _entry(self, root: Path, path: Path, kind: str, marker: str | None = None) -> dict[str, Any]:
        try:
            stat = path.stat()
            size = stat.st_size if path.is_file() else None
        except OSError:
            size = None
        return {
            "type": kind,
            "path": str(path.relative_to(root)).replace("\\", "/") or ".",
            "name": path.name,
            "marker": marker,
            "size": size,
        }

    def _file_marker(self, path: Path) -> str | None:
        name = path.name
        suffix = path.suffix.lower()
        if self.COMPOSE_NAMES.match(name) or ("compose" in name.lower() and suffix in {".yml", ".yaml"}):
            return "compose_file"
        if suffix in self.DB_SUFFIXES:
            return "database"
        if suffix in self.ARCHIVE_SUFFIXES:
            return "archive"
        if name in self.MANIFEST_NAMES:
            return "manifest"
        return None

    def _archive_member_marker(self, name: str) -> str | None:
        member = Path(name)
        suffix = member.suffix.lower()
        if suffix in self.ARCHIVE_SUFFIXES:
            return "archive"
        lowered = name.lower()
        if self.COMPOSE_NAMES.match(member.name) or ("compose" in lowered and suffix in {".yml", ".yaml"}):
            return "compose_file"
        if suffix in self.DB_SUFFIXES:
            return "database"
        if member.name in self.MANIFEST_NAMES:
            return "manifest"
        return None

    def _zip_member_signature(self, path: Path) -> dict[str, Any]:
        try:
            with zipfile.ZipFile(path) as archive:
                members = sorted(
                    (info.filename, info.file_size, info.CRC)
                    for info in archive.infolist()
                    if not info.is_dir()
                )
        except zipfile.BadZipFile as exc:
            raise HTTPException(400, f"bad zip file: {exc}") from exc
        digest = hashlib.sha256(json.dumps(members, separators=(",", ":")).encode("utf-8")).hexdigest()
        return {
            "signature_hash": digest,
            "entry_count": len(members),
            "uncompressed_bytes": sum(size for _, size, _ in members),
        }

    def _zip_member_sha256(self, archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
        digest = hashlib.sha256()
        with archive.open(info) as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _zip_member_record(
        self,
        req: ArchiveSQLiteQuarantineProbeRequest,
        info: zipfile.ZipInfo,
        digest: str | None = None,
    ) -> dict[str, Any]:
        return {
            "source_id": req.source_id,
            "archive": req.archive,
            "member_path": info.filename,
            "name": Path(info.filename).name,
            "size": info.file_size,
            "compressed_size": info.compress_size,
            "crc": info.CRC,
            "sha256": digest,
            "marker": self._archive_member_marker(info.filename),
        }

    def _quarantine_target(self, source_id: str, archive_path: str, member_path: str, digest: str) -> Path:
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(member_path).name).strip("._") or "member.sqlite"
        target_dir = QUARANTINE_ROOT / "sqlite" / stable_id("artifact", f"{source_id}-{archive_path}-{member_path}-{digest}")
        target = (target_dir / safe_name).resolve()
        root = QUARANTINE_ROOT.resolve()
        if not is_relative_to(target, root):
            raise HTTPException(400, "quarantine target escapes quarantine root")
        return target

    def _quarantine_path(self, raw_path: str) -> Path:
        root = QUARANTINE_ROOT.resolve()
        if raw_path.startswith("/kernel/quarantine"):
            path = Path(raw_path)
        else:
            if raw_path.startswith(("/", "\\")):
                raise HTTPException(400, "quarantine preview path must be under /kernel/quarantine or relative to it")
            path = QUARANTINE_ROOT / raw_path
        path = path.resolve()
        if not is_relative_to(path, root):
            raise HTTPException(400, "path escapes quarantine root")
        return path

    def _extract_zip_member_to_quarantine(
        self,
        archive: zipfile.ZipFile,
        info: zipfile.ZipInfo,
        target: Path,
        replace_existing: bool,
    ) -> dict[str, Any]:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not replace_existing:
            return {
                "status": "reused_existing",
                "path": str(target),
                "size": target.stat().st_size,
                "sha256": self._file_sha256(target),
            }
        digest = hashlib.sha256()
        size = 0
        with archive.open(info) as handle, target.open("wb") as output:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
                output.write(chunk)
                size += len(chunk)
        receipt = {
            "created_at": utc_now(),
            "source_member": {
                "filename": info.filename,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "crc": info.CRC,
            },
            "quarantine_path": str(target),
            "sha256": digest.hexdigest(),
            "policy": "quarantine copy only; source archive untouched",
        }
        target.with_suffix(target.suffix + ".receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        return {
            "status": "extracted",
            "path": str(target),
            "size": size,
            "sha256": digest.hexdigest(),
        }

    def _sqlite_schema_probe(self, path: Path, table_limit: int, count_rows: bool) -> dict[str, Any]:
        if not path.is_file():
            raise HTTPException(404, "quarantined SQLite file not found")
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro&immutable=1", uri=True)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only=ON")
            rows = conn.execute(
                """
                SELECT type, name, tbl_name, sql
                FROM sqlite_master
                WHERE type IN ('table', 'view')
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY type, name
                LIMIT ?
                """,
                (table_limit,),
            ).fetchall()
            objects = []
            for row in rows:
                name = row["name"]
                columns = conn.execute(f"PRAGMA table_info({self._sqlite_quote(name)})").fetchall()
                count = None
                count_error = None
                if count_rows and row["type"] == "table":
                    try:
                        count = conn.execute(f"SELECT COUNT(*) AS c FROM {self._sqlite_quote(name)}").fetchone()["c"]
                    except sqlite3.Error as exc:
                        count_error = str(exc)
                objects.append({
                    "type": row["type"],
                    "name": name,
                    "table": row["tbl_name"],
                    "row_count": count,
                    "row_count_error": count_error,
                    "columns": [
                        {
                            "name": column["name"],
                            "type": column["type"],
                            "notnull": bool(column["notnull"]),
                            "primary_key": bool(column["pk"]),
                        }
                        for column in columns
                    ],
                    "sql_preview": (row["sql"] or "")[:500],
                })
            total_objects = conn.execute(
                """
                SELECT COUNT(*) AS c
                FROM sqlite_master
                WHERE type IN ('table', 'view')
                  AND name NOT LIKE 'sqlite_%'
                """
            ).fetchone()["c"]
        except sqlite3.Error as exc:
            raise HTTPException(400, f"SQLite read-only schema probe failed: {exc}") from exc
        finally:
            if conn:
                conn.close()
        return {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": self._file_sha256(path),
            "total_objects": total_objects,
            "listed_objects": len(objects),
            "truncated": total_objects > len(objects),
            "objects": objects,
        }

    def _sqlite_quote(self, name: str) -> str:
        return '"' + name.replace('"', '""') + '"'

    def _sqlite_cell_preview(self, value: Any, max_chars: int) -> dict[str, Any]:
        if value is None:
            return {"type": "null", "value": None}
        if isinstance(value, bytes):
            return {
                "type": "bytes",
                "length": len(value),
                "sha256": hashlib.sha256(value).hexdigest(),
                "preview_hex": value[: min(32, len(value))].hex(),
            }
        if isinstance(value, (int, float)):
            return {"type": type(value).__name__, "value": value}
        text = str(value)
        encoded = text.encode("utf-8", errors="replace")
        return {
            "type": "text",
            "length": len(text),
            "byte_length": len(encoded),
            "truncated": len(text) > max_chars,
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "preview": text[:max_chars],
        }

    def _agentic_table_role(self, table_name: str, columns: list[dict[str, Any]]) -> dict[str, Any]:
        haystack = " ".join([table_name] + [column.get("name", "") for column in columns]).lower()
        roles = []
        role_tokens = {
            "agent_memory": ["memory", "atom", "content", "message", "conversation", "session", "preference"],
            "receipt_provenance": ["receipt", "provenance", "source", "hash", "sha", "stored_at", "created_at"],
            "geometry_lattice": ["lattice", "coordinate", "vector", "embedding", "e8", "node"],
            "workflow_event": ["event", "log", "run", "task", "status", "checkpoint"],
            "knowledge_document": ["document", "chunk", "text", "summary", "title", "path"],
            "identity": ["agent", "user", "owner", "persona", "identity"],
        }
        for role, tokens in role_tokens.items():
            hits = [token for token in tokens if token in haystack]
            if hits:
                roles.append({"role": role, "hits": hits})
        return {
            "primary": roles[0]["role"] if roles else "unknown",
            "roles": roles,
            "score": self._agentic_role_score(table_name, columns),
        }

    def _agentic_role_score(self, table_name: str, columns: list[dict[str, Any]]) -> int:
        role = self._agentic_table_role_no_score(table_name, columns)
        return sum(len(item["hits"]) for item in role)

    def _agentic_table_role_no_score(self, table_name: str, columns: list[dict[str, Any]]) -> list[dict[str, Any]]:
        haystack = " ".join([table_name] + [column.get("name", "") for column in columns]).lower()
        role_tokens = {
            "agent_memory": ["memory", "atom", "content", "message", "conversation", "session", "preference"],
            "receipt_provenance": ["receipt", "provenance", "source", "hash", "sha", "stored_at", "created_at"],
            "geometry_lattice": ["lattice", "coordinate", "vector", "embedding", "e8", "node"],
            "workflow_event": ["event", "log", "run", "task", "status", "checkpoint"],
            "knowledge_document": ["document", "chunk", "text", "summary", "title", "path"],
            "identity": ["agent", "user", "owner", "persona", "identity"],
        }
        roles = []
        for role, tokens in role_tokens.items():
            hits = [token for token in tokens if token in haystack]
            if hits:
                roles.append({"role": role, "hits": hits})
        return roles

    def _memory_mapping_hints(self, table_name: str, columns: list[dict[str, Any]]) -> dict[str, Any]:
        names = [column.get("name", "") for column in columns]
        lowered = {name.lower(): name for name in names}

        def first(*tokens: str) -> str | None:
            for token in tokens:
                for name in names:
                    if token in name.lower():
                        return name
            return None

        return {
            "candidate_atom_id": first("atom", "node_id", "id", "hash"),
            "candidate_content": first("payload", "receipt_json", "text", "message", "summary", "data", "coord_json"),
            "candidate_timestamp": first("created_at", "stored_at", "updated_at", "timestamp", "time"),
            "candidate_source_hash": first("sha", "hash", "item_hash"),
            "candidate_provenance": first("source", "path", "receipt", "provenance"),
            "has_json_like_columns": [
                name for name in names
                if any(token in name.lower() for token in ["json", "data", "metadata", "coordinates"])
            ],
            "primary_key_columns": [
                column["name"] for column in columns
                if column.get("primary_key")
            ],
            "suggested_identity": lowered.get("receipt_id")
            or lowered.get("node_id")
            or first("atom", "id", "hash")
            or "row_sha256",
        }

    def _agentic_sqlite_summary(self, schema: dict[str, Any], previews: list[dict[str, Any]]) -> dict[str, Any]:
        role_counts: dict[str, int] = {}
        row_total = 0
        for preview in previews:
            role = preview.get("agentic_role", {}).get("primary", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
            if preview.get("row_count") is not None:
                row_total += int(preview["row_count"])
        likely_memory_tables = [
            preview["table"]
            for preview in previews
            if preview.get("agentic_role", {}).get("primary") in {
                "agent_memory",
                "receipt_provenance",
                "knowledge_document",
                "workflow_event",
                "geometry_lattice",
            }
        ]
        return {
            "total_schema_objects": schema.get("total_objects"),
            "previewed_tables": len(previews),
            "previewed_row_count_total": row_total,
            "role_counts": role_counts,
            "likely_memory_tables": likely_memory_tables,
            "agent_use": [
                "use previews to identify durable memory, provenance, and workflow-event tables",
                "prefer row-level deterministic hashes for import identity",
                "preserve source archive, member path, quarantine path, and table name in every future atom receipt",
            ],
        }

    def _unified_memory_contract(self) -> dict[str, Any]:
        return {
            "version": "mmdb-readonly-dry-run-v1",
            "records": {
                "memory_atom": [
                    "atom_id",
                    "record_type",
                    "content",
                    "content_hash",
                    "timestamp",
                    "source",
                    "geometry",
                    "provenance",
                    "row_hash",
                ],
                "memory_edge": [
                    "edge_id",
                    "from_atom_id",
                    "to_atom_id",
                    "relation",
                    "cost",
                    "source",
                    "row_hash",
                ],
                "receipt": [
                    "receipt_id",
                    "run_id",
                    "step_id",
                    "controller",
                    "status",
                    "timestamp",
                    "receipt_json",
                    "source",
                    "row_hash",
                ],
            },
        }

    def _mmdb_table_mapping(self, table_name: str, columns: list[dict[str, Any]]) -> dict[str, Any]:
        if table_name == "receipts":
            return {
                "target_record": "receipt",
                "identity_columns": ["receipt_id"],
                "content_column": "receipt_json",
                "timestamp_column": "timestamp_utc",
                "semantic_role": "receipt provenance and workflow event history",
            }
        if table_name == "lattice_nodes":
            return {
                "target_record": "memory_atom",
                "identity_columns": ["node_id"],
                "content_column": "payload_json",
                "source_hash_column": "content_hash",
                "geometry_columns": ["lattice_type", "dim", "coord_json", "shell", "mass"],
                "semantic_role": "memory atom with E8/Leech geometry metadata",
            }
        if table_name == "lattice_edges":
            return {
                "target_record": "memory_edge",
                "identity_columns": ["node_id", "neighbor_id", "relation"],
                "semantic_role": "recall/traversal graph edge",
            }
        hints = self._memory_mapping_hints(table_name, columns)
        return {
            "target_record": "generic_memory_atom",
            "identity_columns": hints.get("primary_key_columns") or [hints.get("suggested_identity", "row_sha256")],
            "content_column": hints.get("candidate_content"),
            "timestamp_column": hints.get("candidate_timestamp"),
            "source_hash_column": hints.get("candidate_source_hash"),
            "semantic_role": "generic table; requires review before import",
        }

    def _mmdb_transform_candidate(
        self,
        path: Path,
        db_sha: str,
        table: dict[str, Any],
        row: dict[str, Any],
        max_cell_chars: int,
    ) -> dict[str, Any]:
        table_name = table["name"]
        columns = table.get("columns", [])
        mapping = self._mmdb_table_mapping(table_name, columns)
        identity_columns = mapping.get("identity_columns") or []
        primary_key = {
            column: row.get(column)
            for column in identity_columns
            if column in row
        }
        row_hash = self._mmdb_row_hash(db_sha, table_name, primary_key, row)
        source = {
            "quarantine_path": str(path),
            "db_sha256": db_sha,
            "table": table_name,
            "primary_key": primary_key,
            "row_hash": row_hash,
        }
        json_validation = {
            name: self._json_validation(row.get(name))
            for name in self._json_columns(columns)
        }

        if table_name == "receipts":
            receipt_id = str(row.get("receipt_id") or row_hash)
            return {
                "target_record": "receipt",
                "receipt_id": receipt_id,
                "atom_id": f"mmdb:receipt:{receipt_id}",
                "run_id": row.get("run_id"),
                "step_id": row.get("step_id"),
                "controller": row.get("controller"),
                "status": row.get("status"),
                "timestamp": row.get("timestamp_utc"),
                "content": self._sqlite_cell_preview(row.get("receipt_json"), max_cell_chars),
                "json_validation": json_validation,
                "source": source,
            }
        if table_name == "lattice_nodes":
            node_id = str(row.get("node_id") or row_hash)
            return {
                "target_record": "memory_atom",
                "atom_id": f"mmdb:node:{node_id}",
                "record_type": row.get("kind"),
                "content": self._sqlite_cell_preview(row.get("payload_json"), max_cell_chars),
                "content_hash": row.get("content_hash"),
                "geometry": {
                    "lattice_type": row.get("lattice_type"),
                    "dim": row.get("dim"),
                    "coord_json": self._sqlite_cell_preview(row.get("coord_json"), max_cell_chars),
                    "shell": row.get("shell"),
                    "mass": row.get("mass"),
                },
                "json_validation": json_validation,
                "source": source,
            }
        if table_name == "lattice_edges":
            edge_key = row_hash[:32]
            return {
                "target_record": "memory_edge",
                "edge_id": f"mmdb:edge:{edge_key}",
                "from_atom_id": f"mmdb:node:{row.get('node_id')}",
                "to_atom_id": f"mmdb:node:{row.get('neighbor_id')}",
                "relation": row.get("relation"),
                "cost": row.get("cost"),
                "json_validation": json_validation,
                "source": source,
            }
        return {
            "target_record": mapping.get("target_record", "generic_memory_atom"),
            "atom_id": f"mmdb:generic:{row_hash[:32]}",
            "content": {
                key: self._sqlite_cell_preview(value, max_cell_chars)
                for key, value in row.items()
            },
            "json_validation": json_validation,
            "source": source,
        }

    def _mmdb_table_validation(
        self,
        table_name: str,
        columns: list[dict[str, Any]],
        rows: list[sqlite3.Row],
    ) -> dict[str, Any]:
        json_columns = self._json_columns(columns)
        validation = {
            "evaluated_rows": len(rows),
            "json_columns": {},
            "required_field_errors": [],
        }
        for column in json_columns:
            stats = {"valid": 0, "invalid": 0, "null": 0, "types": {}, "sample_error": None}
            for row in rows:
                result = self._json_validation(row[column])
                if result["status"] == "null":
                    stats["null"] += 1
                elif result["valid"]:
                    stats["valid"] += 1
                    json_type = result.get("json_type", "unknown")
                    stats["types"][json_type] = stats["types"].get(json_type, 0) + 1
                else:
                    stats["invalid"] += 1
                    stats["sample_error"] = stats["sample_error"] or result.get("error")
            validation["json_columns"][column] = stats
        required = {
            "receipts": ["receipt_id", "run_id", "step_id", "controller", "receipt_json"],
            "lattice_nodes": ["node_id", "kind", "lattice_type", "coord_json"],
            "lattice_edges": ["node_id", "neighbor_id", "relation"],
        }.get(table_name, [])
        for row_index, row in enumerate(rows[:100]):
            for column in required:
                if row[column] in (None, ""):
                    validation["required_field_errors"].append({"row_index": row_index, "column": column})
        return validation

    def _json_columns(self, columns: list[dict[str, Any]]) -> list[str]:
        return [
            column["name"]
            for column in columns
            if any(token in column["name"].lower() for token in ["json", "payload", "metadata"])
        ]

    def _json_validation(self, value: Any) -> dict[str, Any]:
        if value in (None, ""):
            return {"status": "null", "valid": False}
        if not isinstance(value, str):
            return {"status": "not_text", "valid": False, "type": type(value).__name__}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            return {"status": "invalid", "valid": False, "error": str(exc)}
        if isinstance(parsed, dict):
            preview = sorted(parsed.keys())[:20]
            json_type = "object"
        elif isinstance(parsed, list):
            preview = {"length": len(parsed)}
            json_type = "array"
        else:
            preview = parsed
            json_type = type(parsed).__name__
        return {"status": "valid", "valid": True, "json_type": json_type, "preview": preview}

    def _mmdb_row_hash(self, db_sha: str, table_name: str, primary_key: dict[str, Any], row: dict[str, Any]) -> str:
        material = {
            "contract": self._unified_memory_contract()["version"],
            "db_sha256": db_sha,
            "table": table_name,
            "primary_key": primary_key,
            "row": self._json_safe(row),
        }
        payload = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, bytes):
            return {"__bytes_sha256__": hashlib.sha256(value).hexdigest(), "length": len(value)}
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._json_safe(item) for item in value]
        return value

    def _breakdown_strategy(self, suffix: str, marker: str | None, is_archive_member: bool) -> dict[str, Any]:
        if suffix in self.DB_SUFFIXES:
            return {
                "mode": "sqlite_table_windows",
                "first_probe": "quarantine copy, SQLite read-only schema probe, then table-level row windows",
                "notes": ["avoid raw byte splitting unless SQLite cannot open", "prefer table-by-table export receipts"],
            }
        if marker == "archive" and not is_archive_member:
            return {
                "mode": "archive_member_batches",
                "first_probe": "manifest scan, group members by suffix/domain, then hash or extract selected batches",
                "notes": ["do not recursively explode nested archives by default", "prefer member-level manifests"],
            }
        if suffix in {".json", ".jsonl", ".ndjson"}:
            return {
                "mode": "json_record_windows",
                "first_probe": "sample head/tail, detect JSON vs JSONL, then split by records",
                "notes": ["keep each chunk parse-valid where possible"],
            }
        if suffix in {".csv", ".tsv"}:
            return {
                "mode": "tabular_row_windows",
                "first_probe": "detect header and delimiter, then split by row windows",
                "notes": ["repeat header in materialized chunks"],
            }
        if suffix in {".md", ".txt", ".log", ".py", ".js", ".ts", ".tsx", ".yaml", ".yml", ".toml"}:
            return {
                "mode": "text_line_windows",
                "first_probe": "decode sample, split on line boundaries under target byte size",
                "notes": ["preserve line ranges and encoding receipt"],
            }
        return {
            "mode": "binary_byte_ranges",
            "first_probe": "fixed byte-range hash chunks for evidence identity only",
            "notes": ["parsing requires a domain-specific adapter before import"],
        }

    def _byte_ranges(self, size: int, chunk_size: int, limit: int) -> list[dict[str, int]]:
        ranges = []
        offset = 0
        while offset < size and len(ranges) < limit:
            end = min(size, offset + chunk_size)
            ranges.append({"start": offset, "end_exclusive": end, "size": end - offset})
            offset = end
        return ranges

    def _find_manifest_member(self, archive: zipfile.ZipFile) -> str | None:
        names = [info.filename for info in archive.infolist() if not info.is_dir()]
        for name in names:
            if Path(name).name == "MANIFEST.md":
                return name
        for name in names:
            if Path(name).name == "README.md":
                return name
        return None

    def _parse_corpus_manifest(self, text: str) -> dict[str, Any]:
        def find_int(pattern: str) -> int | None:
            match = re.search(pattern, text, re.IGNORECASE)
            return int(match.group(1).replace(",", "")) if match else None

        def find_text(pattern: str) -> str | None:
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else None

        distribution = []
        in_distribution = False
        duplicate_collapsed_total = 0
        high_duplicate_rows = []
        for line in text.splitlines():
            if line.strip().lower().startswith("## distribution"):
                in_distribution = True
                continue
            if in_distribution and line.startswith("## "):
                in_distribution = False
            if in_distribution:
                match = re.match(r"- `([^`]+)`: (\d+) files?", line.strip())
                if match:
                    distribution.append({"bucket": match.group(1), "files": int(match.group(2))})
            if line.startswith("|") and "`" in line:
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if len(cells) >= 5 and cells[-1].isdigit():
                    duplicates = int(cells[-1])
                    duplicate_collapsed_total += duplicates
                    if duplicates:
                        high_duplicate_rows.append({
                            "bucket": cells[0],
                            "path": cells[1].strip("`"),
                            "size": cells[2],
                            "sha12": cells[3].strip("`"),
                            "duplicates_collapsed": duplicates,
                        })
        high_duplicate_rows.sort(key=lambda item: item["duplicates_collapsed"], reverse=True)
        return {
            "title": text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else "",
            "workspace_root": find_text(r"- Workspace root: `([^`]+)`"),
            "total_files_included": find_int(r"- Total files included: ([\d,]+)"),
            "total_size": find_text(r"- Total size: ([^\r\n]+)"),
            "files_skipped": find_int(r"- Files skipped [^:]*: ([\d,]+)"),
            "read_errors": find_int(r"- Source files with read errors: ([\d,]+)"),
            "distribution": distribution,
            "duplicates_collapsed_total_in_listed_manifest": duplicate_collapsed_total,
            "top_duplicate_rows": high_duplicate_rows[:20],
        }

    def _file_sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _normalized_suffixes(self, suffixes: list[str] | None) -> set[str] | None:
        if not suffixes:
            return None
        return {suffix.lower() if suffix.startswith(".") else f".{suffix.lower()}" for suffix in suffixes}

    def _hash_slice_result(
        self,
        source: dict[str, Any],
        request: dict[str, Any],
        entries: list[dict[str, Any]],
        skipped: dict[str, int],
        truncated: bool,
    ) -> dict[str, Any]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for entry in entries:
            groups.setdefault(entry["sha256"], []).append(entry)
        duplicate_groups = [
            {"sha256": digest, "copies": len(items), "items": items}
            for digest, items in groups.items()
            if len(items) > 1
        ]
        duplicate_groups.sort(key=lambda group: (-group["copies"], group["sha256"]))
        duplicate_bytes = sum(
            sum(int(item.get("size") or 0) for item in group["items"][1:])
            for group in duplicate_groups
        )
        return {
            "source": source,
            "request": request,
            "policy": "bounded hash slice; no files are modified, moved, deleted, or extracted to disk",
            "summary": {
                "hashed": len(entries),
                "unique_hashes": len(groups),
                "duplicate_groups": len(duplicate_groups),
                "duplicate_bytes_if_approved": duplicate_bytes,
                "skipped": skipped,
                "truncated": truncated,
            },
            "duplicates": duplicate_groups,
            "entries": entries,
        }

    def _archive_compare_classification(self, signatures: list[str], outer_hashes: list[str], include_outer_hash: bool) -> str:
        same_members = len(set(signatures)) == 1
        same_outer = len(set(outer_hashes)) == 1 if include_outer_hash else False
        if same_members and same_outer:
            return "byte_identical_archive"
        if same_members:
            return "content_equivalent_zip_members"
        return "different_archive_contents"

    def _preferred_archive_retention(self, archives: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not archives:
            return None
        role_rank = {
            "evidence_substrate": 100,
            "active_module_substrate": 90,
            "creative_yard": 80,
            "design_doctrine": 70,
        }
        return sorted(
            archives,
            key=lambda item: (
                -role_rank.get(item.get("source_role"), 0),
                item.get("path", ""),
            ),
        )[0]

    def _archive_domain(self, name: str) -> str:
        text = name.lower()
        domains = [
            ("memory", ["mmdb", "memory", "receipt", "ledger"]),
            ("agent", ["agent", "daemon", "hub", "arena", "brain"]),
            ("geometry", ["e8", "geometry", "morphon", "dimensional", "crystal"]),
            ("runtime", ["tmn", "cqe", "cmplx", "mcp", "tool", "runtime"]),
            ("cognitive", ["snap", "speedlight", "tarpit", "mdhg", "aletheia"]),
        ]
        for domain, tokens in domains:
            if any(token in text for token in tokens):
                return domain
        return "unknown"

    def _archive_priority(self, name: str, size: int) -> int:
        domain = self._archive_domain(name)
        base = {
            "runtime": 90,
            "memory": 88,
            "agent": 84,
            "geometry": 78,
            "cognitive": 74,
            "unknown": 40,
        }[domain]
        if size > 500_000_000:
            base -= 12
        elif size < 5_000_000:
            base += 5
        return max(0, min(base, 100))

    def _inventory_result(
        self,
        source: dict[str, Any],
        req: SourceInventoryRequest,
        markers: dict[str, int],
        entries: list[dict[str, Any]],
        truncated: bool,
    ) -> dict[str, Any]:
        return {
            "source": source,
            "request": req.model_dump(),
            "summary": {
                "entries": len(entries),
                **markers,
            },
            "policy": "bounded read-only inventory; no archive extraction, database writes, or service startup",
            "truncated": truncated,
            "entries": entries,
        }


class ModuleAdapter:
    def __init__(self, registry: RepoRegistry):
        self.registry = registry

    def tree(self, name: str, rel_path: str = ".", max_depth: int = 2, limit: int = 300) -> dict[str, Any]:
        root = self.registry.module_root(name)
        base = safe_join(root, rel_path)
        if not base.exists():
            raise HTTPException(404, "path not found")
        entries: list[dict[str, Any]] = []
        base_depth = len(base.relative_to(root).parts)
        for current, dirs, files in os.walk(base):
            current_path = Path(current)
            rel_current = current_path.relative_to(root)
            depth = len(rel_current.parts) - base_depth
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache"}]
            if depth >= max_depth:
                dirs[:] = []
            for dirname in dirs:
                path = current_path / dirname
                entries.append({"type": "dir", "path": str(path.relative_to(root)).replace("\\", "/")})
                if len(entries) >= limit:
                    return {"module": name, "path": rel_path, "truncated": True, "entries": entries}
            for filename in files:
                path = current_path / filename
                try:
                    size = path.stat().st_size
                except OSError:
                    size = None
                entries.append({"type": "file", "path": str(path.relative_to(root)).replace("\\", "/"), "size": size})
                if len(entries) >= limit:
                    return {"module": name, "path": rel_path, "truncated": True, "entries": entries}
        return {"module": name, "path": rel_path, "truncated": False, "entries": entries}

    def read_file(self, name: str, rel_path: str, max_bytes: int = 200_000) -> dict[str, Any]:
        root = self.registry.module_root(name)
        path = safe_join(root, rel_path)
        if not path.is_file():
            raise HTTPException(404, "file not found")
        data = path.read_bytes()[:max_bytes]
        truncated = path.stat().st_size > len(data)
        text = data.decode("utf-8", errors="replace")
        return {
            "module": name,
            "path": rel_path,
            "bytes_read": len(data),
            "truncated": truncated,
            "content": text,
        }

    def search(self, name: str, query: str, glob: str | None = None, limit: int = 50) -> dict[str, Any]:
        root = self.registry.module_root(name)
        if not root.is_dir():
            raise HTTPException(404, "module is not cloned")
        cmd = ["rg", "--line-number", "--column", "--no-heading", "--hidden", "-g", "!.git", "-m", "5"]
        if glob:
            cmd.extend(["-g", glob])
        cmd.append(query)
        proc = run(cmd, cwd=root, timeout=60)
        lines = proc.stdout.splitlines()[:limit]
        results = []
        for line in lines:
            parts = line.split(":", 3)
            if len(parts) == 4:
                path, line_no, col, text = parts
                results.append({"path": path, "line": int(line_no), "column": int(col), "text": text})
            else:
                results.append({"raw": line})
        return {
            "module": name,
            "query": query,
            "glob": glob,
            "return_code": proc.returncode,
            "truncated": len(proc.stdout.splitlines()) > limit,
            "results": results,
        }


class CapabilityProbe:
    def __init__(self, registry: RepoRegistry, ledger: PromotionLedger):
        self.registry = registry
        self.ledger = ledger

    def probe(self, name: str, mode: str = "static", include_search_examples: bool = True) -> dict[str, Any]:
        module = self.registry.module(name)
        root = self.registry.module_root(name)
        if not root.is_dir():
            raise HTTPException(404, "module is not cloned")

        files = self._top_level_files(root)
        dirs = self._top_level_dirs(root)
        ledger_module = self.ledger.module(name) or {}
        checks: list[dict[str, Any]] = []
        capabilities: list[str] = []
        risks: list[str] = []
        evidence: dict[str, Any] = {}

        self._check(checks, "git_repository", (root / ".git").exists(), "module has a local git checkout")
        self._check(checks, "python_manifest", any(f in files for f in {"pyproject.toml", "setup.py", "requirements.txt"}), "Python project markers found")
        self._check(checks, "node_manifest", "package.json" in files, "Node project marker found")
        self._check(checks, "dockerfile", "Dockerfile" in files or "dockerfile" in {f.lower() for f in files}, "Dockerfile found")
        self._check(checks, "compose_file", any(f.startswith("docker-compose") or f == "compose.yml" for f in files), "Compose file found")
        self._check(checks, "tests", "tests" in dirs or "test" in dirs or any(f.startswith("pytest") for f in files), "test markers found")
        self._check(checks, "docs", "README.md" in files or "AGENTS.md" in files, "operator docs found")

        if self._rg_has(root, "FastAPI\\("):
            capabilities.append("fastapi_surface")
        if self._rg_has(root, "FastMCP|@mcp\\.tool|mcp\\.server"):
            capabilities.append("mcp_surface")
        if self._rg_has(root, "@app\\.(get|post|put|delete|patch)|APIRouter\\("):
            capabilities.append("python_api_routes")
        if (root / "src").is_dir():
            capabilities.append("src_tree")
        if (root / "cmplx-nextjs").is_dir() or self._rg_has(root, "**/src/app/api/**/route.ts", search_files=True):
            capabilities.append("nextjs_api_routes")

        route_examples = self._rg_examples(
            root,
            "@app\\.(get|post|put|delete|patch)|router\\.(get|post|put|delete|patch)|APIRouter\\(",
            include_search_examples,
        )
        mcp_examples = self._rg_examples(root, "FastMCP|@mcp\\.tool|mcp\\.server", include_search_examples)
        evidence["route_examples"] = route_examples
        evidence["mcp_examples"] = mcp_examples
        evidence["entry_files"] = self._entry_file_candidates(root)
        evidence["ledger_status"] = ledger_module.get("status")
        evidence["ledger_score"] = (ledger_module.get("score") or {}).get("promotion_score")
        evidence["ledger_recommended_action"] = ledger_module.get("recommended_action")

        if ledger_module.get("status") in {"needs_slice_index", "unindexed_review"}:
            risks.append("ledger marks this module as requiring bounded review before promotion")
        large_files = ((ledger_module.get("local") or {}).get("large_files") or 0)
        if large_files >= 100:
            risks.append(f"large-file load is high ({large_files}); promote slices only")
        if mode == "light":
            evidence["python_syntax_probe"] = self._python_syntax_probe(root)

        score = self._score(checks, capabilities, risks, ledger_module)
        return {
            "module": name,
            "role": module.get("role"),
            "mode": mode,
            "score": score,
            "status": self._status(score, risks),
            "capabilities": sorted(set(capabilities)),
            "checks": checks,
            "risks": risks,
            "evidence": evidence,
            "policy": {
                "mutation": "disabled by default" if not ALLOW_MUTATION else "enabled",
                "promotion_rule": "promote behavior behind adapters before copying source",
            },
        }

    def promotion_plan(self, name: str, target: str = "CMPLX-PartsFactory", include_probe: bool = True) -> dict[str, Any]:
        module = self.registry.module(name)
        ledger_module = self.ledger.module(name) or {}
        probe = self.probe(name) if include_probe else None
        capabilities = set((probe or {}).get("capabilities", []))
        actions: list[dict[str, Any]] = []

        actions.append({
            "phase": "adapter",
            "action": f"create a read-only {name} adapter under the repo-kernel controller",
            "reason": "keeps source identity intact while proving live capabilities",
        })
        if "fastapi_surface" in capabilities or "python_api_routes" in capabilities:
            actions.append({
                "phase": "api",
                "action": "map discovered FastAPI/APIRouter endpoints into a controller route registry",
                "reason": "API behavior is directly discoverable",
            })
        if "mcp_surface" in capabilities:
            actions.append({
                "phase": "mcp",
                "action": "wrap MCP tools as delegated module capabilities",
                "reason": "module already contains MCP-style tool surfaces",
            })
        if "nextjs_api_routes" in capabilities:
            actions.append({
                "phase": "frontend-api",
                "action": "catalog Next.js API route handlers as secondary service surfaces",
                "reason": "web API behavior may need translation rather than direct import",
            })
        actions.append({
            "phase": "tests",
            "action": "add a capability smoke test before any source promotion",
            "reason": "promotion should be based on behavior, not file volume",
        })

        return {
            "module": name,
            "target": target,
            "role": module.get("role"),
            "ledger_status": ledger_module.get("status"),
            "ledger_action": ledger_module.get("recommended_action"),
            "probe": probe,
            "actions": actions,
            "copy_policy": {
                "default": "do not copy source into the master until adapter probes pass",
                "preferred": "delegate through controller/adapters first",
                "archive": "archive or demote only after target coverage exists",
            },
        }

    def _top_level_files(self, root: Path) -> set[str]:
        return {p.name for p in root.iterdir() if p.is_file()}

    def _top_level_dirs(self, root: Path) -> set[str]:
        return {p.name for p in root.iterdir() if p.is_dir()}

    def _check(self, checks: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    def _rg_has(self, root: Path, pattern: str, search_files: bool = False) -> bool:
        cmd = ["rg", "--files", "-g", pattern] if search_files else ["rg", "-q", "--hidden", "-g", "!.git", pattern]
        proc = run(cmd, cwd=root, timeout=15)
        return proc.returncode == 0

    def _rg_examples(self, root: Path, pattern: str, enabled: bool, limit: int = 8) -> list[dict[str, Any]]:
        if not enabled:
            return []
        proc = run(["rg", "--line-number", "--column", "--no-heading", "--hidden", "-g", "!.git", pattern], cwd=root, timeout=20)
        examples = []
        for line in proc.stdout.splitlines()[:limit]:
            parts = line.split(":", 3)
            if len(parts) == 4:
                path, line_no, col, text = parts
                examples.append({"path": path, "line": int(line_no), "column": int(col), "text": text.strip()[:240]})
        return examples

    def _entry_file_candidates(self, root: Path) -> list[str]:
        candidates = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            "compose.yml",
            "package.json",
            "README.md",
            "AGENTS.md",
        ]
        return [candidate for candidate in candidates if (root / candidate).exists()]

    def _python_syntax_probe(self, root: Path, limit: int = 40) -> dict[str, Any]:
        py_files = []
        for base in ["src", "."]:
            base_path = root / base
            if base_path.is_dir():
                py_files.extend(p for p in base_path.rglob("*.py") if ".git" not in p.parts and "__pycache__" not in p.parts)
            if py_files:
                break
        selected = py_files[:limit]
        if not selected:
            return {"checked": 0, "ok": None, "detail": "no Python files selected"}
        proc = run(["python", "-m", "py_compile", *[str(p) for p in selected]], cwd=root, timeout=60)
        return {"checked": len(selected), "ok": proc.returncode == 0, "stderr": proc.stderr[-2000:]}

    def _score(self, checks: list[dict[str, Any]], capabilities: list[str], risks: list[str], ledger_module: dict[str, Any]) -> dict[str, Any]:
        check_points = sum(5 for check in checks if check["ok"])
        capability_points = len(set(capabilities)) * 12
        ledger_points = min(float((ledger_module.get("score") or {}).get("promotion_score") or 0), 100.0) * 0.35
        risk_penalty = len(risks) * 12
        readiness = max(0.0, min(100.0, check_points + capability_points + ledger_points - risk_penalty))
        return {
            "readiness": round(readiness, 1),
            "check_points": check_points,
            "capability_points": capability_points,
            "ledger_points": round(ledger_points, 1),
            "risk_penalty": risk_penalty,
        }

    def _status(self, score: dict[str, Any], risks: list[str]) -> str:
        readiness = score["readiness"]
        if readiness >= 75 and not risks:
            return "adapter_ready"
        if readiness >= 55:
            return "probe_ready"
        if readiness >= 30:
            return "review_first"
        return "hold"


class ModuleSurfaceCatalog:
    HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}
    IGNORED_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache"}

    def __init__(self, registry: RepoRegistry):
        self.registry = registry
        self._cache: dict[tuple[str, int], tuple[float, dict[str, Any]]] = {}
        self._cache_ttl_seconds = float(os.environ.get("REPO_KERNEL_SURFACE_CACHE_TTL", "300"))

    def catalog(self, name: str, limit: int = 500) -> dict[str, Any]:
        cache_key = (name, limit)
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached[0] < self._cache_ttl_seconds:
            return {**cached[1], "cached": True}

        root = self.registry.module_root(name)
        if not root.is_dir():
            raise HTTPException(404, "module is not cloned")

        routes: list[dict[str, Any]] = []
        mcp_tools: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        python_files = self._candidate_python_files(root)

        for path in python_files:
            try:
                size = path.stat().st_size
            except OSError:
                continue
            rel = self._rel(root, path)
            if size > 2_000_000:
                skipped.append({"path": rel, "reason": "larger than 2MB"})
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError as exc:
                skipped.append({"path": rel, "reason": f"syntax error: line {exc.lineno}"})
                continue
            except OSError as exc:
                skipped.append({"path": rel, "reason": str(exc)})
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if isinstance(node, ast.Call):
                        tool = self._tool_from_call(node, rel)
                        if tool:
                            mcp_tools.append(tool)
                    continue
                for decorator in node.decorator_list:
                    route = self._route_from_decorator(decorator, rel, node)
                    if route:
                        routes.append(route)
                        continue
                    tool = self._tool_from_decorator(decorator, rel, node)
                    if tool:
                        mcp_tools.append(tool)

        nextjs_routes = self._nextjs_routes(root, limit)
        result = {
            "module": name,
            "adapter_id": self.adapter_id(name),
            "routes": routes[:limit],
            "mcp_tools": mcp_tools[:limit],
            "nextjs_routes": nextjs_routes,
            "summary": {
                "route_count": len(routes),
                "mcp_tool_count": len(mcp_tools),
                "nextjs_route_count": len(nextjs_routes),
                "skipped_count": len(skipped),
            },
            "skipped": skipped[:50],
            "policy": {
                "mode": "static surface extraction",
                "mutation": "disabled by default" if not ALLOW_MUTATION else "enabled",
            },
            "cached": False,
        }
        self._cache[cache_key] = (time.time(), result)
        return result

    def adapter_id(self, name: str) -> str:
        return "adapter-" + "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")

    def _candidate_python_files(self, root: Path) -> list[Path]:
        patterns = [
            "@app\\.(get|post|put|delete|patch|options|head)",
            "@router\\.(get|post|put|delete|patch|options|head)",
            "APIRouter\\(",
            "@mcp\\.tool",
            "FastMCP",
            "Tool",
        ]
        files: dict[str, Path] = {}
        for pattern in patterns:
            proc = run(["rg", "--files-with-matches", "--hidden", "-g", "!.git", "-g", "**/*.py", pattern, "."], cwd=root, timeout=20)
            for line in proc.stdout.splitlines():
                path = (root / line.lstrip(".\\/")).resolve()
                if path.is_file() and self._allowed(path):
                    files[str(path)] = path
        return list(files.values())

    def _nextjs_routes(self, root: Path, limit: int) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        proc = run(["rg", "--files", "-g", "**/src/app/api/**/route.ts", "-g", "**/src/app/api/**/route.tsx"], cwd=root, timeout=20)
        routes = []
        for line in proc.stdout.splitlines()[:limit]:
            path = (root / line).resolve()
            if not path.is_file() or not self._allowed(path):
                continue
            rel = self._rel(root, path)
            api_path = self._nextjs_api_path(rel)
            methods = self._nextjs_methods(path)
            routes.append({"kind": "nextjs_route", "file": rel, "path": api_path, "methods": methods})
        return routes

    def _route_from_decorator(self, decorator: ast.AST, rel: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any] | None:
        func = decorator.func if isinstance(decorator, ast.Call) else decorator
        if not isinstance(func, ast.Attribute) or func.attr.lower() not in self.HTTP_METHODS:
            return None
        path = None
        if isinstance(decorator, ast.Call) and decorator.args:
            first = decorator.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                path = first.value
        return {
            "kind": "fastapi_route",
            "file": rel,
            "line": getattr(node, "lineno", None),
            "method": func.attr.upper(),
            "path": path,
            "function": node.name,
            "doc": ast.get_docstring(node),
        }

    def _tool_from_decorator(self, decorator: ast.AST, rel: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any] | None:
        func = decorator.func if isinstance(decorator, ast.Call) else decorator
        if not isinstance(func, ast.Attribute) or func.attr != "tool":
            return None
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        return {
            "kind": "mcp_tool",
            "file": rel,
            "line": getattr(node, "lineno", None),
            "name": node.name,
            "arguments": args,
            "doc": ast.get_docstring(node),
        }

    def _tool_from_call(self, node: ast.Call, rel: str) -> dict[str, Any] | None:
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        if func_name != "Tool":
            return None

        values: dict[str, Any] = {}
        for keyword in node.keywords:
            if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, (str, int, float, bool)):
                values[keyword.arg or ""] = keyword.value.value
            elif keyword.arg == "inputSchema":
                try:
                    values["inputSchema"] = ast.literal_eval(keyword.value)
                except (ValueError, SyntaxError):
                    values["inputSchema"] = None
        name = values.get("name")
        if not isinstance(name, str) and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                name = first.value
        if "description" not in values and len(node.args) >= 2:
            second = node.args[1]
            if isinstance(second, ast.Constant) and isinstance(second.value, str):
                values["description"] = second.value
        if "inputSchema" not in values and len(node.args) >= 3:
            try:
                values["inputSchema"] = ast.literal_eval(node.args[2])
            except (ValueError, SyntaxError):
                values["inputSchema"] = None
        if not isinstance(name, str):
            return None
        return {
            "kind": "mcp_tool_decl",
            "file": rel,
            "line": getattr(node, "lineno", None),
            "name": name,
            "description": values.get("description"),
            "input_schema": values.get("inputSchema"),
        }

    def _nextjs_api_path(self, rel: str) -> str:
        marker = "/src/app/api/"
        normalized = "/" + rel.replace("\\", "/")
        if marker not in normalized:
            return normalized
        suffix = normalized.split(marker, 1)[1]
        suffix = suffix.rsplit("/route.", 1)[0]
        return "/api/" + suffix.strip("/")

    def _nextjs_methods(self, path: Path) -> list[str]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        methods = []
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]:
            if f"function {method}" in text or f"const {method}" in text or f"export async function {method}" in text:
                methods.append(method)
        return methods

    def _allowed(self, path: Path) -> bool:
        return not any(part in self.IGNORED_DIRS for part in path.parts)

    def _rel(self, root: Path, path: Path) -> str:
        return str(path.relative_to(root)).replace("\\", "/")


class RepoKernelAdapterRegistry:
    def __init__(
        self,
        registry: RepoRegistry,
        adapter: ModuleAdapter,
        probe_runner: CapabilityProbe,
        surface_catalog: ModuleSurfaceCatalog,
    ):
        self.registry = registry
        self.adapter = adapter
        self.probe_runner = probe_runner
        self.surface_catalog = surface_catalog

    def list_adapters(self) -> dict[str, Any]:
        adapters = []
        for module in registry.modules():
            ledger_module = ledger.module(module["name"]) or {}
            adapters.append({
                "module": module["name"],
                "adapter_id": self.surface_catalog.adapter_id(module["name"]),
                "role": module.get("role"),
                "status": ledger_module.get("status", "unknown"),
                "recommended_action": ledger_module.get("recommended_action"),
                "safe_actions": ["probe", "promotion_plan", "surface_catalog", "search", "tree", "read_file"],
                "mutation": "disabled by default" if not ALLOW_MUTATION else "enabled",
            })
        return {"adapters": adapters}

    def describe(self, name: str) -> dict[str, Any]:
        module = self.registry.module(name)
        ledger_module = ledger.module(name) or {}
        return {
            "module": module,
            "adapter_id": self.surface_catalog.adapter_id(name),
            "ledger_status": ledger_module.get("status"),
            "safe_actions": ["probe", "promotion_plan", "surface_catalog", "search", "tree", "read_file"],
            "call_endpoint": f"/api/adapters/{name}/call",
            "surface_endpoint": f"/api/adapters/{name}/surfaces",
        }

    def unification_worklist(self, gitnexus: Any | None = None, limit: int = 20, include_probe: bool = False) -> dict[str, Any]:
        bounded = max(1, min(limit, 100))
        hints: dict[str, Any] = {"top_repo_hints": [], "shared_historical_names": [], "recommended_work": []}
        hint_error = None
        if gitnexus is not None:
            try:
                hints = gitnexus.unification_hints(limit=max(bounded, 25))
            except HTTPException as exc:
                hint_error = {"status_code": exc.status_code, "error": exc.detail}
        hints_by_alias = {item.get("repo"): item for item in hints.get("top_repo_hints", []) if item.get("repo")}
        ledger_modules = {
            item.get("name"): item
            for item in self.probe_runner.ledger.read().get("modules", [])
            if item.get("name")
        }

        items = []
        for module in self.registry.modules():
            name = module["name"]
            ledger_module = ledger_modules.get(name, {})
            alias = ledger_module.get("gitnexus_alias") or self._guess_gitnexus_alias(name)
            hint = hints_by_alias.get(alias)
            graph = hint.get("stats") if hint else ledger_module.get("gitnexus", {})
            probe = None
            if include_probe and module.get("cloned", True):
                probe = self.probe_runner.probe(name, mode="static", include_search_examples=False)
            action = self._unification_next_action(name, ledger_module, hint, probe)
            items.append({
                "module": name,
                "role": module.get("role"),
                "local_path": module.get("local_path"),
                "gitnexus_alias": alias,
                "gitnexus_indexed": bool(hint or ledger_module.get("gitnexus_indexed")),
                "graph": {
                    "files": self._int_graph(graph, "files"),
                    "nodes": self._int_graph(graph, "nodes", "symbols"),
                    "edges": self._int_graph(graph, "edges"),
                    "communities": self._int_graph(graph, "communities", "clusters"),
                    "processes": self._int_graph(graph, "processes"),
                    "routes": self._int_graph(graph, "routes"),
                    "tools": self._int_graph(graph, "tools"),
                },
                "ledger_status": ledger_module.get("status", "unknown"),
                "ledger_action": ledger_module.get("recommended_action"),
                "adapter_id": self.surface_catalog.adapter_id(name),
                "adapter_endpoint": f"/api/adapters/{name}",
                "safe_actions": ["probe", "promotion_plan", "surface_catalog", "search", "tree", "read_file"],
                "probe_status": probe.get("status") if probe else None,
                "next_action": action,
                "next_reads": self._unification_next_reads(name, alias, action),
                "priority_score": self._unification_priority(ledger_module, hint, action, name),
                "policy": "read-only adapter and evidence work; no source move or runtime activation",
            })

        items.sort(key=lambda item: (item["priority_score"], item["module"]), reverse=True)
        mapped_aliases = {item["gitnexus_alias"] for item in items}
        unmapped_gitnexus = [
            item
            for item in hints.get("top_repo_hints", [])
            if item.get("role") != "clean_repo_checkout" and item.get("repo") not in mapped_aliases
        ]
        return {
            "worklist": "repo-unification-worklist",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "repo-kernel adapters joined with GitNexus graph evidence and promotion ledger",
            "summary": {
                "module_count": len(items),
                "gitnexus_indexed_module_count": sum(1 for item in items if item["gitnexus_indexed"]),
                "probe_included": include_probe,
                "hint_status": hints.get("status"),
                "hint_error": hint_error,
            },
            "top_modules": items[:bounded],
            "unmapped_gitnexus_evidence": unmapped_gitnexus[:bounded],
            "shared_historical_names": hints.get("shared_historical_names", [])[:bounded],
            "recommended_work": [
                {
                    "lane": "adapter_completion",
                    "targets": [item["module"] for item in items if item["next_action"]["lane"] in {"adapter_ready_candidate", "surface_catalog_review"}][:6],
                    "reason": "turn high-confidence repo surfaces into stable canonical API contracts",
                },
                {
                    "lane": "slice_filtering",
                    "targets": [item["module"] for item in items if item["next_action"]["lane"] == "slice_filter_before_adapter"][:6],
                    "reason": "large/noisy repos need bounded slices before adapter promotion",
                },
                {
                    "lane": "capability_canon",
                    "targets": [item.get("name") for item in hints.get("shared_historical_names", [])[:6]],
                    "reason": "shared historical names should be mapped to canonical capability ids before source movement",
                },
            ],
            "policy": {
                "merge_order": "prove through adapters first, then promote behavior, then move source only when coverage exists",
                "mutation": "all listed next reads are safe; writes still require promotion ledger approval",
                "ports": "port reassignment remains deferred until control routes are stable",
            },
        }

    def slice_candidates(self, name: str, gitnexus: Any | None = None, limit: int = 20) -> dict[str, Any]:
        module = self.registry.module(name)
        root = self.registry.module_root(name)
        if not root.is_dir():
            raise HTTPException(404, "module is not cloned")
        ledger_module = self.probe_runner.ledger.module(name) or {}
        alias = ledger_module.get("gitnexus_alias") or self._guess_gitnexus_alias(name)
        graph_summary = None
        graph_error = None
        if gitnexus is not None:
            try:
                graph_summary = gitnexus.graph_summary(alias, limit=12)
            except HTTPException as exc:
                graph_error = {"status_code": exc.status_code, "error": exc.detail}

        candidates = []
        for path in self._slice_seed_paths(root):
            summary = self._slice_path_summary(root, path)
            if summary["file_count"] == 0 and summary["doc_count"] == 0:
                continue
            classification = self._slice_classification(path, summary, graph_summary)
            candidates.append({
                "path": path.as_posix(),
                "classification": classification,
                "summary": summary,
                "priority_score": self._slice_priority(classification, summary),
                "next_reads": [
                    f"/api/adapters/{name}/call action=tree path={path.as_posix()} max_depth=2",
                    f"/api/adapters/{name}/call action=search query=FastAPI glob={path.as_posix()}/**",
                    f"/api/adapters/{name}/call action=search query=@mcp.tool glob={path.as_posix()}/**",
                ],
                "promotion_rule": "promote as a bounded adapter slice before copying source",
            })
        candidates.sort(key=lambda item: (item["priority_score"], item["path"]), reverse=True)
        return {
            "module": name,
            "role": module.get("role"),
            "ledger_status": ledger_module.get("status"),
            "gitnexus_alias": alias,
            "graph": {
                "status": "ready" if graph_summary else "unavailable",
                "error": graph_error,
                "top_communities": (graph_summary or {}).get("communities", [])[:8],
                "labels": (graph_summary or {}).get("labels", [])[:8],
            },
            "candidate_count": len(candidates),
            "candidates": candidates[: max(1, min(limit, 100))],
            "api_layer_needs": [
                {
                    "area": "slice_promotion_receipts",
                    "need": "record which candidate paths become canonical capability sources before moving code",
                    "current_bridge": f"GET /api/adapters/{name}/slice-candidates",
                },
                {
                    "area": "vendor_noise_filter",
                    "need": "keep large external/test shards as evidence until a specific capability requires them",
                    "current_bridge": "classification quarantine_external_or_vendor",
                },
            ],
            "policy": {
                "read": "slice candidates are filesystem and GitNexus evidence only",
                "write": "no source files are moved or rewritten by this endpoint",
                "next_step": "promote one bounded slice into a canonical system API only after tests are added",
            },
        }

    def slice_candidate_matrix(
        self,
        gitnexus: Any | None = None,
        modules: list[str] | None = None,
        limit_per_module: int = 12,
        include_review: bool = False,
    ) -> dict[str, Any]:
        selected = self._slice_matrix_modules(gitnexus=gitnexus, modules=modules, include_review=include_review)
        grouped: dict[str, list[dict[str, Any]]] = {}
        module_summaries = []
        for module in selected:
            try:
                report = self.slice_candidates(module, gitnexus=gitnexus, limit=limit_per_module)
            except HTTPException as exc:
                module_summaries.append({"module": module, "error": exc.detail, "status": exc.status_code})
                continue
            module_summaries.append({
                "module": module,
                "role": report.get("role"),
                "ledger_status": report.get("ledger_status"),
                "candidate_count": report.get("candidate_count"),
                "gitnexus_alias": report.get("gitnexus_alias"),
            })
            for candidate in report.get("candidates", []):
                system = candidate.get("classification", {}).get("system") or "unknown"
                grouped.setdefault(system, []).append({
                    "module": module,
                    "path": candidate.get("path"),
                    "lane": candidate.get("classification", {}).get("lane"),
                    "reason": candidate.get("classification", {}).get("reason"),
                    "priority_score": candidate.get("priority_score"),
                    "summary": candidate.get("summary"),
                    "intake_plan": f"/api/adapters/{module}/slice-intake-plan?path={urllib.parse.quote(str(candidate.get('path') or ''))}",
                    "promotion_rule": candidate.get("promotion_rule"),
                })
        for candidates in grouped.values():
            candidates.sort(key=lambda item: (item.get("priority_score") or 0, item.get("module") or ""), reverse=True)
        return {
            "matrix": "slice-candidate-matrix",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "modules": module_summaries,
            "systems": [
                {
                    "system": system,
                    "candidate_count": len(candidates),
                    "top_candidates": candidates[:20],
                }
                for system, candidates in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
            ],
            "recommended_next_intakes": self._matrix_next_intakes(grouped),
            "policy": {
                "read": "matrix is assembled from adapter slice candidates and GitNexus graph summaries",
                "write": "no source movement or runtime activation occurs here",
                "use": "pick one high-value bounded slice, generate an intake plan, then add route/tests before promotion",
            },
        }

    def slice_intake_plan(self, name: str, path: str, gitnexus: Any | None = None) -> dict[str, Any]:
        if not path:
            raise HTTPException(400, "path is required")
        candidates = self.slice_candidates(name, gitnexus=gitnexus, limit=100)
        selected = next((item for item in candidates.get("candidates", []) if item.get("path") == path), None)
        if selected is None:
            root = self.registry.module_root(name)
            rel = Path(path)
            target = root / rel
            if not target.exists():
                raise HTTPException(404, f"slice path not found for {name}: {path}")
            summary = self._slice_path_summary(root, rel)
            classification = self._slice_classification(rel, summary, None)
            selected = {
                "path": rel.as_posix(),
                "classification": classification,
                "summary": summary,
                "priority_score": self._slice_priority(classification, summary),
                "promotion_rule": "promote as a bounded adapter slice before copying source",
            }
        classification = selected["classification"]
        system = classification.get("system") or "unknown"
        lane = classification.get("lane")
        canonical_base = self._canonical_system_base(system)
        capability_id = self._slice_capability_id(name, selected["path"], lane)
        return {
            "plan": "slice-intake-plan",
            "module": name,
            "path": selected["path"],
            "capability_id": capability_id,
            "target_system": system,
            "target_lane": lane,
            "canonical_base": canonical_base,
            "classification": classification,
            "summary": selected["summary"],
            "proposed_routes": self._slice_proposed_routes(system, capability_id, canonical_base),
            "controller_changes": [
                {
                    "step": "catalog",
                    "action": "keep the slice behind the existing module adapter and expose only read summaries first",
                    "read": f"/api/adapters/{name}/call action=tree path={selected['path']} max_depth=2",
                },
                {
                    "step": "canonical-contract",
                    "action": f"add a {system} capability entry with this slice as implementation evidence",
                    "read": f"/api/adapters/{name}/slice-candidates",
                },
                {
                    "step": "tests",
                    "action": "add route-registration and mutation-policy tests before any source promotion",
                    "test_target": f"tests/test_{re.sub(r'[^a-z0-9]+', '_', capability_id.lower()).strip('_')}.py",
                },
                {
                    "step": "promotion-ledger",
                    "action": "record the selected path as a bounded promotion candidate, not whole-repo source movement",
                    "policy": selected.get("promotion_rule"),
                },
            ],
            "mcp_tools_to_add": [
                f"repo_kernel_{re.sub(r'[^a-z0-9]+', '_', capability_id.lower()).strip('_')}_summary",
                f"repo_kernel_{re.sub(r'[^a-z0-9]+', '_', capability_id.lower()).strip('_')}_read",
            ],
            "risks": self._slice_intake_risks(selected),
            "policy": {
                "read": "intake plan only; source remains in its clean repo checkout",
                "write": "requires explicit promotion approval and tests",
                "ports": "no port reassignment for a slice until the canonical route is stable",
            },
        }

    def canonical_slice_registry(
        self,
        gitnexus: Any | None = None,
        system: str | None = None,
        modules: list[str] | None = None,
    ) -> dict[str, Any]:
        matrix = self.slice_candidate_matrix(
            gitnexus=gitnexus,
            modules=modules or ["CMPLXDevKit"],
            limit_per_module=25,
            include_review=False,
        )
        slices = []
        for group in matrix.get("systems", []):
            if system and group["system"] != system:
                continue
            for candidate in group.get("top_candidates", []):
                if group["system"] in {"evidence", "unknown"}:
                    continue
                lane = candidate.get("lane")
                capability_id = self._slice_capability_id(candidate["module"], candidate["path"], lane)
                route_id = self._slice_route_id(capability_id)
                slices.append({
                    "capability_id": capability_id,
                    "route_id": route_id,
                    "system": group["system"],
                    "module": candidate["module"],
                    "path": candidate["path"],
                    "lane": lane,
                    "reason": candidate.get("reason"),
                    "priority_score": candidate.get("priority_score"),
                    "summary": candidate.get("summary"),
                    "canonical_routes": {
                        "summary": f"/api/global/{group['system']}/slices/{route_id}",
                        "tree": f"/api/global/{group['system']}/slices/{route_id}/tree",
                        "call_plan": f"/api/global/{group['system']}/slices/{route_id}/call-plan",
                    },
                    "source_reads": [
                        f"/api/adapters/{candidate['module']}/slice-intake-plan?path={urllib.parse.quote(candidate['path'])}",
                        f"/api/adapters/{candidate['module']}/call action=tree path={candidate['path']} max_depth=2",
                    ],
                    "write_policy": "read-only summary/tree and plan-only call-plan until promotion approval",
                })
        slices.sort(key=lambda item: (item["priority_score"] or 0, item["capability_id"]), reverse=True)
        return {
            "registry": "canonical-slice-registry",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "system": system,
            "slice_count": len(slices),
            "slices": slices,
            "source_matrix": "/api/slice-candidate-matrix",
            "policy": {
                "read": "canonical slice routes delegate to module adapters",
                "execute": "call-plan only; no slice execution is enabled",
                "promotion": "route existence is not source promotion",
            },
        }

    def canonical_slice(self, system: str, slice_id: str, gitnexus: Any | None = None) -> dict[str, Any]:
        record = self._canonical_slice_record(system, slice_id, gitnexus=gitnexus)
        intake = self.slice_intake_plan(record["module"], record["path"], gitnexus=gitnexus)
        return {
            "slice": record,
            "intake_plan": intake,
            "policy": "read-only canonical slice summary; implementation remains in repo adapter",
        }

    def canonical_slice_tree(
        self,
        system: str,
        slice_id: str,
        gitnexus: Any | None = None,
        max_depth: int = 2,
        limit: int = 200,
    ) -> dict[str, Any]:
        record = self._canonical_slice_record(system, slice_id, gitnexus=gitnexus)
        tree = self.adapter.tree(record["module"], rel_path=record["path"], max_depth=max_depth, limit=limit)
        return {
            "slice": record,
            "tree": tree,
            "policy": "read-only canonical slice tree through module adapter",
        }

    def canonical_slice_call_plan(
        self,
        system: str,
        slice_id: str,
        req: GlobalSystemCallPlanRequest,
        gitnexus: Any | None = None,
    ) -> dict[str, Any]:
        record = self._canonical_slice_record(system, slice_id, gitnexus=gitnexus)
        return {
            "system": system,
            "slice": record,
            "operation": req.operation,
            "name": req.name,
            "arguments": req.arguments,
            "dry_run": req.dry_run,
            "planned_reads": record.get("source_reads", []),
            "execution": "not executed; canonical slice routes are plan-only until promotion approval",
            "policy": {
                "read": "source reads remain adapter-bounded",
                "write": "blocked by mutation policy",
                "ports": "no port assignment for a slice call-plan",
            },
        }

    def octa64_capability(self, gitnexus: Any | None = None) -> dict[str, Any]:
        record = self._canonical_slice_record("code-execution", "cmplxdevkit-code-execution-runtime-slice-src-octa64", gitnexus=gitnexus)
        tree = self.adapter.tree("CMPLXDevKit", rel_path="src/octa64", max_depth=1, limit=50)
        return {
            "capability": "octa64",
            "capability_id": record["capability_id"],
            "system": "code-execution",
            "status": "canonical_read_surface",
            "source": {
                "module": "CMPLXDevKit",
                "path": "src/octa64",
                "adapter_id": self.surface_catalog.adapter_id("CMPLXDevKit"),
                "slice": record,
            },
            "purpose": "bounded pack/VM/graph-executor runtime candidate for code-execution planning",
            "files": tree.get("entries", []),
            "api": {
                "summary": "/api/global/code-execution/octa64",
                "tree": "/api/global/code-execution/octa64/tree",
                "file": "/api/global/code-execution/octa64/files/{path}",
                "call_plan": "/api/global/code-execution/octa64/call-plan",
            },
            "pack_model": {
                "size_bytes": 512,
                "ports": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                "fields": [
                    "version",
                    "lane",
                    "quadrant",
                    "arm",
                    "portmap",
                    "effects",
                    "bytecode",
                    "cas_links",
                    "constraints",
                    "proof",
                    "ledger",
                    "ecc",
                    "spare",
                ],
            },
            "vm_opcodes": [
                "NOP",
                "STREAM_CONST",
                "MAP_ZSCORE",
                "FILTER_ABS_GT",
                "EMIT_FS",
                "PARTITIONS_TABLE",
                "EMIT_RECEIPT",
                "PARITY_CHECK",
            ],
            "entrypoints": [
                {
                    "name": "encode_packs/decode_packs",
                    "file": "src/octa64/codec.py",
                    "mode": "serialization",
                },
                {
                    "name": "run_pack",
                    "file": "src/octa64/vm.py",
                    "mode": "single-pack VM function",
                },
                {
                    "name": "Executor.run_macrocycles",
                    "file": "src/octa64/executor.py",
                    "mode": "graph execution loop",
                },
                {
                    "name": "run_graph.py",
                    "file": "src/octa64/run_graph.py",
                    "mode": "CLI entrypoint evidence",
                },
            ],
            "activation_state": {
                "execution": "disabled",
                "reason": "source is promoted as a read/control surface first; running pack graphs requires an approved sandbox and output policy",
                "next_gate": "define sandboxed graph input/output contract and tests before enabling execution",
            },
            "known_issues": [
                {
                    "area": "entrypoint_import",
                    "issue": "run_graph.py imports octa_vm.executor while this checkout exposes the slice under src/octa64",
                    "impact": "CLI execution requires import-path normalization before activation",
                },
            ],
            "policy": {
                "read": "source files and tree are readable through module adapter",
                "write": "filesystem emit and receipt operations remain blocked by call-plan route",
                "ports": "no host port assigned to octa64",
            },
        }

    def octa64_tree(self, max_depth: int = 2, limit: int = 100) -> dict[str, Any]:
        return {
            "capability": "octa64",
            "tree": self.adapter.tree("CMPLXDevKit", rel_path="src/octa64", max_depth=max_depth, limit=limit),
            "policy": "read-only source tree through CMPLXDevKit adapter",
        }

    def octa64_read_file(self, path: str, max_bytes: int = 120_000) -> dict[str, Any]:
        normalized = path.replace("\\", "/").strip("/")
        allowed = {"__init__.py", "codec.py", "executor.py", "pack.py", "run_graph.py", "vm.py"}
        if normalized not in allowed:
            raise HTTPException(403, f"octa64 file is not allowlisted: {path}")
        return {
            "capability": "octa64",
            "file": normalized,
            "data": self.adapter.read_file("CMPLXDevKit", f"src/octa64/{normalized}", max_bytes=max_bytes),
            "policy": "read-only source file through CMPLXDevKit adapter",
        }

    def octa64_call_plan(self, req: GlobalSystemCallPlanRequest) -> dict[str, Any]:
        known_operations = {
            "encode_packs": "serialize 512-byte packs with codec.encode_packs",
            "decode_packs": "deserialize 512-byte packs with codec.decode_packs",
            "run_pack": "evaluate one pack opcode against VMState",
            "load_graph": "load graph JSON into Executor graph model",
            "run_macrocycles": "walk graph nodes across quadrant/lane/b-cycle schedule",
            "run_graph": "CLI-style graph execution wrapper",
        }
        operation_key = req.name.replace("-", "_").lower()
        matched = known_operations.get(operation_key)
        return {
            "system": "code-execution",
            "capability": "octa64",
            "operation": req.operation,
            "name": req.name,
            "known_operation": matched is not None,
            "operation_summary": matched or "unmapped octa64 operation; inspect source before promotion",
            "arguments": req.arguments,
            "dry_run": req.dry_run,
            "planned_reads": [
                "/api/global/code-execution/octa64",
                "/api/global/code-execution/octa64/tree",
                "/api/global/code-execution/octa64/files/pack.py",
                "/api/global/code-execution/octa64/files/vm.py",
                "/api/global/code-execution/octa64/files/executor.py",
            ],
            "execution": "not executed; octa64 execution is blocked until sandbox, input, output, and receipt policy are approved",
            "promotion_gates": [
                "add input graph schema validation",
                "define output directory policy outside source repos",
                "block arbitrary filesystem writes from EMIT_FS and EMIT_RECEIPT or route them to quarantine",
                "add deterministic smoke tests for pack encode/decode and run_pack without external writes",
            ],
            "policy": {
                "read": "allowed",
                "execute": "blocked",
                "write": "blocked",
                "ports": "none",
            },
        }

    def mcp_os_validation_capability(self, gitnexus: Any | None = None) -> dict[str, Any]:
        source_path = "CMPLXLOCALMCP/mcp_os/validation"
        record = self._canonical_slice_record(
            "validation",
            "cmplxdevkit-validation-tool-slice-cmplxlocalmcp-mcp-os-validation",
            gitnexus=gitnexus,
        )
        tree = self.adapter.tree("CMPLXDevKit", rel_path=source_path, max_depth=1, limit=80)
        return {
            "capability": "mcp-os-validation",
            "capability_id": record["capability_id"],
            "system": "validation",
            "status": "canonical_read_surface",
            "source": {
                "module": "CMPLXDevKit",
                "path": source_path,
                "adapter_id": self.surface_catalog.adapter_id("CMPLXDevKit"),
                "slice": record,
            },
            "purpose": "MCP OS validation framework evidence, suite catalog, diagnostics surface, and activation plan",
            "files": tree.get("entries", []),
            "api": {
                "summary": "/api/global/validation/mcp-os",
                "tree": "/api/global/validation/mcp-os/tree",
                "file": "/api/global/validation/mcp-os/files/{path}",
                "call_plan": "/api/global/validation/mcp-os/call-plan",
            },
            "exported_symbols": [
                "ValidationResult",
                "ValidationSuite",
                "UniversalSystemValidator",
                "AGRMMDHGValidator",
                "ValidationRunner",
                "run_validation",
            ],
            "suite_catalog": [
                {
                    "suite": "universal_system",
                    "runner": "UniversalSystemValidator.run_all_tests",
                    "test_count": 15,
                    "areas": ["translator", "crystal", "snap", "temporal", "identity", "receipt", "provenance"],
                },
                {
                    "suite": "agrm_mdhg",
                    "runner": "AGRMMDHGValidator.run_all_tests",
                    "test_count": 20,
                    "areas": ["mdhg", "ca_field", "agrm_router", "planet", "network"],
                },
                {
                    "suite": "mcp_tools",
                    "runner": "MCPToolsValidator.run_all_tests",
                    "test_count": 24,
                    "areas": ["layer1", "layer2", "layer3", "layer4", "layer5", "system", "audit"],
                },
                {
                    "suite": "integration",
                    "runner": "SystemValidator.validate_integration",
                    "test_count": 4,
                    "areas": ["full_data_flow", "error_recovery", "multi_planet_coordination", "governance_enforcement"],
                },
                {
                    "suite": "diagnostics",
                    "runner": "SystemDiagnostics.run_full_diagnostics",
                    "test_count": 7,
                    "areas": ["resources", "python", "dependencies", "filesystem", "mcp_server", "universal_system", "agrm_mdhg"],
                },
            ],
            "cli_surface": [
                "python -m mcp_os.validation.runner --all",
                "python -m mcp_os.validation.runner --universal",
                "python -m mcp_os.validation.runner --agrm --mdhg",
                "python -m mcp_os.validation.runner --all --json --output results.json",
            ],
            "known_issues": [
                {
                    "area": "missing_symbol",
                    "issue": "__init__.py and runner.py import ValidationRegistry, but system_validator.py does not define it in this checkout",
                    "impact": "package import or runner construction may fail before suites can execute",
                },
                {
                    "area": "cli_branch",
                    "issue": "runner.py documents --mcp, but main() does not route --mcp to validate_mcp_tools",
                    "impact": "MCP tool validation exists in source but is not reachable through the documented CLI flag",
                },
                {
                    "area": "benchmarks",
                    "issue": "README and SystemValidator reference benchmarks, but no benchmarks module is present in this slice tree",
                    "impact": "performance validation requires source repair or a new canonical benchmark implementation",
                },
            ],
            "activation_state": {
                "execution": "disabled",
                "reason": "validation suites import broad MCP OS runtime dependencies and may write result files through the CLI",
                "next_gate": "repair import/CLI issues, define dependency sandbox, then enable one suite at a time",
            },
            "policy": {
                "read": "source files and suite catalog are readable through module adapter",
                "execute": "blocked by call-plan route",
                "write": "result-file output and runtime side effects are blocked until sandbox policy exists",
                "ports": "no host port assigned to the validation slice",
            },
        }

    def mcp_os_validation_tree(self, max_depth: int = 2, limit: int = 120) -> dict[str, Any]:
        return {
            "capability": "mcp-os-validation",
            "tree": self.adapter.tree(
                "CMPLXDevKit",
                rel_path="CMPLXLOCALMCP/mcp_os/validation",
                max_depth=max_depth,
                limit=limit,
            ),
            "policy": "read-only source tree through CMPLXDevKit adapter",
        }

    def mcp_os_validation_read_file(self, path: str, max_bytes: int = 160_000) -> dict[str, Any]:
        normalized = path.replace("\\", "/").strip("/")
        allowed = {
            "__init__.py",
            "agrm_mdhg_validator.py",
            "diagnostics.py",
            "mcp_tools_validator.py",
            "README.md",
            "runner.py",
            "system_validator.py",
            "universal_system_validator.py",
        }
        if normalized not in allowed:
            raise HTTPException(403, f"mcp-os-validation file is not allowlisted: {path}")
        return {
            "capability": "mcp-os-validation",
            "file": normalized,
            "data": self.adapter.read_file(
                "CMPLXDevKit",
                f"CMPLXLOCALMCP/mcp_os/validation/{normalized}",
                max_bytes=max_bytes,
            ),
            "policy": "read-only source file through CMPLXDevKit adapter",
        }

    def mcp_os_validation_call_plan(self, req: GlobalSystemCallPlanRequest) -> dict[str, Any]:
        known_operations = {
            "run_all": "run ValidationRunner.run_all over universal and AGRM+MDHG suites",
            "run_universal": "run UniversalSystemValidator.run_all_tests",
            "run_agrm_mdhg": "run AGRMMDHGValidator.run_all_tests",
            "validate_mcp_tools": "run MCPToolsValidator.run_all_tests after CLI routing is repaired",
            "diagnostics": "run SystemDiagnostics.run_full_diagnostics",
            "quick_check": "run SystemDiagnostics.quick_check",
            "generate_report": "render SystemValidator.generate_report from suite results",
        }
        operation_key = req.name.replace("-", "_").lower()
        matched = known_operations.get(operation_key)
        return {
            "system": "validation",
            "capability": "mcp-os-validation",
            "operation": req.operation,
            "name": req.name,
            "known_operation": matched is not None,
            "operation_summary": matched or "unmapped validation operation; inspect source before promotion",
            "arguments": req.arguments,
            "dry_run": req.dry_run,
            "planned_reads": [
                "/api/global/validation/mcp-os",
                "/api/global/validation/mcp-os/tree",
                "/api/global/validation/mcp-os/files/system_validator.py",
                "/api/global/validation/mcp-os/files/runner.py",
                "/api/global/validation/mcp-os/files/diagnostics.py",
            ],
            "execution": "not executed; mcp-os validation suites are blocked until imports, dependency sandbox, and output policy are approved",
            "promotion_gates": [
                "define or remove ValidationRegistry before package import activation",
                "route --mcp to MCPToolsValidator or remove the documented flag",
                "decide whether missing benchmarks are repaired, replaced, or dropped from the canonical API",
                "add deterministic dry-run smoke tests for ValidationResult and ValidationSuite serialization",
                "route any JSON report output to a controller-owned quarantine path outside source repos",
            ],
            "policy": {
                "read": "allowed",
                "execute": "blocked",
                "write": "blocked",
                "ports": "none",
            },
        }

    def cqe_modular_capability(self, gitnexus: Any | None = None) -> dict[str, Any]:
        source_path = "src/cqe_modular_atomic"
        record = self._canonical_slice_record(
            "synthesis",
            "cmplxdevkit-cqe-core-slice-src-cqe-modular-atomic",
            gitnexus=gitnexus,
        )
        tree = self.adapter.tree("CMPLXDevKit", rel_path=source_path, max_depth=1, limit=50)
        return {
            "capability": "cqe-modular",
            "capability_id": record["capability_id"],
            "system": "synthesis",
            "status": "canonical_read_surface",
            "source": {
                "module": "CMPLXDevKit",
                "path": source_path,
                "adapter_id": self.surface_catalog.adapter_id("CMPLXDevKit"),
                "slice": record,
            },
            "purpose": "small CQE atomic synthesis core with Pack, Module, normalizer, slicer, braid, and overlay evidence",
            "files": tree.get("entries", []),
            "api": {
                "summary": "/api/global/synthesis/cqe-modular",
                "tree": "/api/global/synthesis/cqe-modular/tree",
                "file": "/api/global/synthesis/cqe-modular/files/{path}",
                "call_plan": "/api/global/synthesis/cqe-modular/call-plan",
            },
            "pack_model": {
                "fields": ["weyl_id", "chamber_id", "gsl", "meta", "payload", "fastlane", "pack_id", "hash"],
                "seal": "json sorted hash over core fields, excluding pack_id",
                "default_gsl": {"base": 24, "octave_k": 2, "riser": 7},
            },
            "module_catalog": [
                {"name": "Normalizer", "kind": "normalizer", "effect": "adds comparator metadata"},
                {"name": "WeylSlicer", "kind": "slicer", "effect": "adds slice metadata from weyl_id"},
                {"name": "BraidComposer", "kind": "composer", "effect": "adds toy braid_score and fence rules"},
                {"name": "EchoOverlay", "kind": "overlay", "effect": "adds prompt case variants"},
            ],
            "entrypoints": [
                {"name": "run_once", "file": "src/cqe_modular_atomic/engine.py", "mode": "linear synthesis pipeline"},
                {"name": "Pack.seal", "file": "src/cqe_modular_atomic/cqe_sdk.py", "mode": "pack hash/receipt primitive"},
                {"name": "EchoOverlay.process", "file": "src/cqe_modular_atomic/echo_overlay.py", "mode": "overlay module evidence"},
            ],
            "known_issues": [
                {
                    "area": "import_path",
                    "issue": "engine.py and echo_overlay.py import cqe_sdk as a top-level module",
                    "impact": "activation requires PYTHONPATH/package normalization or relative imports",
                },
                {
                    "area": "determinism",
                    "issue": "Pack.pack_id defaults to sha256(os.urandom(16)) while seal() hashes only core fields",
                    "impact": "repeatable synthesis tests must pass an explicit pack_id or compare hash rather than pack_id",
                },
            ],
            "activation_state": {
                "execution": "disabled",
                "reason": "source is promoted as a read/control surface first; even low-risk synthesis execution needs deterministic input/output contract tests",
                "next_gate": "normalize imports and add deterministic Pack.seal/run_once smoke tests before enabling execution",
            },
            "policy": {
                "read": "source files and module catalog are readable through module adapter",
                "execute": "blocked by call-plan route",
                "write": "blocked; this slice currently appears side-effect free but still needs a promotion gate",
                "ports": "no host port assigned to cqe-modular",
            },
        }

    def cqe_modular_tree(self, max_depth: int = 2, limit: int = 80) -> dict[str, Any]:
        return {
            "capability": "cqe-modular",
            "tree": self.adapter.tree("CMPLXDevKit", rel_path="src/cqe_modular_atomic", max_depth=max_depth, limit=limit),
            "policy": "read-only source tree through CMPLXDevKit adapter",
        }

    def cqe_modular_read_file(self, path: str, max_bytes: int = 80_000) -> dict[str, Any]:
        normalized = path.replace("\\", "/").strip("/")
        allowed = {"cqe_sdk.py", "echo_overlay.py", "engine.py"}
        if normalized not in allowed:
            raise HTTPException(403, f"cqe-modular file is not allowlisted: {path}")
        return {
            "capability": "cqe-modular",
            "file": normalized,
            "data": self.adapter.read_file("CMPLXDevKit", f"src/cqe_modular_atomic/{normalized}", max_bytes=max_bytes),
            "policy": "read-only source file through CMPLXDevKit adapter",
        }

    def cqe_modular_call_plan(self, req: GlobalSystemCallPlanRequest) -> dict[str, Any]:
        known_operations = {
            "run_once": "run the toy linear CQE synthesis pipeline over one prompt",
            "seal_pack": "compute a Pack hash over sorted core fields",
            "normalize": "apply Normalizer.process to add comparator metadata",
            "weyl_slice": "apply WeylSlicer.process to add slice metadata",
            "compose_braid": "apply BraidComposer.process to add braid_score metadata",
            "echo_overlay": "apply EchoOverlay.process to add prompt variants",
        }
        operation_key = req.name.replace("-", "_").lower()
        matched = known_operations.get(operation_key)
        return {
            "system": "synthesis",
            "capability": "cqe-modular",
            "operation": req.operation,
            "name": req.name,
            "known_operation": matched is not None,
            "operation_summary": matched or "unmapped CQE modular operation; inspect source before promotion",
            "arguments": req.arguments,
            "dry_run": req.dry_run,
            "planned_reads": [
                "/api/global/synthesis/cqe-modular",
                "/api/global/synthesis/cqe-modular/tree",
                "/api/global/synthesis/cqe-modular/files/cqe_sdk.py",
                "/api/global/synthesis/cqe-modular/files/engine.py",
            ],
            "execution": "not executed; cqe-modular remains plan-only until deterministic import and output policy are approved",
            "promotion_gates": [
                "normalize cqe_sdk imports for package-safe execution",
                "add deterministic Pack.seal tests with explicit pack_id",
                "define canonical synthesis request/response schema for prompt-to-pack output",
                "decide whether EchoOverlay is part of the canonical pipeline or a separate overlay plugin",
            ],
            "policy": {
                "read": "allowed",
                "execute": "blocked",
                "write": "blocked",
                "ports": "none",
            },
        }

    def devkit_ingest_capability(self, gitnexus: Any | None = None) -> dict[str, Any]:
        source_path = "devkit"
        record = self._canonical_slice_record(
            "knowledge",
            "cmplxdevkit-knowledge-ingest-slice-devkit",
            gitnexus=gitnexus,
        )
        tree = self.adapter.tree("CMPLXDevKit", rel_path=source_path, max_depth=2, limit=80)
        return {
            "capability": "devkit-ingest",
            "capability_id": record["capability_id"],
            "system": "knowledge",
            "status": "canonical_read_surface",
            "source": {
                "module": "CMPLXDevKit",
                "path": source_path,
                "adapter_id": self.surface_catalog.adapter_id("CMPLXDevKit"),
                "slice": record,
            },
            "purpose": "knowledge ingestion evidence for OCR, embedding/index stubs, and Qwen intake orchestration",
            "files": tree.get("entries", []),
            "api": {
                "summary": "/api/global/knowledge/devkit-ingest",
                "tree": "/api/global/knowledge/devkit-ingest/tree",
                "file": "/api/global/knowledge/devkit-ingest/files/{path}",
                "call_plan": "/api/global/knowledge/devkit-ingest/call-plan",
            },
            "tool_catalog": [
                {
                    "name": "ocr_image_to_text",
                    "file": "devkit/ingest/ocr_pipeline.py",
                    "mode": "OCR helper",
                    "dependencies": ["Pillow", "pytesseract"],
                },
                {
                    "name": "embed_texts_stub",
                    "file": "devkit/ingest/embed_and_index.py",
                    "mode": "embedding placeholder",
                    "output": "384-dimensional zero-vector placeholders",
                },
                {
                    "name": "index_atoms_stub",
                    "file": "devkit/ingest/embed_and_index.py",
                    "mode": "indexing placeholder",
                    "output": "debug JSONL-style tab lines",
                },
                {
                    "name": "qwen_pipeline_cli",
                    "file": "devkit/scripts/qwen_pipeline_cli.ps1",
                    "mode": "PowerShell wrapper evidence",
                    "output": "delegates to historical Qwen intake script",
                },
            ],
            "known_issues": [
                {
                    "area": "write_path",
                    "issue": "index_atoms_stub writes to projects/CMPLXNEXT/artifacts/embed_index_stub.jsonl relative to the process cwd",
                    "impact": "activation requires routing output to a controller-owned quarantine/artifact path",
                },
                {
                    "area": "optional_dependencies",
                    "issue": "ocr_image_to_text requires Pillow and pytesseract, and tesseract must be installed outside Python",
                    "impact": "OCR execution needs dependency and binary checks before enabling runtime use",
                },
                {
                    "area": "historical_paths",
                    "issue": "qwen_pipeline_cli.ps1 defaults to old D:\\Work Files and cmplx_submodules paths",
                    "impact": "wrapper must be repathed to current workspace folders before it can be considered live",
                },
            ],
            "activation_state": {
                "execution": "disabled",
                "reason": "ingest tools can read external files and write index artifacts; they need explicit sandbox and output policy",
                "next_gate": "define canonical ingest request/response schema, dependency checks, and artifact quarantine path",
            },
            "policy": {
                "read": "source files and tool catalog are readable through module adapter",
                "execute": "blocked by call-plan route",
                "write": "blocked until artifact output is routed through repo-kernel policy",
                "ports": "no host port assigned to devkit-ingest",
            },
        }

    def devkit_ingest_tree(self, max_depth: int = 2, limit: int = 80) -> dict[str, Any]:
        return {
            "capability": "devkit-ingest",
            "tree": self.adapter.tree("CMPLXDevKit", rel_path="devkit", max_depth=max_depth, limit=limit),
            "policy": "read-only source tree through CMPLXDevKit adapter",
        }

    def devkit_ingest_read_file(self, path: str, max_bytes: int = 80_000) -> dict[str, Any]:
        normalized = path.replace("\\", "/").strip("/")
        allowed = {
            "ingest/embed_and_index.py",
            "ingest/ocr_pipeline.py",
            "scripts/qwen_pipeline_cli.ps1",
        }
        if normalized not in allowed:
            raise HTTPException(403, f"devkit-ingest file is not allowlisted: {path}")
        return {
            "capability": "devkit-ingest",
            "file": normalized,
            "data": self.adapter.read_file("CMPLXDevKit", f"devkit/{normalized}", max_bytes=max_bytes),
            "policy": "read-only source file through CMPLXDevKit adapter",
        }

    def devkit_ingest_call_plan(self, req: GlobalSystemCallPlanRequest) -> dict[str, Any]:
        known_operations = {
            "ocr_image_to_text": "extract text from one image path with Pillow and pytesseract",
            "embed_texts_stub": "return placeholder 384-dimensional vectors for supplied text chunks",
            "index_atoms_stub": "append atom id/source debug records to an index artifact file",
            "qwen_pipeline_cli": "invoke the historical Qwen intake PowerShell wrapper after repathing",
        }
        operation_key = req.name.replace("-", "_").lower()
        matched = known_operations.get(operation_key)
        return {
            "system": "knowledge",
            "capability": "devkit-ingest",
            "operation": req.operation,
            "name": req.name,
            "known_operation": matched is not None,
            "operation_summary": matched or "unmapped ingest operation; inspect source before promotion",
            "arguments": req.arguments,
            "dry_run": req.dry_run,
            "planned_reads": [
                "/api/global/knowledge/devkit-ingest",
                "/api/global/knowledge/devkit-ingest/tree",
                "/api/global/knowledge/devkit-ingest/files/ingest/ocr_pipeline.py",
                "/api/global/knowledge/devkit-ingest/files/ingest/embed_and_index.py",
                "/api/global/knowledge/devkit-ingest/files/scripts/qwen_pipeline_cli.ps1",
            ],
            "execution": "not executed; devkit-ingest remains plan-only until dependency, path, and artifact-write policy are approved",
            "promotion_gates": [
                "replace historical absolute paths with repo-kernel source/workspace paths",
                "define OCR dependency probe for Pillow, pytesseract, and tesseract binary",
                "route index_atoms_stub output to a controller-owned artifact/quarantine directory",
                "define canonical ingest request/response schema for OCR text, embeddings, atom ids, and provenance",
                "decide whether Qwen intake wrapper is a knowledge-ingest tool or an external-ai-portal bridge",
            ],
            "policy": {
                "read": "allowed",
                "execute": "blocked",
                "write": "blocked",
                "ports": "none",
            },
        }

    def mcp_local_os_capability(self, gitnexus: Any | None = None) -> dict[str, Any]:
        source_path = "CMPLXLOCALMCP/mcp_os"
        record = self._canonical_slice_record(
            "mcp",
            "cmplxdevkit-mcp-local-os-slice-cmplxlocalmcp-mcp-os",
            gitnexus=gitnexus,
        )
        tree = self.adapter.tree("CMPLXDevKit", rel_path=source_path, max_depth=1, limit=120)
        return {
            "capability": "mcp-local-os",
            "capability_id": record["capability_id"],
            "system": "mcp",
            "status": "canonical_read_surface",
            "source": {
                "module": "CMPLXDevKit",
                "path": source_path,
                "adapter_id": self.surface_catalog.adapter_id("CMPLXDevKit"),
                "slice": record,
            },
            "purpose": "local MCP OS catalog over server/client/proxy/tool-registry code without starting the runtime",
            "files": tree.get("entries", []),
            "api": {
                "summary": "/api/global/mcp/local-os",
                "tree": "/api/global/mcp/local-os/tree",
                "file": "/api/global/mcp/local-os/files/{path}",
                "call_plan": "/api/global/mcp/local-os/call-plan",
            },
            "mcp_tool_layers": [
                {"layer": "layer1_morphonic", "count": 3, "examples": ["l1_morphon_generate", "l1_mglc_execute", "l1_seed_expand"]},
                {"layer": "layer2_geometric", "count": 4, "examples": ["l2_e8_project", "l2_leech_nearest", "l2_weyl_navigate", "l2_niemeier_classify"]},
                {"layer": "layer3_operational", "count": 2, "examples": ["l3_morsr_optimize", "l3_conservation_check"]},
                {"layer": "layer4_governance", "count": 3, "examples": ["l4_digital_root", "l4_seven_witness", "l4_policy_check"]},
                {"layer": "layer5_interface", "count": 3, "examples": ["l5_embed", "l5_query_similar", "l5_transform"]},
                {"layer": "system", "count": 3, "examples": ["sys_info", "sys_cache_stats", "sys_resolve_handle"]},
                {"layer": "universal", "count": 15, "examples": ["universal_translate", "crystal_store", "identity_register"]},
            ],
            "integration_registry": {
                "claimed_tool_count": 37,
                "categories": [
                    "quorum",
                    "think_tank",
                    "agent_orchestration",
                    "planetary_db",
                    "receipts",
                    "health",
                    "tmn",
                    "geometric",
                    "governance",
                    "controller_hierarchy",
                    "mmdb",
                    "speedlight",
                    "snap",
                    "workflow",
                    "advanced_composite",
                ],
            },
            "entrypoints": [
                {"name": "python -m mcp_os server", "file": "CMPLXLOCALMCP/mcp_os/__main__.py", "mode": "stdio MCP server"},
                {"name": "CMPLXMCPServer", "file": "CMPLXLOCALMCP/mcp_os/server/server.py", "mode": "MCP list_tools/call_tool handlers"},
                {"name": "CMPLXClient", "file": "CMPLXLOCALMCP/mcp_os/client/client.py", "mode": "typed client proxy"},
                {"name": "CMPLXToolRegistry", "file": "CMPLXLOCALMCP/mcp_os/cmplx_integration/registry.py", "mode": "CMPLX toolkit registry evidence"},
            ],
            "known_issues": [
                {
                    "area": "missing_dependency",
                    "issue": "server/tools.py imports unified_families.cmplx.functions, which is not proven available in the repo-kernel runtime",
                    "impact": "server activation requires dependency/package mapping or a replacement composition helper",
                },
                {
                    "area": "missing_import",
                    "issue": "cmplx_integration/registry.py calls asyncio.iscoroutinefunction without importing asyncio",
                    "impact": "registry tool execution can fail until the import is repaired",
                },
                {
                    "area": "runtime_side_effects",
                    "issue": "client startup launches a server subprocess over stdio and registry tools may emit receipts under data_root",
                    "impact": "activation needs process supervision and artifact/receipt output policy",
                },
            ],
            "activation_state": {
                "execution": "disabled",
                "reason": "the MCP OS is a broad runtime with subprocess, handle-cache, receipt, and dependency concerns",
                "next_gate": "promote one layer/tool family at a time after dependency repair and runtime supervision policy",
            },
            "policy": {
                "read": "source files, inventory, and tool catalogs are readable through module adapter",
                "execute": "blocked by call-plan route",
                "write": "blocked until receipt/cache/data_root outputs are routed through policy",
                "ports": "no host port assigned; original transport is stdio MCP",
            },
        }

    def mcp_local_os_tree(self, max_depth: int = 2, limit: int = 200) -> dict[str, Any]:
        return {
            "capability": "mcp-local-os",
            "tree": self.adapter.tree("CMPLXDevKit", rel_path="CMPLXLOCALMCP/mcp_os", max_depth=max_depth, limit=limit),
            "policy": "read-only source tree through CMPLXDevKit adapter",
        }

    def mcp_local_os_read_file(self, path: str, max_bytes: int = 180_000) -> dict[str, Any]:
        normalized = path.replace("\\", "/").strip("/")
        allowed = {
            "__main__.py",
            "README.md",
            "MCP_OS_INVENTORY.md",
            "requirements.txt",
            "server/server.py",
            "server/tools.py",
            "server/universal_tools.py",
            "client/client.py",
            "controllers/proxy.py",
            "controllers/registry.py",
            "cmplx_integration/registry.py",
            "cmplx_integration/advanced_tools.py",
            "modules/pipeline.py",
            "codec/encoder.py",
        }
        if normalized not in allowed:
            raise HTTPException(403, f"mcp-local-os file is not allowlisted: {path}")
        return {
            "capability": "mcp-local-os",
            "file": normalized,
            "data": self.adapter.read_file("CMPLXDevKit", f"CMPLXLOCALMCP/mcp_os/{normalized}", max_bytes=max_bytes),
            "policy": "read-only source file through CMPLXDevKit adapter",
        }

    def mcp_local_os_call_plan(self, req: GlobalSystemCallPlanRequest) -> dict[str, Any]:
        known_operations = {
            "list_tools": "enumerate MCP server Tool schemas without invoking handlers",
            "call_tool": "route one MCP tool call through CMPLXMCPServer after activation gates",
            "start_server": "start python -m mcp_os server under supervised stdio runtime",
            "client_call": "use CMPLXClient typed proxy method against a supervised server",
            "register_cmplx_tools": "load CMPLXToolRegistry categories after dependency repair",
            "resolve_handle": "resolve a server-side handle through sys_resolve_handle policy",
        }
        operation_key = req.name.replace("-", "_").lower()
        matched = known_operations.get(operation_key)
        return {
            "system": "mcp",
            "capability": "mcp-local-os",
            "operation": req.operation,
            "name": req.name,
            "known_operation": matched is not None,
            "operation_summary": matched or "unmapped MCP local OS operation; inspect source before promotion",
            "arguments": req.arguments,
            "dry_run": req.dry_run,
            "planned_reads": [
                "/api/global/mcp/local-os",
                "/api/global/mcp/local-os/tree",
                "/api/global/mcp/local-os/files/MCP_OS_INVENTORY.md",
                "/api/global/mcp/local-os/files/server/server.py",
                "/api/global/mcp/local-os/files/server/tools.py",
                "/api/global/mcp/local-os/files/client/client.py",
            ],
            "execution": "not executed; mcp-local-os remains plan-only until dependency, subprocess, handle-cache, and receipt policy are approved",
            "promotion_gates": [
                "repair or map unified_families dependency for server/tools.py",
                "add missing asyncio import or replacement in cmplx_integration/registry.py",
                "define supervised stdio MCP runtime lifecycle behind repo-kernel",
                "route handle registry, cache, data_root, and receipts to controller-owned paths",
                "activate one layer family at a time starting with read-only list_tools/schema inspection",
            ],
            "policy": {
                "read": "allowed",
                "execute": "blocked",
                "write": "blocked",
                "ports": "none; stdio transport only until activation",
            },
        }

    def call(self, name: str, req: AdapterCallRequest) -> dict[str, Any]:
        args = req.args or {}
        if req.action == "probe":
            return self._wrap(name, req.action, self.probe_runner.probe(
                name,
                mode=args.get("mode", "static"),
                include_search_examples=bool(args.get("include_search_examples", False)),
            ))
        if req.action == "promotion_plan":
            return self._wrap(name, req.action, self.probe_runner.promotion_plan(
                name,
                target=args.get("target", "CMPLX-PartsFactory"),
                include_probe=bool(args.get("include_probe", True)),
            ))
        if req.action == "surface_catalog":
            return self._wrap(name, req.action, self.surface_catalog.catalog(name, limit=int(args.get("limit", 500))))
        if req.action == "search":
            query = args.get("query")
            if not query:
                raise HTTPException(400, "search action requires args.query")
            return self._wrap(name, req.action, self.adapter.search(
                name,
                query,
                glob=args.get("glob"),
                limit=int(args.get("limit", 50)),
            ))
        if req.action == "tree":
            return self._wrap(name, req.action, self.adapter.tree(
                name,
                rel_path=args.get("path", "."),
                max_depth=int(args.get("max_depth", 2)),
                limit=int(args.get("limit", 300)),
            ))
        if req.action == "read_file":
            path = args.get("path")
            if not path:
                raise HTTPException(400, "read_file action requires args.path")
            return self._wrap(name, req.action, self.adapter.read_file(
                name,
                path,
                max_bytes=int(args.get("max_bytes", 200_000)),
            ))
        raise HTTPException(400, f"unsupported adapter action: {req.action}")

    def _wrap(self, name: str, action: str, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "module": name,
            "adapter_id": self.surface_catalog.adapter_id(name),
            "action": action,
            "mutation": "disabled by default" if not ALLOW_MUTATION else "enabled",
            "result": result,
        }

    def _guess_gitnexus_alias(self, module: str) -> str:
        aliases = {
            "CMPLXUNI": "rk-cmplxuni",
            "CMPLXMCP": "rk-cmplxmcp",
            "CMPLXDevKit": "rk-cmplxdevkit",
            "CMPLX-TMN-main": "rk-cmplx-tmn-main",
            "CMPLX-TMN1": "rk-cmplx-tmn1",
            "CMPLX-Monorepo": "rk-cmplx-monorepo",
            "CMPLX-Manny": "rk-cmplx-manny",
            "CMPLX-Formalization": "rk-cmplx-formalization",
            "scout-demo-service": "rk-scout-demo-service",
            "CMPLX-PartsFactory": "cmplx-partsfactory-root",
        }
        return aliases.get(module, f"rk-{module.lower()}")

    def _unification_next_action(
        self,
        name: str,
        ledger_module: dict[str, Any],
        hint: dict[str, Any] | None,
        probe: dict[str, Any] | None,
    ) -> dict[str, Any]:
        status = ledger_module.get("status", "unknown")
        if name == "CMPLX-PartsFactory":
            return {
                "lane": "controller_root",
                "action": "keep as the active housing/control repo; use GitNexus graph only for later internal extraction planning",
                "risk": "repo has no stable source promotion role",
            }
        if status == "filtered_candidate":
            return {
                "lane": "slice_filter_before_adapter",
                "action": "identify bounded reusable tool slices and exclude vendor/external shards before promotion",
                "risk": "large graph surface can drown canonical API decisions",
            }
        if status in {"needs_slice_index", "unindexed_review"}:
            return {
                "lane": "bounded_index_first",
                "action": "select subdirectories for GitNexus/index review before adapter promotion",
                "risk": "full-root scan or promotion is too noisy",
            }
        if status == "promoted_candidate":
            return {
                "lane": "adapter_ready_candidate" if (probe or {}).get("status") in {None, "adapter_ready", "probe_ready"} else "surface_catalog_review",
                "action": "keep expanding canonical routes and tests from this first-wave adapter source",
                "risk": "do not copy implementation source until behavior is covered",
            }
        if status in {"reference_candidate", "archive_reference"}:
            return {
                "lane": "reference_cross_check",
                "action": "use as provenance and gap-check evidence after canonical candidates are mapped",
                "risk": "do not make this the primary implementation source yet",
            }
        if status == "canonical_doctrine":
            return {
                "lane": "doctrine_evidence",
                "action": "attach docs/specs to capability governance instead of runtime routes",
                "risk": "runtime merge is not expected",
            }
        if hint:
            stats = hint.get("stats") or {}
            routes = self._int_graph(stats, "routes")
            tools = self._int_graph(stats, "tools")
            files = self._int_graph(stats, "files")
            nodes = self._int_graph(stats, "nodes", "symbols")
            processes = self._int_graph(stats, "processes")
            if routes or tools:
                return {
                    "lane": "adapter_ready_candidate",
                    "action": "join surfaced routes/tools to canonical adapter contracts before source movement",
                    "risk": "keep runtime activation dry-run until adapter coverage is explicit",
                }
            if files > 1000 or nodes > 50_000 or processes > 100:
                return {
                    "lane": "slice_filter_before_adapter",
                    "action": "identify bounded reusable tool slices and exclude vendor/external shards before promotion",
                    "risk": "large graph surface can drown canonical API decisions",
                }
            return {
                "lane": "surface_catalog_review",
                "action": "inspect GitNexus graph and surface catalog before deciding promotion state",
                "risk": "ledger status is not first-wave",
            }
        return {
            "lane": "manual_review",
            "action": "inspect module metadata and decide whether it needs GitNexus indexing or archive disposition",
            "risk": "insufficient indexed evidence",
        }

    def _unification_priority(
        self,
        ledger_module: dict[str, Any],
        hint: dict[str, Any] | None,
        action: dict[str, Any],
        name: str,
    ) -> int:
        base = int((hint or {}).get("priority_score") or 0)
        ledger_score = int(float((ledger_module.get("score") or {}).get("promotion_score") or 0) * 100)
        lane_bonus = {
            "adapter_ready_candidate": 8000,
            "surface_catalog_review": 5000,
            "slice_filter_before_adapter": 4500,
            "bounded_index_first": 3000,
            "doctrine_evidence": 1500,
            "reference_cross_check": 900,
            "controller_root": 300,
        }.get(action["lane"], 0)
        if name in {"scout-demo-service", "CMPLX-PartsFactory"}:
            lane_bonus -= 4000
        return base + ledger_score + lane_bonus

    def _unification_next_reads(self, module: str, alias: str, action: dict[str, Any]) -> list[str]:
        reads = [
            f"/api/adapters/{module}",
            f"/api/adapters/{module}/call",
            f"/api/gitnexus/graph-summary?repo={urllib.parse.quote(alias)}&limit=10",
        ]
        if action["lane"] in {"slice_filter_before_adapter", "bounded_index_first"}:
            reads.append(f"/api/adapters/{module}/call action=tree path=. max_depth=2")
            reads.append(f"/api/adapters/{module}/call action=search query=FastAPI")
        else:
            reads.append(f"/api/adapters/{module}/surfaces")
            reads.append(f"/api/promotion-plan/{module}")
        return reads

    def _int_graph(self, graph: dict[str, Any] | None, *keys: str) -> int:
        graph = graph or {}
        for key in keys:
            try:
                return int(graph.get(key) or 0)
            except (TypeError, ValueError):
                continue
        return 0

    def _slice_matrix_modules(
        self,
        gitnexus: Any | None,
        modules: list[str] | None,
        include_review: bool,
    ) -> list[str]:
        if modules:
            return [module for module in modules if module]
        worklist = self.unification_worklist(gitnexus=gitnexus, limit=25, include_probe=False)
        preferred_lanes = {"slice_filter_before_adapter"}
        if include_review:
            preferred_lanes.update({"bounded_index_first", "surface_catalog_review"})
        selected = [
            item["module"]
            for item in worklist.get("top_modules", [])
            if item.get("next_action", {}).get("lane") in preferred_lanes
        ]
        return selected[:6] or ["CMPLXDevKit"]

    def _matrix_next_intakes(self, grouped: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        preferred_order = ["code-execution", "validation", "synthesis", "mcp", "knowledge", "geometry", "formalization", "evidence", "unknown"]
        intakes = []
        for system in preferred_order:
            candidates = grouped.get(system, [])
            if not candidates:
                continue
            top = candidates[0]
            intakes.append({
                "system": system,
                "module": top["module"],
                "path": top["path"],
                "lane": top["lane"],
                "priority_score": top["priority_score"],
                "intake_plan": top["intake_plan"],
            })
        return intakes

    def _canonical_system_base(self, system: str) -> str:
        bases = {
            "code-execution": "/api/global/code-execution",
            "validation": "/api/global/validation",
            "synthesis": "/api/global/synthesis",
            "mcp": "/api/global/mcp",
            "knowledge": "/api/global/knowledge",
            "geometry": "/api/global/geometry",
            "formalization": "/api/global/formalization",
            "evidence": "/api/evidence",
            "unknown": "/api/global",
        }
        return bases.get(system, f"/api/global/{system}")

    def _slice_capability_id(self, module: str, path: str, lane: str | None) -> str:
        raw = f"{module}.{lane or 'slice'}.{path}"
        return re.sub(r"[^a-z0-9]+", ".", raw.lower()).strip(".")

    def _slice_route_id(self, capability_id: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", capability_id.lower()).strip("-")

    def _canonical_slice_record(self, system: str, slice_id: str, gitnexus: Any | None = None) -> dict[str, Any]:
        registry = self.canonical_slice_registry(gitnexus=gitnexus, system=system)
        for record in registry.get("slices", []):
            if slice_id in {record.get("capability_id"), record.get("route_id")}:
                return record
        raise HTTPException(404, f"unknown canonical slice for {system}: {slice_id}")

    def _slice_proposed_routes(self, system: str, capability_id: str, canonical_base: str) -> list[dict[str, str]]:
        safe_id = self._slice_route_id(capability_id)
        return [
            {
                "method": "GET",
                "path": f"{canonical_base}/slices/{safe_id}",
                "purpose": "return canonical slice summary and source evidence",
            },
            {
                "method": "GET",
                "path": f"{canonical_base}/slices/{safe_id}/tree",
                "purpose": "return bounded tree view through the module adapter",
            },
            {
                "method": "POST",
                "path": f"{canonical_base}/slices/{safe_id}/call-plan",
                "purpose": "plan execution or promotion behavior without running mutating code",
            },
        ]

    def _slice_intake_risks(self, candidate: dict[str, Any]) -> list[dict[str, str]]:
        risks = []
        summary = candidate.get("summary", {})
        lane = (candidate.get("classification") or {}).get("lane")
        if lane in {"quarantine_external_or_vendor", "nested_duplicate_review"}:
            risks.append({"level": "high", "risk": "candidate is evidence-first and should not become a primary implementation source"})
        if summary.get("large_file_count"):
            risks.append({"level": "medium", "risk": "large files require bounded reads and explicit file-level promotion"})
        if summary.get("file_count", 0) > 200:
            risks.append({"level": "medium", "risk": "slice is still broad; choose child paths before promotion"})
        if not risks:
            risks.append({"level": "low", "risk": "bounded slice; normal adapter tests and mutation policy still apply"})
        return risks

    def _slice_seed_paths(self, root: Path) -> list[Path]:
        seeds = []
        preferred = [
            "src/octa64",
            "src/cqe_modular_atomic",
            "src/cqe_good_example",
            "src/cqe_organized",
            "CMPLXLOCALMCP/mcp_os",
            "CMPLXLOCALMCP/mcp_os/validation",
            "devkit/ingest",
            "Handshake Entry-Build Guide",
            "CMPLXDevKit/Handshake Entry-Build Guide",
        ]
        for rel in preferred:
            if (root / rel).exists():
                seeds.append(Path(rel))
        for child in sorted([path for path in root.iterdir() if path.is_dir()], key=lambda path: path.name.lower()):
            rel = child.relative_to(root)
            if rel not in seeds and child.name not in {".git", ".gitnexus", ".claude", ".reuse", "LICENSES"}:
                seeds.append(rel)
        return seeds

    def _slice_path_summary(self, root: Path, rel: Path, sample_limit: int = 8) -> dict[str, Any]:
        base = root / rel
        files = []
        total_bytes = 0
        code_count = 0
        doc_count = 0
        large_count = 0
        suffixes: dict[str, int] = {}
        if base.is_file():
            iterable = [base]
        else:
            iterable = [path for path in base.rglob("*") if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts]
        for path in iterable[:20_000]:
            try:
                size = path.stat().st_size
            except OSError:
                continue
            total_bytes += size
            suffix = path.suffix.lower() or "<none>"
            suffixes[suffix] = suffixes.get(suffix, 0) + 1
            if suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".sql", ".sh", ".ps1"}:
                code_count += 1
            if suffix in {".md", ".rst", ".txt", ".docx", ".pdf"}:
                doc_count += 1
            if size > 2_000_000:
                large_count += 1
            if len(files) < sample_limit:
                files.append(path.relative_to(root).as_posix())
        file_count = len(iterable)
        return {
            "file_count": file_count,
            "code_file_count": code_count,
            "doc_count": doc_count,
            "bytes": total_bytes,
            "large_file_count": large_count,
            "top_suffixes": sorted(
                [{"suffix": suffix, "count": count} for suffix, count in suffixes.items()],
                key=lambda item: (-item["count"], item["suffix"]),
            )[:8],
            "sample_files": files,
        }

    def _slice_classification(self, rel: Path, summary: dict[str, Any], graph_summary: dict[str, Any] | None) -> dict[str, Any]:
        path = rel.as_posix().lower()
        if "cqe_organized" in path:
            return {
                "lane": "quarantine_external_or_vendor",
                "system": "evidence",
                "reason": "large organized CQE/vendor/test shard; keep searchable but do not promote whole",
            }
        if path == "cmplxdevkit":
            return {
                "lane": "nested_duplicate_review",
                "system": "evidence",
                "reason": "nested copy contains duplicated docs/local MCP material; inspect bounded children rather than promoting parent",
            }
        if "mcp_os/validation" in path or "validation" in path:
            return {
                "lane": "validation_tool_slice",
                "system": "validation",
                "reason": "bounded validation tools match existing validation global API lane",
            }
        if "mcp_os" in path:
            return {
                "lane": "mcp_local_os_slice",
                "system": "mcp",
                "reason": "local MCP operating surface can inform MCP runtime selection",
            }
        if "octa64" in path:
            return {
                "lane": "code_execution_runtime_slice",
                "system": "code-execution",
                "reason": "small VM/executor/codec package fits static code-execution runtime candidate work",
            }
        if "cqe_modular_atomic" in path:
            return {
                "lane": "cqe_core_slice",
                "system": "synthesis",
                "reason": "small modular CQE core is a better source than monolithic organized shards",
            }
        if "cqe_good_example" in path:
            return {
                "lane": "cqe_example_capability_slice",
                "system": "geometry",
                "reason": "curated CQE examples contain geometry, speedlight, lattice, atom, and validation skills",
            }
        if "ingest" in path or path == "devkit":
            return {
                "lane": "knowledge_ingest_slice",
                "system": "knowledge",
                "reason": "OCR/embed/index tooling belongs behind knowledge ingest planning",
            }
        if "handshake" in path or summary["doc_count"] > summary["code_file_count"]:
            return {
                "lane": "doctrine_doc_slice",
                "system": "formalization",
                "reason": "documentation/spec evidence should attach to governance and clean-image doctrine",
            }
        return {
            "lane": "review_slice",
            "system": "unknown",
            "reason": "candidate needs a focused surface catalog/read before promotion",
        }

    def _slice_priority(self, classification: dict[str, Any], summary: dict[str, Any]) -> int:
        lane = classification["lane"]
        lane_weight = {
            "code_execution_runtime_slice": 9000,
            "validation_tool_slice": 8500,
            "cqe_core_slice": 8000,
            "knowledge_ingest_slice": 7600,
            "mcp_local_os_slice": 7300,
            "cqe_example_capability_slice": 7000,
            "doctrine_doc_slice": 4200,
            "nested_duplicate_review": 2600,
            "review_slice": 2500,
            "quarantine_external_or_vendor": -5000,
        }.get(lane, 0)
        size_penalty = min(summary["file_count"], 5000) // 2
        code_bonus = min(summary["code_file_count"], 300) * 8
        doc_bonus = min(summary["doc_count"], 50) * 4
        large_penalty = summary["large_file_count"] * 300
        return lane_weight + code_bonus + doc_bonus - size_penalty - large_penalty


class RegisteredSystemsBundle:
    """Thin wrapper over registered repos, preserving each repo as its own root."""

    def __init__(
        self,
        registry: RepoRegistry,
        adapter: ModuleAdapter,
        probe_runner: CapabilityProbe,
        surface_catalog: ModuleSurfaceCatalog,
    ):
        self.registry = registry
        self.adapter = adapter
        self.probe_runner = probe_runner
        self.surface_catalog = surface_catalog

    def select_modules(self, req: RegisteredBundleRequest) -> list[dict[str, Any]]:
        if req.modules:
            return [self.registry.module(name) for name in req.modules]
        excluded = set(req.exclude or [])
        modules = [
            module for module in self.registry.modules()
            if module.get("name") not in excluded
        ]
        modules.sort(key=lambda item: item.get("pushed_at") or item.get("updated_at") or "")
        if req.count is not None:
            return modules[:req.count]
        return modules

    def describe(self, req: RegisteredBundleRequest) -> dict[str, Any]:
        modules = self.select_modules(req)
        return {
            "bundle_id": self._bundle_id(modules),
            "purpose": "registered-systems wrapper; repo roots stay separate, API/CLI is unified",
            "policy": {
                "parts_factory_role": "housing and wrapper yard, not an ingredient",
                "source_merge": "not yet; behavior is wrapped before files are rewritten or repathed",
                "settings": "each command runs with that module root as cwd and a module-scoped environment",
                "native_execution": "disabled unless explicitly requested for supported allowlisted commands",
            },
            "api": [
                "GET /api/registered-bundle",
                "POST /api/registered-bundle",
                "POST /api/registered-bundle/run",
            ],
            "cli": "python scripts\\registered_systems_bundle.py run status",
            "modules": [self._module_view(module) for module in modules],
        }

    def run(self, req: RegisteredBundleRunRequest) -> dict[str, Any]:
        modules = self.select_modules(req)
        results = [self._run_one(module, req) for module in modules]
        return {
            "bundle_id": self._bundle_id(modules),
            "command": req.command,
            "modules": [module["name"] for module in modules],
            "results": results,
        }

    def _run_one(self, module: dict[str, Any], req: RegisteredBundleRunRequest) -> dict[str, Any]:
        name = module["name"]
        root = self.registry.module_root(name)
        if req.command == "status":
            return self._status(module, root, req.timeout_seconds)
        if req.command == "probe":
            return {
                "module": name,
                "command": req.command,
                "cwd": str(root),
                "result": self.probe_runner.probe(name, mode="static", include_search_examples=False),
            }
        if req.command == "surface_catalog":
            return {
                "module": name,
                "command": req.command,
                "cwd": str(root),
                "result": self.surface_catalog.catalog(name, limit=req.limit),
            }
        if req.command == "tree":
            return {
                "module": name,
                "command": req.command,
                "cwd": str(root),
                "result": self.adapter.tree(name, rel_path=req.path, max_depth=2, limit=req.limit),
            }
        if req.command == "readme":
            return self._read_first_existing(module, ["README.md", "readme.md"], req.limit)
        if req.command == "native_verify":
            return self._native_verify(module, root, req)
        raise HTTPException(400, f"unsupported bundle command: {req.command}")

    def _status(self, module: dict[str, Any], root: Path, timeout_seconds: int) -> dict[str, Any]:
        proc = run(["git", "status", "--short", "--branch"], cwd=root, timeout=timeout_seconds)
        return {
            "module": module["name"],
            "command": "status",
            "cwd": str(root),
            "role": module.get("role"),
            "pushed_at": module.get("pushed_at"),
            "pinned_commit": module.get("pinned_commit"),
            "return_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }

    def _read_first_existing(self, module: dict[str, Any], names: list[str], limit: int) -> dict[str, Any]:
        root = self.registry.module_root(module["name"])
        for name in names:
            path = root / name
            if path.is_file():
                return {
                    "module": module["name"],
                    "command": "readme",
                    "cwd": str(root),
                    "result": self.adapter.read_file(module["name"], name, max_bytes=min(limit * 1000, 200_000)),
                }
        return {
            "module": module["name"],
            "command": "readme",
            "cwd": str(root),
            "error": "no README file found",
        }

    def _native_verify(
        self,
        module: dict[str, Any],
        root: Path,
        req: RegisteredBundleRunRequest,
    ) -> dict[str, Any]:
        commands = self._native_commands(module)
        verify = commands.get("native_verify")
        if not verify:
            return {
                "module": module["name"],
                "command": "native_verify",
                "cwd": str(root),
                "supported": False,
                "reason": "no allowlisted native verification command for this module yet",
            }
        if not req.execute_native:
            return {
                "module": module["name"],
                "command": "native_verify",
                "cwd": str(root),
                "supported": True,
                "dry_run": True,
                "native_command": verify,
                "reason": "set execute_native=true to run this module-owned command",
            }
        proc = subprocess.run(
            verify,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=req.timeout_seconds,
            check=False,
            env=self._module_env(module, root),
        )
        return {
            "module": module["name"],
            "command": "native_verify",
            "cwd": str(root),
            "supported": True,
            "dry_run": False,
            "native_command": verify,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-20_000:],
            "stderr": proc.stderr[-20_000:],
        }

    def _native_commands(self, module: dict[str, Any]) -> dict[str, list[str]]:
        name = module["name"]
        if name == "CMPLXMCP":
            return {"native_verify": ["python", "verify-mcp.py"]}
        return {}

    def _module_env(self, module: dict[str, Any], root: Path) -> dict[str, str]:
        env = os.environ.copy()
        env.update({
            "CMPLX_SYSTEM_NAME": module["name"],
            "CMPLX_SYSTEM_ROLE": str(module.get("role") or ""),
            "CMPLX_SYSTEM_ROOT": str(root),
        })
        return env

    def _module_view(self, module: dict[str, Any]) -> dict[str, Any]:
        root = self.registry.module_root(module["name"])
        commands = sorted({"status", "probe", "surface_catalog", "tree", "readme", *self._native_commands(module)})
        return {
            "name": module["name"],
            "role": module.get("role"),
            "local_path": module.get("local_path"),
            "container_path": str(root),
            "pushed_at": module.get("pushed_at"),
            "pinned_commit": module.get("pinned_commit"),
            "settings_scope": {
                "cwd": str(root),
                "env_keys": ["CMPLX_SYSTEM_NAME", "CMPLX_SYSTEM_ROLE", "CMPLX_SYSTEM_ROOT"],
                "repo_files_remain_in_place": True,
            },
            "commands": commands,
        }

    def _bundle_id(self, modules: list[dict[str, Any]]) -> str:
        names = "+".join(module["name"] for module in modules)
        return stable_id("registered-bundle", names)


class RuntimeTopology:
    PORT_HINT_RE = re.compile(r"(?:localhost:|127\.0\.0\.1:|port\s+)(\d{2,5})", re.IGNORECASE)
    PORT_RANGE_RE = re.compile(r"ports?\s+(\d{2,5})\s*-\s*(\d{2,5})", re.IGNORECASE)
    COMPOSE_PORT_RE = re.compile(r'"?(\d{2,5}):(\d{2,5})"?')
    COMPOSE_IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}

    def __init__(self, registry: RepoRegistry):
        self.registry = registry

    def topology(self, name: str) -> dict[str, Any]:
        root = self.registry.module_root(name)
        module = self.registry.module(name)
        readme_hints = self._readme_hints(root)
        compose_services = self._compose_services(root)
        return {
            "module": name,
            "role": module.get("role"),
            "readme_ports": readme_hints["ports"],
            "readme_port_ranges": readme_hints["ranges"],
            "compose_services": compose_services,
            "runtime_urls": self._runtime_urls(readme_hints["ports"], compose_services),
        }

    def host_module_root(self, name: str) -> str | None:
        if not HOST_REPOS_ROOT:
            return None
        return str(Path(HOST_REPOS_ROOT) / name).replace("\\", "/")

    def all_topologies(self, modules: list[str] | None = None) -> dict[str, Any]:
        names = modules or default_promotion_modules()
        return {"modules": [self.topology(name) for name in names]}

    def compose_evidence(self, name: str, recursive: bool = True, limit: int = 80) -> dict[str, Any]:
        root = self.registry.module_root(name)
        compose_files = self._compose_files(root, recursive=recursive, limit=limit)
        files = []
        all_services = []
        for compose in compose_files:
            services = self._parse_compose(compose, root)
            files.append({
                "file": str(compose.relative_to(root)).replace("\\", "/"),
                "service_count": len(services),
                "services": services,
            })
            all_services.extend(services)
        host_ports = sorted({
            port["host"]
            for service in all_services
            for port in service.get("ports", [])
            if port.get("host")
        })
        dependencies = sorted({
            dep
            for service in all_services
            for dep in service.get("depends_on", [])
            if dep
        })
        profiles = sorted({
            profile
            for service in all_services
            for profile in service.get("profiles", [])
            if profile
        })
        build_contexts = sorted({
            service["build"]
            for service in all_services
            if service.get("build")
        })
        images = sorted({
            service["image"]
            for service in all_services
            if service.get("image")
        })
        return {
            "module": name,
            "policy": "compose is evidence/preflight only; do not treat it as an activation command or deployment authority",
            "summary": {
                "compose_files": len(files),
                "services": len(all_services),
                "host_ports": host_ports,
                "dependency_edges": len(dependencies),
                "profiles": profiles,
                "build_contexts": len(build_contexts),
                "images": len(images),
                "truncated": len(compose_files) >= limit,
            },
            "quick_tips": self._compose_quick_tips(all_services, host_ports, dependencies, profiles, build_contexts),
            "files": files,
        }

    def compose_evidence_all(self, modules: list[str] | None = None, recursive: bool = True, limit_per_module: int = 80) -> dict[str, Any]:
        names = modules or default_promotion_modules()
        return {
            "policy": "compose files are preflight checklists for adapters/controllers; service startup remains explicit and separate",
            "modules": [self.compose_evidence(name, recursive=recursive, limit=limit_per_module) for name in names],
        }

    def health_check(self, modules: list[str] | None = None, timeout_seconds: float = 1.5, limit: int = 80) -> dict[str, Any]:
        checks = []
        for topology in self.all_topologies(modules).get("modules", []):
            for target in topology.get("runtime_urls", [])[:limit]:
                checks.append(self._check_url(topology["module"], target, timeout_seconds))
                if len(checks) >= limit:
                    return {"checks": checks, "truncated": True}
        return {"checks": checks, "truncated": False}

    def health_check_targets(self, targets: list[dict[str, Any]], timeout_seconds: float = 1.5, limit: int = 80) -> dict[str, Any]:
        checks = []
        for target in targets[:limit]:
            checks.append(self._check_url(target.get("module") or "unknown", target, timeout_seconds))
        return {"checks": checks, "truncated": len(targets) > limit}

    def _readme_hints(self, root: Path) -> dict[str, Any]:
        ports: dict[int, dict[str, Any]] = {}
        ranges = []
        for rel in ["README.md", "AGENTS.md"]:
            path = root / rel
            if not path.is_file():
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for index, line in enumerate(lines, start=1):
                for match in self.PORT_HINT_RE.finditer(line):
                    port = int(match.group(1))
                    ports[port] = {"port": port, "file": rel, "line": index, "text": line.strip()[:220]}
                for match in self.PORT_RANGE_RE.finditer(line):
                    ranges.append({
                        "start": int(match.group(1)),
                        "end": int(match.group(2)),
                        "file": rel,
                        "line": index,
                        "text": line.strip()[:220],
                    })
        return {"ports": list(ports.values()), "ranges": ranges}

    def _compose_services(self, root: Path) -> list[dict[str, Any]]:
        services = []
        for compose in self._compose_files(root, recursive=False, limit=80):
            services.extend(self._parse_compose(compose, root))
        return services

    def _compose_files(self, root: Path, recursive: bool, limit: int) -> list[Path]:
        patterns = ("docker-compose*.yml", "compose*.yml", "docker-compose*.yaml", "compose*.yaml")
        found: list[Path] = []
        if recursive:
            for pattern in patterns:
                for path in root.rglob(pattern):
                    if self._ignored_path(path):
                        continue
                    found.append(path)
                    if len(found) >= limit:
                        return sorted(set(found))
        else:
            for pattern in patterns:
                found.extend(root.glob(pattern))
        return sorted(set(found))[:limit]

    def _ignored_path(self, path: Path) -> bool:
        return any(part in self.COMPOSE_IGNORE_DIRS for part in path.parts)

    def _parse_compose(self, compose: Path, root: Path) -> list[dict[str, Any]]:
        try:
            lines = compose.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
        services = []
        in_services = False
        current: dict[str, Any] | None = None
        active_list: str | None = None
        for line in lines:
            stripped = line.strip()
            if stripped == "services:":
                in_services = True
                continue
            if not in_services:
                continue
            if stripped.endswith(":") and not line.startswith((" ", "\t")):
                if current:
                    services.append(current)
                    current = None
                in_services = False
                active_list = None
                continue
            service_match = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", line)
            if service_match:
                if current:
                    services.append(current)
                service_name = service_match.group(1)
                current = {
                    "service": service_name,
                    "compose_file": str(compose.relative_to(root)).replace("\\", "/"),
                    "evidence_role": "preflight_hint",
                    "container_name": None,
                    "build": None,
                    "image": None,
                    "runtime_kind": "unknown",
                    "ports": [],
                    "depends_on": [],
                    "profiles": [],
                    "volumes": [],
                    "env_files": [],
                }
                active_list = None
                continue
            if not current:
                continue
            if stripped.startswith("container_name:"):
                current["container_name"] = stripped.split(":", 1)[1].strip()
                active_list = None
            elif stripped.startswith("image:"):
                current["image"] = stripped.split(":", 1)[1].strip()
                current["runtime_kind"] = self._runtime_kind(current["service"], current["image"], None)
                active_list = None
            elif stripped.startswith("build:"):
                current["build"] = stripped.split(":", 1)[1].strip()
                current["runtime_kind"] = self._runtime_kind(current["service"], None, current["build"])
                active_list = "build"
            elif stripped.startswith("ports:"):
                active_list = "ports"
                for host, container in self.COMPOSE_PORT_RE.findall(stripped):
                    current["ports"].append({"host": int(host), "container": int(container)})
            elif active_list == "ports" and re.match(r'^-\s*"?\d{2,5}:\d{2,5}"?', stripped):
                for host, container in self.COMPOSE_PORT_RE.findall(stripped):
                    current["ports"].append({"host": int(host), "container": int(container)})
            elif stripped.startswith("depends_on:"):
                inline = stripped.split(":", 1)[1].strip()
                current["depends_on"].extend(self._compose_inline_list(inline))
                active_list = "depends_on"
            elif stripped.startswith("profiles:"):
                inline = stripped.split(":", 1)[1].strip()
                current["profiles"].extend(self._compose_inline_list(inline))
                active_list = "profiles"
            elif stripped.startswith("env_file:"):
                inline = stripped.split(":", 1)[1].strip()
                current["env_files"].extend(self._compose_inline_list(inline))
                active_list = "env_files"
            elif stripped.startswith("volumes:"):
                active_list = "volumes"
            elif stripped.startswith("- ") and active_list in {"depends_on", "profiles", "env_files", "volumes"}:
                value = stripped[2:].strip().strip('"').strip("'")
                if value and not self.COMPOSE_PORT_RE.search(value):
                    current[active_list].append(value[:220])
        if current:
            services.append(current)
        return services

    def _compose_inline_list(self, value: str) -> list[str]:
        value = value.strip()
        if not value:
            return []
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]
            return [item.strip().strip('"').strip("'") for item in value.split(",") if item.strip()]
        return [value.strip('"').strip("'")]

    def _compose_quick_tips(
        self,
        services: list[dict[str, Any]],
        host_ports: list[int],
        dependencies: list[str],
        profiles: list[str],
        build_contexts: list[str],
    ) -> list[str]:
        tips = [
            "Use compose as a checklist for required ports, service names, env files, build contexts, and dependency ordering.",
            "Adapters/controllers should translate these hints into explicit health checks and one-service-at-a-time activation plans.",
        ]
        if host_ports:
            tips.append(f"Declared host ports: {', '.join(str(port) for port in host_ports[:20])}.")
        if dependencies:
            tips.append(f"Declared service dependencies include: {', '.join(dependencies[:20])}.")
        if profiles:
            tips.append(f"Profiles indicate optional capability groups: {', '.join(profiles[:20])}.")
        if build_contexts:
            tips.append(f"{len(build_contexts)} local build context(s) may identify real runtime modules worth adapting.")
        if not services:
            tips.append("No compose services found; rely on README, package manifests, and static adapter surfaces.")
        return tips

    def _runtime_urls(self, readme_ports: list[dict[str, Any]], compose_services: list[dict[str, Any]]) -> list[dict[str, Any]]:
        targets: dict[tuple[str, int], dict[str, Any]] = {}
        for hint in readme_ports:
            port = hint["port"]
            targets[("readme", port)] = {
                "kind": "readme_hint",
                "service": None,
                "host_port": port,
                "container_port": None,
                "url": f"http://localhost:{port}",
                "source": hint,
            }
        for service in compose_services:
            for port in service.get("ports", []):
                host_port = port["host"]
                targets[(service["service"], host_port)] = {
                    "kind": "compose_service",
                    "service": service["service"],
                    "container_name": service.get("container_name"),
                    "runtime_kind": service.get("runtime_kind") or self._runtime_kind(service["service"], service.get("image"), service.get("build")),
                    "host_port": host_port,
                    "container_port": port["container"],
                    "url": self._target_url(host_port, service.get("runtime_kind")),
                    "health_url": self._health_url(host_port, service.get("runtime_kind")),
                    "source": service.get("compose_file"),
                }
        return list(targets.values())

    def _check_url(self, module: str, target: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
        runtime_kind = target.get("runtime_kind") or "http"
        url = target.get("health_url") or target.get("url")
        result = {
            "module": module,
            "service": target.get("service"),
            "host_port": target.get("host_port"),
            "runtime_kind": runtime_kind,
            "url": url,
            "ok": False,
            "status": None,
            "error": None,
        }
        if runtime_kind in {"tcp", "postgres", "redis"}:
            return self._check_tcp(result, timeout_seconds)
        try:
            with urllib.request.urlopen(url, timeout=timeout_seconds) as resp:
                result["status"] = resp.status
                result["ok"] = 200 <= resp.status < 500
        except urllib.error.HTTPError as exc:
            result["status"] = exc.code
            result["ok"] = exc.code < 500
        except Exception as exc:
            result["error"] = str(exc)[:220]
        return result

    def _check_tcp(self, result: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
        port = result.get("host_port")
        if not port:
            result["error"] = "missing host_port"
            return result
        host = "localhost"
        url = result.get("url") or ""
        if "://" in str(url):
            parsed = urllib.parse.urlparse(str(url))
            host = parsed.hostname or host
            port = parsed.port or port
        try:
            with socket.create_connection((host, int(port)), timeout=timeout_seconds):
                result["ok"] = True
                result["status"] = "tcp_open"
        except Exception as exc:
            result["error"] = str(exc)[:220]
        return result

    def _runtime_kind(self, service: str, image: str | None, build: str | None) -> str:
        haystack = f"{service} {image or ''} {build or ''}".lower()
        if "postgres" in haystack or service.endswith("-pg") or service.endswith("_pg"):
            return "postgres"
        if "redis" in haystack:
            return "redis"
        if "ngrok" in haystack:
            return "http"
        if "cmplxcode" in haystack:
            return "http"
        return "http"

    def _health_url(self, host_port: int, runtime_kind: str | None) -> str:
        if runtime_kind in {"postgres", "redis"}:
            return ""
        return f"http://localhost:{host_port}/health"

    def _target_url(self, host_port: int, runtime_kind: str | None) -> str:
        if runtime_kind in {"postgres", "redis"}:
            return f"tcp://localhost:{host_port}"
        return f"http://localhost:{host_port}"


class RuntimeActivationPlanner:
    INFRA_SERVICES = {"tmn2-pg", "tmn2-redis"}

    def __init__(self, registry: RepoRegistry, unified: "UnifiedAIWorkflowRegistry", topology: RuntimeTopology):
        self.registry = registry
        self.unified = unified
        self.topology = topology

    def plan(self, req: RuntimeActivationPlanRequest) -> dict[str, Any]:
        workflow = self.unified.workflow(req.workflow, modules=req.modules)
        module_plans = []
        for entry in workflow.get("entries", []):
            module = entry["module"]
            targets = [{**target, "module": module} for target in entry.get("runtime_targets", [])]
            if not targets and req.workflow == "mcp_tools" and module == "CMPLXMCP":
                targets = [{**target, "module": module} for target in self.topology.topology(module).get("runtime_urls", [])]
            module_plans.append(self._module_plan(module, targets, include_infra=req.include_infra))
        return {
            "workflow": req.workflow,
            "modules": module_plans,
            "policy": {
                "execution": "plan only; this endpoint never starts containers or processes",
                "compose": "compose is evidence/preflight, not the application layer",
                "ports": "honor repo README and compose-declared port assignments as hints",
                "approval": "starting any service requires explicit user approval and a separate activation action",
            },
        }

    def _module_plan(self, module: str, targets: list[dict[str, Any]], include_infra: bool) -> dict[str, Any]:
        root = self.registry.module_root(module)
        host_root = self.topology.host_module_root(module)
        compose_targets = [target for target in targets if target.get("kind") == "compose_service" and target.get("service")]
        readme_targets = [target for target in targets if target.get("kind") == "readme_hint"]
        compose_services = []
        if include_infra and compose_targets:
            compose_services.extend(sorted(self.INFRA_SERVICES))
        compose_services.extend(target["service"] for target in compose_targets if target.get("service") not in compose_services)

        commands = []
        if compose_services:
            commands.append({
                "type": "compose_preflight_evidence",
                "container_cwd": str(root),
                "host_cwd": host_root,
                "command": "review compose evidence; do not launch from this plan",
                "services": compose_services,
                "confidence": "high",
                "notes": [
                    "compose service and host ports are declared in the source repo",
                    "treat compose as a quick tip sheet for ports, dependency order, env files, and build contexts",
                    "controllers/adapters own actual runtime activation",
                ],
            })
        for target in readme_targets:
            hint = self._readme_command_hint(module, target)
            commands.append({
                "type": "manual_readme_runtime",
                "container_cwd": str(root),
                "host_cwd": host_root,
                "command": hint["command"],
                "port": target.get("host_port"),
                "source": target.get("source"),
                "confidence": hint["confidence"],
                "transport": hint["transport"],
                "notes": hint["notes"],
            })
        return {
            "module": module,
            "runtime_targets": targets,
            "commands": commands,
        }

    def _readme_command_hint(self, module: str, target: dict[str, Any]) -> dict[str, Any]:
        port = target.get("host_port")
        if module == "CMPLXUNI" and port == 3000:
            return {
                "command": "cd cmplx-nextjs; npm install; npm run dev",
                "transport": "http",
                "confidence": "medium",
                "notes": ["README explicitly says Next.js is accessed at localhost:3000"],
            }
        if module == "CMPLXMCP" and port == 8900:
            if CMPLXMCP_RUNTIME_SHIM_AVAILABLE:
                module_root = self.topology.host_module_root(module) or "./repo_kernel/repos/CMPLXMCP"
                return {
                    "command": f"docker run --rm -i -v {module_root}:/module:ro cmplxmcp-runtime:probe",
                    "transport": "stdio_mcp",
                    "confidence": "medium",
                    "notes": [
                        "Dedicated CMPLXMCP runtime shim has been scaffolded and probed",
                        "Probe constructs CMPLXMCPServer through server.server",
                        "Transport is stdio MCP; do not assume HTTP port 8900 until an HTTP/SSE bridge is added",
                    ],
                }
            return {
                "command": "python mcp-server-entry.py",
                "transport": "stdio_mcp_or_http_uncertain",
                "confidence": "low",
                "notes": [
                    "README client example mentions http://localhost:8900",
                    "mcp-server-entry.py starts an MCP stdio server and does not visibly bind port 8900",
                    "treat this as an investigation target before relying on HTTP routing",
                ],
            }
        return {
            "command": f"start runtime described by README for port {port}",
            "transport": "unknown",
            "confidence": "low",
            "notes": ["README mentions the port but no repo compose service was mapped to it"],
        }


class RuntimeIssueReporter:
    def __init__(self, topology: RuntimeTopology, activation: RuntimeActivationPlanner):
        self.topology = topology
        self.activation = activation

    def report(self) -> dict[str, Any]:
        issues = []
        if not HOST_REPOS_ROOT:
            issues.append({
                "severity": "medium",
                "area": "activation",
                "issue": "host repo root is not configured",
                "detail": "activation plans can only return container paths",
            })

        for workflow in ["memory", "mcp_tools"]:
            plan = self.activation.plan(RuntimeActivationPlanRequest(workflow=workflow))
            for module in plan.get("modules", []):
                for command in module.get("commands", []):
                    if command.get("confidence") == "low":
                        issues.append({
                            "severity": "medium",
                            "area": "runtime_transport",
                            "module": module["module"],
                            "issue": "runtime command has low confidence",
                            "command": command.get("command"),
                            "notes": command.get("notes", []),
                        })

        if importlib.util.find_spec("numpy") is None and not CMPLXMCP_RUNTIME_SHIM_AVAILABLE:
            issues.append({
                "severity": "medium",
                "area": "runtime_dependency",
                "module": "CMPLXMCP",
                "issue": "repo-kernel image lacks numpy for direct CMPLXMCP imports",
                "detail": "CMPLXMCP setup.py declares numpy; direct import probing failed until a dedicated runtime image or dependency install is added",
            })

        if not CMPLXMCP_RUNTIME_SHIM_AVAILABLE:
            issues.append({
                "severity": "medium",
                "area": "package_identity",
                "module": "CMPLXMCP",
                "issue": "historical package name mcp_os is not present as a directory",
                "detail": "entry points reference mcp_os, while the cloned repo root contains server/ and client/ packages directly",
            })
        else:
            issues.append({
                "severity": "low",
                "area": "runtime_transport",
                "module": "CMPLXMCP",
                "issue": "CMPLXMCP shim is stdio-only until an HTTP/SSE bridge is added",
                "detail": "The dedicated shim resolves dependency/package probing, but live HTTP routing still requires a bridge.",
            })

        memory_plan = self.activation.plan(RuntimeActivationPlanRequest(workflow="memory"))
        memory_targets = []
        for module in memory_plan.get("modules", []):
            memory_targets.extend(module.get("runtime_targets", []))
        if memory_targets:
            health = self.topology.health_check_targets(memory_targets, timeout_seconds=0.4, limit=12)
            if not any(check.get("ok") for check in health.get("checks", [])):
                issues.append({
                    "severity": "low",
                    "area": "runtime_health",
                    "issue": "no memory runtime target is currently healthy",
                    "detail": "memory API will use static adapter fallback until services are started",
                })

        return {
            "issues": issues,
            "summary": {
                "issue_count": len(issues),
                "high": sum(1 for issue in issues if issue["severity"] == "high"),
                "medium": sum(1 for issue in issues if issue["severity"] == "medium"),
                "low": sum(1 for issue in issues if issue["severity"] == "low"),
            },
        }


class UnifiedAIWorkflowRegistry:
    WORKFLOWS = {
        "memory": ["memory", "mmdb", "atom", "receipt", "ledger", "family"],
        "mcp_tools": ["mcp", "tool", "cmplx_info"],
        "agent_orchestration": ["agent", "daemon", "coop", "spawn", "identity", "thinktank"],
        "knowledge": ["kb", "library", "semantic", "atlas", "papers", "code", "query"],
        "training": ["train", "trainer", "teaching", "evaluate"],
        "geometry": ["e8", "lattice", "leech", "weyl", "niemeier", "morphon", "morsr", "glyph", "crystal"],
        "code_execution": ["code", "polyglot", "execute", "sandbox", "portal"],
        "pipeline": ["pipeline", "ingress", "egress", "intake", "staging", "harvester"],
        "external_ai_portal": ["portal", "ngrok", "workspace", "gateway"],
        "formalization": ["formal", "proof", "theorem", "axiom", "planner", "octet", "unfold", "handshake", "channel_"],
        "ai_runtime": ["infer", "model", "embed", "generate", "llm", "chat", "ai_hub"],
        "operations": ["health", "status", "metrics", "dashboard", "domain_manager", "manager", "restart", "scale", "report", "ready", "cache", "port-controller", "dock"],
        "eventing": ["broadcast", "subscribe", "dispatch", "publish", "events", "channels", "subscribers", "replay"],
        "community": ["board", "bounty", "bounties", "thread", "posts", "openclaw", "claw", "planet"],
        "economy": ["economy", "mint", "marketplace", "commission", "lend", "stake", "buyback", "pools"],
        "validation": ["validation", "validate", "conservation", "gate", "audit", "quality", "surplus", "partition", "rules"],
        "synthesis": ["brain", "integrator", "integrate", "interrogation", "canon", "librarian", "free5e", "porter", "discover", "study", "questions", "saturation"],
        "simulation": ["simulation", "sim", "ca_sim", "create_ca", "step_ca", "entropy", "panels", "inject", "julia", "planet"],
    }

    def __init__(
        self,
        registry: RepoRegistry,
        surface_catalog: ModuleSurfaceCatalog,
        topology: RuntimeTopology,
    ):
        self.registry = registry
        self.surface_catalog = surface_catalog
        self.topology = topology

    def list_workflows(self, modules: list[str] | None = None) -> dict[str, Any]:
        names = modules or default_promotion_modules()
        module_data = {name: self._module_workflow_data(name) for name in names}
        workflows = []
        for workflow in self.WORKFLOWS:
            entries = [data for data in module_data.values() if data["matches"].get(workflow)]
            workflows.append({
                "workflow": workflow,
                "module_count": len(entries),
                "modules": [
                    {
                        "module": entry["module"],
                        "routes": len(entry["matches"][workflow]["routes"]),
                        "mcp_tools": len(entry["matches"][workflow]["mcp_tools"]),
                        "runtime_targets": len(entry["matches"][workflow]["runtime_targets"]),
                    }
                    for entry in entries
                ],
            })
        return {
            "kernel": KERNEL_ID,
            "unification_policy": "one workflow API layer at a time; honor module runtime ports before live calls",
            "workflows": workflows,
        }

    def workflow(self, workflow: str, modules: list[str] | None = None) -> dict[str, Any]:
        if workflow not in self.WORKFLOWS:
            raise HTTPException(404, f"unknown workflow: {workflow}")
        names = modules or default_promotion_modules()
        entries = []
        for name in names:
            data = self._module_workflow_data(name)
            match = data["matches"].get(workflow)
            if match:
                entries.append({
                    "module": name,
                    "adapter_id": self.surface_catalog.adapter_id(name),
                    "routes": match["routes"][:80],
                    "mcp_tools": match["mcp_tools"][:80],
                    "runtime_targets": match["runtime_targets"][:80],
                })
        return {
            "workflow": workflow,
            "keywords": self.WORKFLOWS[workflow],
            "entries": entries,
            "contract": self._contract(workflow),
        }

    def route_plan(self, workflow: str, modules: list[str] | None = None) -> dict[str, Any]:
        data = self.workflow(workflow, modules=modules)
        steps = []
        for entry in data["entries"]:
            if entry["runtime_targets"]:
                steps.append({
                    "module": entry["module"],
                    "step": "runtime",
                    "action": "prefer live service URL when healthy",
                    "targets": entry["runtime_targets"][:10],
                })
            if entry["mcp_tools"]:
                steps.append({
                    "module": entry["module"],
                    "step": "mcp",
                    "action": "map matching MCP tools behind unified workflow tool calls",
                    "tools": entry["mcp_tools"][:10],
                })
            if entry["routes"]:
                steps.append({
                    "module": entry["module"],
                    "step": "api",
                    "action": "map matching FastAPI/Next routes behind unified workflow routes",
                    "routes": entry["routes"][:10],
                })
        return {
            "workflow": workflow,
            "contract": data["contract"],
            "steps": steps,
            "live_call_policy": {
                "default": "health-check first; then route to the documented host port",
                "fallback": "use static adapter surfaces when service is not running",
                "mutation": "do not call mutating routes automatically",
            },
        }

    def _module_workflow_data(self, name: str) -> dict[str, Any]:
        surfaces = self.surface_catalog.catalog(name, limit=2000)
        topology = self.topology.topology(name)
        matches: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for workflow, keywords in self.WORKFLOWS.items():
            routes = [route for route in surfaces.get("routes", []) + surfaces.get("nextjs_routes", []) if self._matches(route, keywords)]
            mcp_tools = [tool for tool in surfaces.get("mcp_tools", []) if self._matches(tool, keywords)]
            runtime_targets = [target for target in topology.get("runtime_urls", []) if self._matches(target, keywords)]
            if routes or mcp_tools or runtime_targets:
                matches[workflow] = {
                    "routes": routes,
                    "mcp_tools": mcp_tools,
                    "runtime_targets": runtime_targets,
                }
        return {"module": name, "matches": matches}

    def _matches(self, item: dict[str, Any], keywords: list[str]) -> bool:
        haystack = json.dumps(item, ensure_ascii=False).lower()
        return any(keyword.lower() in haystack for keyword in keywords)

    def _contract(self, workflow: str) -> dict[str, Any]:
        return {
            "base_path": f"/api/unified/workflows/{workflow}",
            "verbs": ["describe", "route_plan", "health_first_live_call"],
            "input": "JSON object with workflow-specific payload",
            "output": "JSON object with module, adapter_id, target, result/ref",
        }


class MemoryWorkflowController:
    READ_TOOL_NAMES = {"list_families", "get_family_stats", "get_atom", "query_atoms", "get_receipts_for_atom"}
    WRITE_TOOL_NAMES = {"insert_atom", "insert_receipt", "log_e8_operation", "log_speedlight_receipt", "assign_mdhg_address"}

    def __init__(self, unified: UnifiedAIWorkflowRegistry, topology: RuntimeTopology):
        self.unified = unified
        self.topology = topology

    def capabilities(self) -> dict[str, Any]:
        workflow = self.unified.workflow("memory")
        read_tools = []
        write_tools = []
        read_routes = []
        write_routes = []
        runtime_targets = []
        for entry in workflow.get("entries", []):
            runtime_targets.extend({**target, "module": entry["module"]} for target in entry.get("runtime_targets", []))
            for tool in entry.get("mcp_tools", []):
                name = tool.get("name")
                if name in self.READ_TOOL_NAMES:
                    read_tools.append({**tool, "module": entry["module"]})
                elif name in self.WRITE_TOOL_NAMES:
                    write_tools.append({**tool, "module": entry["module"]})
            for route in entry.get("routes", []):
                item = {**route, "module": entry["module"]}
                if route.get("method") == "GET":
                    read_routes.append(item)
                else:
                    write_routes.append(item)
        return {
            "workflow": "memory",
            "base_path": "/api/unified/memory",
            "read_tools": read_tools,
            "write_tools": write_tools,
            "read_routes": read_routes,
            "write_routes": write_routes,
            "runtime_targets": runtime_targets,
            "policy": {
                "read": "may be routed after health check",
                "write": "plan only unless explicitly approved outside this controller",
                "fallback": "static adapter surfaces",
            },
        }

    def query_plan(self, req: MemoryQueryRequest) -> dict[str, Any]:
        caps = self.capabilities()
        desired_tools = self._desired_tools(req)
        tool_candidates = [tool for tool in caps["read_tools"] if tool.get("name") in desired_tools]
        route_candidates = [
            route for route in caps["read_routes"]
            if self._route_matches_memory_query(route, req)
        ]
        runtime_candidates = caps["runtime_targets"]
        health = self.topology.health_check_targets(runtime_candidates, timeout_seconds=0.5, limit=20)
        return {
            "workflow": "memory",
            "operation": "query",
            "request": req.model_dump(),
            "selected_strategy": "runtime_if_healthy_else_static_adapter",
            "tool_candidates": tool_candidates[:20],
            "route_candidates": route_candidates[:20],
            "runtime_candidates": runtime_candidates[:20],
            "health": health,
            "dry_run": req.dry_run,
            "execution": "not executed; no live healthy memory runtime was selected" if req.dry_run else "live execution disabled for this first memory layer",
        }

    def receipt_plan(self, req: MemoryQueryRequest) -> dict[str, Any]:
        caps = self.capabilities()
        tools = [tool for tool in caps["read_tools"] + caps["write_tools"] if "receipt" in tool.get("name", "")]
        routes = [route for route in caps["read_routes"] + caps["write_routes"] if "receipt" in json.dumps(route).lower()]
        return {
            "workflow": "memory",
            "operation": "receipt",
            "request": req.model_dump(),
            "tool_candidates": tools[:30],
            "route_candidates": routes[:30],
            "policy": "write-capable receipt tools are returned as candidates only; do not execute without explicit approval",
        }

    def runtime_preflight(self) -> dict[str, Any]:
        caps = self.capabilities()
        by_module: dict[str, list[dict[str, Any]]] = {}
        for target in caps["runtime_targets"]:
            by_module.setdefault(target["module"], []).append(target)

        modules = []
        all_targets = []
        for module, targets in by_module.items():
            service_names = sorted({target.get("service") for target in targets if target.get("service")})
            compose = self.topology.compose_evidence(module, recursive=True, limit=120)
            compose_services = [
                service
                for file_info in compose.get("files", [])
                for service in file_info.get("services", [])
                if service.get("service") in service_names
            ]
            all_targets.extend(targets)
            modules.append({
                "module": module,
                "needed_services": service_names,
                "runtime_targets": targets,
                "compose_evidence": compose_services,
                "missing_compose_services": sorted(set(service_names) - {service.get("service") for service in compose_services}),
                "preflight": [
                    "confirm required env files exist before launch",
                    "confirm host ports are free",
                    "start dependencies before memory HTTP services",
                    "run health checks before allowing live memory writes",
                ],
            })

        health = self.topology.health_check_targets(all_targets, timeout_seconds=0.5, limit=30)
        return {
            "workflow": "memory",
            "operation": "runtime_preflight",
            "policy": "preflight only; does not start containers, write Postgres, or extract evidence",
            "modules": modules,
            "health": health,
            "next_gate": "explicit approval to activate selected services one at a time",
        }

    def corpus_import_plan(self, req: MemoryCorpusImportPlanRequest, sources: SourceUniverse) -> dict[str, Any]:
        summary = sources.archive_corpus_summary(SourceArchiveCorpusSummaryRequest(
            source_id=req.source_id,
            path=req.archive,
            max_bytes=1_000_000,
        ))
        manifest = sources.archive_manifest(SourceArchiveManifestRequest(
            source_id=req.source_id,
            path=req.archive,
            limit=req.manifest_limit,
        ))
        db_members = [entry for entry in manifest.get("entries", []) if entry.get("marker") == "database"]
        db_hashes = sources.archive_hash_slice(ArchiveHashSliceRequest(
            source_id=req.source_id,
            path=req.archive,
            limit=req.manifest_limit,
            max_member_bytes=req.max_db_member_bytes,
            include_suffixes=[".sqlite", ".sqlite3", ".db"],
        ))
        top_duplicates = summary.get("summary", {}).get("top_duplicate_rows", [])
        candidates = sorted(
            db_members,
            key=lambda item: (
                0 if "active" in item.get("path", "").lower() else 1,
                item.get("size") or 0,
                item.get("path", ""),
            ),
        )[:30]
        return {
            "workflow": "memory",
            "operation": "corpus_import_plan",
            "request": req.model_dump(),
            "policy": "plan only; no archive extraction, Postgres writes, or SQLite mutation",
            "corpus_summary": summary.get("summary"),
            "database_member_count_listed": len(db_members),
            "database_hash_summary": db_hashes.get("summary"),
            "database_candidates": candidates,
            "top_duplicate_rows": top_duplicates[:20],
            "import_gates": [
                "select one or more database candidates by path and hash",
                "extract selected members to a quarantine/staging directory only after approval",
                "open SQLite read-only and inspect schema/table counts",
                "map rows to the unified memory contract",
                "write to Postgres only after explicit approval and backup/export receipt",
            ],
            "recommended_first_candidates": candidates[:5],
        }

    def mmdb_import_compatibility(self, req: MMDBImportCompatibilityRequest, sources: SourceUniverse) -> dict[str, Any]:
        dry_run = sources.mmdb_import_dry_run(MMDBImportDryRunRequest(
            path=req.path,
            tables=req.tables,
            sample_limit=req.sample_limit,
            max_rows_per_table=req.max_rows_per_table,
            include_samples=True,
        ))
        caps = self.capabilities()
        health = self.topology.health_check_targets(caps["runtime_targets"], timeout_seconds=0.5, limit=30)
        target_plans = [
            self._target_compatibility_plan("memory_atom", dry_run, caps),
            self._target_compatibility_plan("receipt", dry_run, caps),
            self._target_compatibility_plan("memory_edge", dry_run, caps),
        ]
        blockers = self._mmdb_import_blockers(target_plans, health)
        return {
            "workflow": "memory",
            "operation": "mmdb_import_compatibility",
            "policy": "compatibility plan only; no live runtime calls, no Postgres writes, no source mutation",
            "request": req.model_dump(),
            "dry_run_summary": dry_run.get("summary"),
            "source": dry_run.get("source"),
            "target_plans": target_plans,
            "runtime_health": health,
            "recommended_strategy": self._mmdb_recommended_strategy(target_plans, blockers),
            "staging_contract": self._mmdb_staging_contract(),
            "blockers": blockers,
            "next_gates": [
                "implement a repo-kernel staging adapter that stores import receipts before live writes",
                "add exact target-family selection for CMPLXUNI MMDB tools",
                "define memory_edge semantics before using DAG or graph write surfaces",
                "start and health-check selected memory runtime only after approval",
                "request explicit approval before any write-capable importer is added or run",
            ],
        }

    def _desired_tools(self, req: MemoryQueryRequest) -> set[str]:
        if req.atom_id:
            return {"get_atom", "get_receipts_for_atom"}
        if req.sql:
            return {"query_atoms"}
        if req.family:
            return {"get_family_stats", "list_families"}
        return {"list_families", "get_family_stats", "query_atoms"}

    def _route_matches_memory_query(self, route: dict[str, Any], req: MemoryQueryRequest) -> bool:
        haystack = json.dumps(route).lower()
        if req.atom_id and "atom" in haystack:
            return True
        if req.sql and ("query" in haystack or "table" in haystack):
            return True
        if req.family and ("family" in haystack or "stats" in haystack):
            return True
        return any(token in haystack for token in ["memory", "mmdb", "atom", "receipt", "ledger"])

    def _target_compatibility_plan(self, target: str, dry_run: dict[str, Any], caps: dict[str, Any]) -> dict[str, Any]:
        source_tables = [
            table["table"]
            for table in dry_run.get("tables", [])
            if table.get("mapping", {}).get("target_record") == target
        ]
        candidate_rows = sum(
            int(table.get("candidate_rows") or 0)
            for table in dry_run.get("tables", [])
            if table.get("mapping", {}).get("target_record") == target
        )
        tool_matches = self._compatible_tools(target, caps)
        route_matches = self._compatible_routes(target, caps)
        coverage = "strong" if tool_matches else "partial" if route_matches else "missing"
        if target == "memory_edge" and coverage != "missing":
            coverage = "partial"
        return {
            "target_record": target,
            "source_tables": source_tables,
            "candidate_rows": candidate_rows,
            "coverage": coverage,
            "tool_candidates": tool_matches,
            "route_candidates": route_matches,
            "adapter_recommendation": self._adapter_recommendation(target, coverage),
        }

    def _compatible_tools(self, target: str, caps: dict[str, Any]) -> list[dict[str, Any]]:
        names = {
            "memory_atom": {"insert_atom"},
            "receipt": {"insert_receipt", "log_speedlight_receipt"},
            "memory_edge": {"assign_mdhg_address", "log_e8_operation"},
        }.get(target, set())
        tools = [
            tool for tool in caps.get("write_tools", [])
            if tool.get("name") in names
        ]
        return tools[:10]

    def _compatible_routes(self, target: str, caps: dict[str, Any]) -> list[dict[str, Any]]:
        tokens = {
            "memory_atom": ["store", "bridge", "ingest", "workflow/memory"],
            "receipt": ["receipt", "mint"],
            "memory_edge": ["dag_edge", "bond", "edge"],
        }.get(target, [])
        routes = []
        for route in caps.get("write_routes", []):
            haystack = json.dumps(route).lower()
            if any(token in haystack for token in tokens):
                routes.append(route)
        return routes[:12]

    def _adapter_recommendation(self, target: str, coverage: str) -> dict[str, Any]:
        if target == "memory_edge":
            return {
                "mode": "staging_required",
                "reason": "edge semantics need a neutral graph staging shape before mapping to DAG, bond, or MDHG write surfaces",
            }
        if coverage == "strong":
            return {
                "mode": "adapter_then_runtime",
                "reason": "write-capable surfaces exist, but family selection, runtime health, and approval gates are still required",
            }
        return {
            "mode": "adapter_required",
            "reason": "no direct safe write surface fully matches this target record",
        }

    def _mmdb_import_blockers(self, target_plans: list[dict[str, Any]], health: dict[str, Any]) -> list[dict[str, Any]]:
        blockers = []
        healthy = [item for item in health.get("results", []) if item.get("ok")]
        if not healthy:
            blockers.append({
                "severity": "high",
                "area": "runtime_health",
                "issue": "no memory runtime target is currently healthy",
                "resolution": "use static compatibility only until selected memory services are approved and healthy",
            })
        for plan in target_plans:
            if plan["coverage"] == "missing":
                blockers.append({
                    "severity": "medium",
                    "area": "surface_coverage",
                    "issue": f"no compatible write surface for {plan['target_record']}",
                    "resolution": "add repo-kernel staging adapter before live import",
                })
            if plan["target_record"] == "memory_edge":
                blockers.append({
                    "severity": "medium",
                    "area": "edge_semantics",
                    "issue": "memory_edge maps to graph recall relationships, not simple atom/receipt rows",
                    "resolution": "preserve edges in staging until DAG/bond/MDHG semantics are selected",
                })
        blockers.append({
            "severity": "high",
            "area": "write_approval",
            "issue": "Postgres and runtime writes remain explicitly approval-gated",
            "resolution": "produce backup/export receipt and request approval before any write-capable importer",
        })
        return blockers

    def _mmdb_recommended_strategy(self, target_plans: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> dict[str, Any]:
        high_blockers = [item for item in blockers if item.get("severity") == "high"]
        return {
            "selected": "repo_kernel_staging_adapter_first",
            "why": [
                "dry-run records have stable row hashes and provenance",
                "live write surfaces are present but not health-verified",
                "edge records need a neutral staging shape",
                "Postgres writes require explicit approval",
            ],
            "can_do_now": [
                "persist import recipe artifacts",
                "generate staging schema",
                "compare target fields to static write surfaces",
                "run additional read-only dry-runs on other MMDB candidates",
            ],
            "cannot_do_without_approval": [
                "start memory services",
                "call insert/store/mint/write endpoints",
                "write Postgres",
            ],
            "blocked": bool(high_blockers),
        }

    def _mmdb_staging_contract(self) -> dict[str, Any]:
        return {
            "tables": {
                "memory_import_atoms": [
                    "row_hash PRIMARY KEY",
                    "atom_id",
                    "record_type",
                    "content_json",
                    "content_hash",
                    "geometry_json",
                    "source_json",
                    "status",
                ],
                "memory_import_edges": [
                    "row_hash PRIMARY KEY",
                    "edge_id",
                    "from_atom_id",
                    "to_atom_id",
                    "relation",
                    "cost",
                    "source_json",
                    "status",
                ],
                "memory_import_receipts": [
                    "row_hash PRIMARY KEY",
                    "receipt_id",
                    "run_id",
                    "step_id",
                    "controller",
                    "status",
                    "timestamp",
                    "receipt_json",
                    "source_json",
                ],
            },
            "policy": "staging contract only; implement as read-only recipe until write approval is granted",
        }


class MCPToolsWorkflowController:
    READ_PREFIXES = ("get_", "list_", "query_", "verify_", "sys_", "universal_stats")
    MUTATING_WORDS = (
        "insert",
        "store",
        "register",
        "merge",
        "remember",
        "generate",
        "log_",
        "assign",
        "mint",
        "create",
        "execute",
        "optimize",
        "transform",
        "translate",
    )

    def __init__(self, unified: UnifiedAIWorkflowRegistry, topology: RuntimeTopology):
        self.unified = unified
        self.topology = topology

    def capabilities(self) -> dict[str, Any]:
        workflow = self.unified.workflow("mcp_tools")
        tools = []
        routes = []
        runtime_targets = []
        for entry in workflow.get("entries", []):
            runtime_targets.extend({**target, "module": entry["module"]} for target in entry.get("runtime_targets", []))
            for tool in entry.get("mcp_tools", []):
                tools.append(self._normalize_tool(tool, entry["module"]))
            for route in entry.get("routes", []):
                routes.append({**route, "module": entry["module"]})

        grouped: dict[str, int] = {}
        for tool in tools:
            grouped[tool["category"]] = grouped.get(tool["category"], 0) + 1

        return {
            "workflow": "mcp_tools",
            "base_path": "/api/unified/mcp-tools",
            "tool_count": len(tools),
            "route_count": len(routes),
            "runtime_target_count": len(runtime_targets),
            "categories": grouped,
            "tools": tools,
            "routes": routes,
            "runtime_targets": runtime_targets,
            "policy": {
                "execution": "plan first; live execution requires healthy runtime and explicit non-dry-run request",
                "write_safety": "mutating tools are identified and not executed automatically",
                "fallback": "static adapter tool contract",
            },
        }

    def list_tools(self, query: str | None = None, category: str | None = None, limit: int = 200) -> dict[str, Any]:
        tools = self.capabilities()["tools"]
        if query:
            q = query.lower()
            tools = [tool for tool in tools if q in json.dumps(tool, ensure_ascii=False).lower()]
        if category:
            tools = [tool for tool in tools if tool.get("category") == category]
        return {"workflow": "mcp_tools", "count": len(tools), "tools": tools[:limit]}

    def tool_detail(self, tool_name: str) -> dict[str, Any]:
        matches = [tool for tool in self.capabilities()["tools"] if tool.get("name") == tool_name]
        if not matches:
            fuzzy = [tool for tool in self.capabilities()["tools"] if tool_name.lower() in tool.get("name", "").lower()]
            if fuzzy:
                return {"tool_name": tool_name, "exact": False, "matches": fuzzy[:20]}
            raise HTTPException(404, f"unknown MCP tool: {tool_name}")
        return {"tool_name": tool_name, "exact": True, "matches": matches}

    def call_plan(self, req: MCPToolCallPlanRequest) -> dict[str, Any]:
        caps = self.capabilities()
        candidates = [tool for tool in caps["tools"] if tool.get("name") == req.tool_name]
        if req.prefer_module:
            preferred = [tool for tool in candidates if tool.get("module") == req.prefer_module]
            if preferred:
                candidates = preferred
        if not candidates:
            fuzzy = [tool for tool in caps["tools"] if req.tool_name.lower() in tool.get("name", "").lower()]
            return {
                "workflow": "mcp_tools",
                "operation": "call_plan",
                "request": req.model_dump(),
                "error": "no exact tool match",
                "suggestions": fuzzy[:20],
            }

        modules = sorted({tool["module"] for tool in candidates})
        runtime_targets = [
            target for target in caps["runtime_targets"]
            if target.get("module") in modules
        ]
        if not runtime_targets:
            for module in modules:
                runtime_targets.extend({**target, "module": module} for target in self.topology.topology(module).get("runtime_urls", []))
        health = self.topology.health_check_targets(runtime_targets, timeout_seconds=0.5, limit=20)
        mutating = any(tool.get("safety") == "mutating" for tool in candidates)
        execution = "not executed; dry_run requested"
        if not req.dry_run:
            execution = "not executed; live MCP execution is intentionally disabled until a healthy runtime transport is selected"
        return {
            "workflow": "mcp_tools",
            "operation": "call_plan",
            "request": req.model_dump(),
            "selected_strategy": "healthy_runtime_transport_else_static_tool_contract",
            "candidates": candidates,
            "runtime_candidates": runtime_targets[:20],
            "health": health,
            "mutating": mutating,
            "execution": execution,
        }

    def _normalize_tool(self, tool: dict[str, Any], module: str) -> dict[str, Any]:
        name = tool.get("name", "")
        normalized = {**tool, "module": module}
        normalized["category"] = self._category(name)
        normalized["safety"] = self._safety(name)
        normalized["input_schema"] = normalized.get("input_schema")
        return normalized

    def _category(self, name: str) -> str:
        if name.startswith("l1_"):
            return "morphonic_foundation"
        if name.startswith("l2_"):
            return "geometric_engine"
        if name.startswith("l3_"):
            return "operational_systems"
        if name.startswith("l4_"):
            return "governance"
        if name.startswith("l5_"):
            return "interface"
        if name.startswith("sys_"):
            return "system"
        if name.startswith(("list_", "get_", "query_", "insert_", "log_", "assign_")):
            return "mmdb_memory"
        if name.startswith(("crystal_", "temporal_", "hypothesis_", "identity_", "audit_", "verify_", "universal_")):
            return "universal_crystal"
        return "other"

    def _safety(self, name: str) -> str:
        if name.startswith(self.READ_PREFIXES) or name in {"crystal_retrieve", "crystal_resonance_query", "temporal_query", "identity_history", "audit_provenance", "verify_receipt"}:
            return "read"
        if any(word in name for word in self.MUTATING_WORDS):
            return "mutating"
        if name.startswith(("l1_", "l2_", "l3_", "l4_", "l5_")):
            return "compute"
        return "unknown"


class PrototypeEvidenceBridge:
    ROOT_DOCS = [
        "CLAIMS_VS_CODE.md",
        "STACKS.md",
        "INVENTORY.md",
        "SUMMARY.md",
        "FINAL_STATE.md",
        "PLAN.md",
        "CONFLICTS.md",
    ]
    KEY_CSVS = [
        "_scripts/inventory.csv",
        "_scripts/bridge_files.csv",
        "_scripts/phase4_stack_catalog.csv",
        "_scripts/phase5_claims_detail.csv",
    ]
    SUPERSEDED_WRAPPERS = {"controller.py", "api.py", "mcp_server.py"}

    def __init__(self, roots: list[Path] | None = None):
        self.roots = roots or [
            PROTOTYPE_EVIDENCE_ROOT,
            Path("/sources/PartsFactory/Unification Prototypes"),
            Path("D:/PartsFactory/Unification Prototypes"),
        ]
        self._overview_cache: dict[str, Any] | None = None
        self._overview_cache_at = 0.0
        self._overview_cache_ttl = 300.0

    def overview(self) -> dict[str, Any]:
        if self._overview_cache and time.time() - self._overview_cache_at < self._overview_cache_ttl:
            return self._overview_cache
        root = self._root()
        if root is None:
            return {
                "source": "claude-unification-prototypes",
                "status": "missing",
                "checked_roots": [str(path) for path in self.roots],
                "integration_policy": self._integration_policy(),
            }
        root_docs = self._root_docs(root)
        csvs = [self._csv_summary(root / relative) for relative in self.KEY_CSVS]
        bridges = self.bridges(limit=15)
        docs = self.docs(limit=15)
        wrappers = self._wrapper_summary(root)
        overview = {
            "source": "claude-unification-prototypes",
            "status": "ready",
            "root": str(root),
            "root_docs": root_docs,
            "csvs": csvs,
            "bridges": {
                "pair_count": bridges["pair_count"],
                "file_count": bridges["file_count"],
                "top_pairs": bridges["pairs"],
            },
            "docs_harvest": {
                "tool_count": docs["tool_count"],
                "doc_count": docs["doc_count"],
                "top_tools": docs["tools"],
            },
            "superseded_wrappers": wrappers,
            "integration_policy": self._integration_policy(),
            "api_layer_needs": self.api_layer_needs(),
        }
        self._overview_cache = overview
        self._overview_cache_at = time.time()
        return overview

    def fast_summary(self) -> dict[str, Any]:
        if self._overview_cache and time.time() - self._overview_cache_at < self._overview_cache_ttl:
            return {
                "source": self._overview_cache.get("source"),
                "status": self._overview_cache.get("status"),
                "root": self._overview_cache.get("root"),
                "bridge_file_count": (self._overview_cache.get("bridges") or {}).get("file_count"),
                "docs_harvest_count": (self._overview_cache.get("docs_harvest") or {}).get("doc_count"),
                "superseded_wrapper_count": (self._overview_cache.get("superseded_wrappers") or {}).get("count"),
            }
        root = self._root()
        if root is None:
            return {
                "source": "claude-unification-prototypes",
                "status": "missing",
                "checked_roots": [str(path) for path in self.roots],
            }
        return {
            "source": "claude-unification-prototypes",
            "status": "mounted",
            "root": str(root),
            "bridge_file_count": None,
            "docs_harvest_count": None,
            "superseded_wrapper_count": None,
            "detail": "use /api/prototype-evidence for full counted evidence",
        }

    def docs(self, limit: int = 50) -> dict[str, Any]:
        root = self._require_root()
        tools_root = root / "tools"
        tools = []
        doc_count = 0
        if tools_root.exists():
            for tool_dir in sorted([path for path in tools_root.iterdir() if path.is_dir()], key=lambda path: path.name.lower()):
                docs = []
                docs_dir = tool_dir / "docs"
                if docs_dir.exists():
                    docs = sorted([path for path in docs_dir.glob("*.md") if path.is_file()], key=lambda path: path.name.lower())
                if docs:
                    doc_count += len(docs)
                    tools.append({
                        "tool": tool_dir.name,
                        "doc_count": len(docs),
                        "sample_docs": [self._rel(path, root) for path in docs[:5]],
                    })
        tools.sort(key=lambda item: (-item["doc_count"], item["tool"].lower()))
        return {
            "source": "claude-unification-prototypes",
            "root": str(root),
            "tool_count": len(tools),
            "doc_count": doc_count,
            "tools": tools[:limit],
            "use": "feed documented capability claims into the knowledge controller as evidence, not as executable runtime",
        }

    def bridges(self, limit: int = 50) -> dict[str, Any]:
        root = self._require_root()
        bridges_root = root / "bridges"
        pairs = []
        file_count = 0
        if bridges_root.exists():
            for pair_dir in sorted([path for path in bridges_root.iterdir() if path.is_dir()], key=lambda path: path.name.lower()):
                files = sorted([path for path in pair_dir.rglob("*") if self._is_evidence_file(path)], key=lambda path: path.name.lower())
                if files:
                    file_count += len(files)
                    pairs.append({
                        "pair": pair_dir.name,
                        "file_count": len(files),
                        "sample_files": [self._rel(path, root) for path in files[:5]],
                    })
        pairs.sort(key=lambda item: (-item["file_count"], item["pair"].lower()))
        return {
            "source": "claude-unification-prototypes",
            "root": str(root),
            "pair_count": len(pairs),
            "file_count": file_count,
            "pairs": pairs[:limit],
            "use": "rank cross-system routing and unification work by historical bridge density",
        }

    def read(self, req: PrototypeEvidenceReadRequest) -> dict[str, Any]:
        root = self._require_root()
        target = self._safe_path(root, req.path)
        if not target.exists() or not target.is_file():
            raise HTTPException(404, f"prototype evidence file not found: {req.path}")
        raw = target.read_bytes()[: req.max_bytes]
        text = raw.decode("utf-8", errors="replace")
        return {
            "source": "claude-unification-prototypes",
            "root": str(root),
            "path": self._rel(target, root),
            "bytes_returned": len(raw),
            "truncated": target.stat().st_size > len(raw),
            "content": text,
        }

    def search(self, q: str, limit: int = 20) -> dict[str, Any]:
        if not q:
            raise HTTPException(400, "q is required")
        root = self._require_root()
        needle = q.lower()
        matches: list[dict[str, Any]] = []
        self._search_claims_csv(root, needle, limit, matches)
        self._search_docs(root, needle, limit, matches)
        self._search_root_docs(root, needle, limit, matches)
        return {
            "source": "claude-unification-prototypes",
            "query": q,
            "data": {
                "matches": matches[:limit],
                "match_count": len(matches[:limit]),
                "root": str(root),
            },
            "policy": "read-only claim evidence for knowledge routing; not executable runtime",
        }

    def api_layer_needs(self) -> list[dict[str, Any]]:
        return [
            {
                "area": "knowledge_claims_lane",
                "need": "ingest tools/<system>/docs/*.md and CLAIMS_VS_CODE.md as documented capability claims for /api/global/knowledge",
                "current_bridge": "GET /api/prototype-evidence/docs and GET /api/prototype-evidence/read?path=CLAIMS_VS_CODE.md",
            },
            {
                "area": "bridge_density_prioritization",
                "need": "use bridges/<pair>/ counts and _scripts/bridge_files.csv to choose the next cross-system route slices",
                "current_bridge": "GET /api/prototype-evidence/bridges",
            },
            {
                "area": "historical_stack_catalog",
                "need": "merge STACKS.md and phase4_stack_catalog.csv into runtime topology as historical compose evidence",
                "current_bridge": "GET /api/prototype-evidence/read?path=STACKS.md",
            },
            {
                "area": "wrapper_disposition",
                "need": "treat generated controller.py/api.py/mcp_server.py files as superseded by ModuleAdapter unless a human promotes a specific wrapper",
                "current_bridge": "superseded_wrappers inventory",
            },
        ]

    def _root(self) -> Path | None:
        for path in self.roots:
            if path.exists() and path.is_dir():
                return path
        return None

    def _require_root(self) -> Path:
        root = self._root()
        if root is None:
            raise HTTPException(404, "prototype evidence root is not mounted")
        return root

    def _root_docs(self, root: Path) -> list[dict[str, Any]]:
        docs = []
        for name in self.ROOT_DOCS:
            path = root / name
            docs.append({
                "path": name,
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
            })
        return docs

    def _csv_summary(self, path: Path) -> dict[str, Any]:
        root = self._require_root()
        if not path.exists():
            return {"path": self._rel(path, root), "exists": False, "rows": 0, "columns": []}
        rows = 0
        columns: list[str] = []
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            try:
                columns = next(reader)
            except StopIteration:
                columns = []
            for _ in reader:
                rows += 1
        return {
            "path": self._rel(path, root),
            "exists": True,
            "bytes": path.stat().st_size,
            "rows": rows,
            "columns": columns[:20],
        }

    def _wrapper_summary(self, root: Path) -> dict[str, Any]:
        tools_root = root / "tools"
        wrappers = []
        if tools_root.exists():
            for tool_dir in sorted([path for path in tools_root.iterdir() if path.is_dir()], key=lambda path: path.name.lower()):
                found = [name for name in sorted(self.SUPERSEDED_WRAPPERS) if (tool_dir / name).exists()]
                if found:
                    wrappers.append({"tool": tool_dir.name, "files": [f"tools/{tool_dir.name}/{name}" for name in found]})
        return {
            "count": sum(len(item["files"]) for item in wrappers),
            "tools": wrappers,
            "status": "superseded-by-module-adapter",
        }

    def _search_claims_csv(self, root: Path, needle: str, limit: int, matches: list[dict[str, Any]]) -> None:
        claims_csv = root / "_scripts" / "phase5_claims_detail.csv"
        if not claims_csv.exists():
            return
        with claims_csv.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                haystack = " ".join(str(row.get(field) or "") for field in ("tool", "doc", "token", "status", "backed_in")).lower()
                if needle not in haystack:
                    continue
                status = row.get("status") or ""
                matches.append({
                    "kind": "prototype_claim_token",
                    "tool": row.get("tool"),
                    "title": row.get("token") or row.get("doc") or row.get("tool"),
                    "summary": f"{row.get('token')} in {row.get('doc')} is {status}; backed_in={row.get('backed_in') or 'none'}",
                    "matched_field": "claims_detail",
                    "relative_path": row.get("doc"),
                    "confidence": self._claim_confidence(status),
                    "raw": row,
                })
                if len(matches) >= limit:
                    return

    def _search_docs(self, root: Path, needle: str, limit: int, matches: list[dict[str, Any]]) -> None:
        tools_root = root / "tools"
        if not tools_root.exists() or len(matches) >= limit:
            return
        for docs_dir in sorted(tools_root.glob("*/docs"), key=lambda path: path.as_posix().lower()):
            tool = docs_dir.parent.name
            for path in sorted(docs_dir.glob("*.md"), key=lambda item: item.name.lower()):
                if len(matches) >= limit:
                    return
                rel = self._rel(path, root)
                text = path.read_text(encoding="utf-8", errors="replace")[:120_000]
                name_hit = needle in path.name.lower()
                body_hit = needle in text.lower()
                if not name_hit and not body_hit:
                    continue
                matches.append({
                    "kind": "prototype_doc_claim",
                    "tool": tool,
                    "title": path.name,
                    "summary": self._snippet(text, needle) if body_hit else f"doc filename matched: {path.name}",
                    "matched_field": "doc_body" if body_hit else "doc_name",
                    "relative_path": rel,
                    "confidence": 0.55,
                    "raw": {"tool": tool, "path": rel},
                })

    def _search_root_docs(self, root: Path, needle: str, limit: int, matches: list[dict[str, Any]]) -> None:
        if len(matches) >= limit:
            return
        for name in self.ROOT_DOCS:
            if len(matches) >= limit:
                return
            path = root / name
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")[:120_000]
            name_hit = needle in name.lower()
            body_hit = needle in text.lower()
            if not name_hit and not body_hit:
                continue
            matches.append({
                "kind": "prototype_root_doc",
                "tool": None,
                "title": name,
                "summary": self._snippet(text, needle) if body_hit else f"root doc filename matched: {name}",
                "matched_field": "doc_body" if body_hit else "doc_name",
                "relative_path": name,
                "confidence": 0.5,
                "raw": {"path": name},
            })

    def _claim_confidence(self, status: str) -> float:
        lowered = status.lower()
        if lowered == "backed_own":
            return 1.0
        if lowered == "backed_other":
            return 0.7
        if lowered == "unbacked":
            return 0.2
        return 0.4

    def _snippet(self, text: str, needle: str, radius: int = 180) -> str:
        lowered = text.lower()
        index = lowered.find(needle)
        if index < 0:
            return text[: radius * 2].replace("\n", " ").strip()
        start = max(0, index - radius)
        end = min(len(text), index + len(needle) + radius)
        return text[start:end].replace("\n", " ").strip()

    def _is_evidence_file(self, path: Path) -> bool:
        return path.is_file() and path.suffix != ".pyc" and "__pycache__" not in path.parts

    def _safe_path(self, root: Path, relative_path: str) -> Path:
        target = (root / relative_path).resolve()
        resolved_root = root.resolve()
        try:
            target.relative_to(resolved_root)
        except ValueError as exc:
            raise HTTPException(403, "prototype evidence path escapes the evidence root") from exc
        return target

    def _rel(self, path: Path, root: Path) -> str:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return path.as_posix()

    def _integration_policy(self) -> dict[str, str]:
        return {
            "runtime_authority": "repo-kernel ModuleAdapter and global controllers stay authoritative for live calls",
            "prototype_role": "Claude prototype outputs are evidence for claims, bridges, stacks, and priority",
            "mutation": "read-only evidence ingestion only; no generated wrapper execution",
        }


class GitNexusBridge:
    READ_PATHS = ["/api/info", "/api/repos", "/api/repo", "/api/grep", "/api/processes", "/api/process", "/api/clusters", "/api/cluster"]
    WRITE_VERBS = re.compile(
        r"\b(CREATE|MERGE|SET|DELETE|DETACH|DROP|REMOVE|LOAD\s+CSV|CALL\s+DB|CALL\s+APOC|INDEX|CONSTRAINT)\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        api_base: str = GITNEXUS_API_BASE,
        aggregate_db: Path = GITNEXUS_AGGREGATE_DB,
        meta_path: Path = GITNEXUS_META_PATH,
    ):
        self.api_base = api_base.rstrip("/")
        self.aggregate_db = aggregate_db
        self.meta_path = meta_path

    def status(self, include_repos: bool = True, repo_limit: int = 20) -> dict[str, Any]:
        info = self._safe_http(lambda: self._get_json("/api/info"))
        repos = self._safe_http(lambda: self.repos(limit=repo_limit)) if include_repos else {"ok": False, "skipped": True}
        aggregate = self.aggregate_summary()
        local_meta = self.local_meta()
        return {
            "tool": "gitnexus",
            "status": self._status_label(info, repos, aggregate),
            "api_base": self.api_base,
            "info": info,
            "repos": repos,
            "local_meta": local_meta,
            "aggregate_reports": aggregate,
            "safe_api": {
                "read_paths": self.READ_PATHS,
                "repo_kernel_routes": [
                    "GET /api/gitnexus/status",
                    "GET /api/gitnexus/repos",
                    "GET /api/gitnexus/repos/{repo}",
                    "GET /api/gitnexus/graph-summary",
                    "GET /api/gitnexus/unification-hints",
                    "GET /api/gitnexus/grep",
                    "GET /api/gitnexus/aggregate",
                    "GET /api/gitnexus/aggregate/search",
                ],
                "blocked": ["analyze", "index", "clean", "remove", "augment", "embed", "delete", "write cypher"],
            },
            "use_in_repo_kernel_work": [
                "Use repo inventory before broad recursive filesystem scans.",
                "Use graph summaries to identify high-surface repos and likely controller seams before refactors.",
                "Use aggregate report search to compare historical claims against current routed capabilities.",
            ],
            "policy": {
                "read": "GitNexus is exposed as bounded read-only graph and report evidence.",
                "write": "index/analyze/remove/augment/embed and write Cypher are not routed through repo-kernel.",
                "authority": "GitNexus evidence informs routing and promotion; repo-kernel APIs remain the execution authority.",
            },
        }

    def local_meta(self) -> dict[str, Any]:
        path = self._first_existing([self.meta_path, Path("D:/PartsFactory/CMPLX-PartsFactory/.gitnexus/meta.json")])
        if path is None:
            return {"status": "missing", "checked_paths": [str(self.meta_path), "D:/PartsFactory/CMPLX-PartsFactory/.gitnexus/meta.json"]}
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            return {"status": "invalid_json", "path": str(path), "error": str(exc)}
        return {"status": "ready", "path": str(path), "data": data}

    def repos(self, limit: int = 100) -> dict[str, Any]:
        data = self._get_json("/api/repos")
        repos = data if isinstance(data, list) else data.get("repos", [])
        sorted_repos = sorted(
            [repo for repo in repos if isinstance(repo, dict)],
            key=lambda item: self._repo_nodes(item),
            reverse=True,
        )
        return {
            "source": "gitnexus-api",
            "repo_count": len(sorted_repos),
            "repos": sorted_repos[:limit],
            "truncated": len(sorted_repos) > limit,
        }

    def repo(self, repo: str) -> dict[str, Any]:
        if not repo:
            raise HTTPException(400, "repo is required")
        return {
            "source": "gitnexus-api",
            "repo": repo,
            "data": self._get_json("/api/repo", {"repo": repo}),
            "policy": "read-only repository metadata from GitNexus",
        }

    def graph_summary(self, repo: str, limit: int = 20) -> dict[str, Any]:
        if not repo:
            raise HTTPException(400, "repo is required")
        limit = max(1, min(limit, 100))
        labels = self._read_cypher(repo, f"MATCH (n) RETURN labels(n) AS labels, count(n) AS count LIMIT {limit}")
        process_count = self._read_cypher(repo, "MATCH (p:Process) RETURN count(p) AS count LIMIT 1")
        community_count = self._read_cypher(repo, "MATCH (c:Community) RETURN count(c) AS count LIMIT 1")
        processes = self._get_json("/api/processes", {"repo": repo}).get("processes", [])
        communities = self._get_json("/api/clusters", {"repo": repo}).get("clusters", [])
        return {
            "source": "gitnexus-api",
            "repo": repo,
            "labels": labels.get("result", labels),
            "process_count": self._first_count(process_count),
            "community_count": self._first_count(community_count),
            "processes": processes[:limit],
            "communities": communities[:limit],
            "policy": "canned read-only graph summary; raw graph export is intentionally not exposed here",
        }

    def grep(self, repo: str, pattern: str, limit: int = 20) -> dict[str, Any]:
        if not repo:
            raise HTTPException(400, "repo is required")
        if not pattern:
            raise HTTPException(400, "pattern is required")
        return {
            "source": "gitnexus-api",
            "repo": repo,
            "pattern": pattern,
            "data": self._get_json("/api/grep", {"repo": repo, "pattern": pattern, "limit": max(1, min(limit, 100))}),
            "policy": "read-only grep through GitNexus index",
        }

    def unification_hints(self, limit: int = 12) -> dict[str, Any]:
        bounded = max(1, min(limit, 50))
        repos = []
        repo_error = None
        try:
            repos = self.repos(limit=200).get("repos", [])
        except HTTPException as exc:
            repo_error = {"status_code": exc.status_code, "error": exc.detail}
        aggregate = self.aggregate_summary()
        repo_hints = [hint for repo in repos if (hint := self._repo_hint(repo)) is not None]
        repo_hints.sort(key=lambda item: item["priority_score"], reverse=True)
        shared_names = aggregate.get("shared_names", []) if aggregate.get("status") == "ready" else []
        return {
            "source": "gitnexus",
            "status": "ready" if repos and aggregate.get("status") == "ready" else "partial",
            "repo_error": repo_error,
            "top_repo_hints": repo_hints[:bounded],
            "shared_historical_names": shared_names[:bounded],
            "recommended_work": [
                {
                    "lane": "large_surface_adapter_review",
                    "reason": "largest indexed repo graphs are most likely to contain unpromoted routes, tools, or duplicated implementations",
                    "targets": [item["repo"] for item in repo_hints[:5]],
                },
                {
                    "lane": "shared_name_canon",
                    "reason": "names appearing in multiple historical systems should become canonical capability ids before code is moved",
                    "targets": [item.get("name") for item in shared_names[:5]],
                },
                {
                    "lane": "controller_refactor_evidence",
                    "reason": "cmplx-partsfactory-root graph communities identify the first controller modules to extract later without starting that refactor now",
                    "targets": ["/api/gitnexus/graph-summary?repo=cmplx-partsfactory-root&limit=10"],
                },
            ],
            "policy": "read-only prioritization evidence; promotion and refactor work still require the repo-kernel ledger and tests",
        }

    def aggregate_summary(self) -> dict[str, Any]:
        path = self._aggregate_db_path()
        if path is None:
            return {
                "status": "missing",
                "checked_paths": [str(self.aggregate_db), "D:/PartsFactory/CMPLX-PartsFactory/data/gitnexus_index.sqlite"],
            }
        with self._open_aggregate(path) as conn:
            total = conn.execute("select count(*) from gitnexus_reports").fetchone()[0]
            by_system = self._group_counts(conn, "system")
            by_language = self._group_counts(conn, "language")
            by_status = self._group_counts(conn, "implement_status")
            shared_names = [
                dict(row)
                for row in conn.execute(
                    """
                    select name, count(distinct system) as system_count, group_concat(distinct system) as systems, count(*) as report_count
                    from gitnexus_reports
                    group by name
                    having count(distinct system) > 1
                    order by system_count desc, report_count desc, name asc
                    limit 25
                    """
                )
            ]
        return {
            "status": "ready",
            "path": str(path),
            "total_reports": total,
            "by_system": by_system,
            "by_language": by_language,
            "by_status": by_status,
            "shared_names": shared_names,
            "use": "historical report evidence for capability gap checks and cross-system unification priority",
        }

    def aggregate_search(
        self,
        q: str | None = None,
        system: str | None = None,
        language: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        path = self._aggregate_db_path()
        if path is None:
            raise HTTPException(404, "GitNexus aggregate DB is not available")
        clauses = []
        params: list[Any] = []
        if q:
            clauses.append("(lower(name) like ? or lower(source_path) like ? or lower(capability_summary) like ?)")
            needle = f"%{q.lower()}%"
            params.extend([needle, needle, needle])
        if system:
            clauses.append("lower(system) = ?")
            params.append(system.lower())
        if language:
            clauses.append("lower(language) = ?")
            params.append(language.lower())
        where = f"where {' and '.join(clauses)}" if clauses else ""
        bounded = max(1, min(limit, 500))
        with self._open_aggregate(path) as conn:
            rows = [
                dict(row)
                for row in conn.execute(
                    f"""
                    select report_id, name, source_path, source_id, system, language, implement_status, confidence, capability_summary
                    from gitnexus_reports
                    {where}
                    order by system asc, name asc
                    limit ?
                    """,
                    [*params, bounded],
                )
            ]
        return {
            "source": "gitnexus-aggregate-db",
            "path": str(path),
            "query": q,
            "system": system,
            "language": language,
            "result_count": len(rows),
            "results": rows,
            "policy": "read-only historical report search; use as evidence before promotion",
        }

    def _read_cypher(self, repo: str, cypher: str) -> dict[str, Any]:
        self._validate_read_cypher(cypher)
        return self._post_json("/api/query", {"repo": repo, "cypher": cypher}, query={"repo": repo})

    def _validate_read_cypher(self, cypher: str) -> None:
        if self.WRITE_VERBS.search(cypher):
            raise HTTPException(403, "GitNexus Cypher bridge allows read-only MATCH/RETURN style queries only")

    def _get_json(self, path: str, query: dict[str, Any] | None = None, timeout: float = 5.0) -> Any:
        url = self._url(path, query=query)
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        return self._request_json(req, timeout=timeout)

    def _post_json(self, path: str, payload: dict[str, Any], query: dict[str, Any] | None = None, timeout: float = 8.0) -> Any:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url(path, query=query),
            data=body,
            method="POST",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        return self._request_json(req, timeout=timeout)

    def _request_json(self, req: urllib.request.Request, timeout: float) -> Any:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read(2_000_000)
                text = raw.decode("utf-8", errors="replace")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read(4000).decode("utf-8", errors="replace")
            raise HTTPException(exc.code, f"GitNexus HTTP error: {detail}") from exc
        except urllib.error.URLError as exc:
            raise HTTPException(502, f"GitNexus is not reachable at {self.api_base}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise HTTPException(502, f"GitNexus returned non-JSON response: {exc}") from exc

    def _url(self, path: str, query: dict[str, Any] | None = None) -> str:
        clean = path if path.startswith("/") else f"/{path}"
        encoded = urllib.parse.urlencode(query or {}, doseq=True)
        return f"{self.api_base}{clean}{'?' + encoded if encoded else ''}"

    def _safe_http(self, callback: Any) -> dict[str, Any]:
        try:
            data = callback()
        except HTTPException as exc:
            return {"ok": False, "status_code": exc.status_code, "error": exc.detail}
        return {"ok": True, "data": data}

    def _aggregate_db_path(self) -> Path | None:
        return self._first_existing([self.aggregate_db, Path("D:/PartsFactory/CMPLX-PartsFactory/data/gitnexus_index.sqlite")])

    def _open_aggregate(self, path: Path) -> sqlite3.Connection:
        uri = f"file:{path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _group_counts(self, conn: sqlite3.Connection, column: str) -> list[dict[str, Any]]:
        return [
            {"value": row["value"], "count": row["count"]}
            for row in conn.execute(
                f"""
                select coalesce(nullif({column}, ''), 'unknown') as value, count(*) as count
                from gitnexus_reports
                group by value
                order by count desc, value asc
                limit 50
                """
            )
        ]

    def _first_existing(self, paths: list[Path]) -> Path | None:
        for path in paths:
            if path.exists():
                return path
        return None

    def _repo_nodes(self, repo: dict[str, Any]) -> int:
        stats = repo.get("stats") or {}
        try:
            return int(stats.get("nodes") or 0)
        except (TypeError, ValueError):
            return 0

    def _repo_hint(self, repo: dict[str, Any]) -> dict[str, Any] | None:
        name = repo.get("name")
        if not name:
            return None
        stats = repo.get("stats") or {}
        nodes = self._int_stat(stats, "nodes")
        files = self._int_stat(stats, "files")
        processes = self._int_stat(stats, "processes")
        communities = self._int_stat(stats, "communities")
        if name.startswith("rk-"):
            role = "clean_repo_checkout"
            priority_score = nodes + (processes * 30) + (communities * 10)
        elif name.startswith("cmplx-partsfactory"):
            role = "active_controller"
            priority_score = nodes + (processes * 20) + (communities * 8)
        elif "output-reports" in name:
            role = "historical_report_index"
            priority_score = files * 5
        else:
            role = "historical_source_index"
            priority_score = nodes // 2
        return {
            "repo": name,
            "role": role,
            "path": repo.get("path"),
            "indexed_at": repo.get("indexedAt"),
            "stats": stats,
            "priority_score": priority_score,
            "next_read": f"/api/gitnexus/graph-summary?repo={urllib.parse.quote(str(name))}&limit=10"
            if role in {"clean_repo_checkout", "active_controller", "historical_source_index"}
            else f"/api/gitnexus/repos/{urllib.parse.quote(str(name))}",
        }

    def _int_stat(self, stats: dict[str, Any], key: str) -> int:
        try:
            return int(stats.get(key) or 0)
        except (TypeError, ValueError):
            return 0

    def _first_count(self, data: dict[str, Any]) -> int | None:
        result = data.get("result") if isinstance(data, dict) else None
        if not result:
            return None
        try:
            return int(result[0].get("count"))
        except (AttributeError, TypeError, ValueError, IndexError):
            return None

    def _status_label(self, info: dict[str, Any], repos: dict[str, Any], aggregate: dict[str, Any]) -> str:
        if info.get("ok") and repos.get("ok") and aggregate.get("status") == "ready":
            return "ready"
        if info.get("ok") or aggregate.get("status") == "ready":
            return "partial"
        return "unavailable"


class GlobalSystemController:
    STATIC_ADAPTER_SYSTEMS = {"mcp", "agent-orchestration", "code-execution"}
    LIVE_UPSTREAMS = {
        "memory": [
            {"name": "pocket-memory-api", "url": "http://localhost:8816", "health_url": "http://localhost:8816/health", "host_port": 8816, "source": "running Docker container"},
            {"name": "agenthub-db-bridge", "url": "http://localhost:8817", "health_url": "http://localhost:8817/health", "host_port": 8817, "source": "running Docker container"},
            {"name": "mmdb-unified", "url": "http://localhost:8824", "health_url": "http://localhost:8824/health", "host_port": 8824, "container_port": 8084, "source": "running Docker container"},
            {"name": "mdhg-unified", "url": "http://localhost:8825", "health_url": "http://localhost:8825/health", "host_port": 8825, "container_port": 8085, "source": "running Docker container"},
            {"name": "postgres", "url": "tcp://localhost:5432", "host_port": 5432, "runtime_kind": "postgres", "source": "running Docker container"},
            {"name": "postgres-cache", "url": "tcp://localhost:55432", "host_port": 55432, "container_port": 5432, "runtime_kind": "postgres", "source": "running Docker container"},
        ],
        "knowledge": [
            {"name": "research-api", "url": "http://localhost:3000", "health_url": "http://localhost:3000/health", "host_port": 3000, "source": "running Docker container"},
            {
                "name": "research-api-jupyter",
                "container_name": "research-api",
                "url": "http://localhost:8888",
                "host_port": 8888,
                "health_path": "/",
                "enabled": False,
                "disabled_reason": "observed container port refuses connections; keep as evidence until Jupyter is explicitly started or removed",
                "source": "running Docker container",
            },
            {"name": "db-aggregator-api", "url": "http://localhost:8815", "health_url": "http://localhost:8815/health", "host_port": 8815, "source": "running Docker container"},
        ],
        "ai-runtime": [
            {"name": "research-api", "url": "http://localhost:3000", "health_url": "http://localhost:3000/health", "host_port": 3000, "source": "running Docker container"},
            {"name": "manny-manifold-api", "url": "http://localhost:8840", "health_url": "http://localhost:8840/health", "host_port": 8840, "source": "running Docker container"},
        ],
        "geometry": [
            {"name": "snap-unified", "url": "http://localhost:8823", "health_url": "http://localhost:8823/health", "host_port": 8823, "container_port": 8083, "source": "running Docker container"},
            {"name": "mdhg-unified", "url": "http://localhost:8825", "health_url": "http://localhost:8825/health", "host_port": 8825, "container_port": 8085, "source": "running Docker container"},
            {"name": "tarpit-api", "url": "http://localhost:8844", "health_url": "http://localhost:8844/health", "host_port": 8844, "source": "running Docker container"},
            {"name": "unique-systems-api", "url": "http://localhost:8842", "health_url": "http://localhost:8842/health", "host_port": 8842, "source": "running Docker container"},
        ],
        "validation": [
            {"name": "speedlight-api", "url": "http://localhost:8843", "health_url": "http://localhost:8843/health", "host_port": 8843, "source": "running Docker container"},
            {"name": "db-aggregator-api", "url": "http://localhost:8815", "health_url": "http://localhost:8815/health", "host_port": 8815, "source": "running Docker container"},
        ],
        "synthesis": [
            {"name": "manny-manifold-api", "url": "http://localhost:8840", "health_url": "http://localhost:8840/health", "host_port": 8840, "source": "running Docker container"},
            {"name": "unique-systems-api", "url": "http://localhost:8842", "health_url": "http://localhost:8842/health", "host_port": 8842, "source": "running Docker container"},
        ],
        "operations": [
            {"name": "repo-kernel", "url": "http://localhost:8786", "health_url": "http://localhost:8786/api/health", "host_port": 8786, "source": "running Docker container"},
            {"name": "gitnexus-rebuild-server", "url": "http://localhost:4747", "host_port": 4747, "source": "running Docker container"},
            {"name": "gitnexus-rebuild-web", "url": "http://localhost:4173", "host_port": 4173, "source": "running Docker container"},
        ],
        "external-ai-portal": [
            {"name": "ngrok-cmplx", "url": "http://localhost:4040", "host_port": 4040, "source": "running Docker container"},
            {"name": "opencode-session", "url": "http://localhost:4096", "health_url": "http://localhost:4096/health", "host_port": 4096, "source": "running Docker container"},
        ],
    }

    SYSTEMS = {
        "mcp": {
            "workflow": "mcp_tools",
            "keywords": ["mcp", "tool", "adapter", "controller", "codec", "validation", "universal"],
            "canonical_base": "/api/global/mcp",
            "canonical_ports": [
                {"port": 8900, "transport": "http/sse or stdio bridge", "source": "CMPLXMCP and CMPLXUNI README evidence"},
                {"port": 8902, "transport": "http", "source": "CMPLXUNI library MCP chain evidence"},
                {"port": 11113, "transport": "http", "source": "CMPLX-TMN-main tmn2-kb-mcp compose service"},
            ],
        },
        "memory": {
            "workflow": "memory",
            "keywords": ["memory", "mmdb", "atom", "receipt", "ledger", "family", "mdhg"],
            "canonical_base": "/api/global/memory",
            "canonical_ports": [
                {"port": 11002, "transport": "postgres", "source": "CMPLX-TMN-main tmn2-pg compose service"},
                {"port": 11120, "transport": "http", "source": "CMPLX-TMN-main tmn2-mmdb compose service"},
                {"port": 11121, "transport": "http", "source": "CMPLX-TMN-main tmn2-mmdb-pg-bridge compose service"},
                {"port": 11122, "transport": "http", "source": "CMPLX-TMN-main tmn2-mmdb-discovery compose service"},
                {"port": 11123, "transport": "http", "source": "CMPLX-TMN-main tmn2-data-steward compose service"},
                {"port": 11195, "transport": "http", "source": "CMPLX-TMN-main tmn2-receipt compose service"},
            ],
        },
        "agent-orchestration": {
            "workflow": "agent_orchestration",
            "keywords": ["agent", "daemon", "coop", "spawn", "identity", "thinktank", "persona", "orchestration", "quorum"],
            "canonical_base": "/api/global/agent-orchestration",
            "canonical_ports": [
                {"port": 11030, "transport": "http", "source": "CMPLX-TMN-main tmn2-identity compose service"},
                {"port": 11031, "transport": "http", "source": "CMPLX-TMN-main tmn2-coop compose service"},
                {"port": 11032, "transport": "http", "source": "CMPLX-TMN-main tmn2-daemon compose service"},
                {"port": 11040, "transport": "http", "source": "CMPLX-TMN-main tmn2-thinktank compose service"},
                {"port": 11161, "transport": "http", "source": "CMPLX-TMN-main tmn2-agent-manager compose service"},
                {"port": 11197, "transport": "http", "source": "CMPLX-TMN-main tmn2-spawn compose service"},
                {"port": 11200, "transport": "http", "source": "CMPLX-TMN-main tmn2-agent compose service"},
                {"port": 11300, "transport": "http", "source": "CMPLX-TMN-main README CMPLXCode agent UI evidence"},
            ],
        },
        "knowledge": {
            "workflow": "knowledge",
            "keywords": ["knowledge", "kb", "library", "archive", "document", "paper", "corpus", "semantic", "embedding", "vector", "query", "search", "atlas", "blackboard"],
            "canonical_base": "/api/global/knowledge",
            "canonical_ports": [
                {"port": 11050, "transport": "http", "source": "CMPLX-TMN-main tmn2-library compose service"},
                {"port": 11051, "transport": "http", "source": "CMPLX-TMN-main tmn2-semantic compose service"},
                {"port": 11053, "transport": "http", "source": "CMPLX-TMN-main tmn2-atlas compose service"},
                {"port": 11100, "transport": "http", "source": "CMPLX-TMN-main tmn2-kb-papers compose service"},
                {"port": 11101, "transport": "http", "source": "CMPLX-TMN-main tmn2-kb-code compose service"},
                {"port": 11102, "transport": "http", "source": "CMPLX-TMN-main tmn2-kb-sql compose service"},
                {"port": 11103, "transport": "postgres", "source": "CMPLX-TMN-main tmn2-kb-pg compose service"},
                {"port": 11110, "transport": "http", "source": "CMPLX-TMN-main tmn2-kb-discovery compose service"},
                {"port": 11111, "transport": "http", "source": "CMPLX-TMN-main tmn2-kb-processor compose service"},
                {"port": 11112, "transport": "http", "source": "CMPLX-TMN-main tmn2-kb-query compose service"},
                {"port": 11131, "transport": "http", "source": "CMPLX-TMN-main tmn2-jacobian-blackboard compose service"},
                {"port": 11300, "transport": "http", "source": "CMPLX-TMN-main tmn2-cmplxcode compose service"},
            ],
        },
        "geometry": {
            "workflow": "geometry",
            "keywords": ["geometry", "e8", "lattice", "leech", "weyl", "niemeier", "morphon", "morsr", "glyph", "crystal", "mdhg"],
            "canonical_base": "/api/global/geometry",
            "canonical_ports": [
                {"port": 11153, "transport": "http", "source": "CMPLX-TMN-main tmn2-morphon compose service"},
                {"port": 11181, "transport": "http", "source": "CMPLX-TMN-main tmn2-glyph compose service"},
                {"port": 11182, "transport": "http", "source": "CMPLX-TMN-main tmn2-crystal compose service"},
                {"port": 11190, "transport": "http", "source": "CMPLX-TMN-main tmn2-morsr compose service"},
                {"port": 11212, "transport": "http", "source": "CMPLX-TMN-main tmn2-morphon-field compose service"},
            ],
        },
        "training": {
            "workflow": "training",
            "keywords": ["training", "train", "trainer", "teaching", "evaluate", "evaluation", "rl-trainer", "optimize"],
            "canonical_base": "/api/global/training",
            "canonical_ports": [
                {"port": 11091, "transport": "http", "source": "CMPLX-TMN-main tmn2-teaching compose service"},
                {"port": 11092, "transport": "http", "source": "CMPLX-TMN-main tmn2-trainer compose service"},
                {"port": 11093, "transport": "http", "source": "CMPLX-TMN-main tmn2-rl-trainer compose service"},
            ],
        },
        "code-execution": {
            "workflow": "code_execution",
            "keywords": ["code", "execute", "execution", "polyglot", "sandbox", "portal", "cmplxcode", "runner", "eval"],
            "canonical_base": "/api/global/code-execution",
            "canonical_ports": [
                {"port": 11070, "transport": "http", "source": "CMPLX-TMN-main tmn2-portal compose service"},
                {"port": 11071, "transport": "http", "source": "CMPLX-TMN-main tmn2-portal-companion compose service"},
                {"port": 11072, "transport": "http", "source": "CMPLX-TMN-main tmn2-sandbox-interface compose service"},
                {"port": 11082, "transport": "http", "source": "CMPLX-TMN-main tmn2-mdhg-sandbox compose service"},
                {"port": 11101, "transport": "http", "source": "CMPLX-TMN-main tmn2-kb-code compose service"},
                {"port": 11300, "transport": "http", "source": "CMPLX-TMN-main tmn2-cmplxcode compose service"},
            ],
        },
        "pipeline": {
            "workflow": "pipeline",
            "keywords": ["pipeline", "ingress", "egress", "intake", "staging", "harvester", "harvest", "reviewer"],
            "canonical_base": "/api/global/pipeline",
            "canonical_ports": [
                {"port": 11060, "transport": "http", "source": "CMPLX-TMN-main tmn2-intake compose service"},
                {"port": 11061, "transport": "http", "source": "CMPLX-TMN-main tmn2-harvester compose service"},
                {"port": 11062, "transport": "http", "source": "CMPLX-TMN-main tmn2-ingress-egress compose service"},
                {"port": 11063, "transport": "http", "source": "CMPLX-TMN-main tmn2-staging compose service"},
                {"port": 11113, "transport": "http", "source": "CMPLX-TMN-main tmn2-pipeline compose service"},
                {"port": 11142, "transport": "http", "source": "CMPLX-TMN-main tmn2-intake-reviewer compose service"},
            ],
        },
        "external-ai-portal": {
            "workflow": "external_ai_portal",
            "keywords": ["portal", "ngrok", "workspace", "gateway", "external", "companion"],
            "canonical_base": "/api/global/external-ai-portal",
            "canonical_ports": [
                {"port": 11000, "transport": "http", "source": "CMPLX-TMN-main tmn2-gateway compose service"},
                {"port": 11070, "transport": "http", "source": "CMPLX-TMN-main tmn2-portal compose service"},
                {"port": 11071, "transport": "http", "source": "CMPLX-TMN-main tmn2-portal-companion compose service"},
                {"port": 14041, "transport": "http", "source": "CMPLX-TMN-main tmn2-ngrok compose service"},
            ],
        },
        "formalization": {
            "workflow": "formalization",
            "keywords": ["formal", "proof", "theorem", "axiom", "planner", "octet", "unfold", "handshake", "channel_", "prefire", "legal_e8", "pal4"],
            "canonical_base": "/api/global/formalization",
            "canonical_ports": [],
        },
        "ai-runtime": {
            "workflow": "ai_runtime",
            "keywords": ["infer", "model", "models", "embed", "generate", "llm", "chat", "ai_hub"],
            "canonical_base": "/api/global/ai-runtime",
            "canonical_ports": [
                {"port": 3000, "transport": "http", "source": "CMPLXUNI Next/API chat and model surface evidence"},
            ],
        },
        "operations": {
            "workflow": "operations",
            "keywords": ["health", "status", "metrics", "dashboard", "domain_manager", "manager", "restart", "scale", "report", "ready", "cache", "port-controller", "dock"],
            "canonical_base": "/api/global/operations",
            "canonical_ports": [
                {"port": 11150, "transport": "http", "source": "CMPLX-TMN-main tmn2-dashboard compose service"},
                {"port": 11151, "transport": "http", "source": "CMPLX-TMN-main tmn2-port-controller compose service"},
                {"port": 11152, "transport": "http", "source": "CMPLX-TMN-main tmn2-dock compose service"},
                {"port": 11160, "transport": "http", "source": "CMPLX-TMN-main tmn2-engine-manager compose service"},
                {"port": 11161, "transport": "http", "source": "CMPLX-TMN-main tmn2-agent-manager compose service"},
                {"port": 11162, "transport": "http", "source": "CMPLX-TMN-main tmn2-data-manager compose service"},
                {"port": 11163, "transport": "http", "source": "CMPLX-TMN-main tmn2-economy-manager compose service"},
                {"port": 11172, "transport": "http", "source": "CMPLX-TMN-main tmn2-orchestration-manager compose service"},
            ],
        },
        "eventing": {
            "workflow": "eventing",
            "keywords": ["broadcast", "subscribe", "dispatch", "publish", "events", "channels", "subscribers", "replay"],
            "canonical_base": "/api/global/eventing",
            "canonical_ports": [
                {"port": 11191, "transport": "http", "source": "CMPLX-TMN-main tmn2-broadcast compose service"},
                {"port": 11192, "transport": "http", "source": "CMPLX-TMN-main tmn2-subscribe compose service"},
                {"port": 11193, "transport": "http", "source": "CMPLX-TMN-main tmn2-dispatch compose service"},
            ],
        },
        "community": {
            "workflow": "community",
            "keywords": ["board", "bounty", "bounties", "thread", "posts", "openclaw", "claw", "planet"],
            "canonical_base": "/api/global/community",
            "canonical_ports": [
                {"port": 11001, "transport": "http", "source": "CMPLX-TMN-main tmn2-board compose service"},
                {"port": 11073, "transport": "http", "source": "CMPLX-TMN-main tmn2-board-claw-bridge compose service"},
            ],
        },
        "economy": {
            "workflow": "economy",
            "keywords": ["economy", "mint", "marketplace", "commission", "lend", "stake", "buyback", "pools"],
            "canonical_base": "/api/global/economy",
            "canonical_ports": [
                {"port": 11043, "transport": "http", "source": "CMPLX-TMN-main tmn2-mint compose service"},
                {"port": 11090, "transport": "http", "source": "CMPLX-TMN-main tmn2-economy compose service"},
                {"port": 11163, "transport": "http", "source": "CMPLX-TMN-main tmn2-economy-manager compose service"},
            ],
        },
        "validation": {
            "workflow": "validation",
            "keywords": ["validation", "validate", "conservation", "gate", "audit", "quality", "surplus", "partition", "rules"],
            "canonical_base": "/api/global/validation",
            "canonical_ports": [
                {"port": 11123, "transport": "http", "source": "CMPLX-TMN-main tmn2-data-steward compose service"},
                {"port": 11194, "transport": "http", "source": "CMPLX-TMN-main tmn2-conservation compose service"},
                {"port": 11196, "transport": "http", "source": "CMPLX-TMN-main tmn2-gate compose service"},
            ],
        },
        "synthesis": {
            "workflow": "synthesis",
            "keywords": ["brain", "integrator", "integrate", "interrogation", "canon", "librarian", "free5e", "porter", "discover", "study", "questions", "saturation"],
            "canonical_base": "/api/global/synthesis",
            "canonical_ports": [
                {"port": 11052, "transport": "http", "source": "CMPLX-TMN-main tmn2-integrator compose service"},
                {"port": 11132, "transport": "http", "source": "CMPLX-TMN-main tmn2-canon-builder compose service"},
                {"port": 11140, "transport": "http", "source": "CMPLX-TMN-main tmn2-interrogation compose service"},
                {"port": 11141, "transport": "http", "source": "CMPLX-TMN-main tmn2-interrogation-orchestrator compose service"},
                {"port": 11143, "transport": "http", "source": "CMPLX-TMN-main tmn2-folder-librarian compose service"},
                {"port": 11170, "transport": "http", "source": "CMPLX-TMN-main tmn2-free5e-porter compose service"},
                {"port": 11202, "transport": "http", "source": "CMPLX-TMN-main tmn2-brain compose service"},
            ],
        },
        "simulation": {
            "workflow": "simulation",
            "keywords": ["simulation", "sim", "ca_sim", "create_ca", "step_ca", "entropy", "panels", "inject", "julia", "planet"],
            "canonical_base": "/api/global/simulation",
            "canonical_ports": [
                {"port": 11080, "transport": "http", "source": "CMPLX-TMN-main tmn2-sim compose service"},
                {"port": 11081, "transport": "http", "source": "CMPLX-TMN-main tmn2-ca-sim compose service"},
                {"port": 11083, "transport": "http", "source": "CMPLX-TMN-main tmn2-cpl compose service"},
            ],
        },
    }

    def __init__(
        self,
        registry: RepoRegistry,
        unified: UnifiedAIWorkflowRegistry,
        topology: RuntimeTopology,
        surface_catalog: ModuleSurfaceCatalog,
        mcp_tools: MCPToolsWorkflowController,
        memory: MemoryWorkflowController,
        agent_orchestration: Any | None = None,
        knowledge: Any | None = None,
        prototype_evidence: PrototypeEvidenceBridge | None = None,
        gitnexus: GitNexusBridge | None = None,
    ):
        self.registry = registry
        self.unified = unified
        self.topology = topology
        self.surface_catalog = surface_catalog
        self.mcp_tools = mcp_tools
        self.memory = memory
        self.agent_orchestration = agent_orchestration
        self.knowledge = knowledge
        self.prototype_evidence = prototype_evidence
        self.gitnexus = gitnexus

    def list_systems(self) -> dict[str, Any]:
        return {
            "systems": [
                {
                    "system": name,
                    "canonical_base": config["canonical_base"],
                    "workflow": config["workflow"],
                    "policy": "global routes normalize repo-local services without moving source",
                }
                for name, config in self.SYSTEMS.items()
            ]
        }

    def location_map(self, system: str | None = None, modules: list[str] | None = None) -> dict[str, Any]:
        systems = [system] if system else list(self.SYSTEMS)
        locations = [self._system_location(name, modules=modules) for name in systems]
        return {
            "count": len(locations),
            "systems": locations,
            "policy": {
                "source": "repo checkouts stay under repo_kernel/repos/<module>",
                "api": "global aliases live under /api/global/<system>; generic routes live under /api/global-systems/<system>",
                "ports": "canonical ports are desired ownership; observed ports are evidence until selected and health-checked",
                "moves": "path and hosting moves are represented here before any source or runtime mutation",
            },
        }

    def coverage(self, modules: list[str] | None = None, limit_unassigned: int = 200) -> dict[str, Any]:
        names = modules or self._registered_module_names()
        module_reports = []
        totals = {
            "routes": 0,
            "tools": 0,
            "runtime_targets": 0,
            "assigned": 0,
            "unassigned": 0,
            "multi_owner": 0,
        }
        unassigned_samples = []
        multi_owner_samples = []
        system_totals = {
            system: {"routes": 0, "tools": 0, "runtime_targets": 0}
            for system in self.SYSTEMS
        }

        for name in names:
            report = self._module_coverage(name, limit_unassigned=limit_unassigned)
            module_reports.append(report)
            for key in totals:
                totals[key] += report["summary"][key]
            for system, counts in report["system_counts"].items():
                for kind, count in counts.items():
                    system_totals[system][kind] += count
            unassigned_samples.extend(report["unassigned"][: max(0, limit_unassigned - len(unassigned_samples))])
            multi_owner_samples.extend(report["multi_owner"][: max(0, limit_unassigned - len(multi_owner_samples))])

        return {
            "module_count": len(module_reports),
            "systems": list(self.SYSTEMS),
            "summary": {
                **totals,
                "coverage_ratio": round(totals["assigned"] / max(1, totals["assigned"] + totals["unassigned"]), 4),
            },
            "system_totals": system_totals,
            "modules": module_reports,
            "unassigned_samples": unassigned_samples[:limit_unassigned],
            "multi_owner_samples": multi_owner_samples[:limit_unassigned],
            "implementation_needs": self._implementation_needs(totals, unassigned_samples, multi_owner_samples),
            "policy": {
                "assigned": "a surface is assigned when it matches at least one global system keyword set",
                "unassigned": "add a global system lane, expand keywords, or explicitly classify as ignored",
                "multi_owner": "keep all candidates, then define precedence only when live routing needs it",
                "mutation": "coverage only; no source moves or runtime calls",
            },
        }

    def port_reassignment_plan(self, modules: list[str] | None = None) -> dict[str, Any]:
        location_map = self.location_map(modules=modules)
        canonical_index: dict[int, list[dict[str, Any]]] = {}
        observed_index: dict[int, list[dict[str, Any]]] = {}
        systems = []

        for item in location_map["systems"]:
            system = item["system"]
            canonical_ports = item["port_map"]["canonical_ports"]
            observed_ports = item["port_map"]["observed_ports"]
            for port in canonical_ports:
                if isinstance(port.get("port"), int):
                    canonical_index.setdefault(port["port"], []).append({
                        "system": system,
                        "transport": port.get("transport"),
                        "source": port.get("source"),
                    })
            for port in observed_ports:
                if isinstance(port.get("host_port"), int):
                    observed_index.setdefault(port["host_port"], []).append({
                        "system": system,
                        "module": port.get("module"),
                        "service": port.get("service"),
                        "url": port.get("url"),
                        "source": port.get("source"),
                    })
            systems.append({
                "system": system,
                "public_control_endpoint": item["hosted_locations"]["canonical_base"],
                "generic_control_endpoint": item["hosted_locations"]["generic_base"],
                "public_control_port": 8786,
                "current_upstream_ports": observed_ports,
                "desired_upstream_ports": canonical_ports,
                "reassignment_status": "planned_not_moved",
            })

        canonical_conflicts = {
            port: owners
            for port, owners in canonical_index.items()
            if len({owner["system"] for owner in owners}) > 1
        }
        observed_shared = {
            port: owners
            for port, owners in observed_index.items()
            if len({owner["system"] for owner in owners}) > 1
        }
        return {
            "control_layer": {
                "service": "repo-kernel",
                "public_port": 8786,
                "base_url": "http://localhost:8786",
                "routing_mode": "path-based global system control before port reassignment",
            },
            "system_count": len(systems),
            "systems": systems,
            "canonical_conflicts": canonical_conflicts,
            "observed_shared_ports": observed_shared,
            "phases": [
                {
                    "phase": 1,
                    "name": "freeze current evidence",
                    "action": "keep existing service ports as upstream evidence; route users through /api/global/<system>",
                },
                {
                    "phase": 2,
                    "name": "select runtime slice",
                    "action": "choose one system lane, health-check its upstream services, and mark owner/port intent in the location map",
                },
                {
                    "phase": 3,
                    "name": "move public access",
                    "action": "make repo-kernel the public API surface while upstream services remain internal or compose-local",
                },
                {
                    "phase": 4,
                    "name": "reassign collisions",
                    "action": "resolve shared or conflicting host ports one lane at a time after the control route is live",
                },
            ],
            "policy": {
                "no_bulk_port_moves": "do not change host ports across the whole stack at once",
                "single_control_layer": "all callers should target repo-kernel /api/global/<system> first",
                "approval_gate": "actual compose port edits or service restarts require explicit approval per selected slice",
            },
        }

    def runtime_slice_plan(
        self,
        modules: list[str] | None = None,
        check_health: bool = False,
        timeout_seconds: float = 0.7,
        limit: int = 18,
    ) -> dict[str, Any]:
        coverage = self.coverage(modules=modules, limit_unassigned=50)
        location_map = self.location_map(modules=modules)
        locations = {item["system"]: item for item in location_map["systems"]}
        recommendations = []

        for system in self.SYSTEMS:
            counts = coverage["system_totals"].get(system, {})
            surface_count = sum(counts.values())
            observed_upstreams = self._live_upstreams(system)
            upstreams = [upstream for upstream in observed_upstreams if upstream.get("enabled", True)]
            disabled_upstreams = [upstream for upstream in observed_upstreams if not upstream.get("enabled", True)]
            health_report = {"checks": [], "truncated": False}
            if check_health and upstreams:
                synthetic_checks = []
                health_targets = []
                for upstream in upstreams:
                    if upstream.get("name") == "repo-kernel":
                        synthetic_checks.append({
                            "module": "docker-runtime",
                            "service": "repo-kernel",
                            "host_port": upstream.get("host_port"),
                            "runtime_kind": "http",
                            "url": upstream.get("health_url"),
                            "ok": True,
                            "status": "self",
                            "error": None,
                        })
                    else:
                        health_targets.append(self._runtime_health_target(system, upstream))
                health_report = self.topology.health_check_targets(
                    health_targets,
                    timeout_seconds=timeout_seconds,
                    limit=len(health_targets),
                )
                health_report["checks"] = synthetic_checks + health_report.get("checks", [])
            health_checks = health_report.get("checks", [])
            healthy_count = sum(1 for item in health_checks if item.get("ok"))
            unhealthy_count = len(health_checks) - healthy_count
            status, action = self._runtime_slice_status(upstreams, check_health, healthy_count, unhealthy_count)
            score = self._runtime_slice_score(system, surface_count, upstreams, check_health, healthy_count, unhealthy_count)
            location = locations[system]
            recommendations.append({
                "system": system,
                "score": score,
                "status": status,
                "next_action": action,
                "control_endpoint": location["hosted_locations"]["canonical_base"],
                "generic_endpoint": location["hosted_locations"]["generic_base"],
                "surface_counts": counts,
                "surface_count": surface_count,
                "live_upstream_count": len(upstreams),
                "healthy_upstream_count": healthy_count if check_health else None,
                "unhealthy_upstream_count": unhealthy_count if check_health else None,
                "live_upstreams": upstreams,
                "disabled_upstreams": disabled_upstreams,
                "health": health_report,
                "port_move_policy": "route behind repo-kernel first; defer host port edits until this slice is verified",
            })

        recommendations.sort(
            key=lambda item: (
                item["score"],
                item["live_upstream_count"],
                item["surface_count"],
                item["system"],
            ),
            reverse=True,
        )
        limited = recommendations[:limit]
        return {
            "control_layer": {
                "service": "repo-kernel",
                "public_port": 8786,
                "base_url": "http://localhost:8786",
                "routing_rule": "call /api/global/<system> while upstream services keep their existing ports",
            },
            "module_count": coverage["module_count"],
            "system_count": len(recommendations),
            "health_checked": check_health,
            "recommendations": limited,
            "next_best_steps": [
                {
                    "step": index + 1,
                    "system": item["system"],
                    "action": item["next_action"],
                    "control_endpoint": item["control_endpoint"],
                }
                for index, item in enumerate(limited[:5])
            ],
            "policy": {
                "one_slice_at_a_time": "activate one global system lane, verify routing, then proceed to the next lane",
                "no_bulk_port_moves": "do not reassign compose host ports until the selected lane is reachable through repo-kernel",
                "merge_rule": "same-name capabilities remain aggregated across all registered repos",
                "mutation": "this plan does not edit compose files or restart services",
            },
        }

    def describe(self, system: str, modules: list[str] | None = None) -> dict[str, Any]:
        config = self._config(system)
        names = modules or self._registered_module_names()
        workflow = self.unified.workflow(config["workflow"], modules=names)
        skills = self.skills(system, modules=names, limit=500)
        path_map = self._path_map(workflow.get("entries", []))
        tools = self._tools(system, modules=names, limit=2000)
        routes = self._routes(system, modules=names, limit=2000)
        ports = self.ports(system, modules=names)
        return {
            "system": system,
            "canonical_base": config["canonical_base"],
            "global_api": self._global_api(config["canonical_base"]),
            "module_count": len(path_map),
            "modules": path_map,
            "tool_count": len(tools),
            "route_count": len(routes),
            "skill_count": skills["count"],
            "port_count": ports["count"],
            "tools": tools[:200],
            "routes": routes[:200],
            "skills": skills["skills"][:100],
            "ports": ports["ports"],
            "canonical_ports": config["canonical_ports"],
            "routing_policy": {
                "pathing": "all repo references are reported as repo_kernel/repos/<module>/... local paths",
                "runtime": "health-check before live routing; static contracts are the fallback",
                "merge": "same-name capabilities are aggregated, not overwritten",
                "mutation": "planning only until an explicit live runtime and non-dry-run command is approved",
            },
        }

    def tools(self, system: str, modules: list[str] | None = None, q: str | None = None, limit: int = 500) -> dict[str, Any]:
        tools = self._tools(system, modules=modules, limit=2000)
        if q:
            needle = q.lower()
            tools = [tool for tool in tools if needle in json.dumps(tool, ensure_ascii=False).lower()]
        return {"system": system, "count": len(tools), "tools": tools[:limit]}

    def routes(self, system: str, modules: list[str] | None = None, q: str | None = None, limit: int = 500) -> dict[str, Any]:
        routes = self._routes(system, modules=modules, limit=2000)
        if q:
            needle = q.lower()
            routes = [route for route in routes if needle in json.dumps(route, ensure_ascii=False).lower()]
        return {"system": system, "count": len(routes), "routes": routes[:limit]}

    def ports(self, system: str, modules: list[str] | None = None) -> dict[str, Any]:
        self._config(system)
        names = modules or self._registered_module_names()
        ports = []
        for name in names:
            topology = self.topology.topology(name)
            for target in topology.get("runtime_urls", []):
                if self._matches_system(system, target):
                    ports.append(self._normalize_target(name, target))
            for service in topology.get("compose_services", []):
                if self._matches_system(system, service):
                    ports.append(self._normalize_target(name, {**service, "kind": "compose_service"}))
        return {"system": system, "count": len(ports), "ports": ports}

    def skills(self, system: str, modules: list[str] | None = None, limit: int = 500) -> dict[str, Any]:
        self._config(system)
        names = modules or self._registered_module_names()
        skills: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for name in names:
            root = self.registry.module_root(name)
            if not root.is_dir():
                continue
            for path in self._skill_files(root):
                rel = str(path.relative_to(root)).replace("\\", "/")
                key = (name, rel)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if not self._matches_system(system, {"path": rel, "content": text[:2000], "module": name}):
                    continue
                skills.append({
                    "module": name,
                    "path": rel,
                    "local_path": f"repo_kernel/repos/{name}/{rel}",
                    "title": self._skill_title(path, text),
                    "bytes": path.stat().st_size,
                    "preview": text[:500],
                })
                if len(skills) >= limit:
                    return {"system": system, "count": len(skills), "skills": skills}
        return {"system": system, "count": len(skills), "skills": skills}

    def call_plan(self, system: str, req: GlobalSystemCallPlanRequest) -> dict[str, Any]:
        self._config(system)
        if system == "mcp" and req.operation == "tool":
            candidates = [tool for tool in self._tools(system, modules=None, limit=5000) if tool.get("name") == req.name]
            if req.prefer_module:
                preferred = [tool for tool in candidates if tool.get("module") == req.prefer_module]
                if preferred:
                    candidates = preferred
            if not candidates:
                suggestions = [
                    tool for tool in self._tools(system, modules=None, limit=5000)
                    if req.name.lower() in tool.get("name", "").lower()
                ]
                return {
                    "system": system,
                    "operation": "tool",
                    "request": req.model_dump(),
                    "error": "no exact tool match",
                    "suggestions": suggestions[:20],
                }
            modules = sorted({tool["module"] for tool in candidates})
            ports = [port for port in self.ports(system, modules=modules)["ports"] if port.get("module") in modules]
            health = self.topology.health_check_targets(ports, timeout_seconds=0.5, limit=20)
            return {
                "system": system,
                "canonical_base": self.SYSTEMS[system]["canonical_base"],
                "operation": "tool",
                "request": req.model_dump(),
                "candidates": candidates,
                "runtime_candidates": ports[:20],
                "health": health,
                "execution": "not executed; global MCP tool routing is planning-only",
            }
        if req.operation == "tool":
            candidates = [tool for tool in self._tools(system, modules=None, limit=5000) if tool.get("name") == req.name]
            if req.prefer_module:
                preferred = [tool for tool in candidates if tool.get("module") == req.prefer_module]
                if preferred:
                    candidates = preferred
            if not candidates:
                suggestions = [
                    tool for tool in self._tools(system, modules=None, limit=5000)
                    if req.name.lower() in tool.get("name", "").lower()
                ]
                return {
                    "system": system,
                    "operation": "tool",
                    "request": req.model_dump(),
                    "error": "no exact tool match",
                    "suggestions": suggestions[:20],
                }
            modules = sorted({tool["module"] for tool in candidates})
            ports = [port for port in self.ports(system, modules=modules)["ports"] if port.get("module") in modules]
            health = self.topology.health_check_targets(ports, timeout_seconds=0.5, limit=20)
            return {
                "system": system,
                "canonical_base": self.SYSTEMS[system]["canonical_base"],
                "operation": "tool",
                "request": req.model_dump(),
                "candidates": candidates,
                "runtime_candidates": ports[:20],
                "health": health,
                "execution": f"not executed; global {system} tool routing is planning-only",
            }
        if system == "memory" and req.operation == "query":
            return {
                "system": system,
                "canonical_base": self.SYSTEMS[system]["canonical_base"],
                "operation": "query",
                "plan": self.memory.query_plan(MemoryQueryRequest(**req.arguments)),
            }
        if system == "memory" and req.operation == "receipt":
            return {
                "system": system,
                "canonical_base": self.SYSTEMS[system]["canonical_base"],
                "operation": "receipt",
                "plan": self.memory.receipt_plan(MemoryQueryRequest(**req.arguments)),
            }
        if system == "agent-orchestration" and req.operation == "plan":
            if self.agent_orchestration is None:
                raise HTTPException(500, "agent orchestration workflow is not available")
            arguments = dict(req.arguments)
            arguments.setdefault("intent", req.name)
            arguments.setdefault("dry_run", req.dry_run)
            if req.prefer_module:
                arguments.setdefault("prefer_module", req.prefer_module)
            return {
                "system": system,
                "canonical_base": self.SYSTEMS[system]["canonical_base"],
                "operation": "plan",
                "plan": self.agent_orchestration.plan(AgentOrchestrationPlanRequest(**arguments)),
            }
        if system == "knowledge" and req.operation == "plan":
            if self.knowledge is None:
                raise HTTPException(500, "knowledge workflow is not available")
            arguments = dict(req.arguments)
            arguments.setdefault("task", req.name)
            arguments.setdefault("dry_run", req.dry_run)
            if req.prefer_module:
                arguments.setdefault("prefer_module", req.prefer_module)
            return {
                "system": system,
                "canonical_base": self.SYSTEMS[system]["canonical_base"],
                "operation": "plan",
                "plan": self.knowledge.plan(KnowledgePlanRequest(**arguments)),
            }
        if req.operation == "route":
            routes = [
                route for route in self._routes(system, modules=None, limit=2000)
                if req.name.lower() in json.dumps(route, ensure_ascii=False).lower()
            ]
            return {
                "system": system,
                "operation": "route",
                "request": req.model_dump(),
                "candidates": routes[:20],
                "execution": "not executed; global route layer is planning-only",
            }
        if req.operation == "service":
            ports = [
                port for port in self.ports(system)["ports"]
                if req.name.lower() in json.dumps(port, ensure_ascii=False).lower()
            ]
            health = self.topology.health_check_targets(ports, timeout_seconds=0.5, limit=20)
            return {
                "system": system,
                "operation": "service",
                "request": req.model_dump(),
                "candidates": ports[:20],
                "health": health,
                "execution": "not started; service activation requires explicit approval",
            }
        raise HTTPException(400, f"unsupported global {system} operation: {req.operation}")

    def _tools(self, system: str, modules: list[str] | None, limit: int) -> list[dict[str, Any]]:
        config = self._config(system)
        workflow = self.unified.workflow(config["workflow"], modules=modules or self._registered_module_names())
        tools = []
        for entry in workflow.get("entries", []):
            for tool in entry.get("mcp_tools", []):
                tools.append(self.mcp_tools._normalize_tool(tool, entry["module"]))
        return sorted(
            (
                {
                    **tool,
                    "canonical_path": f"{config['canonical_base']}/tools/{tool.get('name')}",
                    "local_source": self._local_source(tool),
                }
                for tool in tools
            ),
            key=lambda item: (item.get("name", ""), item.get("module", "")),
        )[:limit]

    def _routes(self, system: str, modules: list[str] | None, limit: int) -> list[dict[str, Any]]:
        config = self._config(system)
        workflow = self.unified.workflow(config["workflow"], modules=modules or self._registered_module_names())
        routes = []
        for entry in workflow.get("entries", []):
            for route in entry.get("routes", []):
                routes.append({
                    **route,
                    "module": entry["module"],
                    "canonical_base": config["canonical_base"],
                    "canonical_path": self._canonical_route_path(system, route),
                    "local_source": self._local_source({**route, "module": entry["module"]}),
                })
        return routes[:limit]

    def _system_location(self, system: str, modules: list[str] | None = None) -> dict[str, Any]:
        config = self._config(system)
        names = modules or self._registered_module_names()
        workflow = self.unified.workflow(config["workflow"], modules=names)
        module_paths = self._path_map(workflow.get("entries", []))
        ports = self.ports(system, modules=names)["ports"]
        return {
            "system": system,
            "workflow": config["workflow"],
            "status": "mapped_not_moved",
            "hosted_locations": {
                "canonical_base": config["canonical_base"],
                "generic_base": f"/api/global-systems/{system}",
                "active_paths": self._global_api(config["canonical_base"]),
                "generic_paths": self._global_api(f"/api/global-systems/{system}"),
                "controller": "services/repo-kernel/server.py",
                "host_runtime": "repo-kernel FastAPI service; live service activation remains separate",
            },
            "path_map": {
                "module_count": len(module_paths),
                "module_roots": module_paths,
                "rewrite_rule": "rewrite stale repo references to repo_kernel/repos/<module>/<relative-path>",
            },
            "port_map": {
                "canonical_ports": config["canonical_ports"],
                "observed_ports": self._dedupe_ports(ports),
                "observed_count": len(ports),
                "canonical_ownership": [
                    {
                        **port,
                        "host": "localhost",
                        "base_url": f"http://localhost:{port['port']}" if isinstance(port.get("port"), int) else None,
                        "status": "reserved_for_global_system_mapping",
                    }
                    for port in config["canonical_ports"]
                ],
            },
            "move_plan": [
                "keep repo source in place under repo_kernel/repos",
                "route callers through the canonical /api/global/<system> path",
                "treat compose/readme ports as hosted-location evidence until health checked",
                "move stale path references into this map before editing service code",
            ],
        }

    def _module_coverage(self, name: str, limit_unassigned: int) -> dict[str, Any]:
        surfaces = self.surface_catalog.catalog(name, limit=2000)
        topology = self.topology.topology(name)
        unassigned = []
        multi_owner = []
        summary = {
            "routes": 0,
            "tools": 0,
            "runtime_targets": 0,
            "assigned": 0,
            "unassigned": 0,
            "multi_owner": 0,
        }
        system_counts = {
            system: {"routes": 0, "tools": 0, "runtime_targets": 0}
            for system in self.SYSTEMS
        }

        items: list[dict[str, Any]] = []
        for route in surfaces.get("routes", []) + surfaces.get("nextjs_routes", []):
            items.append(self._coverage_item(name, "routes", route))
        for tool in surfaces.get("mcp_tools", []):
            items.append(self._coverage_item(name, "tools", tool))
        for target in topology.get("runtime_urls", []):
            items.append(self._coverage_item(name, "runtime_targets", self._normalize_target(name, target)))

        for item in items:
            kind = item["kind"]
            summary[kind] += 1
            owners = self._matching_systems(item)
            item["owners"] = owners
            if owners:
                summary["assigned"] += 1
                for owner in owners:
                    system_counts[owner][kind] += 1
            else:
                summary["unassigned"] += 1
                if len(unassigned) < limit_unassigned:
                    unassigned.append(item)
            if len(owners) > 1:
                summary["multi_owner"] += 1
                if len(multi_owner) < limit_unassigned:
                    multi_owner.append(item)

        return {
            "module": name,
            "local_root": f"repo_kernel/repos/{name}",
            "summary": {
                **summary,
                "coverage_ratio": round(summary["assigned"] / max(1, summary["assigned"] + summary["unassigned"]), 4),
            },
            "system_counts": system_counts,
            "unassigned": unassigned,
            "multi_owner": multi_owner,
        }

    def _coverage_item(self, module: str, kind: str, item: dict[str, Any]) -> dict[str, Any]:
        file = item.get("file")
        return {
            "module": module,
            "kind": kind,
            "name": item.get("name") or item.get("function") or item.get("service") or item.get("path") or item.get("url"),
            "method": item.get("method") or ",".join(item.get("methods", [])) if item.get("methods") else item.get("method"),
            "path": item.get("path"),
            "service": item.get("service"),
            "host_port": item.get("host_port"),
            "url": item.get("url"),
            "file": file,
            "local_source": f"repo_kernel/repos/{module}/{file}" if file else f"repo_kernel/repos/{module}",
            "evidence": item,
        }

    def _matching_systems(self, item: dict[str, Any]) -> list[str]:
        return [system for system in self.SYSTEMS if self._matches_system(system, item)]

    def _implementation_needs(
        self,
        totals: dict[str, int],
        unassigned_samples: list[dict[str, Any]],
        multi_owner_samples: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        needs = []
        if totals["unassigned"]:
            needs.append({
                "priority": 1,
                "area": "unassigned_surfaces",
                "count": totals["unassigned"],
                "action": "classify unassigned routes/tools/ports into a new global system lane or expand an existing lane keyword set",
                "sample_names": [item.get("name") for item in unassigned_samples[:10]],
            })
        if totals["multi_owner"]:
            needs.append({
                "priority": 2,
                "area": "multi_owner_routing",
                "count": totals["multi_owner"],
                "action": "define primary routing precedence for surfaces that match more than one global system",
                "sample_names": [item.get("name") for item in multi_owner_samples[:10]],
            })
        if not needs:
            needs.append({
                "priority": 3,
                "area": "coverage_review",
                "count": 0,
                "action": "all discovered surfaces match at least one global system; review multi-module duplicates before live routing",
                "sample_names": [],
            })
        return needs

    def _dedupe_ports(self, ports: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[Any, Any, Any]] = set()
        deduped = []
        for port in ports:
            key = (port.get("module"), port.get("host_port"), port.get("service"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(port)
        return sorted(
            deduped,
            key=lambda item: (
                str(item.get("host_port") or ""),
                str(item.get("module") or ""),
                str(item.get("service") or ""),
            ),
        )

    def _path_map(self, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        modules = []
        for entry in entries:
            name = entry["module"]
            root = self.registry.module_root(name)
            modules.append({
                "module": name,
                "role": self.registry.module(name).get("role"),
                "local_root": f"repo_kernel/repos/{name}",
                "resolved_root": str(root),
                "adapter_id": entry.get("adapter_id"),
                "routes": len(entry.get("routes", [])),
                "mcp_tools": len(entry.get("mcp_tools", [])),
                "runtime_targets": len(entry.get("runtime_targets", [])),
            })
        return modules

    def _registered_module_names(self) -> list[str]:
        excluded = {"CMPLX-PartsFactory", "scout-demo-service"}
        modules = [module for module in self.registry.modules() if module.get("name") not in excluded]
        modules.sort(key=lambda module: module.get("pushed_at") or module.get("updated_at") or "")
        return [module["name"] for module in modules]

    def _skill_files(self, root: Path) -> list[Path]:
        files = []
        for pattern in ("SKILL.md", "SKILLS.md"):
            files.extend(root.rglob(pattern))
        return [
            path for path in files
            if ".git" not in path.parts
            and "node_modules" not in path.parts
            and path.is_file()
            and path.stat().st_size <= 200_000
        ]

    def _skill_title(self, path: Path, text: str) -> str:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip() or path.stem
        return path.parent.name if path.name == "SKILL.md" else path.stem

    def _canonical_route_path(self, system: str, route: dict[str, Any]) -> str:
        base = self.SYSTEMS[system]["canonical_base"]
        path = route.get("path") or route.get("path_pattern") or route.get("file") or "/"
        return f"{base}/routes/{str(path).strip('/')}"

    def _local_source(self, item: dict[str, Any]) -> str | None:
        module = item.get("module")
        file = item.get("file")
        if module and file:
            return f"repo_kernel/repos/{module}/{file}"
        return None

    def _normalize_target(self, module: str, target: dict[str, Any]) -> dict[str, Any]:
        return {
            "module": module,
            "kind": target.get("kind"),
            "service": target.get("service"),
            "host_port": target.get("host_port") or target.get("host"),
            "container_port": target.get("container_port") or target.get("container"),
            "url": target.get("url"),
            "transport": target.get("transport") or self._infer_transport(target),
            "source": target.get("source") or target.get("compose_file"),
            "local_root": f"repo_kernel/repos/{module}",
        }

    def _infer_transport(self, target: dict[str, Any]) -> str:
        haystack = json.dumps(target, ensure_ascii=False).lower()
        if "sse" in haystack:
            return "http/sse"
        if "postgres" in haystack or "5432" in haystack:
            return "postgres"
        if "redis" in haystack or "6379" in haystack:
            return "redis"
        return "http"

    def _matches_system(self, system: str, item: dict[str, Any]) -> bool:
        keywords = self._config(system)["keywords"]
        haystack = json.dumps(item, ensure_ascii=False).lower()
        return any(keyword in haystack for keyword in keywords)

    def memory_routing_contract(self, check_health: bool = False, timeout_seconds: float = 0.7) -> dict[str, Any]:
        upstreams = [upstream for upstream in self._live_upstreams("memory") if upstream.get("enabled", True)]
        routed = []
        for upstream in upstreams:
            item = dict(upstream)
            item["internal_url"] = self._runtime_base_url(upstream)
            item["read_paths"] = self._memory_allowed_paths(upstream["name"])
            item["write_policy"] = "blocked by global controller; use call-plan/receipt-plan until a write gate is approved"
            routed.append(item)
        health = {"checks": [], "truncated": False}
        if check_health:
            plan = self.runtime_slice_plan(
                modules=["CMPLXUNI", "CMPLX-TMN-main"],
                check_health=True,
                timeout_seconds=timeout_seconds,
                limit=18,
            )
            memory = next(item for item in plan["recommendations"] if item["system"] == "memory")
            health = memory["health"]
        return {
            "system": "memory",
            "control_endpoint": "/api/global/memory",
            "status": "ready_for_control_route",
            "public_routes": [
                "GET /api/global/memory/upstreams",
                "GET /api/global/memory/health",
                "GET /api/global/memory/read/{service}/{path}",
                "GET /api/global/memory/search?q=<term>",
            ],
            "upstreams": routed,
            "health": health,
            "policy": {
                "read": "approved read-only upstream paths may be proxied through repo-kernel",
                "write": "mutating upstream calls remain disabled in this first routed slice",
                "ports": "upstream service ports stay unchanged; repo-kernel is the public control surface",
            },
        }

    def memory_read_proxy(self, service: str, path: str = "", query: dict[str, Any] | None = None) -> dict[str, Any]:
        upstream = self._memory_upstream(service)
        if upstream.get("runtime_kind") in {"tcp", "postgres", "redis"}:
            raise HTTPException(400, f"{service} is not an HTTP memory upstream")
        normalized_path = self._normalize_proxy_path(path)
        if not self._memory_path_allowed(service, normalized_path):
            raise HTTPException(403, f"read path is not approved for memory upstream {service}: {normalized_path}")
        base_url = self._runtime_base_url(upstream)
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            raise HTTPException(400, f"{service} has no HTTP base URL")
        url = f"{base_url}{normalized_path}"
        clean_query = {key: value for key, value in (query or {}).items() if key not in {"service", "path"}}
        if clean_query:
            url = f"{url}?{urllib.parse.urlencode(clean_query, doseq=True)}"
        result = {
            "system": "memory",
            "service": service,
            "method": "GET",
            "path": normalized_path,
            "url": url,
            "ok": False,
            "status": None,
            "content_type": None,
            "data": None,
            "error": None,
            "policy": "read-only proxy through repo-kernel; no upstream host port move",
        }
        try:
            req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json, text/plain;q=0.8, */*;q=0.5"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                raw = resp.read(500_000)
                result["status"] = resp.status
                result["ok"] = 200 <= resp.status < 500
                result["content_type"] = resp.headers.get("content-type")
                result["data"] = self._decode_proxy_response(raw, result["content_type"])
        except urllib.error.HTTPError as exc:
            raw = exc.read(200_000)
            result["status"] = exc.code
            result["ok"] = exc.code < 500
            result["content_type"] = exc.headers.get("content-type")
            result["data"] = self._decode_proxy_response(raw, result["content_type"])
        except Exception as exc:
            result["error"] = str(exc)[:300]
        return result

    def memory_search(self, q: str, service: str = "pocket-memory-api", limit: int = 20) -> dict[str, Any]:
        if not q:
            raise HTTPException(400, "q is required")
        return self.memory_read_proxy(service, "search", query={"q": q, "limit": limit})

    def geometry_routing_contract(self, check_health: bool = False, timeout_seconds: float = 0.7) -> dict[str, Any]:
        upstreams = [upstream for upstream in self._live_upstreams("geometry") if upstream.get("enabled", True)]
        routed = []
        for upstream in upstreams:
            item = dict(upstream)
            item["internal_url"] = self._runtime_base_url(upstream)
            item["read_paths"] = self._geometry_allowed_paths(upstream["name"])
            item["write_policy"] = "blocked by global controller; geometry mutations remain call-plan only"
            routed.append(item)
        health = {"checks": [], "truncated": False}
        if check_health:
            plan = self.runtime_slice_plan(
                modules=["CMPLXUNI", "CMPLX-TMN-main"],
                check_health=True,
                timeout_seconds=timeout_seconds,
                limit=18,
            )
            geometry = next(item for item in plan["recommendations"] if item["system"] == "geometry")
            health = geometry["health"]
        return {
            "system": "geometry",
            "control_endpoint": "/api/global/geometry",
            "status": "ready_for_control_route",
            "public_routes": [
                "GET /api/global/geometry/upstreams",
                "GET /api/global/geometry/health",
                "GET /api/global/geometry/read/{service}/{path}",
            ],
            "upstreams": routed,
            "health": health,
            "policy": {
                "read": "approved geometry/state/metric paths may be proxied through repo-kernel",
                "write": "create, add, process, store, and mutation routes are disabled in this first geometry slice",
                "ports": "upstream service ports stay unchanged; repo-kernel is the public control surface",
            },
        }

    def geometry_read_proxy(self, service: str, path: str = "", query: dict[str, Any] | None = None) -> dict[str, Any]:
        upstream = self._geometry_upstream(service)
        normalized_path = self._normalize_proxy_path(path)
        if not self._geometry_path_allowed(service, normalized_path):
            raise HTTPException(403, f"read path is not approved for geometry upstream {service}: {normalized_path}")
        return self._read_proxy("geometry", service, normalized_path, upstream, query=query)

    def operations_routing_contract(self, check_health: bool = False, timeout_seconds: float = 0.7) -> dict[str, Any]:
        upstreams = [upstream for upstream in self._live_upstreams("operations") if upstream.get("enabled", True)]
        routed = []
        for upstream in upstreams:
            item = dict(upstream)
            item["internal_url"] = self._runtime_base_url(upstream)
            item["read_paths"] = self._operations_allowed_paths(upstream["name"])
            item["write_policy"] = "blocked by global controller; operations mutations and restarts remain approval-gated"
            routed.append(item)
        health = {"checks": [], "truncated": False}
        if check_health:
            plan = self.runtime_slice_plan(
                modules=["CMPLXUNI", "CMPLX-TMN-main"],
                check_health=True,
                timeout_seconds=timeout_seconds,
                limit=18,
            )
            operations = next(item for item in plan["recommendations"] if item["system"] == "operations")
            health = operations["health"]
        return {
            "system": "operations",
            "control_endpoint": "/api/global/operations",
            "status": "ready_for_control_route",
            "public_routes": [
                "GET /api/global/operations/upstreams",
                "GET /api/global/operations/health",
                "GET /api/global/operations/read/{service}/{path}",
                "GET /api/gitnexus/status",
                "GET /api/gitnexus/graph-summary",
                "GET /api/gitnexus/aggregate/search",
            ],
            "upstreams": routed,
            "health": health,
            "api_layer_needs": [
                {
                    "area": "gitnexus_evidence_lane",
                    "need": "use GitNexus repo graphs and historical reports before broad scans or promotion decisions",
                    "current_bridge": "GET /api/gitnexus/status and GET /api/gitnexus/aggregate/search",
                },
                {
                    "area": "gitnexus_refresh_policy",
                    "need": "add an approval-gated refresh/index route later so graph indexes can be updated after large controller edits",
                    "current_bridge": "read-only bridge; CLI analyze/index remain outside repo-kernel",
                },
            ],
            "policy": {
                "read": "approved status/control-plane paths may be proxied or synthesized through repo-kernel",
                "write": "restart, scale, mutation, and GitNexus write paths remain disabled",
                "ports": "upstream service ports stay unchanged; repo-kernel is the public control surface",
            },
        }

    def operations_read_proxy(self, service: str, path: str = "", query: dict[str, Any] | None = None) -> dict[str, Any]:
        upstream = self._operations_upstream(service)
        normalized_path = self._normalize_proxy_path(path)
        if not self._operations_path_allowed(service, normalized_path):
            raise HTTPException(403, f"read path is not approved for operations upstream {service}: {normalized_path}")
        if service == "repo-kernel":
            return self._repo_kernel_self_read(normalized_path)
        return self._read_proxy("operations", service, normalized_path, upstream, query=query)

    def knowledge_routing_contract(self, check_health: bool = False, timeout_seconds: float = 0.7) -> dict[str, Any]:
        observed = self._live_upstreams("knowledge")
        upstreams = [upstream for upstream in observed if upstream.get("enabled", True)]
        routed = []
        for upstream in upstreams:
            item = dict(upstream)
            item["internal_url"] = self._runtime_base_url(upstream)
            item["read_paths"] = self._knowledge_allowed_paths(upstream["name"])
            item["write_policy"] = "blocked by global controller; indexing/import/write operations remain approval-gated"
            routed.append(item)
        health = {"checks": [], "truncated": False}
        if check_health:
            plan = self.runtime_slice_plan(
                modules=["CMPLXUNI", "CMPLX-TMN-main"],
                check_health=True,
                timeout_seconds=timeout_seconds,
                limit=18,
            )
            knowledge = next(item for item in plan["recommendations"] if item["system"] == "knowledge")
            health = knowledge["health"]
        return {
            "system": "knowledge",
            "control_endpoint": "/api/global/knowledge",
            "status": "ready_for_control_route_with_disabled_evidence",
            "public_routes": [
                "GET /api/global/knowledge/upstreams",
                "GET /api/global/knowledge/health",
                "GET /api/global/knowledge/search?q=<term>",
                "GET /api/global/knowledge/read/{service}/{path}",
            ],
            "upstreams": routed,
            "disabled_upstreams": [upstream for upstream in observed if not upstream.get("enabled", True)],
            "health": health,
            "api_layer_needs": [
                {
                    "area": "native_knowledge_search",
                    "need": "define one canonical /api/global/knowledge/search response shape over db-aggregator results, repo surfaces, and future indexes",
                    "current_bridge": "db-aggregator-api /search",
                },
                {
                    "area": "research_api_contract",
                    "need": "research-api currently exposes health only; add or identify read endpoints before routing corpus/query traffic there",
                    "current_bridge": "health-only upstream",
                },
                {
                    "area": "jupyter_runtime",
                    "need": "research-api-jupyter refuses container connections on :8888; keep disabled until explicitly started or removed",
                    "current_bridge": "disabled evidence",
                },
            ],
            "policy": {
                "read": "approved search/catalog/receipt/status paths may be proxied through repo-kernel",
                "write": "discover, enqueue, import, index, report generation, and mutation routes remain disabled",
                "ports": "upstream service ports stay unchanged; repo-kernel is the public control surface",
            },
        }

    def knowledge_read_proxy(self, service: str, path: str = "", query: dict[str, Any] | None = None) -> dict[str, Any]:
        upstream = self._knowledge_upstream(service)
        normalized_path = self._normalize_proxy_path(path)
        if not self._knowledge_path_allowed(service, normalized_path):
            raise HTTPException(403, f"read path is not approved for knowledge upstream {service}: {normalized_path}")
        return self._read_proxy("knowledge", service, normalized_path, upstream, query=query)

    def knowledge_search(self, q: str, service: str = "db-aggregator-api", limit: int = 20) -> dict[str, Any]:
        if not q:
            raise HTTPException(400, "q is required")
        return self.knowledge_read_proxy(service, "search", query={"q": q, "limit": limit})

    def live_slice_routing_contract(self, system: str, check_health: bool = False, timeout_seconds: float = 0.7) -> dict[str, Any]:
        self._config(system)
        observed = self._live_upstreams(system)
        if not observed and system in self.STATIC_ADAPTER_SYSTEMS:
            return self.static_adapter_routing_contract(system)
        upstreams = [upstream for upstream in observed if self._slice_upstream_enabled(system, upstream)]
        disabled = [upstream for upstream in observed if not self._slice_upstream_enabled(system, upstream)]
        routed = []
        for upstream in upstreams:
            item = dict(upstream)
            item["internal_url"] = self._runtime_base_url(upstream)
            item["read_paths"] = self._live_slice_allowed_paths(system, upstream["name"])
            item["write_policy"] = "blocked by global controller; this routed slice is read-only"
            routed.append(item)
        health = {"checks": [], "truncated": False}
        if check_health:
            health_targets = [{**item, "service": item.get("name"), "module": system} for item in upstreams]
            health = self.topology.health_check_targets(health_targets, timeout_seconds=timeout_seconds, limit=20)
        status = "ready_for_control_route" if upstreams else "mapped_with_disabled_evidence"
        return {
            "system": system,
            "control_endpoint": self.SYSTEMS[system]["canonical_base"],
            "status": status,
            "public_routes": [
                f"GET /api/global/{system}/upstreams",
                f"GET /api/global/{system}/health",
                f"GET /api/global/{system}/read/{{service}}/{{path}}",
            ],
            "upstreams": routed,
            "disabled_upstreams": disabled,
            "health": health,
            "api_layer_needs": self._live_slice_api_layer_needs(system, disabled),
            "policy": {
                "read": "approved status/catalog/summary paths may be proxied through repo-kernel",
                "write": "execution, generation, validation mutation, portal control, and auth-gated actions remain blocked",
                "ports": "upstream service ports stay unchanged; repo-kernel is the public control surface",
            },
        }

    def live_slice_read_proxy(self, system: str, service: str, path: str = "", query: dict[str, Any] | None = None) -> dict[str, Any]:
        if system in self.STATIC_ADAPTER_SYSTEMS and service == "repo-kernel-adapter":
            normalized_path = self._normalize_proxy_path(path)
            return self._static_adapter_read(system, normalized_path)
        upstream = self._live_slice_upstream(system, service)
        normalized_path = self._normalize_proxy_path(path)
        if not self._live_slice_path_allowed(system, service, normalized_path):
            raise HTTPException(403, f"read path is not approved for {system} upstream {service}: {normalized_path}")
        return self._read_proxy(system, service, normalized_path, upstream, query=query)

    def static_adapter_routing_contract(self, system: str) -> dict[str, Any]:
        config = self._config(system)
        ports = self.ports(system).get("ports", [])
        activation_candidates = [port for port in ports if port.get("host_port")]
        adapter = {
            "name": "repo-kernel-adapter",
            "system": system,
            "internal_url": f"self:{config['canonical_base']}",
            "source": "repo-kernel static adapter and repo evidence",
            "read_paths": ["/", "/summary", "/ports", "/activation-candidates"],
            "write_policy": "blocked by global controller; execution and service activation require explicit promotion",
            "activation_candidate_count": len(activation_candidates),
        }
        return {
            "system": system,
            "control_endpoint": config["canonical_base"],
            "status": "ready_for_static_control_route",
            "public_routes": [
                f"GET /api/global/{system}/upstreams",
                f"GET /api/global/{system}/health",
                f"GET /api/global/{system}/read/repo-kernel-adapter/summary",
                f"GET /api/global/{system}/read/repo-kernel-adapter/ports",
                f"GET /api/global/{system}/read/repo-kernel-adapter/activation-candidates",
            ],
            "upstreams": [adapter],
            "disabled_upstreams": [],
            "health": {
                "checks": [
                    {
                        "module": "repo-kernel",
                        "service": "repo-kernel-adapter",
                        "runtime_kind": "static",
                        "url": f"self:{config['canonical_base']}",
                        "ok": True,
                        "status": "static_adapter_ready",
                    }
                ],
                "truncated": False,
            },
            "activation_candidates": activation_candidates[:20],
            "api_layer_needs": [
                {
                    "area": f"{system}_live_runtime_selection",
                    "need": f"select which {system} activation candidate should become a live upstream before enabling execution",
                    "current_bridge": f"GET /api/global/{system}/read/repo-kernel-adapter/activation-candidates",
                },
                {
                    "area": f"{system}_fast_surface_cache",
                    "need": f"persist a compact {system} tool/route index so large static surface reads do not block the controller",
                    "current_bridge": f"GET /api/global/{system}/read/repo-kernel-adapter/summary",
                },
            ],
            "policy": {
                "read": "static adapter evidence and activation candidates are readable through repo-kernel",
                "write": "MCP calls, agent spawning, code execution, and service activation remain plan-only",
                "ports": "candidate ports are evidence only until a live runtime is selected",
            },
        }

    def global_query(self, req: GlobalQueryRequest) -> dict[str, Any]:
        allowed_systems = {"memory", "knowledge", "geometry", "operations"}
        systems = [system for system in req.systems if system in allowed_systems]
        rejected_systems = [system for system in req.systems if system not in allowed_systems]
        plan = [
            {"system": "memory", "call": f"GET /api/global/memory/search?q={req.q}&limit={req.limit}"},
            {"system": "knowledge", "call": f"GET /api/global/knowledge/search?q={req.q}&limit={req.limit}"},
            {"system": "knowledge", "call": f"GET /api/global/knowledge/prototype-claims?q={req.q}&limit={req.limit}"},
            {"system": "knowledge", "call": f"GET /api/gitnexus/aggregate/search?q={req.q}&limit={req.limit}"},
            {"system": "geometry", "call": "GET /api/global/geometry/read/tarpit-api/stats and /api/global/geometry/read/unique-systems-api/summary"},
            {"system": "operations", "call": "GET /api/global/operations/read/repo-kernel/api/health"},
        ]
        plan = [item for item in plan if item["system"] in systems]
        if req.dry_run:
            return {
                "query": req.q,
                "dry_run": True,
                "systems": systems,
                "rejected_systems": rejected_systems,
                "planned_calls": plan,
                "execution": "not executed; dry_run requested",
            }

        results: list[dict[str, Any]] = []
        context: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        if "memory" in systems:
            self._global_query_try("memory", lambda: self.memory_search(req.q, limit=req.limit), results, context, errors, req)
        if "knowledge" in systems:
            self._global_query_try("knowledge", lambda: self.knowledge_search(req.q, limit=req.limit), results, context, errors, req)
            if self.prototype_evidence is not None:
                self._global_query_try("prototype_claims", lambda: self.prototype_evidence.search(req.q, limit=req.limit), results, context, errors, req)
            if self.gitnexus is not None:
                self._global_query_try("gitnexus_reports", lambda: self.gitnexus.aggregate_search(q=req.q, limit=req.limit), results, context, errors, req)
        if "geometry" in systems:
            self._global_query_try("geometry_tarpit", lambda: self.geometry_read_proxy("tarpit-api", "stats"), results, context, errors, req)
            self._global_query_try("geometry_unique_systems", lambda: self.geometry_read_proxy("unique-systems-api", "summary"), results, context, errors, req)
        if "operations" in systems and req.include_context:
            self._global_query_try("operations", lambda: self.operations_read_proxy("repo-kernel", "api/health"), results, context, errors, req)

        ranked_results = self._rank_global_query_records(self._dedupe_global_query_records(results), req.q)
        ranked_context = self._rank_global_query_records(self._dedupe_global_query_records(context), req.q)
        limited_results = ranked_results[:req.limit]
        return {
            "query": req.q,
            "schema_version": 2,
            "dry_run": False,
            "systems": systems,
            "rejected_systems": rejected_systems,
            "result_count": len(limited_results),
            "context_count": len(ranked_context),
            "results": limited_results,
            "context": ranked_context,
            "errors": errors,
            "api_layer_needs": [
                {
                    "area": "ranking_tuning",
                    "need": "tune scoring weights with real user queries and add recency/source-quality boosts",
                    "current_bridge": "deterministic text/local-ref/confidence scoring",
                },
                {
                    "area": "snippet_generation",
                    "need": "add highlighted snippets for live upstream records after prototype evidence snippets prove useful",
                    "current_bridge": "prototype claim/doc snippets",
                },
            ],
            "policy": {
                "read_only": "fanout uses only routed read/search endpoints",
                "no_upstream_ports": "all calls go through repo-kernel controller methods",
                "partial_failure": "slice failures are returned in errors without failing the whole query",
            },
        }

    def tool_workbook(self, check_health: bool = False, timeout_seconds: float = 0.7, include_external_evidence: bool = True) -> dict[str, Any]:
        contracts = [
            self.memory_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds),
            self.geometry_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds),
            self.operations_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds),
            self.knowledge_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds),
            self.live_slice_routing_contract("ai-runtime", check_health=check_health, timeout_seconds=timeout_seconds),
            self.live_slice_routing_contract("validation", check_health=check_health, timeout_seconds=timeout_seconds),
            self.live_slice_routing_contract("synthesis", check_health=check_health, timeout_seconds=timeout_seconds),
            self.live_slice_routing_contract("external-ai-portal", check_health=check_health, timeout_seconds=timeout_seconds),
            self.static_adapter_routing_contract("mcp"),
            self.static_adapter_routing_contract("agent-orchestration"),
            self.static_adapter_routing_contract("code-execution"),
        ]
        tools = []
        api_layer_needs = [
            {
                "area": "global_query_fanout",
                "need": "tune /api/global/query ranking and add snippets after canonical result schema v2",
                "current_bridge": "GET /api/global/query",
            },
            {
                "area": "workbook_refresh",
                "need": "keep this workbook as the active inventory whenever a routed slice or allowed path changes",
                "current_bridge": "GET /api/global-tool-workbook",
            },
        ]
        for contract in contracts:
            system = contract["system"]
            for upstream in contract.get("upstreams", []):
                read_paths = upstream.get("read_paths", [])
                tools.append({
                    "system": system,
                    "service": upstream["name"],
                    "control_endpoint": contract["control_endpoint"],
                    "public_routes": contract["public_routes"],
                    "read_paths": read_paths,
                    "example": self._workbook_example(system, upstream["name"], read_paths),
                    "write_policy": upstream.get("write_policy"),
                    "status": contract.get("status"),
                })
            api_layer_needs.extend(contract.get("api_layer_needs", []))
        named_capabilities = self._named_capability_inventory()
        tools.extend(named_capabilities)

        external_evidence = None
        if include_external_evidence and self.prototype_evidence is not None:
            external_evidence = self.prototype_evidence.overview()
            api_layer_needs.extend(external_evidence.get("api_layer_needs", []))
        gitnexus_evidence = None
        if include_external_evidence and self.gitnexus is not None:
            gitnexus_evidence = self.gitnexus.status(include_repos=True, repo_limit=12)

        return {
            "workbook": "global-live-tool-workbook",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "control_layer": {
                "service": "repo-kernel",
                "base_url": "http://localhost:8786",
                "policy": "use repo-kernel global endpoints in live work; do not call upstream service ports directly unless debugging the controller",
            },
            "routed_systems": [
                {
                    "system": contract["system"],
                    "status": contract.get("status"),
                    "control_endpoint": contract["control_endpoint"],
                    "public_routes": contract["public_routes"],
                    "upstream_count": len(contract.get("upstreams", [])),
                    "disabled_upstreams": contract.get("disabled_upstreams", []),
                    "health": contract.get("health") if check_health else None,
                    "policy": contract.get("policy"),
                }
                for contract in contracts
            ],
            "available_live_tools": tools,
            "named_capabilities": named_capabilities,
            "external_evidence": external_evidence,
            "gitnexus_evidence": gitnexus_evidence,
            "quick_use": [
                {
                    "intent": "Check controller health through the operations slice",
                    "method": "GET",
                    "path": "/api/global/operations/read/repo-kernel/api/health",
                },
                {
                    "intent": "Search across routed slices",
                    "method": "GET",
                    "path": "/api/global/query?q=receipt&limit=10",
                },
                {
                    "intent": "Search live memory records",
                    "method": "GET",
                    "path": "/api/global/memory/search?q=receipt&limit=5",
                },
                {
                    "intent": "Search live knowledge/catalog records",
                    "method": "GET",
                    "path": "/api/global/knowledge/search?q=adapter&limit=5",
                },
                {
                    "intent": "Inspect geometry/tarpit atom stats",
                    "method": "GET",
                    "path": "/api/global/geometry/read/tarpit-api/stats",
                },
                {
                    "intent": "Inspect unique-system coverage",
                    "method": "GET",
                    "path": "/api/global/geometry/read/unique-systems-api/summary",
                },
                {
                    "intent": "Check GitNexus indexed repos and aggregate report evidence",
                    "method": "GET",
                    "path": "/api/gitnexus/status",
                },
                {
                    "intent": "Search historical GitNexus report claims before promotion",
                    "method": "GET",
                    "path": "/api/gitnexus/aggregate/search?q=memory&limit=10",
                },
                {
                    "intent": "Inspect DevKit knowledge-ingest capability",
                    "method": "GET",
                    "path": "/api/global/knowledge/devkit-ingest",
                },
                {
                    "intent": "Inspect local MCP OS tool catalog",
                    "method": "GET",
                    "path": "/api/global/mcp/local-os",
                },
                {
                    "intent": "Inspect octa64 code-execution capability",
                    "method": "GET",
                    "path": "/api/global/code-execution/octa64",
                },
                {
                    "intent": "Inspect MCP OS validation suite catalog",
                    "method": "GET",
                    "path": "/api/global/validation/mcp-os",
                },
                {
                    "intent": "Inspect CQE modular synthesis capability",
                    "method": "GET",
                    "path": "/api/global/synthesis/cqe-modular",
                },
            ],
            "blocked_by_design": [
                "mutating upstream paths are blocked in the first routed slices",
                "research-api-jupyter is disabled evidence until it is explicitly fixed or removed",
                "GitNexus analyze/index/remove/augment/embed and write Cypher are blocked until an explicit refresh policy exists",
                "host port reassignment is deferred until routed slices are stable",
            ],
            "api_layer_needs": api_layer_needs,
            "use_rules": [
                "prefer /api/global/<system>/... over upstream localhost ports",
                "use /api/global-tool-workbook at the start of live work to refresh what is actually available",
                "treat 403 as an intentional safety block, not as a missing service",
                "treat 409 disabled upstreams as evidence that needs a runtime decision",
                "for repeated query params, encode them as key=value&key=value rather than a list string",
            ],
        }

    def _named_capability_inventory(self) -> list[dict[str, Any]]:
        return [
            {
                "system": "code-execution",
                "service": "repo-kernel-named-capability",
                "capability": "octa64",
                "control_endpoint": "/api/global/code-execution/octa64",
                "public_routes": [
                    "/api/global/code-execution/octa64",
                    "/api/global/code-execution/octa64/tree",
                    "/api/global/code-execution/octa64/files/{path}",
                    "/api/global/code-execution/octa64/call-plan",
                ],
                "read_paths": ["/", "/tree", "/files/pack.py", "/files/vm.py", "/files/executor.py"],
                "example": "/api/global/code-execution/octa64",
                "write_policy": "read-only and call-plan only",
                "status": "canonical_read_surface",
            },
            {
                "system": "knowledge",
                "service": "repo-kernel-named-capability",
                "capability": "devkit-ingest",
                "control_endpoint": "/api/global/knowledge/devkit-ingest",
                "public_routes": [
                    "/api/global/knowledge/devkit-ingest",
                    "/api/global/knowledge/devkit-ingest/tree",
                    "/api/global/knowledge/devkit-ingest/files/{path}",
                    "/api/global/knowledge/devkit-ingest/call-plan",
                ],
                "read_paths": [
                    "/",
                    "/tree",
                    "/files/ingest/ocr_pipeline.py",
                    "/files/ingest/embed_and_index.py",
                    "/files/scripts/qwen_pipeline_cli.ps1",
                ],
                "example": "/api/global/knowledge/devkit-ingest",
                "write_policy": "read-only and call-plan only",
                "status": "canonical_read_surface",
            },
            {
                "system": "mcp",
                "service": "repo-kernel-named-capability",
                "capability": "mcp-local-os",
                "control_endpoint": "/api/global/mcp/local-os",
                "public_routes": [
                    "/api/global/mcp/local-os",
                    "/api/global/mcp/local-os/tree",
                    "/api/global/mcp/local-os/files/{path}",
                    "/api/global/mcp/local-os/call-plan",
                ],
                "read_paths": [
                    "/",
                    "/tree",
                    "/files/MCP_OS_INVENTORY.md",
                    "/files/server/server.py",
                    "/files/server/tools.py",
                    "/files/client/client.py",
                ],
                "example": "/api/global/mcp/local-os",
                "write_policy": "read-only and call-plan only",
                "status": "canonical_read_surface",
            },
            {
                "system": "validation",
                "service": "repo-kernel-named-capability",
                "capability": "mcp-os-validation",
                "control_endpoint": "/api/global/validation/mcp-os",
                "public_routes": [
                    "/api/global/validation/mcp-os",
                    "/api/global/validation/mcp-os/tree",
                    "/api/global/validation/mcp-os/files/{path}",
                    "/api/global/validation/mcp-os/call-plan",
                ],
                "read_paths": ["/", "/tree", "/files/system_validator.py", "/files/runner.py", "/files/diagnostics.py"],
                "example": "/api/global/validation/mcp-os",
                "write_policy": "read-only and call-plan only",
                "status": "canonical_read_surface",
            },
            {
                "system": "synthesis",
                "service": "repo-kernel-named-capability",
                "capability": "cqe-modular",
                "control_endpoint": "/api/global/synthesis/cqe-modular",
                "public_routes": [
                    "/api/global/synthesis/cqe-modular",
                    "/api/global/synthesis/cqe-modular/tree",
                    "/api/global/synthesis/cqe-modular/files/{path}",
                    "/api/global/synthesis/cqe-modular/call-plan",
                ],
                "read_paths": ["/", "/tree", "/files/cqe_sdk.py", "/files/engine.py"],
                "example": "/api/global/synthesis/cqe-modular",
                "write_policy": "read-only and call-plan only",
                "status": "canonical_read_surface",
            },
        ]

    def compact_state(self, check_health: bool = False, timeout_seconds: float = 0.7) -> dict[str, Any]:
        workbook = self.tool_workbook(check_health=check_health, timeout_seconds=timeout_seconds, include_external_evidence=False)
        routed = workbook["routed_systems"]
        routed_names = {item["system"] for item in routed}
        live_tool_count_by_system: dict[str, int] = {}
        for tool in workbook["available_live_tools"]:
            live_tool_count_by_system[tool["system"]] = live_tool_count_by_system.get(tool["system"], 0) + 1
        ready = [item["system"] for item in routed if str(item.get("status", "")).startswith("ready")]
        disabled = [
            {"system": item["system"], "disabled_upstreams": item.get("disabled_upstreams", [])}
            for item in routed
            if item.get("disabled_upstreams")
        ]
        external_evidence = {}
        if self.prototype_evidence is not None:
            external_evidence = self.prototype_evidence.fast_summary()
        gitnexus_evidence = None
        if self.gitnexus is not None:
            aggregate = self.gitnexus.aggregate_summary()
            gitnexus_evidence = {
                "source": "gitnexus",
                "status": aggregate.get("status"),
                "total_reports": aggregate.get("total_reports"),
                "system_count": len(aggregate.get("by_system", [])),
                "route": "/api/gitnexus/status",
            }
        next_static = [
            system
            for system in ("ai-runtime", "validation", "synthesis", "external-ai-portal", "code-execution", "agent-orchestration", "mcp")
            if system not in routed_names
        ]
        return {
            "state": "global-control-compact",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "control_layer": workbook["control_layer"],
            "summary": {
                "routed_system_count": len(routed),
                "ready_system_count": len(ready),
                "available_live_tool_count": len(workbook["available_live_tools"]),
                "quick_use_count": len(workbook["quick_use"]),
                "disabled_upstream_count": sum(len(item.get("disabled_upstreams", [])) for item in routed),
            },
            "routed_systems": [
                {
                    "system": item["system"],
                    "status": item["status"],
                    "control_endpoint": item["control_endpoint"],
                    "upstream_count": item["upstream_count"],
                    "live_tool_count": live_tool_count_by_system.get(item["system"], 0),
                    "disabled_upstream_count": len(item.get("disabled_upstreams", [])),
                }
                for item in routed
            ],
            "external_evidence": {
                "source": external_evidence.get("source"),
                "status": external_evidence.get("status"),
                "root": external_evidence.get("root"),
                "bridge_file_count": external_evidence.get("bridge_file_count"),
                "docs_harvest_count": external_evidence.get("docs_harvest_count"),
                "superseded_wrapper_count": external_evidence.get("superseded_wrapper_count"),
                "detail": external_evidence.get("detail"),
            } if external_evidence else None,
            "gitnexus_evidence": gitnexus_evidence,
            "next_routing_candidates": next_static,
            "api_layer_needs": workbook["api_layer_needs"],
            "blocked_by_design": workbook["blocked_by_design"],
            "fast_paths": {
                "workbook": "/api/global-tool-workbook",
                "query": "/api/global/query?q=<term>",
                "runtime_slices_fast": "/api/global-runtime-slices?modules=CMPLXUNI&modules=CMPLX-TMN-main&limit=18",
            },
            "notes": [
                "compact state avoids all-repo coverage scans",
                "use full /api/global-coverage only when the longer scan is acceptable",
                "host port moves remain deferred",
            ],
        }

    def clean_system_image_plan(self) -> dict[str, Any]:
        routed_systems = [
            "memory",
            "knowledge",
            "geometry",
            "operations",
            "ai-runtime",
            "validation",
            "synthesis",
            "external-ai-portal",
            "mcp",
            "agent-orchestration",
            "code-execution",
        ]
        return {
            "plan": "clean-system-image",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "current_controller": {
                "status": "gathering_control_layer_complete_for_primary_runtime_queue",
                "service": "repo-kernel",
                "current_shape": "large monolithic FastAPI/MCP control file over clean repo checkouts and read-only live slices",
                "routed_systems": routed_systems,
                "evidence_sources": [
                    "repo_kernel/repos clean GitHub checkouts",
                    "live Docker services routed through /api/global/<system>",
                    "Claude Unification Prototypes read-only evidence",
                    "historical compose and docs catalogs",
                    "self-state SQLite ledgers",
                ],
            },
            "problems_to_resolve": [
                {
                    "problem": "controller_monolith",
                    "symptom": "server.py now mixes models, routes, adapters, workflow controllers, state, evidence, and policy",
                    "resolution": "split into package modules without changing public route contracts first",
                },
                {
                    "problem": "history_vs_runtime_confusion",
                    "symptom": "old wrappers, docs, compose files, and live services can look equally authoritative",
                    "resolution": "declare source truth levels and promotion gates before any rewrite",
                },
                {
                    "problem": "surface_scan_latency",
                    "symptom": "large MCP/agent/code surfaces can block full tool scans",
                    "resolution": "persist compact surface indexes and reserve deep scans for explicit endpoints",
                },
                {
                    "problem": "port_and_activation_ambiguity",
                    "symptom": "many historical ports exist, but only some are live and safe",
                    "resolution": "keep candidate ports as evidence until a health-proved runtime is selected",
                },
                {
                    "problem": "mutation_boundary_sprawl",
                    "symptom": "each controller has local write blocks and policy text",
                    "resolution": "centralize mutation policy enforcement and route classification",
                },
                {
                    "problem": "skill_conflict_and_duplication",
                    "symptom": "multiple repos define similar capabilities under different names",
                    "resolution": "promote capabilities into canonical contracts, preserving all repo evidence as implementations",
                },
            ],
            "target_architecture": {
                "package_layout": [
                    "repo_kernel_app/main.py - FastAPI/MCP assembly only",
                    "repo_kernel_app/models/ - request and response schemas",
                    "repo_kernel_app/routes/ - HTTP route modules by system",
                    "repo_kernel_app/mcp_tools/ - MCP mirror tool modules",
                    "repo_kernel_app/controllers/ - global workflow and system controllers",
                    "repo_kernel_app/adapters/ - repo, live-service, static, prototype, and promotion adapters",
                    "repo_kernel_app/systems/ - canonical memory/knowledge/mcp/etc contracts",
                    "repo_kernel_app/runtime/ - topology, health, activation, port ownership",
                    "repo_kernel_app/evidence/ - source universe, prototype evidence, docs/claims/compose indexes",
                    "repo_kernel_app/governance/ - mutation policy, promotion ledger, route allowlists",
                    "repo_kernel_app/state/ - self-state stores and durable compact indexes",
                ],
                "single_image_rule": "one new system image owns the canonical APIs, policies, state indexes, and adapters; old repos remain evidence/implementation sources until promoted or retired",
                "public_api_rule": "existing /api/global/<system> contracts stay stable while internal modules are split",
                "runtime_rule": "execution-capable runtimes require explicit activation selection, health proof, and mutation policy approval",
            },
            "source_truth_levels": [
                {"level": 1, "name": "live_control_contract", "meaning": "repo-kernel route contract or static adapter endpoint currently served"},
                {"level": 2, "name": "live_runtime_observation", "meaning": "running Docker service observed and read-proxied through repo-kernel"},
                {"level": 3, "name": "clean_repo_surface", "meaning": "static FastAPI/MCP/Next/compose surface extracted from repo_kernel/repos"},
                {"level": 4, "name": "prototype_evidence", "meaning": "Claude or archaeological merge outputs useful for claims, bridges, and gaps"},
                {"level": 5, "name": "historical_hint", "meaning": "README/docs/old compose/path references not yet proven live"},
            ],
            "promotion_lanes": [
                {
                    "lane": "contract_first_refactor",
                    "goal": "split server.py behind the same tests and routes",
                    "first_moves": [
                        "extract request models",
                        "extract PrototypeEvidenceBridge",
                        "extract GlobalSystemController live/static slice contracts",
                        "extract route registration into modules",
                    ],
                },
                {
                    "lane": "capability_canon",
                    "goal": "unify duplicated skills from all repos under canonical capability names",
                    "first_moves": [
                        "build capability registry from routed systems and prototype claims",
                        "map duplicate names to canonical capability ids",
                        "attach every repo implementation as evidence, not as a forked API",
                    ],
                },
                {
                    "lane": "runtime_canon",
                    "goal": "select real live runtimes for static slices",
                    "first_moves": [
                        "choose MCP runtime candidate",
                        "choose agent orchestration runtime candidate",
                        "choose code execution sandbox candidate",
                        "define auth-safe opencode status route",
                    ],
                },
                {
                    "lane": "index_and_cache",
                    "goal": "replace slow deep scans with durable compact indexes",
                    "first_moves": [
                        "persist route/tool/port summaries",
                        "persist prototype evidence counts",
                        "add invalidation on container restart or explicit refresh",
                    ],
                },
                {
                    "lane": "governed_execution",
                    "goal": "allow selected writes only after proof",
                    "first_moves": [
                        "centralize allowlist/denylist classification",
                        "require dry-run plan output for every mutating command",
                        "record approvals and rollback evidence in self-state",
                    ],
                },
            ],
            "new_system_image_definition": {
                "name": "cmplx-clean-control-image",
                "purpose": "a clean, governed, modular controller/runtime image that absorbs the best capabilities from prior repo states",
                "must_include": [
                    "stable global API",
                    "MCP mirror tools",
                    "repo module adapters",
                    "live service adapters",
                    "static activation adapters",
                    "prototype/history evidence ingestion",
                    "promotion ledger",
                    "self-state workfront",
                    "mutation policy enforcement",
                    "durable surface and claim indexes",
                ],
                "must_not_include": [
                    "direct execution of generated wrappers",
                    "implicit port reassignment",
                    "unapproved writes to source repos or databases",
                    "hardcoded historical paths as authority",
                    "slow all-surface scans in compact state endpoints",
                ],
            },
            "next_best_steps": [
                "extract the clean image plan into docs and API so both agents can coordinate from it",
                "create a durable capability registry from current /api/global-state, prototype claims, and routed system contracts",
                "start refactoring server.py by extracting models and prototype evidence first because they have low coupling",
                "add a compact surface-cache lane for MCP, agent orchestration, and code execution",
                "choose the first static slice runtime candidate for live promotion, likely MCP, but keep execution disabled until selected",
            ],
        }

    def capability_registry(self) -> dict[str, Any]:
        workbook = self.tool_workbook(check_health=False, timeout_seconds=0.7, include_external_evidence=False)
        capabilities = []
        service_index: dict[str, dict[str, Any]] = {}
        system_index: dict[str, list[str]] = {}
        for tool in workbook.get("available_live_tools", []):
            system = tool["system"]
            service = tool["service"]
            capability_id = self._capability_id(system, service)
            read_paths = tool.get("read_paths") or []
            status = tool.get("status")
            capability = {
                "id": capability_id,
                "canonical_name": capability_id.replace(".", "_"),
                "system": system,
                "service": service,
                "service_role": self._service_role(system, service, read_paths),
                "control_endpoint": tool.get("control_endpoint"),
                "example": tool.get("example"),
                "read_path_count": len(read_paths),
                "sample_read_paths": read_paths[:8],
                "source_truth_level": self._source_truth_level(status),
                "status": status,
                "safety": {
                    "read": "allowlisted paths only",
                    "write": tool.get("write_policy") or "blocked until explicitly promoted",
                },
                "promotion_state": "live_read_route" if status == "ready_for_control_route" else "static_or_disabled_evidence",
            }
            capabilities.append(capability)
            system_index.setdefault(system, []).append(capability_id)
            service_entry = service_index.setdefault(service, {"service": service, "systems": [], "capabilities": []})
            if system not in service_entry["systems"]:
                service_entry["systems"].append(system)
            service_entry["capabilities"].append(capability_id)

        shared_services = [
            {
                **entry,
                "systems": sorted(entry["systems"]),
                "canonicalization_need": "choose one canonical capability contract while preserving each system-specific route as an implementation",
            }
            for entry in service_index.values()
            if len(entry["systems"]) > 1
        ]
        shared_services.sort(key=lambda item: (-len(item["systems"]), item["service"]))
        capabilities.sort(key=lambda item: (item["system"], item["service"]))
        return {
            "registry": "global-capability-registry",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "current repo-kernel routed systems and static adapters",
            "summary": {
                "capability_count": len(capabilities),
                "system_count": len(system_index),
                "shared_service_count": len(shared_services),
                "prototype_evidence": self.prototype_evidence.fast_summary() if self.prototype_evidence is not None else None,
            },
            "systems": [
                {
                    "system": system,
                    "capability_count": len(ids),
                    "capabilities": sorted(ids),
                }
                for system, ids in sorted(system_index.items())
            ],
            "capabilities": capabilities,
            "shared_services": shared_services,
            "promotion_lanes": [
                {
                    "lane": "merge_shared_services",
                    "goal": "unify duplicate service capabilities behind canonical system contracts",
                    "first_targets": [item["service"] for item in shared_services[:6]],
                },
                {
                    "lane": "define_capability_ids",
                    "goal": "make every promoted ability addressable by a stable id before code is moved",
                    "first_targets": [item["id"] for item in capabilities[:10]],
                },
                {
                    "lane": "attach_best_implementation",
                    "goal": "select the best implementation from repo history without discarding alternate evidence",
                    "first_targets": ["prototype_claims", "repo_static_surfaces", "live_read_routes"],
                },
            ],
            "policy": {
                "not_a_refactor_yet": "this registry stages the clean image work without moving code",
                "source_truth": "live route contracts outrank live observations, which outrank repo surfaces, prototype evidence, and historical hints",
                "mutation": "capability promotion is planning-only until a promotion ledger entry and explicit approval exist",
            },
        }

    def _capability_id(self, system: str, service: str) -> str:
        safe_service = re.sub(r"[^a-z0-9]+", "-", service.lower()).strip("-")
        safe_system = re.sub(r"[^a-z0-9]+", "-", system.lower()).strip("-")
        return f"{safe_system}.{safe_service}"

    def _source_truth_level(self, status: str | None) -> dict[str, Any]:
        if status == "ready_for_control_route":
            return {"level": 1, "name": "live_control_contract"}
        if status == "ready_for_control_route_with_disabled_evidence":
            return {"level": 1, "name": "live_control_contract_with_disabled_evidence"}
        if status == "ready_for_static_control_route":
            return {"level": 3, "name": "clean_repo_surface_static_adapter"}
        return {"level": 5, "name": "historical_or_unclassified_hint"}

    def _service_role(self, system: str, service: str, read_paths: list[str]) -> str:
        haystack = " ".join([system, service, " ".join(read_paths)]).lower()
        roles = [
            ("memory", ["memory", "mmdb", "postgres", "receipt"]),
            ("knowledge", ["knowledge", "research", "catalog", "search", "report"]),
            ("geometry", ["geometry", "tarpit", "snap", "systems", "abilities"]),
            ("controller", ["repo-kernel", "operations", "gitnexus"]),
            ("ai_runtime", ["ai", "model", "manny", "manifold", "research-api"]),
            ("validation", ["validation", "speedlight", "health", "metrics"]),
            ("portal", ["ngrok", "portal", "opencode"]),
            ("mcp", ["mcp", "tool"]),
            ("agent_orchestration", ["agent", "orchestration", "spawn"]),
            ("code_execution", ["code", "execution", "sandbox"]),
        ]
        for role, needles in roles:
            if any(needle in haystack for needle in needles):
                return role
        return "general"

    def _memory_upstream(self, service: str) -> dict[str, Any]:
        for upstream in self._live_upstreams("memory"):
            if upstream.get("name") == service or upstream.get("service") == service:
                if not upstream.get("enabled", True):
                    raise HTTPException(409, f"memory upstream is disabled: {service}")
                return upstream
        raise HTTPException(404, f"unknown memory upstream: {service}")

    def _normalize_proxy_path(self, path: str) -> str:
        cleaned = (path or "").strip()
        if cleaned in {"", "."}:
            return "/"
        cleaned = cleaned.replace("\\", "/").lstrip("/")
        if "://" in cleaned or any(part == ".." for part in cleaned.split("/")):
            raise HTTPException(400, "invalid upstream path")
        return f"/{cleaned}"

    def _memory_allowed_paths(self, service: str) -> list[str]:
        if service in {"pocket-memory-api", "agenthub-db-bridge"}:
            return [
                "/",
                "/health",
                "/mcp/tools",
                "/search",
                "/ingest/status",
                "/discovery/checkpoints",
                "/restore",
                "/receipts",
                "/catalog/sql",
                "/catalog/reports",
                "/catalog/db",
                "/catalog/db/reports",
                "/catalog/code",
                "/catalog/code/stats",
                "/catalog/code/reports",
                "/catalog/doc",
                "/catalog/doc/reports",
            ]
        if service == "mmdb-unified":
            return ["/health", "/crystal/", "/search", "/stats", "/moonshine_feature", "/j_function"]
        if service == "mdhg-unified":
            return [
                "/health",
                "/graph/",
                "/depth/",
                "/session/",
                "/planet/observe/",
                "/planets",
                "/universes",
                "/dynamic/state/",
                "/chain/definition",
                "/chain/state/",
                "/extensions/health",
            ]
        return []

    def _memory_path_allowed(self, service: str, path: str) -> bool:
        allowed = self._memory_allowed_paths(service)
        return any(path == prefix or (prefix != "/" and prefix.endswith("/") and path.startswith(prefix)) for prefix in allowed)

    def _geometry_upstream(self, service: str) -> dict[str, Any]:
        for upstream in self._live_upstreams("geometry"):
            if upstream.get("name") == service or upstream.get("service") == service:
                if not upstream.get("enabled", True):
                    raise HTTPException(409, f"geometry upstream is disabled: {service}")
                return upstream
        raise HTTPException(404, f"unknown geometry upstream: {service}")

    def _geometry_allowed_paths(self, service: str) -> list[str]:
        if service == "snap-unified":
            return [
                "/health",
                "/taxonomy",
                "/angles",
                "/candidate",
                "/evidence",
                "/dna_snapshot",
                "/metrics/jaccard",
                "/metrics/leakage",
                "/metrics/entropy",
                "/snap_state",
            ]
        if service == "mdhg-unified":
            return self._memory_allowed_paths(service)
        if service == "tarpit-api":
            return ["/health", "/atoms", "/atoms/", "/stats"]
        if service == "unique-systems-api":
            return ["/", "/health", "/systems", "/systems/", "/abilities", "/promotion-states", "/summary"]
        return []

    def _geometry_path_allowed(self, service: str, path: str) -> bool:
        allowed = self._geometry_allowed_paths(service)
        return any(path == prefix or (prefix != "/" and prefix.endswith("/") and path.startswith(prefix)) for prefix in allowed)

    def _operations_upstream(self, service: str) -> dict[str, Any]:
        for upstream in self._live_upstreams("operations"):
            if upstream.get("name") == service or upstream.get("service") == service:
                if not upstream.get("enabled", True):
                    raise HTTPException(409, f"operations upstream is disabled: {service}")
                return upstream
        raise HTTPException(404, f"unknown operations upstream: {service}")

    def _operations_allowed_paths(self, service: str) -> list[str]:
        if service == "repo-kernel":
            return ["/", "/api/health"]
        if service == "gitnexus-rebuild-web":
            return ["/"]
        if service == "gitnexus-rebuild-server":
            return GitNexusBridge.READ_PATHS
        return []

    def _operations_path_allowed(self, service: str, path: str) -> bool:
        allowed = self._operations_allowed_paths(service)
        return any(path == prefix or (prefix != "/" and prefix.endswith("/") and path.startswith(prefix)) for prefix in allowed)

    def _repo_kernel_self_read(self, path: str) -> dict[str, Any]:
        if path == "/":
            data = {
                "kernel": KERNEL_ID,
                "modules": len(self.registry.modules()),
                "api": [
                    "/api/health",
                    "/api/global-runtime-slices",
                    "/api/global/memory/upstreams",
                    "/api/global/geometry/upstreams",
                    "/api/global/operations/upstreams",
                ],
            }
        elif path == "/api/health":
            modules = self.registry.modules()
            data = {
                "ok": True,
                "kernel": KERNEL_ID,
                "manifest": str(MANIFEST_PATH),
                "repos_root": str(REPOS_ROOT),
                "module_count": len(modules),
                "cloned_count": sum(1 for module in modules if module.get("cloned")),
                "allow_mutation": ALLOW_MUTATION,
            }
        else:
            raise HTTPException(403, f"repo-kernel self path is not approved: {path}")
        return {
            "system": "operations",
            "service": "repo-kernel",
            "method": "GET",
            "path": path,
            "url": f"self:{path}",
            "ok": True,
            "status": 200,
            "content_type": "application/json",
            "data": data,
            "error": None,
            "policy": "synthetic self-read through repo-kernel; no recursive HTTP call",
        }

    def _knowledge_upstream(self, service: str) -> dict[str, Any]:
        for upstream in self._live_upstreams("knowledge"):
            if upstream.get("name") == service or upstream.get("service") == service:
                if not upstream.get("enabled", True):
                    raise HTTPException(409, f"knowledge upstream is disabled: {service}")
                return upstream
        raise HTTPException(404, f"unknown knowledge upstream: {service}")

    def _knowledge_allowed_paths(self, service: str) -> list[str]:
        if service == "research-api":
            return ["/health"]
        if service == "db-aggregator-api":
            return [
                "/",
                "/health",
                "/mcp/tools",
                "/search",
                "/ingest/status",
                "/discovery/checkpoints",
                "/restore",
                "/receipts",
                "/catalog/sql",
                "/catalog/reports",
                "/catalog/db",
                "/catalog/db/reports",
                "/catalog/code",
                "/catalog/code/stats",
                "/catalog/code/reports",
                "/catalog/doc",
                "/catalog/doc/reports",
            ]
        return []

    def _knowledge_path_allowed(self, service: str, path: str) -> bool:
        allowed = self._knowledge_allowed_paths(service)
        return any(path == prefix or (prefix != "/" and prefix.endswith("/") and path.startswith(prefix)) for prefix in allowed)

    def _live_slice_upstream(self, system: str, service: str) -> dict[str, Any]:
        for upstream in self._live_upstreams(system):
            if upstream.get("name") == service or upstream.get("service") == service:
                if not self._slice_upstream_enabled(system, upstream):
                    raise HTTPException(409, f"{system} upstream is disabled: {service}")
                return upstream
        raise HTTPException(404, f"unknown {system} upstream: {service}")

    def _slice_upstream_enabled(self, system: str, upstream: dict[str, Any]) -> bool:
        if not upstream.get("enabled", True):
            return False
        if system == "external-ai-portal" and upstream.get("name") == "opencode-session":
            return False
        return True

    def _live_slice_allowed_paths(self, system: str, service: str) -> list[str]:
        if system == "ai-runtime":
            if service == "research-api":
                return ["/health"]
            if service == "manny-manifold-api":
                return ["/", "/health", "/status", "/metrics", "/models", "/models/"]
        if system == "validation":
            if service == "speedlight-api":
                return ["/", "/health", "/status", "/metrics", "/summary", "/reports", "/reports/"]
            if service == "db-aggregator-api":
                return self._knowledge_allowed_paths(service)
        if system == "synthesis":
            if service == "manny-manifold-api":
                return ["/", "/health", "/status", "/metrics", "/models", "/models/"]
            if service == "unique-systems-api":
                return ["/", "/health", "/systems", "/systems/", "/abilities", "/promotion-states", "/summary"]
        if system == "external-ai-portal":
            if service == "ngrok-cmplx":
                return ["/", "/status", "/api/tunnels", "/api/tunnels/"]
            if service == "opencode-session":
                return []
        return []

    def _live_slice_path_allowed(self, system: str, service: str, path: str) -> bool:
        allowed = self._live_slice_allowed_paths(system, service)
        return any(path == prefix or (prefix != "/" and prefix.endswith("/") and path.startswith(prefix)) for prefix in allowed)

    def _live_slice_api_layer_needs(self, system: str, disabled: list[dict[str, Any]]) -> list[dict[str, Any]]:
        needs = [
            {
                "area": f"{system}_canonical_response",
                "need": f"normalize {system} read responses after the first safe upstream paths are exercised",
                "current_bridge": f"GET /api/global/{system}/read/{{service}}/{{path}}",
            }
        ]
        if system == "external-ai-portal":
            needs.append({
                "area": "portal_auth_contract",
                "need": "define an auth-safe status path for opencode-session before proxying it through repo-kernel",
                "current_bridge": "opencode-session disabled evidence",
            })
        if disabled:
            needs.append({
                "area": f"{system}_disabled_evidence",
                "need": "decide whether disabled upstreams should be fixed, authenticated, or removed from the live map",
                "current_bridge": ", ".join(str(item.get("name")) for item in disabled),
            })
        return needs

    def _static_adapter_read(self, system: str, path: str) -> dict[str, Any]:
        if path not in {"/", "/summary", "/ports", "/activation-candidates"}:
            raise HTTPException(403, f"static adapter path is not approved for {system}: {path}")
        contract = self.static_adapter_routing_contract(system)
        if path in {"/", "/summary"}:
            data = {
                "system": system,
                "control_endpoint": contract["control_endpoint"],
                "status": contract["status"],
                "adapter": contract["upstreams"][0],
                "activation_candidate_count": len(contract.get("activation_candidates", [])),
                "public_routes": contract["public_routes"],
                "api_layer_needs": contract["api_layer_needs"],
                "policy": contract["policy"],
            }
        elif path == "/ports":
            data = self.ports(system)
        else:
            data = {
                "system": system,
                "activation_candidates": contract.get("activation_candidates", []),
                "selection_policy": "choose one candidate only after health proof and explicit activation approval",
            }
        return {
            "system": system,
            "service": "repo-kernel-adapter",
            "method": "GET",
            "path": path,
            "url": f"self:/api/global/{system}/read/repo-kernel-adapter{path}",
            "ok": True,
            "status": 200,
            "content_type": "application/json",
            "data": data,
            "error": None,
            "policy": "static adapter read through repo-kernel; no tool execution or runtime activation",
        }

    def _global_query_try(
        self,
        source: str,
        call: Any,
        results: list[dict[str, Any]],
        context: list[dict[str, Any]],
        errors: list[dict[str, Any]],
        req: GlobalQueryRequest,
    ) -> None:
        try:
            payload = call()
            normalized = self._normalize_global_query_result(source, payload, req)
            results.extend(normalized["results"])
            context.extend(normalized["context"])
        except HTTPException as exc:
            errors.append({"source": source, "status": exc.status_code, "error": exc.detail})
        except Exception as exc:
            errors.append({"source": source, "status": "error", "error": str(exc)[:300]})

    def _normalize_global_query_result(self, source: str, payload: dict[str, Any], req: GlobalQueryRequest) -> dict[str, list[dict[str, Any]]]:
        if source == "gitnexus_reports":
            results = []
            for item in (payload or {}).get("results", [])[:req.limit]:
                results.append(self._canonical_query_record(
                    system="knowledge",
                    source="gitnexus-aggregate-db",
                    kind="historical_report",
                    title=item.get("name") or item.get("source_path"),
                    matched_field="gitnexus_report",
                    summary=item.get("capability_summary"),
                    confidence=0.45,
                    local_refs=[item.get("source_path")] if item.get("source_path") else [],
                    payload=item,
                ))
            return {"results": results, "context": []}
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            return {"results": [], "context": []}
        query = req.q.lower()
        results: list[dict[str, Any]] = []
        context: list[dict[str, Any]] = []

        if source == "memory":
            for item in data.get("matches", [])[:req.limit]:
                row = item.get("row", {})
                title = row.get("capability_name") or row.get("source_name") or item.get("table")
                results.append(self._canonical_query_record(
                    system="memory",
                    source=payload.get("service"),
                    kind=item.get("table"),
                    title=title,
                    matched_field=item.get("column"),
                    summary=row.get("implementation") or row.get("description") or row.get("notes"),
                    confidence=row.get("confidence"),
                    local_refs=self._extract_local_refs(row.get("file_refs")),
                    payload=row,
                ))
        elif source == "knowledge":
            for item in data.get("sources", [])[:req.limit]:
                results.append(self._canonical_query_record(
                    system="knowledge",
                    source=payload.get("service"),
                    kind=item.get("artifact_kind"),
                    title=item.get("relative_path") or item.get("source_uri"),
                    matched_field="source",
                    summary=item.get("source_uri"),
                    confidence=None,
                    local_refs=[item.get("relative_path")] if item.get("relative_path") else [],
                    payload=item,
                ))
            for group in ("tables", "manifests", "claims"):
                for item in data.get(group, [])[:req.limit]:
                    results.append(self._canonical_query_record(
                        system="knowledge",
                        source=payload.get("service"),
                        kind=group,
                        title=item.get("name") or item.get("source_uri") or group,
                        matched_field=group,
                        summary=item.get("description") or item.get("source_uri"),
                        confidence=item.get("confidence"),
                        local_refs=[item.get("relative_path")] if item.get("relative_path") else [],
                        payload=item,
                    ))
        elif source == "prototype_claims":
            for item in data.get("matches", [])[:req.limit]:
                results.append(self._canonical_query_record(
                    system="knowledge",
                    source="claude-unification-prototypes",
                    kind=item.get("kind"),
                    title=item.get("title") or item.get("relative_path"),
                    matched_field=item.get("matched_field"),
                    summary=item.get("summary"),
                    confidence=item.get("confidence"),
                    local_refs=[item.get("relative_path")] if item.get("relative_path") else [],
                    payload=item,
                ))
        elif source == "geometry_tarpit":
            labels = data.get("top_labels", {})
            label_hits = {key: value for key, value in labels.items() if query in str(key).lower()}
            item = self._canonical_query_record(
                system="geometry",
                source=payload.get("service"),
                kind="tarpit_stats",
                title=f"{data.get('atoms')} tarpit atoms",
                matched_field="top_labels" if label_hits else "context",
                summary=f"Top labels: {', '.join(list(labels)[:8])}",
                confidence=None,
                local_refs=[],
                payload={"atoms": data.get("atoms"), "label_hits": label_hits, "sources": data.get("sources")},
            )
            if label_hits:
                results.append(item)
            elif req.include_context:
                context.append(item)
        elif source == "geometry_unique_systems":
            blob = json.dumps(data, ensure_ascii=False).lower()
            item = self._canonical_query_record(
                system="geometry",
                source=payload.get("service"),
                kind="unique_system_summary",
                title=f"{data.get('systems')} unique systems",
                matched_field="summary" if query in blob else "context",
                summary=f"{data.get('sources_present')} sources present, {data.get('sources_missing')} missing",
                confidence=data.get("sources_present"),
                local_refs=data.get("evidence_sources") or [],
                payload=data,
            )
            if query in blob:
                results.append(item)
            elif req.include_context:
                context.append(item)
        elif source == "operations":
            item = self._canonical_query_record(
                system="operations",
                source=payload.get("service"),
                kind="controller_health",
                title=f"{data.get('kernel')} health",
                matched_field="context",
                summary=f"{data.get('cloned_count')} cloned modules; mutation allowed={data.get('allow_mutation')}",
                confidence=data.get("module_count"),
                local_refs=[data.get("manifest"), data.get("repos_root")],
                payload=data,
            )
            if req.include_context:
                context.append(item)
        return {"results": results, "context": context}

    def _canonical_query_record(
        self,
        system: str,
        source: str | None,
        kind: str | None,
        title: Any,
        matched_field: str | None,
        summary: Any,
        confidence: Any,
        local_refs: list[Any] | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        clean_title = str(title or kind or source or system)
        clean_summary = str(summary or "")[:1200]
        refs = [str(ref) for ref in (local_refs or []) if ref]
        key = self._query_record_key(system, source, kind, clean_title, payload, refs)
        return {
            "id": hashlib.sha256("|".join(key).encode("utf-8", errors="replace")).hexdigest()[:16],
            "system": system,
            "source": source,
            "kind": kind,
            "title": clean_title,
            "summary": clean_summary,
            "matched_field": matched_field,
            "confidence": self._numeric_confidence(confidence),
            "score": 0.0,
            "local_refs": refs,
            "raw": payload,
        }

    def _query_record_key(
        self,
        system: str,
        source: str | None,
        kind: str | None,
        title: str,
        payload: dict[str, Any],
        refs: list[str],
    ) -> tuple[str, str, str, str, str]:
        raw_id = payload.get("id") or payload.get("source_uri") or payload.get("relative_path") or payload.get("name") or ""
        if not raw_id and refs:
            raw_id = refs[0]
        return (system, str(source or ""), str(kind or ""), title.lower().strip(), str(raw_id).lower().strip())

    def _numeric_confidence(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return round(float(value), 4)
        except (TypeError, ValueError):
            return None

    def _extract_local_refs(self, value: Any) -> list[str]:
        if not value:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if item]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed if item]
            except json.JSONDecodeError:
                pass
            return [value]
        return [str(value)]

    def _dedupe_global_query_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}
        for record in records:
            key = record.get("id") or hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()[:16]
            existing = deduped.get(key)
            if not existing:
                deduped[key] = record
                continue
            existing_refs = set(existing.get("local_refs", []))
            for ref in record.get("local_refs", []):
                if ref not in existing_refs:
                    existing.setdefault("local_refs", []).append(ref)
            if len(str(record.get("summary") or "")) > len(str(existing.get("summary") or "")):
                existing["summary"] = record.get("summary")
            if (record.get("confidence") or 0) > (existing.get("confidence") or 0):
                existing["confidence"] = record.get("confidence")
        return list(deduped.values())

    def _rank_global_query_records(self, records: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        needle = query.lower()
        system_weight = {"memory": 8, "knowledge": 7, "geometry": 5, "operations": 2}
        for record in records:
            haystack = " ".join([
                str(record.get("title") or ""),
                str(record.get("summary") or ""),
                json.dumps(record.get("local_refs", []), ensure_ascii=False),
            ]).lower()
            score = system_weight.get(record.get("system"), 1)
            if needle and needle in str(record.get("title", "")).lower():
                score += 30
            if needle and needle in str(record.get("summary", "")).lower():
                score += 15
            if needle and any(needle in str(ref).lower() for ref in record.get("local_refs", [])):
                score += 10
            confidence = record.get("confidence")
            if isinstance(confidence, (int, float)):
                score += min(float(confidence), 10.0)
            score += min(len(record.get("local_refs", [])), 5)
            if needle and needle not in haystack and record.get("matched_field") == "context":
                score -= 5
            record["score"] = round(score, 4)
        return sorted(
            records,
            key=lambda item: (
                item.get("score") or 0,
                str(item.get("system") or ""),
                str(item.get("title") or ""),
            ),
            reverse=True,
        )

    def _workbook_example(self, system: str, service: str, read_paths: list[str]) -> str | None:
        preferred = {
            ("memory", "pocket-memory-api"): "/api/global/memory/search?q=receipt&limit=5",
            ("memory", "mmdb-unified"): "/api/global/memory/read/mmdb-unified/stats",
            ("geometry", "tarpit-api"): "/api/global/geometry/read/tarpit-api/stats",
            ("geometry", "unique-systems-api"): "/api/global/geometry/read/unique-systems-api/summary",
            ("operations", "repo-kernel"): "/api/global/operations/read/repo-kernel/api/health",
            ("operations", "gitnexus-rebuild-web"): "/api/global/operations/read/gitnexus-rebuild-web/",
            ("knowledge", "db-aggregator-api"): "/api/global/knowledge/search?q=adapter&limit=5",
            ("knowledge", "research-api"): "/api/global/knowledge/read/research-api/health",
            ("ai-runtime", "research-api"): "/api/global/ai-runtime/read/research-api/health",
            ("ai-runtime", "manny-manifold-api"): "/api/global/ai-runtime/read/manny-manifold-api/health",
            ("validation", "speedlight-api"): "/api/global/validation/read/speedlight-api/health",
            ("validation", "db-aggregator-api"): "/api/global/validation/read/db-aggregator-api/health",
            ("synthesis", "manny-manifold-api"): "/api/global/synthesis/read/manny-manifold-api/health",
            ("synthesis", "unique-systems-api"): "/api/global/synthesis/read/unique-systems-api/summary",
            ("external-ai-portal", "ngrok-cmplx"): "/api/global/external-ai-portal/read/ngrok-cmplx/api/tunnels",
        }
        if (system, service) in preferred:
            return preferred[(system, service)]
        if not read_paths:
            return None
        path = read_paths[0].strip("/")
        return f"/api/global/{system}/read/{service}/{path}"

    def _read_proxy(
        self,
        system: str,
        service: str,
        normalized_path: str,
        upstream: dict[str, Any],
        query: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if upstream.get("runtime_kind") in {"tcp", "postgres", "redis"}:
            raise HTTPException(400, f"{service} is not an HTTP {system} upstream")
        base_url = self._runtime_base_url(upstream)
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            raise HTTPException(400, f"{service} has no HTTP base URL")
        url = f"{base_url}{normalized_path}"
        clean_query = {key: value for key, value in (query or {}).items() if key not in {"service", "path"}}
        if clean_query:
            url = f"{url}?{urllib.parse.urlencode(clean_query, doseq=True)}"
        result = {
            "system": system,
            "service": service,
            "method": "GET",
            "path": normalized_path,
            "url": url,
            "ok": False,
            "status": None,
            "content_type": None,
            "data": None,
            "error": None,
            "policy": f"read-only proxy through repo-kernel; no upstream {system} port move",
        }
        try:
            req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json, text/plain;q=0.8, */*;q=0.5"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                raw = resp.read(500_000)
                result["status"] = resp.status
                result["ok"] = 200 <= resp.status < 500
                result["content_type"] = resp.headers.get("content-type")
                result["data"] = self._decode_proxy_response(raw, result["content_type"])
        except urllib.error.HTTPError as exc:
            raw = exc.read(200_000)
            result["status"] = exc.code
            result["ok"] = exc.code < 500
            result["content_type"] = exc.headers.get("content-type")
            result["data"] = self._decode_proxy_response(raw, result["content_type"])
        except Exception as exc:
            result["error"] = str(exc)[:300]
        return result

    def _decode_proxy_response(self, raw: bytes, content_type: str | None) -> Any:
        text = raw.decode("utf-8", errors="replace")
        if content_type and "json" in content_type.lower():
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text[:20_000]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text[:20_000]

    def _global_api(self, base: str) -> list[str]:
        return [
            f"GET {base}",
            f"GET {base}/tools",
            f"GET {base}/routes",
            f"GET {base}/ports",
            f"GET {base}/skills",
            f"POST {base}/call-plan",
        ]

    def _live_upstreams(self, system: str) -> list[dict[str, Any]]:
        upstreams = []
        for upstream in self.LIVE_UPSTREAMS.get(system, []):
            item = dict(upstream)
            item.setdefault("service", item.get("name"))
            item["system"] = system
            item["control_base"] = self.SYSTEMS[system]["canonical_base"]
            item["public_url"] = item.get("url")
            item["routing_status"] = "live_upstream_observed_not_moved" if item.get("enabled", True) else "observed_disabled_not_routable"
            upstreams.append(item)
        return upstreams

    def _runtime_base_url(self, upstream: dict[str, Any]) -> str:
        if Path("/.dockerenv").exists():
            name = upstream.get("container_name") or upstream.get("name") or upstream.get("service")
            port = upstream.get("container_port") or upstream.get("host_port")
            if upstream.get("runtime_kind") in {"tcp", "postgres", "redis"}:
                return f"tcp://{name}:{port}"
            return f"http://{name}:{port}"
        return str(upstream.get("url") or "")

    def _runtime_health_target(self, system: str, upstream: dict[str, Any]) -> dict[str, Any]:
        target = dict(upstream)
        target.setdefault("service", target.get("name"))
        target.setdefault("module", "docker-runtime")
        target.setdefault("runtime_kind", "http")
        target["system"] = system
        if Path("/.dockerenv").exists():
            name = target.get("container_name") or target.get("name") or target.get("service")
            port = target.get("container_port") or target.get("host_port")
            if target.get("runtime_kind") in {"tcp", "postgres", "redis"}:
                target["url"] = f"tcp://{name}:{port}"
                target["host_port"] = port
            elif name and port:
                health_path = target.get("health_path")
                health_url = target.get("health_url")
                if not health_path and health_url:
                    parsed = urllib.parse.urlparse(str(health_url))
                    health_path = parsed.path or "/"
                    if parsed.query:
                        health_path = f"{health_path}?{parsed.query}"
                health_path = health_path or "/health"
                target["url"] = f"http://{name}:{port}"
                target["health_url"] = target.get("container_health_url") or f"http://{name}:{port}{health_path}"
        return target

    def _runtime_slice_status(
        self,
        upstreams: list[dict[str, Any]],
        check_health: bool,
        healthy_count: int,
        unhealthy_count: int,
    ) -> tuple[str, str]:
        if not upstreams:
            return (
                "static_mapping_only",
                "keep the global API lane mapped and identify or start a concrete runtime upstream for this system",
            )
        if not check_health:
            return (
                "candidate_needs_health_check",
                "health-check the listed upstreams, then bind them behind the global control endpoint",
            )
        if healthy_count and not unhealthy_count:
            return (
                "ready_for_control_route",
                "bind these upstreams behind the global control endpoint while preserving current host ports",
            )
        if healthy_count:
            return (
                "partial_health",
                "route the healthy upstreams first and mark failed upstreams as follow-up fixes",
            )
        return (
            "needs_runtime_fix",
            "fix or replace the live upstreams before making this system the next routed slice",
        )

    def _runtime_slice_score(
        self,
        system: str,
        surface_count: int,
        upstreams: list[dict[str, Any]],
        check_health: bool,
        healthy_count: int,
        unhealthy_count: int,
    ) -> float:
        priority = {
            "memory": 120,
            "knowledge": 105,
            "geometry": 95,
            "ai-runtime": 90,
            "validation": 85,
            "synthesis": 80,
            "operations": 60,
            "external-ai-portal": 35,
        }.get(system, 20)
        health_score = healthy_count * 30 - unhealthy_count * 15 if check_health else 0
        return round(priority + min(surface_count, 1000) / 20 + len(upstreams) * 18 + health_score, 2)

    def _config(self, system: str) -> dict[str, Any]:
        if system not in self.SYSTEMS:
            raise HTTPException(404, f"unknown global system: {system}")
        return self.SYSTEMS[system]


class AgentOrchestrationWorkflowController:
    ROLE_KEYWORDS = {
        "identity": ["identity", "persona", "profile"],
        "cooperation": ["coop", "collab", "coordinate"],
        "daemon": ["daemon", "worker", "background"],
        "thinktank": ["thinktank", "brain", "arena", "reason"],
        "spawn": ["spawn", "agent", "orchestration"],
        "station": ["station", "portal", "gateway"],
    }

    MUTATING_WORDS = {"spawn", "create", "register", "assign", "start", "stop", "delete", "update", "launch"}

    def __init__(self, unified: UnifiedAIWorkflowRegistry, topology: RuntimeTopology):
        self.unified = unified
        self.topology = topology

    def capabilities(self) -> dict[str, Any]:
        workflow = self.unified.workflow("agent_orchestration")
        routes = []
        tools = []
        runtime_targets = []
        role_index: dict[str, dict[str, Any]] = {
            role: {"routes": 0, "mcp_tools": 0, "runtime_targets": 0, "services": []}
            for role in self.ROLE_KEYWORDS
        }
        for entry in workflow.get("entries", []):
            module = entry["module"]
            for route in entry.get("routes", []):
                item = {**route, "module": module, "safety": self._safety(route)}
                routes.append(item)
                self._add_to_roles(role_index, item, "routes")
            for tool in entry.get("mcp_tools", []):
                item = {**tool, "module": module, "safety": self._safety(tool)}
                tools.append(item)
                self._add_to_roles(role_index, item, "mcp_tools")
            for target in entry.get("runtime_targets", []):
                item = {**target, "module": module, "evidence_role": "compose_or_readme_runtime_hint"}
                runtime_targets.append(item)
                roles = self._roles_for(item)
                for role in roles:
                    role_index[role]["runtime_targets"] += 1
                    service = item.get("service")
                    if service and service not in role_index[role]["services"]:
                        role_index[role]["services"].append(service)

        return {
            "workflow": "agent_orchestration",
            "base_path": "/api/unified/agent-orchestration",
            "route_count": len(routes),
            "mcp_tool_count": len(tools),
            "runtime_target_count": len(runtime_targets),
            "roles": role_index,
            "routes": routes,
            "mcp_tools": tools,
            "runtime_targets": runtime_targets,
            "policy": {
                "execution": "dry-run planning only",
                "compose": "service names and ports are evidence/preflight hints",
                "fallback": "static adapter surfaces before live agent mutation",
                "writes": "spawn/register/start operations require explicit approval",
            },
        }

    def plan(self, req: AgentOrchestrationPlanRequest) -> dict[str, Any]:
        caps = self.capabilities()
        q = " ".join(part for part in [req.intent, req.role or ""] if part).lower()
        modules = {req.prefer_module} if req.prefer_module else None
        routes = [
            route for route in caps["routes"]
            if self._matches_query(route, q) and (not modules or route.get("module") in modules)
        ]
        tools = [
            tool for tool in caps["mcp_tools"]
            if self._matches_query(tool, q) and (not modules or tool.get("module") in modules)
        ]
        runtime_targets = [
            target for target in caps["runtime_targets"]
            if self._matches_query(target, q) and (not modules or target.get("module") in modules)
        ]
        if not runtime_targets and req.role:
            roles = self._role_keywords(req.role)
            runtime_targets = [
                target for target in caps["runtime_targets"]
                if any(token in json.dumps(target).lower() for token in roles)
                and (not modules or target.get("module") in modules)
            ]
        health = self.topology.health_check_targets(runtime_targets, timeout_seconds=0.5, limit=20)
        mutating = any(item.get("safety") == "mutating" for item in routes + tools) or any(word in q for word in self.MUTATING_WORDS)
        return {
            "workflow": "agent_orchestration",
            "operation": "plan",
            "request": req.model_dump(),
            "selected_strategy": "compose_evidence_plus_static_surfaces_then_health_checked_runtime",
            "role_candidates": self._roles_for({"name": q, "service": q}),
            "route_candidates": routes[:30],
            "tool_candidates": tools[:30],
            "runtime_candidates": runtime_targets[:30],
            "health": health,
            "mutating": mutating,
            "execution": "not executed; dry_run requested" if req.dry_run else "not executed; live agent orchestration remains approval-gated",
        }

    def _add_to_roles(self, role_index: dict[str, dict[str, Any]], item: dict[str, Any], bucket: str) -> None:
        for role in self._roles_for(item):
            role_index[role][bucket] += 1

    def _roles_for(self, item: dict[str, Any]) -> list[str]:
        haystack = json.dumps(item, ensure_ascii=False).lower()
        roles = []
        for role, keywords in self.ROLE_KEYWORDS.items():
            if any(keyword in haystack for keyword in keywords):
                roles.append(role)
        return roles

    def _role_keywords(self, role: str) -> list[str]:
        role = role.lower()
        return self.ROLE_KEYWORDS.get(role, [role])

    def _matches_query(self, item: dict[str, Any], query: str) -> bool:
        if not query:
            return True
        haystack = json.dumps(item, ensure_ascii=False).lower()
        tokens = [token for token in re.split(r"[^a-z0-9_]+", query) if len(token) > 2]
        return not tokens or any(token in haystack for token in tokens)

    def _safety(self, item: dict[str, Any]) -> str:
        haystack = json.dumps(item, ensure_ascii=False).lower()
        if any(word in haystack for word in self.MUTATING_WORDS):
            return "mutating"
        if any(word in haystack for word in ["get", "list", "query", "inspect", "status", "health"]):
            return "read"
        return "unknown"


class KnowledgeWorkflowController:
    ROLE_KEYWORDS = {
        "library": ["library", "archive", "document", "paper", "corpus", "dataset"],
        "query": ["query", "search", "retrieve", "lookup", "recall", "find"],
        "semantic": ["semantic", "embedding", "vector", "similarity", "rank"],
        "kb": ["kb", "knowledge", "graph", "taxonomy", "ontology"],
        "code_context": ["code", "symbol", "module", "repo"],
        "ingestion": ["ingest", "harvest", "index", "extract", "parse", "crawl"],
        "atlas": ["atlas", "map", "navigation", "blackboard"],
    }

    READ_WORDS = {"get", "list", "query", "search", "retrieve", "lookup", "find", "inspect", "status", "health"}
    MUTATING_WORDS = {
        "add",
        "create",
        "delete",
        "drop",
        "harvest",
        "index",
        "ingest",
        "insert",
        "load",
        "patch",
        "remove",
        "store",
        "sync",
        "train",
        "update",
        "upsert",
        "write",
    }

    def __init__(self, unified: UnifiedAIWorkflowRegistry, topology: RuntimeTopology):
        self.unified = unified
        self.topology = topology

    def capabilities(self) -> dict[str, Any]:
        workflow = self.unified.workflow("knowledge")
        routes = []
        tools = []
        runtime_targets = []
        role_index: dict[str, dict[str, Any]] = {
            role: {"routes": 0, "mcp_tools": 0, "runtime_targets": 0, "services": [], "modules": []}
            for role in self.ROLE_KEYWORDS
        }

        for entry in workflow.get("entries", []):
            module = entry["module"]
            for route in entry.get("routes", []):
                item = {**route, "module": module, "safety": self._safety(route)}
                item["roles"] = self._roles_for(item)
                routes.append(item)
                self._add_to_roles(role_index, item, "routes", module=module)
            for tool in entry.get("mcp_tools", []):
                item = {**tool, "module": module, "safety": self._safety(tool)}
                item["roles"] = self._roles_for(item)
                tools.append(item)
                self._add_to_roles(role_index, item, "mcp_tools", module=module)
            for target in entry.get("runtime_targets", []):
                item = {**target, "module": module, "evidence_role": "compose_or_readme_runtime_hint"}
                item["roles"] = self._roles_for(item)
                runtime_targets.append(item)
                self._add_to_roles(role_index, item, "runtime_targets", module=module)
                service = item.get("service")
                for role in item["roles"]:
                    if service and service not in role_index[role]["services"]:
                        role_index[role]["services"].append(service)

        return {
            "workflow": "knowledge",
            "base_path": "/api/unified/knowledge",
            "route_count": len(routes),
            "mcp_tool_count": len(tools),
            "runtime_target_count": len(runtime_targets),
            "roles": role_index,
            "routes": routes,
            "mcp_tools": tools,
            "runtime_targets": runtime_targets,
            "agentic_use": {
                "purpose": "Give Codex and other local agents a fast planning surface for search, retrieval, KB, corpus, and semantic/code context work.",
                "best_first_calls": [
                    "GET /api/unified/knowledge/capabilities",
                    "POST /api/unified/knowledge/plan",
                    "GET /api/unified/knowledge/runtime-preflight",
                ],
                "offload_pattern": "Ask repo-kernel for candidate routes/tools/runtime hints, then do bounded reads or adapter calls instead of broad recursive scans.",
            },
            "policy": {
                "execution": "dry-run planning only",
                "compose": "service names and ports are evidence/preflight hints",
                "fallback": "static adapter surfaces before live search/index mutation",
                "writes": "index/ingest/store/update operations require explicit approval",
            },
        }

    def plan(self, req: KnowledgePlanRequest) -> dict[str, Any]:
        caps = self.capabilities()
        query = " ".join(part for part in [req.task, req.query or "", req.role or ""] if part).lower()
        modules = {req.prefer_module} if req.prefer_module else None
        roles = self._role_keywords(req.role) if req.role else []

        routes = [
            route for route in caps["routes"]
            if self._matches_query_or_role(route, query, roles)
            and (not modules or route.get("module") in modules)
        ]
        tools = [
            tool for tool in caps["mcp_tools"]
            if self._matches_query_or_role(tool, query, roles)
            and (not modules or tool.get("module") in modules)
        ]
        runtime_targets = [
            target for target in caps["runtime_targets"]
            if self._matches_query_or_role(target, query, roles)
            and (not modules or target.get("module") in modules)
        ]
        if not runtime_targets and (roles or modules):
            runtime_targets = [
                target for target in caps["runtime_targets"]
                if (not roles or any(role in target.get("roles", []) for role in roles))
                and (not modules or target.get("module") in modules)
            ]

        health = self.topology.health_check_targets(runtime_targets, timeout_seconds=0.5, limit=20)
        mutating = any(item.get("safety") == "mutating" for item in routes + tools) or any(word in query for word in self.MUTATING_WORDS)
        suggested_first_steps = [
            "Use read/search candidates before any indexing or ingestion route.",
            "Prefer static adapter surfaces when runtime health is unknown or unhealthy.",
            "Keep corpus intake bounded by module/source and record evidence receipts before promotion.",
        ]
        return {
            "workflow": "knowledge",
            "operation": "plan",
            "request": req.model_dump(),
            "selected_strategy": "static_knowledge_surfaces_plus_health_checked_runtime_hints",
            "role_candidates": self._roles_for({"name": query, "path": query, "service": query}),
            "route_candidates": routes[:40],
            "tool_candidates": tools[:40],
            "runtime_candidates": runtime_targets[:30],
            "health": health,
            "mutating": mutating,
            "suggested_first_steps": suggested_first_steps,
            "execution": "not executed; dry_run requested" if req.dry_run else "not executed; live knowledge/index operations remain approval-gated",
        }

    def runtime_preflight(self) -> dict[str, Any]:
        caps = self.capabilities()
        by_module: dict[str, list[dict[str, Any]]] = {}
        for target in caps["runtime_targets"]:
            by_module.setdefault(target.get("module", "unknown"), []).append(target)
        health = self.topology.health_check_targets(caps["runtime_targets"], timeout_seconds=0.5, limit=40)
        return {
            "workflow": "knowledge",
            "operation": "runtime_preflight",
            "runtime_target_count": caps["runtime_target_count"],
            "runtime_targets_by_module": by_module,
            "health": health,
            "activation_policy": [
                "Do not start search/index/KB services without explicit approval.",
                "Treat compose and README ports as preflight evidence until a service is selected.",
                "Prefer read-only query routes before ingestion/index routes.",
            ],
        }

    def _add_to_roles(self, role_index: dict[str, dict[str, Any]], item: dict[str, Any], bucket: str, module: str) -> None:
        for role in item.get("roles") or self._roles_for(item):
            role_index[role][bucket] += 1
            if module not in role_index[role]["modules"]:
                role_index[role]["modules"].append(module)

    def _roles_for(self, item: dict[str, Any]) -> list[str]:
        haystack = self._role_haystack(item)
        roles = []
        for role, keywords in self.ROLE_KEYWORDS.items():
            if any(keyword in haystack for keyword in keywords):
                roles.append(role)
        return roles

    def _role_keywords(self, role: str) -> list[str]:
        role = role.lower()
        if role in self.ROLE_KEYWORDS:
            return [role]
        return [matched for matched, keywords in self.ROLE_KEYWORDS.items() if role in keywords] or [role]

    def _matches_query_or_role(self, item: dict[str, Any], query: str, roles: list[str]) -> bool:
        if roles and any(role in item.get("roles", []) for role in roles):
            return True
        return self._matches_query(item, query)

    def _matches_query(self, item: dict[str, Any], query: str) -> bool:
        if not query:
            return True
        haystack = json.dumps(item, ensure_ascii=False).lower()
        tokens = [token for token in re.split(r"[^a-z0-9_]+", query) if len(token) > 2]
        return not tokens or any(token in haystack for token in tokens)

    def _role_haystack(self, item: dict[str, Any]) -> str:
        parts = [
            str(item.get("name") or ""),
            str(item.get("path") or ""),
            str(item.get("function") or ""),
            str(item.get("doc") or ""),
            str(item.get("description") or ""),
            str(item.get("service") or ""),
            str(item.get("container_name") or ""),
            str(item.get("runtime_kind") or ""),
            str(item.get("module") or ""),
            str(item.get("file") or ""),
        ]
        source = item.get("source")
        if isinstance(source, dict):
            parts.append(str(source.get("text") or ""))
            parts.append(str(source.get("file") or ""))
        elif source:
            parts.append(str(source))
        return " ".join(parts).lower()

    def _safety(self, item: dict[str, Any]) -> str:
        haystack = json.dumps(item, ensure_ascii=False).lower()
        if any(word in haystack for word in self.MUTATING_WORDS):
            return "mutating"
        if any(word in haystack for word in self.READ_WORDS):
            return "read"
        return "unknown"


class SelfStateStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS issues (
                    id TEXT PRIMARY KEY,
                    severity TEXT NOT NULL,
                    area TEXT NOT NULL,
                    module TEXT,
                    issue TEXT NOT NULL,
                    status TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS next_actions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    area TEXT NOT NULL,
                    module TEXT,
                    detail TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS workflow_status (
                    workflow TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS session_briefs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS worklog (
                    id TEXT PRIMARY KEY,
                    area TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cleanup_ledger (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source_id TEXT,
                    path TEXT,
                    sha256 TEXT,
                    size INTEGER,
                    detail TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def upsert_decision(self, req: SelfDecisionRequest) -> dict[str, Any]:
        now = utc_now()
        item_id = stable_id("decision", req.title)
        with self._connect() as conn:
            existing = conn.execute("SELECT created_at FROM decisions WHERE id=?", (item_id,)).fetchone()
            conn.execute(
                """
                INSERT INTO decisions(id, title, status, rationale, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title, status=excluded.status, rationale=excluded.rationale,
                    data_json=excluded.data_json, updated_at=excluded.updated_at
                """,
                (item_id, req.title, req.status, req.rationale, json.dumps(req.data), existing["created_at"] if existing else now, now),
            )
        return self.get_one("decisions", item_id)

    def upsert_issue(self, req: SelfIssueRequest) -> dict[str, Any]:
        now = utc_now()
        item_id = stable_id("issue", f"{req.module or 'global'}-{req.issue}")
        with self._connect() as conn:
            existing = conn.execute("SELECT created_at FROM issues WHERE id=?", (item_id,)).fetchone()
            conn.execute(
                """
                INSERT INTO issues(id, severity, area, module, issue, status, detail, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    severity=excluded.severity, area=excluded.area, module=excluded.module,
                    issue=excluded.issue, status=excluded.status, detail=excluded.detail,
                    data_json=excluded.data_json, updated_at=excluded.updated_at
                """,
                (
                    item_id,
                    req.severity,
                    req.area,
                    req.module,
                    req.issue,
                    req.status,
                    req.detail,
                    json.dumps(req.data),
                    existing["created_at"] if existing else now,
                    now,
                ),
            )
        return self.get_one("issues", item_id)

    def upsert_action(self, req: SelfActionRequest) -> dict[str, Any]:
        now = utc_now()
        item_id = stable_id("action", f"{req.module or 'global'}-{req.title}")
        with self._connect() as conn:
            existing = conn.execute("SELECT created_at FROM next_actions WHERE id=?", (item_id,)).fetchone()
            conn.execute(
                """
                INSERT INTO next_actions(id, title, priority, status, area, module, detail, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title, priority=excluded.priority, status=excluded.status,
                    area=excluded.area, module=excluded.module, detail=excluded.detail,
                    data_json=excluded.data_json, updated_at=excluded.updated_at
                """,
                (
                    item_id,
                    req.title,
                    req.priority,
                    req.status,
                    req.area,
                    req.module,
                    req.detail,
                    json.dumps(req.data),
                    existing["created_at"] if existing else now,
                    now,
                ),
            )
        return self.get_one("next_actions", item_id)

    def upsert_workflow(self, req: SelfWorkflowStatusRequest) -> dict[str, Any]:
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_status(workflow, status, summary, data_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(workflow) DO UPDATE SET
                    status=excluded.status, summary=excluded.summary,
                    data_json=excluded.data_json, updated_at=excluded.updated_at
                """,
                (req.workflow, req.status, req.summary, json.dumps(req.data), now),
            )
        return self.get_one("workflow_status", req.workflow, key_column="workflow")

    def add_worklog(self, req: SelfWorklogRequest) -> dict[str, Any]:
        now = utc_now()
        item_id = stable_id("log", f"{now}-{req.area}-{req.message}")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO worklog(id, area, message, data_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (item_id, req.area, req.message, json.dumps(req.data), now),
            )
        return self.get_one("worklog", item_id)

    def upsert_cleanup_record(self, req: CleanupLedgerRecordRequest) -> dict[str, Any]:
        now = utc_now()
        identity = f"{req.kind}-{req.sha256 or 'nohash'}-{req.source_id or 'global'}-{req.path or req.title}"
        item_id = stable_id("cleanup", identity)
        with self._connect() as conn:
            existing = conn.execute("SELECT created_at FROM cleanup_ledger WHERE id=?", (item_id,)).fetchone()
            conn.execute(
                """
                INSERT INTO cleanup_ledger(id, kind, title, status, source_id, path, sha256, size, detail, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    kind=excluded.kind, title=excluded.title, status=excluded.status,
                    source_id=excluded.source_id, path=excluded.path, sha256=excluded.sha256,
                    size=excluded.size, detail=excluded.detail, data_json=excluded.data_json,
                    updated_at=excluded.updated_at
                """,
                (
                    item_id,
                    req.kind,
                    req.title,
                    req.status,
                    req.source_id,
                    req.path,
                    req.sha256,
                    req.size,
                    req.detail,
                    json.dumps(req.data),
                    existing["created_at"] if existing else now,
                    now,
                ),
            )
        return self.get_one("cleanup_ledger", item_id)

    def add_brief(self, title: str, content: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        now = utc_now()
        item_id = stable_id("brief", f"{now}-{title}")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO session_briefs(id, title, content, data_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (item_id, title, content, json.dumps(data or {}), now),
            )
        return self.get_one("session_briefs", item_id)

    def list_table(self, table: str, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        allowed = {"decisions", "issues", "next_actions", "workflow_status", "session_briefs", "worklog", "cleanup_ledger"}
        if table not in allowed:
            raise HTTPException(400, f"unknown self-state table: {table}")
        if table == "next_actions":
            order = "priority DESC, updated_at DESC"
        elif table in {"session_briefs", "worklog"}:
            order = "created_at DESC"
        else:
            order = "updated_at DESC"
        where = ""
        params: list[Any] = []
        if status and table in {"decisions", "issues", "next_actions", "workflow_status", "cleanup_ledger"}:
            where = "WHERE status=?"
            params.append(status)
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(f"SELECT * FROM {table} {where} ORDER BY {order} LIMIT ?", params).fetchall()
        return [self._row(row) for row in rows]

    def get_one(self, table: str, item_id: str, key_column: str = "id") -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(f"SELECT * FROM {table} WHERE {key_column}=?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"self-state item not found: {item_id}")
        return self._row(row)

    def status(self) -> dict[str, Any]:
        with self._connect() as conn:
            counts = {}
            for table in ["decisions", "issues", "next_actions", "workflow_status", "session_briefs", "worklog", "cleanup_ledger"]:
                counts[table] = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        return {
            "state_path": str(self.path),
            "counts": counts,
            "open_issues": self.list_table("issues", status="open", limit=20),
            "next_actions": self.list_table("next_actions", status="open", limit=20),
            "workflows": self.list_table("workflow_status", limit=20),
            "cleanup_candidates": self.list_table("cleanup_ledger", status="candidate", limit=20),
            "latest_brief": self.list_table("session_briefs", limit=1),
        }

    def generate_brief(self) -> dict[str, Any]:
        status = self.status()
        lines = [
            "# Future Session Brief",
            "",
            "Start with repo-kernel before broad filesystem scans.",
            "",
            "Read first:",
            "- docs/REPO_KERNEL_UNIFIED_WORKFLOWS_2026-05-13.md",
            "- docs/REPO_KERNEL_ADAPTER_REGISTRY_2026-05-13.md",
            "- docs/REPO_PROMOTION_LEDGER_2026-05-13.md",
            "- docs/SOURCE_UNIVERSE_2026-05-13.md",
            "- docs/ARCHIVE_TRIAGE_REPORT_2026-05-13.md",
            "",
            "Current open issues:",
        ]
        for issue in status["open_issues"][:8]:
            module = f" [{issue.get('module')}]" if issue.get("module") else ""
            lines.append(f"- {issue['severity']} {issue['area']}{module}: {issue['issue']}")
        lines.extend(["", "Next actions:"])
        for action in status["next_actions"][:8]:
            module = f" [{action.get('module')}]" if action.get("module") else ""
            lines.append(f"- P{action['priority']} {action['area']}{module}: {action['title']}")
        lines.extend(["", "Important constraints:"])
        lines.append("- Do not write Postgres without approval.")
        lines.append("- Do not deploy compose drafts without approval.")
        lines.append("- Treat compose files as evidence/preflight checklists, not the application layer.")
        lines.append("- Treat Manny and OC build as read-only evidence.")
        lines.append("- Promote behavior behind adapters before copying source.")
        return self.add_brief("future session brief", "\n".join(lines), {"source": "self_state"})

    def _row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        if "data_json" in data:
            try:
                data["data"] = json.loads(data.pop("data_json") or "{}")
            except json.JSONDecodeError:
                data["data"] = {}
        return data


registry = RepoRegistry(MANIFEST_PATH, REPOS_ROOT)
adapter = ModuleAdapter(registry)
ledger = PromotionLedger(PROMOTION_LEDGER_PATH)
source_universe = SourceUniverse(REPOS_ROOT)
probe_runner = CapabilityProbe(registry, ledger)
surface_catalog = ModuleSurfaceCatalog(registry)
adapter_registry = RepoKernelAdapterRegistry(registry, adapter, probe_runner, surface_catalog)
registered_bundle = RegisteredSystemsBundle(registry, adapter, probe_runner, surface_catalog)
runtime_topology = RuntimeTopology(registry)
unified_workflows = UnifiedAIWorkflowRegistry(registry, surface_catalog, runtime_topology)
runtime_activation = RuntimeActivationPlanner(registry, unified_workflows, runtime_topology)
runtime_issues = RuntimeIssueReporter(runtime_topology, runtime_activation)
memory_workflow = MemoryWorkflowController(unified_workflows, runtime_topology)
mcp_tools_workflow = MCPToolsWorkflowController(unified_workflows, runtime_topology)
agent_orchestration_workflow = AgentOrchestrationWorkflowController(unified_workflows, runtime_topology)
knowledge_workflow = KnowledgeWorkflowController(unified_workflows, runtime_topology)
prototype_evidence = PrototypeEvidenceBridge()
gitnexus_bridge = GitNexusBridge()

_REPO_KERNEL_DIR = Path(__file__).resolve().parent
if str(_REPO_KERNEL_DIR) not in sys.path:
    sys.path.insert(0, str(_REPO_KERNEL_DIR))

from morphonic_bridge import MorphonicBridge

morphonic_bridge = MorphonicBridge()
global_systems = GlobalSystemController(
    registry,
    unified_workflows,
    runtime_topology,
    surface_catalog,
    mcp_tools_workflow,
    memory_workflow,
    agent_orchestration_workflow,
    knowledge_workflow,
    prototype_evidence,
    gitnexus_bridge,
)
self_state = SelfStateStore(SELF_STATE_PATH)


def default_promotion_modules() -> list[str]:
    modules = []
    for module in ledger.read().get("modules", []):
        if module.get("status") == "promoted_candidate":
            modules.append(module["name"])
        if len(modules) >= 3:
            break
    return modules or ["CMPLXUNI", "CMPLX-TMN-main", "CMPLXMCP"]


def seed_self_state() -> dict[str, Any]:
    decisions = [
        SelfDecisionRequest(
            title="Use repo-kernel as active source universe",
            rationale="Clean GitHub clones are tractable; broad Manny/PartsFactory archive scans are too noisy for primary workflow construction.",
            data={"modules": default_promotion_modules()},
        ),
        SelfDecisionRequest(
            title="Promote behavior behind adapters before copying source",
            rationale="Adapters let us prove capabilities without merging nested git histories or large duplicated source trees.",
        ),
        SelfDecisionRequest(
            title="Unify one AI workflow API layer at a time",
            rationale="Memory and MCP tools are first because they are core to agent workflows and have clear surfaces.",
        ),
        SelfDecisionRequest(
            title="Use runtime health checks before live calls",
            rationale="README and compose ports are treated as activation hints, not proof that services are running.",
        ),
        SelfDecisionRequest(
            title="Treat compose as evidence and preflight, not application layer",
            rationale="Compose files are compact operational tip sheets: ports, service names, env files, dependencies, profiles, and build contexts. Controllers/adapters decide what to activate.",
        ),
    ]
    seeded = {"decisions": [], "issues": [], "next_actions": [], "workflow_status": [], "brief": None, "worklog": None}
    for decision in decisions:
        seeded["decisions"].append(self_state.upsert_decision(decision))

    for issue in runtime_issues.report().get("issues", []):
        seeded["issues"].append(self_state.upsert_issue(SelfIssueRequest(
            severity=issue.get("severity", "medium"),
            area=issue.get("area", "runtime"),
            module=issue.get("module"),
            issue=issue.get("issue", "runtime issue"),
            detail=issue.get("detail") or "; ".join(issue.get("notes", [])),
            data=issue,
        )))

    workflows = unified_workflows.list_workflows().get("workflows", [])
    implemented = {"memory", "mcp_tools", "agent_orchestration", "knowledge"}
    for workflow in workflows:
        status = "implemented_planning_layer" if workflow["workflow"] in implemented else "candidate"
        summary = (
            f"{workflow['module_count']} modules, "
            f"{sum(item.get('routes', 0) for item in workflow.get('modules', []))} routes, "
            f"{sum(item.get('mcp_tools', 0) for item in workflow.get('modules', []))} MCP tools, "
            f"{sum(item.get('runtime_targets', 0) for item in workflow.get('modules', []))} runtime targets"
        )
        seeded["workflow_status"].append(self_state.upsert_workflow(SelfWorkflowStatusRequest(
            workflow=workflow["workflow"],
            status=status,
            summary=summary,
            data=workflow,
        )))

    actions = [
        SelfActionRequest(
            title="Create CMPLXMCP runtime shim plan and scaffold",
            priority=95,
            area="runtime",
            module="CMPLXMCP",
            detail="Resolve mcp_os package identity, numpy dependency, and stdio-vs-HTTP transport before live execution.",
        ),
        SelfActionRequest(
            title="Add agent_orchestration unified workflow layer",
            priority=80,
            area="workflow",
            module="CMPLX-TMN-main",
            detail="Expose identity, coop, daemon, spawn, and thinktank capabilities behind one planning contract.",
        ),
        SelfActionRequest(
            title="Prepare focused memory runtime bring-up",
            priority=75,
            area="runtime",
            module="CMPLX-TMN-main",
            detail="Use activation plan for tmn2-pg, tmn2-redis, tmn2-mmdb, bridge, discovery, and receipt services after explicit approval.",
        ),
        SelfActionRequest(
            title="Persist future session brief after each major slice",
            priority=70,
            area="self",
            detail="Keep future Codex aligned with the builder memory instead of re-deriving context.",
        ),
    ]
    for action in actions:
        seeded["next_actions"].append(self_state.upsert_action(action))

    seeded["worklog"] = self_state.add_worklog(SelfWorklogRequest(
        area="self",
        message="Seeded durable self-state from promotion ledger, runtime issues, and unified workflow coverage.",
    ))
    seeded["brief"] = self_state.generate_brief()
    return seeded


def workfront_report() -> dict[str, Any]:
    open_actions = self_state.list_table("next_actions", status="open", limit=100)
    cleanup_records = self_state.list_table("cleanup_ledger", limit=1000)
    workflow_status = self_state.list_table("workflow_status", limit=100)
    runtime_report = runtime_issues.report()
    workflows = unified_workflows.list_workflows().get("workflows", [])

    exact_duplicates = [
        item for item in cleanup_records
        if item.get("kind") == "exact_file_duplicate" and item.get("status") == "candidate"
    ]
    duplicate_bytes = sum(int(item.get("size") or 0) for item in exact_duplicates)
    workflow_status_by_name = {item["workflow"]: item for item in workflow_status if item.get("workflow")}
    implemented_workflows = [
        name for name, item in workflow_status_by_name.items()
        if item.get("status") == "implemented_planning_layer"
    ]
    candidate_workflows = [
        workflow for workflow in workflows
        if workflow.get("workflow") not in implemented_workflows
    ]
    candidate_workflows.sort(
        key=lambda item: (
            -sum(module.get("routes", 0) for module in item.get("modules", [])),
            -sum(module.get("mcp_tools", 0) for module in item.get("modules", [])),
            item.get("workflow", ""),
        )
    )

    lanes = [
        {
            "lane": "source_universe_cleanup",
            "status": "approval_gated",
            "why_it_matters": "prevents evidence sprawl from consuming every future scan",
            "current_signal": {
                "exact_duplicate_candidate_groups": len(exact_duplicates),
                "candidate_bytes": duplicate_bytes,
            },
            "next_action": _first_action(open_actions, "source_universe") or "review duplicate archive policy",
            "do_now_without_approval": [
                "generate manifests",
                "compare hashes",
                "write cleanup recommendations",
            ],
            "requires_approval": [
                "move archives",
                "delete files",
                "create compressed cold storage",
            ],
        },
        {
            "lane": "memory_import",
            "status": "design_ready_write_gated",
            "why_it_matters": "turns historical MMDB evidence into agent-usable recall without guessing",
            "current_signal": {
                "recipe": "docs/MMDB_READONLY_IMPORT_RECIPE_2026-05-13.md",
                "compatibility_plan": "docs/MMDB_IMPORT_COMPATIBILITY_PLAN_2026-05-13.md",
                "recommended_strategy": "repo_kernel_staging_adapter_first",
            },
            "next_action": _first_action(open_actions, "memory") or "implement local staging adapter after approval",
            "do_now_without_approval": [
                "run more read-only dry-runs",
                "compare recipes to static surfaces",
                "draft staging schema",
            ],
            "requires_approval": [
                "materialize staging database records",
                "start memory services",
                "write Postgres",
            ],
        },
        {
            "lane": "workflow_promotion",
            "status": "ready_for_next_controller",
            "why_it_matters": "keeps unification from becoming only memory tooling",
            "current_signal": {
                "implemented": implemented_workflows,
                "top_candidates": candidate_workflows[:4],
            },
            "next_action": _first_action(open_actions, "workflow") or "promote code_execution workflow controller",
            "do_now_without_approval": [
                "add planning endpoints",
                "add MCP mirrors",
                "catalog static routes and tools",
            ],
            "requires_approval": [
                "call mutating workflow routes",
                "start workflow runtimes",
            ],
        },
        {
            "lane": "runtime_activation",
            "status": "blocked_until_selected",
            "why_it_matters": "prevents compose files from becoming accidental deployment instructions",
            "current_signal": runtime_report,
            "next_action": "choose one service slice for explicit activation approval",
            "do_now_without_approval": [
                "preflight ports",
                "summarize compose evidence",
                "record runtime issues",
            ],
            "requires_approval": [
                "docker compose up for non-kernel services",
                "Postgres writes",
                "live mutating API calls",
            ],
        },
        {
            "lane": "evidence_intake",
            "status": "ongoing",
            "why_it_matters": "the three main folders and nested archives still contain unknown useful systems",
            "current_signal": {
                "mounted_sources": [source["id"] for source in source_universe.sources() if source.get("exists")],
                "policy": "bounded slices; no recursive archive explosion by default",
            },
            "next_action": "select next corpus/source slice after current controller workfront is visible",
            "do_now_without_approval": [
                "bounded inventories",
                "archive manifests",
                "marker scans",
                "read-only SQLite probes",
            ],
            "requires_approval": [
                "bulk extraction",
                "archive deletion",
                "database writes",
            ],
        },
    ]
    return {
        "generated_at": utc_now(),
        "policy": "maintain multiple active lanes; do not overfit to one tool or one improvement line",
        "active_lanes": lanes,
        "recommended_rotation": [
            "finish one bounded memory/staging planning slice",
            "promote the knowledge workflow controller",
            "review source cleanup approval policy",
            "run a fresh evidence intake slice from another source root",
            "only then consider runtime activation",
        ],
        "open_actions": open_actions[:12],
    }


def _first_action(actions: list[dict[str, Any]], area: str) -> str | None:
    for action in actions:
        if action.get("area") == area:
            return action.get("title")
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="CMPLX Repo Kernel",
    version="0.1.0",
    description="FastAPI and MCP adapter layer over clean GitHub repo modules.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("REPO_KERNEL_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp = FastMCP(
    MCP_NAME,
    instructions=(
        "Treat each clean GitHub repository under the repo kernel as a module. "
        "Use the tools to list modules, inspect pinned commits, search, and read files."
    ),
)


@app.get("/")
async def index():
    return {
        "kernel": KERNEL_ID,
        "modules": len(registry.modules()),
        "api": [
            "/api/health",
            "/api/self/status",
            "/api/self/seed-current",
            "/api/self/decisions",
            "/api/self/issues",
            "/api/self/next-actions",
            "/api/self/cleanup-ledger",
            "/api/self/session-brief",
            "/api/self/workfront",
            "/api/promotion-ledger",
            "/api/sources",
            "/api/sources/{source_id}/inventory",
            "/api/sources/{source_id}/markers",
            "/api/sources/{source_id}/archive-manifest",
            "/api/sources/{source_id}/archive-member",
            "/api/sources/{source_id}/archive-corpus-summary",
            "/api/sources/{source_id}/file-hash-slice",
            "/api/sources/{source_id}/archive-hash-slice",
            "/api/sources/{source_id}/archive-sqlite-quarantine-probe",
            "/api/sources/hash-slice-batch",
            "/api/sources/file-breakdown-plan",
            "/api/sources/quarantine/sqlite-preview",
            "/api/sources/quarantine/mmdb-import-dry-run",
            "/api/sources/archive-triage",
            "/api/sources/archive-compare",
            "/api/sources/archive-duplicate-candidates",
            "/api/sources/cleanup-evidence",
            "/api/modules",
            "/api/modules/{name}/probe",
            "/api/modules/{name}/promote-plan",
            "/api/adapters",
            "/api/adapters/{name}/surfaces",
            "/api/adapters/{name}/call",
            "/api/evidence/compose",
            "/api/modules/{name}/compose-evidence",
            "/api/runtime/topology",
            "/api/runtime/health-check",
            "/api/runtime/activation-plan",
            "/api/runtime/issues",
            "/api/unified/workflows",
            "/api/unified/workflows/{workflow}",
            "/api/unified/workflows/{workflow}/route-plan",
            "/api/unified/memory/capabilities",
            "/api/unified/memory/query",
            "/api/unified/memory/receipt-plan",
            "/api/unified/memory/runtime-preflight",
            "/api/unified/memory/corpus-import-plan",
            "/api/unified/memory/mmdb-import-compatibility",
            "/api/unified/mcp-tools/capabilities",
            "/api/unified/mcp-tools/tools",
            "/api/unified/mcp-tools/tools/{tool_name}",
            "/api/unified/mcp-tools/call-plan",
            "/api/unified/agent-orchestration/capabilities",
            "/api/unified/agent-orchestration/plan",
            "/api/unified/knowledge/capabilities",
            "/api/unified/knowledge/plan",
            "/api/unified/knowledge/runtime-preflight",
            "/api/controller/compose-plan",
            "/api/controller/probe",
            "/api/controller/promotion-plan",
            "/mcp/sse",
        ],
    }


@app.get("/api/health")
async def health():
    modules = registry.modules()
    return {
        "ok": True,
        "kernel": KERNEL_ID,
        "manifest": str(MANIFEST_PATH),
        "repos_root": str(REPOS_ROOT),
        "module_count": len(modules),
        "cloned_count": sum(1 for m in modules if m.get("cloned")),
        "allow_mutation": ALLOW_MUTATION,
        "morphonic": morphonic_bridge.status(),
    }


@app.get("/api/self/status")
async def self_status():
    return self_state.status()


@app.post("/api/self/seed-current")
async def self_seed_current():
    return seed_self_state()


@app.get("/api/self/decisions")
async def self_decisions(status: str | None = None, limit: int = Query(default=100, ge=1, le=500)):
    return {"decisions": self_state.list_table("decisions", status=status, limit=limit)}


@app.post("/api/self/decisions")
async def self_add_decision(req: SelfDecisionRequest):
    return self_state.upsert_decision(req)


@app.get("/api/self/issues")
async def self_issues(status: str | None = "open", limit: int = Query(default=100, ge=1, le=500)):
    return {"issues": self_state.list_table("issues", status=status, limit=limit)}


@app.post("/api/self/issues")
async def self_add_issue(req: SelfIssueRequest):
    return self_state.upsert_issue(req)


@app.get("/api/self/next-actions")
async def self_next_actions(status: str | None = "open", limit: int = Query(default=100, ge=1, le=500)):
    return {"next_actions": self_state.list_table("next_actions", status=status, limit=limit)}


@app.post("/api/self/next-actions")
async def self_add_next_action(req: SelfActionRequest):
    return self_state.upsert_action(req)


@app.get("/api/self/workflow-status")
async def self_workflow_status(limit: int = Query(default=100, ge=1, le=500)):
    return {"workflows": self_state.list_table("workflow_status", limit=limit)}


@app.post("/api/self/workflow-status")
async def self_add_workflow_status(req: SelfWorkflowStatusRequest):
    return self_state.upsert_workflow(req)


@app.get("/api/self/worklog")
async def self_worklog(limit: int = Query(default=100, ge=1, le=500)):
    return {"worklog": self_state.list_table("worklog", limit=limit)}


@app.post("/api/self/worklog")
async def self_add_worklog(req: SelfWorklogRequest):
    return self_state.add_worklog(req)


@app.get("/api/self/cleanup-ledger")
async def self_cleanup_ledger(status: str | None = "candidate", limit: int = Query(default=100, ge=1, le=1000)):
    return {"cleanup_ledger": self_state.list_table("cleanup_ledger", status=status, limit=limit)}


@app.post("/api/self/cleanup-ledger")
async def self_add_cleanup_record(req: CleanupLedgerRecordRequest):
    return self_state.upsert_cleanup_record(req)


@app.get("/api/self/session-brief")
async def self_session_briefs(limit: int = Query(default=10, ge=1, le=100)):
    return {"briefs": self_state.list_table("session_briefs", limit=limit)}


@app.post("/api/self/session-brief")
async def self_generate_session_brief():
    return self_state.generate_brief()


@app.get("/api/self/workfront")
async def self_workfront():
    return workfront_report()


@app.get("/api/promotion-ledger")
async def promotion_ledger():
    return ledger.read()


@app.get("/api/sources")
async def source_universe_index():
    return {
        "policy": "source universe is bounded evidence discovery; massive roots are mounted read-only and inventoried in small slices",
        "sources": source_universe.sources(),
    }


@app.post("/api/sources/{source_id}/inventory")
async def source_inventory(source_id: str, req: SourceInventoryRequest | None = None):
    req = req or SourceInventoryRequest(source_id=source_id)
    req.source_id = source_id
    return source_universe.inventory(req)


@app.post("/api/sources/{source_id}/markers")
async def source_markers(source_id: str, req: SourceInventoryRequest | None = None):
    req = req or SourceInventoryRequest(source_id=source_id)
    req.source_id = source_id
    return source_universe.markers(req)


@app.post("/api/sources/{source_id}/archive-manifest")
async def source_archive_manifest(source_id: str, req: SourceArchiveManifestRequest):
    req.source_id = source_id
    return source_universe.archive_manifest(req)


@app.post("/api/sources/{source_id}/archive-member")
async def source_archive_member_read(source_id: str, req: SourceArchiveMemberReadRequest):
    req.source_id = source_id
    return source_universe.archive_member_read(req)


@app.post("/api/sources/{source_id}/archive-corpus-summary")
async def source_archive_corpus_summary(source_id: str, req: SourceArchiveCorpusSummaryRequest):
    req.source_id = source_id
    return source_universe.archive_corpus_summary(req)


@app.post("/api/sources/{source_id}/file-hash-slice")
async def source_file_hash_slice(source_id: str, req: FileHashSliceRequest | None = None):
    req = req or FileHashSliceRequest(source_id=source_id)
    req.source_id = source_id
    return source_universe.file_hash_slice(req)


@app.post("/api/sources/{source_id}/archive-hash-slice")
async def source_archive_hash_slice(source_id: str, req: ArchiveHashSliceRequest):
    req.source_id = source_id
    return source_universe.archive_hash_slice(req)


@app.post("/api/sources/{source_id}/archive-sqlite-quarantine-probe")
async def source_archive_sqlite_quarantine_probe(source_id: str, req: ArchiveSQLiteQuarantineProbeRequest):
    req.source_id = source_id
    return source_universe.archive_sqlite_quarantine_probe(req)


@app.post("/api/sources/hash-slice-batch")
async def source_hash_slice_batch(req: HashSliceBatchRequest):
    return source_universe.hash_slice_batch(req)


@app.post("/api/sources/file-breakdown-plan")
async def source_file_breakdown_plan(req: FileBreakdownPlanRequest):
    return source_universe.file_breakdown_plan(req)


@app.post("/api/sources/quarantine/sqlite-preview")
async def source_quarantine_sqlite_preview(req: QuarantineSQLitePreviewRequest):
    return source_universe.quarantine_sqlite_preview(req)


@app.post("/api/sources/quarantine/mmdb-import-dry-run")
async def source_quarantine_mmdb_import_dry_run(req: MMDBImportDryRunRequest):
    return source_universe.mmdb_import_dry_run(req)


@app.post("/api/sources/archive-triage")
async def source_archive_triage(req: ArchiveTriageRequest | None = None):
    req = req or ArchiveTriageRequest()
    return source_universe.archive_triage(req)


@app.post("/api/sources/archive-compare")
async def source_archive_compare(req: ArchiveCompareRequest):
    return source_universe.archive_compare(req)


@app.post("/api/sources/archive-duplicate-candidates")
async def source_archive_duplicate_candidates(req: ArchiveDuplicateCandidateRequest | None = None):
    req = req or ArchiveDuplicateCandidateRequest()
    return source_universe.archive_duplicate_candidates(req)


@app.post("/api/sources/cleanup-evidence")
async def source_cleanup_evidence(req: CleanupEvidenceRequest | None = None):
    req = req or CleanupEvidenceRequest()
    return source_universe.cleanup_evidence(req)


@app.get("/api/registered-bundle")
async def registered_bundle_default():
    return registered_bundle.describe(RegisteredBundleRequest())


@app.post("/api/registered-bundle")
async def registered_bundle_describe(req: RegisteredBundleRequest | None = None):
    req = req or RegisteredBundleRequest()
    return registered_bundle.describe(req)


@app.post("/api/registered-bundle/run")
async def registered_bundle_run(req: RegisteredBundleRunRequest | None = None):
    req = req or RegisteredBundleRunRequest()
    return registered_bundle.run(req)


@app.get("/api/global-systems")
async def global_system_index():
    return global_systems.list_systems()


@app.get("/api/global-systems/{system}")
async def global_system_detail(system: str, modules: list[str] | None = Query(default=None)):
    return global_systems.describe(system, modules=modules)


@app.get("/api/global-systems/{system}/tools")
async def global_system_tools(
    system: str,
    q: str | None = None,
    modules: list[str] | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
):
    return global_systems.tools(system, modules=modules, q=q, limit=limit)


@app.get("/api/global-systems/{system}/routes")
async def global_system_routes(
    system: str,
    q: str | None = None,
    modules: list[str] | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
):
    return global_systems.routes(system, modules=modules, q=q, limit=limit)


@app.get("/api/global-systems/{system}/ports")
async def global_system_ports(system: str, modules: list[str] | None = Query(default=None)):
    return global_systems.ports(system, modules=modules)


@app.get("/api/global-systems/{system}/skills")
async def global_system_skills(
    system: str,
    modules: list[str] | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
):
    return global_systems.skills(system, modules=modules, limit=limit)


@app.post("/api/global-systems/{system}/call-plan")
async def global_system_call_plan(system: str, req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan(system, req)


@app.get("/api/global-locations")
async def global_location_map(modules: list[str] | None = Query(default=None)):
    return global_systems.location_map(modules=modules)


@app.get("/api/global-locations/{system}")
async def global_system_location_map(system: str, modules: list[str] | None = Query(default=None)):
    return global_systems.location_map(system=system, modules=modules)


@app.get("/api/global-coverage")
async def global_coverage(
    modules: list[str] | None = Query(default=None),
    limit_unassigned: int = Query(default=200, ge=1, le=2000),
):
    return global_systems.coverage(modules=modules, limit_unassigned=limit_unassigned)


@app.get("/api/global-port-plan")
async def global_port_reassignment_plan(modules: list[str] | None = Query(default=None)):
    return global_systems.port_reassignment_plan(modules=modules)


@app.get("/api/global-runtime-slices")
async def global_runtime_slice_plan(
    modules: list[str] | None = Query(default=None),
    check_health: bool = False,
    timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0),
    limit: int = Query(default=18, ge=1, le=18),
):
    return global_systems.runtime_slice_plan(
        modules=modules,
        check_health=check_health,
        timeout_seconds=timeout_seconds,
        limit=limit,
    )


@app.get("/api/global-tool-workbook")
async def global_tool_workbook(
    check_health: bool = False,
    timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0),
):
    return global_systems.tool_workbook(check_health=check_health, timeout_seconds=timeout_seconds)


@app.get("/api/global-state")
async def global_compact_state(
    check_health: bool = False,
    timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0),
):
    return global_systems.compact_state(check_health=check_health, timeout_seconds=timeout_seconds)


@app.get("/api/clean-system-image-plan")
async def clean_system_image_plan():
    return global_systems.clean_system_image_plan()


@app.get("/api/capability-registry")
async def capability_registry():
    return global_systems.capability_registry()


@app.get("/api/prototype-evidence")
async def prototype_evidence_overview():
    return prototype_evidence.overview()


@app.get("/api/prototype-evidence/docs")
async def prototype_evidence_docs(limit: int = Query(default=50, ge=1, le=500)):
    return prototype_evidence.docs(limit=limit)


@app.get("/api/prototype-evidence/bridges")
async def prototype_evidence_bridges(limit: int = Query(default=50, ge=1, le=500)):
    return prototype_evidence.bridges(limit=limit)


@app.get("/api/prototype-evidence/search")
async def prototype_evidence_search(q: str = Query(min_length=1), limit: int = Query(default=20, ge=1, le=100)):
    return prototype_evidence.search(q=q, limit=limit)


@app.get("/api/prototype-evidence/read")
async def prototype_evidence_read(path: str = Query(min_length=1), max_bytes: int = Query(default=120_000, ge=1, le=500_000)):
    return prototype_evidence.read(PrototypeEvidenceReadRequest(path=path, max_bytes=max_bytes))


@app.get("/api/morphonic/status")
async def morphonic_status():
    return morphonic_bridge.status()


@app.get("/api/morphonic/crystal-info")
async def morphonic_crystal_info(bundle: str = Query(default="", min_length=0)):
    if not bundle:
        raise HTTPException(status_code=400, detail="bundle query parameter required")
    return morphonic_bridge.crystal_info(bundle)


@app.get("/api/morphonic/template-stats")
async def morphonic_template_stats(db: str = Query(default="")):
    return morphonic_bridge.template_stats(db or None)


@app.get("/api/gitnexus/status")
async def gitnexus_status(
    include_repos: bool = True,
    repo_limit: int = Query(default=20, ge=1, le=100),
):
    return gitnexus_bridge.status(include_repos=include_repos, repo_limit=repo_limit)


@app.get("/api/gitnexus/repos")
async def gitnexus_repos(limit: int = Query(default=100, ge=1, le=500)):
    return gitnexus_bridge.repos(limit=limit)


@app.get("/api/gitnexus/repos/{repo}")
async def gitnexus_repo(repo: str):
    return gitnexus_bridge.repo(repo)


@app.get("/api/gitnexus/graph-summary")
async def gitnexus_graph_summary(repo: str = Query(min_length=1), limit: int = Query(default=20, ge=1, le=100)):
    return gitnexus_bridge.graph_summary(repo=repo, limit=limit)


@app.get("/api/gitnexus/unification-hints")
async def gitnexus_unification_hints(limit: int = Query(default=12, ge=1, le=50)):
    return gitnexus_bridge.unification_hints(limit=limit)


@app.get("/api/gitnexus/repo-unification-worklist")
async def gitnexus_repo_unification_worklist(
    limit: int = Query(default=20, ge=1, le=100),
    include_probe: bool = False,
):
    return adapter_registry.unification_worklist(gitnexus=gitnexus_bridge, limit=limit, include_probe=include_probe)


@app.get("/api/gitnexus/slice-candidates")
async def gitnexus_slice_candidates(
    module: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    return adapter_registry.slice_candidates(module, gitnexus=gitnexus_bridge, limit=limit)


@app.get("/api/gitnexus/slice-candidate-matrix")
async def gitnexus_slice_candidate_matrix(
    modules: list[str] | None = Query(default=None),
    limit_per_module: int = Query(default=12, ge=1, le=50),
    include_review: bool = False,
):
    return adapter_registry.slice_candidate_matrix(
        gitnexus=gitnexus_bridge,
        modules=modules,
        limit_per_module=limit_per_module,
        include_review=include_review,
    )


@app.get("/api/gitnexus/slice-intake-plan")
async def gitnexus_slice_intake_plan(
    module: str = Query(min_length=1),
    path: str = Query(min_length=1),
):
    return adapter_registry.slice_intake_plan(module, path, gitnexus=gitnexus_bridge)


@app.get("/api/gitnexus/grep")
async def gitnexus_grep(
    repo: str = Query(min_length=1),
    pattern: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    return gitnexus_bridge.grep(repo=repo, pattern=pattern, limit=limit)


@app.get("/api/gitnexus/aggregate")
async def gitnexus_aggregate():
    return gitnexus_bridge.aggregate_summary()


@app.get("/api/gitnexus/aggregate/search")
async def gitnexus_aggregate_search(
    q: str | None = None,
    system: str | None = None,
    language: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
):
    return gitnexus_bridge.aggregate_search(q=q, system=system, language=language, limit=limit)


@app.get("/api/global/query")
async def global_query(
    q: str = Query(min_length=1),
    systems: list[str] | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    include_context: bool = True,
    dry_run: bool = False,
):
    return global_systems.global_query(
        GlobalQueryRequest(
            q=q,
            systems=systems or ["memory", "knowledge", "geometry", "operations"],
            limit=limit,
            include_context=include_context,
            dry_run=dry_run,
        )
    )


@app.post("/api/global/query")
async def global_query_post(req: GlobalQueryRequest):
    return global_systems.global_query(req)


@app.get("/api/global/mcp")
async def global_mcp_detail(modules: list[str] | None = Query(default=None)):
    return global_systems.describe("mcp", modules=modules)


@app.get("/api/global/mcp/tools")
async def global_mcp_tools(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.tools("mcp", q=q, limit=limit)


@app.get("/api/global/mcp/routes")
async def global_mcp_routes(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.routes("mcp", q=q, limit=limit)


@app.get("/api/global/mcp/ports")
async def global_mcp_ports():
    return global_systems.ports("mcp")


@app.get("/api/global/mcp/skills")
async def global_mcp_skills(limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.skills("mcp", limit=limit)


@app.post("/api/global/mcp/call-plan")
async def global_mcp_call_plan(req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan("mcp", req)


@app.get("/api/global/memory")
async def global_memory_detail(modules: list[str] | None = Query(default=None)):
    return global_systems.describe("memory", modules=modules)


@app.get("/api/global/memory/tools")
async def global_memory_tools(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.tools("memory", q=q, limit=limit)


@app.get("/api/global/memory/routes")
async def global_memory_routes(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.routes("memory", q=q, limit=limit)


@app.get("/api/global/memory/ports")
async def global_memory_ports():
    return global_systems.ports("memory")


@app.get("/api/global/memory/skills")
async def global_memory_skills(limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.skills("memory", limit=limit)


@app.post("/api/global/memory/call-plan")
async def global_memory_call_plan(req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan("memory", req)


@app.get("/api/global/memory/upstreams")
async def global_memory_upstreams(
    check_health: bool = False,
    timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0),
):
    return global_systems.memory_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds)


@app.get("/api/global/memory/health")
async def global_memory_health(timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0)):
    contract = global_systems.memory_routing_contract(check_health=True, timeout_seconds=timeout_seconds)
    return {
        "system": "memory",
        "status": contract["status"],
        "health": contract["health"],
        "policy": contract["policy"],
    }


@app.get("/api/global/memory/search")
async def global_memory_search(
    q: str = Query(min_length=1),
    service: str = "pocket-memory-api",
    limit: int = Query(default=20, ge=1, le=200),
):
    return global_systems.memory_search(q=q, service=service, limit=limit)


@app.get("/api/global/memory/read/{service}")
async def global_memory_read_root(service: str, request: Request):
    return global_systems.memory_read_proxy(service, "", query=dict(request.query_params))


@app.get("/api/global/memory/read/{service}/{path:path}")
async def global_memory_read_path(service: str, path: str, request: Request):
    return global_systems.memory_read_proxy(service, path, query=dict(request.query_params))


@app.get("/api/global/agent-orchestration")
async def global_agent_orchestration_detail(modules: list[str] | None = Query(default=None)):
    return global_systems.describe("agent-orchestration", modules=modules)


@app.get("/api/global/agent-orchestration/tools")
async def global_agent_orchestration_tools(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.tools("agent-orchestration", q=q, limit=limit)


@app.get("/api/global/agent-orchestration/routes")
async def global_agent_orchestration_routes(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.routes("agent-orchestration", q=q, limit=limit)


@app.get("/api/global/agent-orchestration/ports")
async def global_agent_orchestration_ports():
    return global_systems.ports("agent-orchestration")


@app.get("/api/global/agent-orchestration/skills")
async def global_agent_orchestration_skills(limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.skills("agent-orchestration", limit=limit)


@app.post("/api/global/agent-orchestration/call-plan")
async def global_agent_orchestration_call_plan(req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan("agent-orchestration", req)


@app.get("/api/global/knowledge")
async def global_knowledge_detail(modules: list[str] | None = Query(default=None)):
    return global_systems.describe("knowledge", modules=modules)


@app.get("/api/global/knowledge/tools")
async def global_knowledge_tools(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.tools("knowledge", q=q, limit=limit)


@app.get("/api/global/knowledge/routes")
async def global_knowledge_routes(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.routes("knowledge", q=q, limit=limit)


@app.get("/api/global/knowledge/ports")
async def global_knowledge_ports():
    return global_systems.ports("knowledge")


@app.get("/api/global/knowledge/skills")
async def global_knowledge_skills(limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.skills("knowledge", limit=limit)


@app.post("/api/global/knowledge/call-plan")
async def global_knowledge_call_plan(req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan("knowledge", req)


@app.get("/api/global/knowledge/upstreams")
async def global_knowledge_upstreams(
    check_health: bool = False,
    timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0),
):
    return global_systems.knowledge_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds)


@app.get("/api/global/knowledge/health")
async def global_knowledge_health(timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0)):
    contract = global_systems.knowledge_routing_contract(check_health=True, timeout_seconds=timeout_seconds)
    return {
        "system": "knowledge",
        "status": contract["status"],
        "health": contract["health"],
        "disabled_upstreams": contract["disabled_upstreams"],
        "api_layer_needs": contract["api_layer_needs"],
        "policy": contract["policy"],
    }


@app.get("/api/global/knowledge/search")
async def global_knowledge_search(
    q: str = Query(min_length=1),
    service: str = "db-aggregator-api",
    limit: int = Query(default=20, ge=1, le=200),
):
    return global_systems.knowledge_search(q=q, service=service, limit=limit)


@app.get("/api/global/knowledge/prototype-claims")
async def global_knowledge_prototype_claims(q: str = Query(min_length=1), limit: int = Query(default=20, ge=1, le=100)):
    return prototype_evidence.search(q=q, limit=limit)


@app.get("/api/global/knowledge/read/{service}")
async def global_knowledge_read_root(service: str, request: Request):
    return global_systems.knowledge_read_proxy(service, "", query=dict(request.query_params))


@app.get("/api/global/knowledge/read/{service}/{path:path}")
async def global_knowledge_read_path(service: str, path: str, request: Request):
    return global_systems.knowledge_read_proxy(service, path, query=dict(request.query_params))


@app.get("/api/global/knowledge/devkit-ingest")
async def global_knowledge_devkit_ingest():
    return adapter_registry.devkit_ingest_capability(gitnexus=gitnexus_bridge)


@app.get("/api/global/knowledge/devkit-ingest/tree")
async def global_knowledge_devkit_ingest_tree(
    max_depth: int = Query(default=2, ge=0, le=6),
    limit: int = Query(default=80, ge=1, le=500),
):
    return adapter_registry.devkit_ingest_tree(max_depth=max_depth, limit=limit)


@app.get("/api/global/knowledge/devkit-ingest/files/{path:path}")
async def global_knowledge_devkit_ingest_file(
    path: str,
    max_bytes: int = Query(default=80_000, ge=1, le=500_000),
):
    return adapter_registry.devkit_ingest_read_file(path, max_bytes=max_bytes)


@app.post("/api/global/knowledge/devkit-ingest/call-plan")
async def global_knowledge_devkit_ingest_call_plan(req: GlobalSystemCallPlanRequest):
    return adapter_registry.devkit_ingest_call_plan(req)


@app.get("/api/global/geometry")
async def global_geometry_detail(modules: list[str] | None = Query(default=None)):
    return global_systems.describe("geometry", modules=modules)


@app.get("/api/global/geometry/tools")
async def global_geometry_tools(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.tools("geometry", q=q, limit=limit)


@app.get("/api/global/geometry/routes")
async def global_geometry_routes(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.routes("geometry", q=q, limit=limit)


@app.get("/api/global/geometry/ports")
async def global_geometry_ports():
    return global_systems.ports("geometry")


@app.get("/api/global/geometry/skills")
async def global_geometry_skills(limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.skills("geometry", limit=limit)


@app.post("/api/global/geometry/call-plan")
async def global_geometry_call_plan(req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan("geometry", req)


@app.get("/api/global/geometry/upstreams")
async def global_geometry_upstreams(
    check_health: bool = False,
    timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0),
):
    return global_systems.geometry_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds)


@app.get("/api/global/geometry/health")
async def global_geometry_health(timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0)):
    contract = global_systems.geometry_routing_contract(check_health=True, timeout_seconds=timeout_seconds)
    return {
        "system": "geometry",
        "status": contract["status"],
        "health": contract["health"],
        "policy": contract["policy"],
    }


@app.get("/api/global/geometry/read/{service}")
async def global_geometry_read_root(service: str, request: Request):
    return global_systems.geometry_read_proxy(service, "", query=dict(request.query_params))


@app.get("/api/global/geometry/read/{service}/{path:path}")
async def global_geometry_read_path(service: str, path: str, request: Request):
    return global_systems.geometry_read_proxy(service, path, query=dict(request.query_params))


@app.get("/api/global/training")
async def global_training_detail(modules: list[str] | None = Query(default=None)):
    return global_systems.describe("training", modules=modules)


@app.get("/api/global/training/tools")
async def global_training_tools(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.tools("training", q=q, limit=limit)


@app.get("/api/global/training/routes")
async def global_training_routes(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.routes("training", q=q, limit=limit)


@app.get("/api/global/training/ports")
async def global_training_ports():
    return global_systems.ports("training")


@app.get("/api/global/training/skills")
async def global_training_skills(limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.skills("training", limit=limit)


@app.post("/api/global/training/call-plan")
async def global_training_call_plan(req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan("training", req)


@app.get("/api/global/code-execution")
async def global_code_execution_detail(modules: list[str] | None = Query(default=None)):
    return global_systems.describe("code-execution", modules=modules)


@app.get("/api/global/code-execution/tools")
async def global_code_execution_tools(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.tools("code-execution", q=q, limit=limit)


@app.get("/api/global/code-execution/routes")
async def global_code_execution_routes(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.routes("code-execution", q=q, limit=limit)


@app.get("/api/global/code-execution/ports")
async def global_code_execution_ports():
    return global_systems.ports("code-execution")


@app.get("/api/global/code-execution/skills")
async def global_code_execution_skills(limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.skills("code-execution", limit=limit)


@app.post("/api/global/code-execution/call-plan")
async def global_code_execution_call_plan(req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan("code-execution", req)


@app.get("/api/global/code-execution/octa64")
async def global_code_execution_octa64():
    return adapter_registry.octa64_capability(gitnexus=gitnexus_bridge)


@app.get("/api/global/code-execution/octa64/tree")
async def global_code_execution_octa64_tree(
    max_depth: int = Query(default=2, ge=0, le=6),
    limit: int = Query(default=100, ge=1, le=500),
):
    return adapter_registry.octa64_tree(max_depth=max_depth, limit=limit)


@app.get("/api/global/code-execution/octa64/files/{path:path}")
async def global_code_execution_octa64_file(
    path: str,
    max_bytes: int = Query(default=120_000, ge=1, le=500_000),
):
    return adapter_registry.octa64_read_file(path, max_bytes=max_bytes)


@app.post("/api/global/code-execution/octa64/call-plan")
async def global_code_execution_octa64_call_plan(req: GlobalSystemCallPlanRequest):
    return adapter_registry.octa64_call_plan(req)


@app.get("/api/global/pipeline")
async def global_pipeline_detail(modules: list[str] | None = Query(default=None)):
    return global_systems.describe("pipeline", modules=modules)


@app.get("/api/global/pipeline/tools")
async def global_pipeline_tools(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.tools("pipeline", q=q, limit=limit)


@app.get("/api/global/pipeline/routes")
async def global_pipeline_routes(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.routes("pipeline", q=q, limit=limit)


@app.get("/api/global/pipeline/ports")
async def global_pipeline_ports():
    return global_systems.ports("pipeline")


@app.get("/api/global/pipeline/skills")
async def global_pipeline_skills(limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.skills("pipeline", limit=limit)


@app.post("/api/global/pipeline/call-plan")
async def global_pipeline_call_plan(req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan("pipeline", req)


@app.get("/api/global/external-ai-portal")
async def global_external_ai_portal_detail(modules: list[str] | None = Query(default=None)):
    return global_systems.describe("external-ai-portal", modules=modules)


@app.get("/api/global/external-ai-portal/tools")
async def global_external_ai_portal_tools(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.tools("external-ai-portal", q=q, limit=limit)


@app.get("/api/global/external-ai-portal/routes")
async def global_external_ai_portal_routes(q: str | None = None, limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.routes("external-ai-portal", q=q, limit=limit)


@app.get("/api/global/external-ai-portal/ports")
async def global_external_ai_portal_ports():
    return global_systems.ports("external-ai-portal")


@app.get("/api/global/external-ai-portal/skills")
async def global_external_ai_portal_skills(limit: int = Query(default=500, ge=1, le=5000)):
    return global_systems.skills("external-ai-portal", limit=limit)


@app.post("/api/global/external-ai-portal/call-plan")
async def global_external_ai_portal_call_plan(req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan("external-ai-portal", req)


@app.get("/api/global/validation/mcp-os")
async def global_validation_mcp_os():
    return adapter_registry.mcp_os_validation_capability(gitnexus=gitnexus_bridge)


@app.get("/api/global/validation/mcp-os/tree")
async def global_validation_mcp_os_tree(
    max_depth: int = Query(default=2, ge=0, le=6),
    limit: int = Query(default=120, ge=1, le=500),
):
    return adapter_registry.mcp_os_validation_tree(max_depth=max_depth, limit=limit)


@app.get("/api/global/validation/mcp-os/files/{path:path}")
async def global_validation_mcp_os_file(
    path: str,
    max_bytes: int = Query(default=160_000, ge=1, le=500_000),
):
    return adapter_registry.mcp_os_validation_read_file(path, max_bytes=max_bytes)


@app.post("/api/global/validation/mcp-os/call-plan")
async def global_validation_mcp_os_call_plan(req: GlobalSystemCallPlanRequest):
    return adapter_registry.mcp_os_validation_call_plan(req)


@app.get("/api/global/synthesis/cqe-modular")
async def global_synthesis_cqe_modular():
    return adapter_registry.cqe_modular_capability(gitnexus=gitnexus_bridge)


@app.get("/api/global/synthesis/cqe-modular/tree")
async def global_synthesis_cqe_modular_tree(
    max_depth: int = Query(default=2, ge=0, le=6),
    limit: int = Query(default=80, ge=1, le=500),
):
    return adapter_registry.cqe_modular_tree(max_depth=max_depth, limit=limit)


@app.get("/api/global/synthesis/cqe-modular/files/{path:path}")
async def global_synthesis_cqe_modular_file(
    path: str,
    max_bytes: int = Query(default=80_000, ge=1, le=500_000),
):
    return adapter_registry.cqe_modular_read_file(path, max_bytes=max_bytes)


@app.post("/api/global/synthesis/cqe-modular/call-plan")
async def global_synthesis_cqe_modular_call_plan(req: GlobalSystemCallPlanRequest):
    return adapter_registry.cqe_modular_call_plan(req)


@app.get("/api/global/mcp/local-os")
async def global_mcp_local_os():
    return adapter_registry.mcp_local_os_capability(gitnexus=gitnexus_bridge)


@app.get("/api/global/mcp/local-os/tree")
async def global_mcp_local_os_tree(
    max_depth: int = Query(default=2, ge=0, le=6),
    limit: int = Query(default=200, ge=1, le=500),
):
    return adapter_registry.mcp_local_os_tree(max_depth=max_depth, limit=limit)


@app.get("/api/global/mcp/local-os/files/{path:path}")
async def global_mcp_local_os_file(
    path: str,
    max_bytes: int = Query(default=180_000, ge=1, le=500_000),
):
    return adapter_registry.mcp_local_os_read_file(path, max_bytes=max_bytes)


@app.post("/api/global/mcp/local-os/call-plan")
async def global_mcp_local_os_call_plan(req: GlobalSystemCallPlanRequest):
    return adapter_registry.mcp_local_os_call_plan(req)


@app.get("/api/global/operations/upstreams")
async def global_operations_upstreams(
    check_health: bool = False,
    timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0),
):
    return global_systems.operations_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds)


@app.get("/api/global/operations/health")
async def global_operations_health(timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0)):
    contract = global_systems.operations_routing_contract(check_health=True, timeout_seconds=timeout_seconds)
    return {
        "system": "operations",
        "status": contract["status"],
        "health": contract["health"],
        "policy": contract["policy"],
    }


@app.get("/api/global/operations/read/{service}")
async def global_operations_read_root(service: str, request: Request):
    return global_systems.operations_read_proxy(service, "", query=dict(request.query_params))


@app.get("/api/global/operations/read/{service}/{path:path}")
async def global_operations_read_path(service: str, path: str, request: Request):
    return global_systems.operations_read_proxy(service, path, query=dict(request.query_params))


@app.get("/api/global/{system}/upstreams")
async def global_live_slice_upstreams(
    system: str,
    check_health: bool = False,
    timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0),
):
    return global_systems.live_slice_routing_contract(system, check_health=check_health, timeout_seconds=timeout_seconds)


@app.get("/api/global/{system}/health")
async def global_live_slice_health(system: str, timeout_seconds: float = Query(default=0.7, ge=0.2, le=5.0)):
    contract = global_systems.live_slice_routing_contract(system, check_health=True, timeout_seconds=timeout_seconds)
    return {
        "system": system,
        "status": contract["status"],
        "health": contract["health"],
        "disabled_upstreams": contract.get("disabled_upstreams", []),
        "api_layer_needs": contract.get("api_layer_needs", []),
        "policy": contract["policy"],
    }


@app.get("/api/global/{system}/read/{service}")
async def global_live_slice_read_root(system: str, service: str, request: Request):
    return global_systems.live_slice_read_proxy(system, service, "", query=dict(request.query_params))


@app.get("/api/global/{system}/read/{service}/{path:path}")
async def global_live_slice_read_path(system: str, service: str, path: str, request: Request):
    return global_systems.live_slice_read_proxy(system, service, path, query=dict(request.query_params))


@app.get("/api/global/{system}")
async def global_alias_detail(system: str, modules: list[str] | None = Query(default=None)):
    return global_systems.describe(system, modules=modules)


@app.get("/api/global/{system}/location")
async def global_alias_location(system: str, modules: list[str] | None = Query(default=None)):
    return global_systems.location_map(system=system, modules=modules)


@app.get("/api/global/{system}/tools")
async def global_alias_tools(
    system: str,
    modules: list[str] | None = Query(default=None),
    q: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
):
    return global_systems.tools(system, modules=modules, q=q, limit=limit)


@app.get("/api/global/{system}/routes")
async def global_alias_routes(
    system: str,
    modules: list[str] | None = Query(default=None),
    q: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
):
    return global_systems.routes(system, modules=modules, q=q, limit=limit)


@app.get("/api/global/{system}/ports")
async def global_alias_ports(system: str, modules: list[str] | None = Query(default=None)):
    return global_systems.ports(system, modules=modules)


@app.get("/api/global/{system}/skills")
async def global_alias_skills(
    system: str,
    modules: list[str] | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
):
    return global_systems.skills(system, modules=modules, limit=limit)


@app.post("/api/global/{system}/call-plan")
async def global_alias_call_plan(system: str, req: GlobalSystemCallPlanRequest):
    return global_systems.call_plan(system, req)


@app.get("/api/modules")
async def list_modules():
    return {"modules": registry.modules()}


@app.get("/api/modules/{name}")
async def inspect_module(name: str):
    return registry.module(name)


@app.get("/api/modules/{name}/tree")
async def module_tree(
    name: str,
    path: str = ".",
    max_depth: int = Query(default=2, ge=0, le=8),
    limit: int = Query(default=300, ge=1, le=2000),
):
    return adapter.tree(name, path, max_depth=max_depth, limit=limit)


@app.get("/api/modules/{name}/file")
async def read_file(name: str, path: str, max_bytes: int = Query(default=200_000, ge=1, le=2_000_000)):
    return adapter.read_file(name, path, max_bytes=max_bytes)


@app.get("/api/modules/{name}/raw", response_class=PlainTextResponse)
async def read_raw(name: str, path: str, max_bytes: int = Query(default=200_000, ge=1, le=2_000_000)):
    data = adapter.read_file(name, path, max_bytes=max_bytes)
    return PlainTextResponse(data["content"])


@app.get("/api/modules/{name}/search")
async def search_module(
    name: str,
    q: str = Query(min_length=1),
    glob: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
):
    return adapter.search(name, q, glob=glob, limit=limit)


@app.post("/api/modules/{name}/probe")
async def probe_module(name: str, req: ProbeRequest | None = None):
    req = req or ProbeRequest()
    return probe_runner.probe(name, mode=req.mode, include_search_examples=req.include_search_examples)


@app.post("/api/modules/{name}/promote-plan")
async def module_promote_plan(name: str, req: PromotionPlanRequest | None = None):
    req = req or PromotionPlanRequest()
    return probe_runner.promotion_plan(name, target=req.target, include_probe=req.include_probe)


@app.get("/api/adapters")
async def list_adapters():
    return adapter_registry.list_adapters()


@app.get("/api/repo-unification-worklist")
async def repo_unification_worklist(
    limit: int = Query(default=20, ge=1, le=100),
    include_probe: bool = False,
):
    return adapter_registry.unification_worklist(gitnexus=gitnexus_bridge, limit=limit, include_probe=include_probe)


@app.get("/api/slice-candidate-matrix")
async def slice_candidate_matrix(
    modules: list[str] | None = Query(default=None),
    limit_per_module: int = Query(default=12, ge=1, le=50),
    include_review: bool = False,
):
    return adapter_registry.slice_candidate_matrix(
        gitnexus=gitnexus_bridge,
        modules=modules,
        limit_per_module=limit_per_module,
        include_review=include_review,
    )


@app.get("/api/global/{system}/slices")
async def global_system_slices(system: str, modules: list[str] | None = Query(default=None)):
    return adapter_registry.canonical_slice_registry(gitnexus=gitnexus_bridge, system=system, modules=modules)


@app.get("/api/global/{system}/slices/{slice_id}")
async def global_system_slice(system: str, slice_id: str):
    return adapter_registry.canonical_slice(system, slice_id, gitnexus=gitnexus_bridge)


@app.get("/api/global/{system}/slices/{slice_id}/tree")
async def global_system_slice_tree(
    system: str,
    slice_id: str,
    max_depth: int = Query(default=2, ge=0, le=6),
    limit: int = Query(default=200, ge=1, le=1000),
):
    return adapter_registry.canonical_slice_tree(
        system,
        slice_id,
        gitnexus=gitnexus_bridge,
        max_depth=max_depth,
        limit=limit,
    )


@app.post("/api/global/{system}/slices/{slice_id}/call-plan")
async def global_system_slice_call_plan(system: str, slice_id: str, req: GlobalSystemCallPlanRequest):
    return adapter_registry.canonical_slice_call_plan(system, slice_id, req, gitnexus=gitnexus_bridge)


@app.get("/api/adapters/{name}")
async def inspect_adapter(name: str):
    return adapter_registry.describe(name)


@app.get("/api/adapters/{name}/surfaces")
async def adapter_surfaces(name: str, limit: int = Query(default=500, ge=1, le=5000)):
    return surface_catalog.catalog(name, limit=limit)


@app.get("/api/adapters/{name}/slice-candidates")
async def adapter_slice_candidates(name: str, limit: int = Query(default=20, ge=1, le=100)):
    return adapter_registry.slice_candidates(name, gitnexus=gitnexus_bridge, limit=limit)


@app.get("/api/adapters/{name}/slice-intake-plan")
async def adapter_slice_intake_plan(name: str, path: str = Query(min_length=1)):
    return adapter_registry.slice_intake_plan(name, path, gitnexus=gitnexus_bridge)


@app.post("/api/adapters/{name}/call")
async def adapter_call(name: str, req: AdapterCallRequest):
    return adapter_registry.call(name, req)


@app.get("/api/evidence/compose")
async def compose_evidence_index(
    modules: list[str] | None = Query(default=None),
    recursive: bool = True,
    limit_per_module: int = Query(default=80, ge=1, le=500),
):
    return runtime_topology.compose_evidence_all(
        modules=modules,
        recursive=recursive,
        limit_per_module=limit_per_module,
    )


@app.get("/api/modules/{name}/compose-evidence")
async def module_compose_evidence(
    name: str,
    recursive: bool = True,
    limit: int = Query(default=80, ge=1, le=500),
):
    return runtime_topology.compose_evidence(name, recursive=recursive, limit=limit)


@app.get("/api/runtime/topology")
async def runtime_topology_view(modules: list[str] | None = Query(default=None)):
    return runtime_topology.all_topologies(modules=modules)


@app.post("/api/runtime/health-check")
async def runtime_health_check(req: RuntimeHealthRequest | None = None):
    req = req or RuntimeHealthRequest()
    return runtime_topology.health_check(
        modules=req.modules,
        timeout_seconds=req.timeout_seconds,
        limit=req.limit,
    )


@app.post("/api/runtime/activation-plan")
async def runtime_activation_plan(req: RuntimeActivationPlanRequest):
    return runtime_activation.plan(req)


@app.get("/api/runtime/issues")
async def runtime_issue_report():
    return runtime_issues.report()


@app.get("/api/unified/workflows")
async def list_unified_workflows(modules: list[str] | None = Query(default=None)):
    return unified_workflows.list_workflows(modules=modules)


@app.get("/api/unified/workflows/{workflow}")
async def unified_workflow(workflow: str, modules: list[str] | None = Query(default=None)):
    return unified_workflows.workflow(workflow, modules=modules)


@app.post("/api/unified/workflows/{workflow}/route-plan")
async def unified_workflow_route_plan(workflow: str, req: ComposePlanRequest | None = None):
    req = req or ComposePlanRequest()
    return unified_workflows.route_plan(workflow, modules=req.modules)


@app.get("/api/unified/memory")
async def unified_memory_index():
    return {
        "workflow": "memory",
        "api": [
            "/api/unified/memory/capabilities",
            "/api/unified/memory/query",
            "/api/unified/memory/receipt-plan",
            "/api/unified/memory/runtime-preflight",
            "/api/unified/memory/corpus-import-plan",
            "/api/unified/memory/mmdb-import-compatibility",
        ],
        "policy": "health-check live runtime ports first; fall back to static adapter surfaces",
    }


@app.get("/api/unified/memory/capabilities")
async def unified_memory_capabilities():
    return memory_workflow.capabilities()


@app.post("/api/unified/memory/query")
async def unified_memory_query(req: MemoryQueryRequest):
    return memory_workflow.query_plan(req)


@app.post("/api/unified/memory/receipt-plan")
async def unified_memory_receipt_plan(req: MemoryQueryRequest):
    return memory_workflow.receipt_plan(req)


@app.get("/api/unified/memory/runtime-preflight")
async def unified_memory_runtime_preflight():
    return memory_workflow.runtime_preflight()


@app.post("/api/unified/memory/corpus-import-plan")
async def unified_memory_corpus_import_plan(req: MemoryCorpusImportPlanRequest | None = None):
    req = req or MemoryCorpusImportPlanRequest()
    return memory_workflow.corpus_import_plan(req, source_universe)


@app.post("/api/unified/memory/mmdb-import-compatibility")
async def unified_memory_mmdb_import_compatibility(req: MMDBImportCompatibilityRequest):
    return memory_workflow.mmdb_import_compatibility(req, source_universe)


@app.get("/api/unified/mcp-tools")
async def unified_mcp_tools_index():
    return {
        "workflow": "mcp_tools",
        "api": [
            "/api/unified/mcp-tools/capabilities",
            "/api/unified/mcp-tools/tools",
            "/api/unified/mcp-tools/tools/{tool_name}",
            "/api/unified/mcp-tools/call-plan",
        ],
        "policy": "plan against static tool contracts first; execute only after runtime transport is healthy and explicitly selected",
    }


@app.get("/api/unified/mcp-tools/capabilities")
async def unified_mcp_tools_capabilities():
    return mcp_tools_workflow.capabilities()


@app.get("/api/unified/mcp-tools/tools")
async def unified_mcp_tools_list(
    q: str | None = None,
    category: str | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
):
    return mcp_tools_workflow.list_tools(query=q, category=category, limit=limit)


@app.get("/api/unified/mcp-tools/tools/{tool_name}")
async def unified_mcp_tool_detail(tool_name: str):
    return mcp_tools_workflow.tool_detail(tool_name)


@app.post("/api/unified/mcp-tools/call-plan")
async def unified_mcp_tool_call_plan(req: MCPToolCallPlanRequest):
    return mcp_tools_workflow.call_plan(req)


@app.get("/api/unified/agent-orchestration")
async def unified_agent_orchestration_index():
    return {
        "workflow": "agent_orchestration",
        "api": [
            "/api/unified/agent-orchestration/capabilities",
            "/api/unified/agent-orchestration/plan",
        ],
        "policy": "compose is evidence for agent service topology; execution remains dry-run and approval-gated",
    }


@app.get("/api/unified/agent-orchestration/capabilities")
async def unified_agent_orchestration_capabilities():
    return agent_orchestration_workflow.capabilities()


@app.post("/api/unified/agent-orchestration/plan")
async def unified_agent_orchestration_plan(req: AgentOrchestrationPlanRequest):
    return agent_orchestration_workflow.plan(req)


@app.get("/api/unified/knowledge")
async def unified_knowledge_index():
    return {
        "workflow": "knowledge",
        "api": [
            "/api/unified/knowledge/capabilities",
            "/api/unified/knowledge/plan",
            "/api/unified/knowledge/runtime-preflight",
        ],
        "policy": "plan read/search/retrieval first; index, ingest, and store operations remain approval-gated",
    }


@app.get("/api/unified/knowledge/capabilities")
async def unified_knowledge_capabilities():
    return knowledge_workflow.capabilities()


@app.post("/api/unified/knowledge/plan")
async def unified_knowledge_plan(req: KnowledgePlanRequest):
    return knowledge_workflow.plan(req)


@app.get("/api/unified/knowledge/runtime-preflight")
async def unified_knowledge_runtime_preflight():
    return knowledge_workflow.runtime_preflight()


@app.post("/api/controller/search")
async def controller_search(req: SearchRequest):
    return adapter.search(req.module, req.query, glob=req.glob, limit=req.limit)


@app.post("/api/controller/compose-plan")
async def compose_plan(req: ComposePlanRequest):
    all_modules = registry.modules()
    selected = [m for m in all_modules if req.modules is None or m["name"] in req.modules]
    return {
        "goal": req.goal,
        "kernel": KERNEL_ID,
        "module_count": len(selected),
        "modules": [
            {
                "name": m["name"],
                "role": m.get("role"),
                "cloned": m.get("cloned"),
                "branch": m.get("branch_runtime") or m.get("default_branch"),
                "commit": m.get("pinned_commit_runtime") or m.get("pinned_commit"),
                "api": m.get("api_base"),
            }
            for m in selected
        ],
        "policy": {
            "repo_identity": "manifest-pinned module",
            "composition": "controller/adapters read module surfaces; do not nest .git histories",
            "mutation": "disabled by default" if not ALLOW_MUTATION else "enabled",
        },
    }


@app.post("/api/controller/probe")
async def controller_probe(req: ComposePlanRequest):
    modules = req.modules or default_promotion_modules()
    results = [probe_runner.probe(name, include_search_examples=False) for name in modules]
    return {"goal": req.goal, "modules": results}


@app.post("/api/controller/promotion-plan")
async def controller_promotion_plan(req: ComposePlanRequest):
    modules = req.modules or default_promotion_modules()
    plans = [probe_runner.promotion_plan(name, include_probe=True) for name in modules]
    return {"goal": req.goal, "target": "CMPLX-PartsFactory", "plans": plans}


@mcp.tool()
async def repo_kernel_list_modules() -> str:
    """List repo-kernel modules and runtime clone status as JSON."""
    return json.dumps({"modules": registry.modules()}, indent=2)


@mcp.tool()
async def repo_kernel_inspect_module(name: str) -> str:
    """Inspect one module's manifest, runtime branch, and pinned commit."""
    return json.dumps(registry.module(name), indent=2)


@mcp.tool()
async def repo_kernel_module_tree(name: str, path: str = ".", max_depth: int = 2, limit: int = 300) -> str:
    """Return a bounded module directory tree."""
    return json.dumps(adapter.tree(name, path, max_depth=max_depth, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_read_file(name: str, path: str, max_bytes: int = 200000) -> str:
    """Read a text file from a repo module."""
    return json.dumps(adapter.read_file(name, path, max_bytes=max_bytes), indent=2)


@mcp.tool()
async def repo_kernel_search(name: str, query: str, glob: str = "", limit: int = 50) -> str:
    """Search a repo module with ripgrep."""
    return json.dumps(adapter.search(name, query, glob=glob or None, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_promotion_ledger() -> str:
    """Return the repo promotion ledger as JSON."""
    return json.dumps(ledger.read(), indent=2)


@mcp.tool()
async def repo_kernel_sources() -> str:
    """List mounted source/evidence roots known to the repo kernel."""
    return json.dumps({"sources": source_universe.sources()}, indent=2)


@mcp.tool()
async def repo_kernel_source_inventory(request_json: str = "{}") -> str:
    """Run a bounded source-root inventory without extracting archives or mutating data."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.inventory(SourceInventoryRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_source_markers(request_json: str = "{}") -> str:
    """Return git/compose/archive/database/manifest markers from a bounded source inventory."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.markers(SourceInventoryRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_archive_manifest(request_json: str) -> str:
    """List zip archive contents without extracting them."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.archive_manifest(SourceArchiveManifestRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_archive_member_read(request_json: str) -> str:
    """Read one text member from a zip archive without extracting it to disk."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.archive_member_read(SourceArchiveMemberReadRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_archive_corpus_summary(request_json: str) -> str:
    """Parse a corpus MANIFEST.md inside a zip archive without extracting it."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.archive_corpus_summary(SourceArchiveCorpusSummaryRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_file_hash_slice(request_json: str = "{}") -> str:
    """Hash a bounded slice of files in a mounted source directory."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.file_hash_slice(FileHashSliceRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_archive_hash_slice(request_json: str) -> str:
    """Hash a bounded slice of members inside a zip archive without extracting them."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.archive_hash_slice(ArchiveHashSliceRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_archive_sqlite_quarantine_probe(request_json: str) -> str:
    """Extract one approved zip SQLite member to quarantine and inspect schema read-only."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.archive_sqlite_quarantine_probe(ArchiveSQLiteQuarantineProbeRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_hash_slice_batch(request_json: str) -> str:
    """Run multiple bounded file/archive hash slices and compare hashes across them."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.hash_slice_batch(HashSliceBatchRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_file_breakdown_plan(request_json: str) -> str:
    """Plan how to break an oversized file or zip member into parseable chunks if normal parsing fails."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.file_breakdown_plan(FileBreakdownPlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_quarantine_sqlite_preview(request_json: str) -> str:
    """Preview bounded rows from a quarantined SQLite copy with agentic memory hints."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.quarantine_sqlite_preview(QuarantineSQLitePreviewRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_mmdb_import_dry_run(request_json: str) -> str:
    """Generate a read-only MMDB memory import recipe from a quarantined SQLite copy."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.mmdb_import_dry_run(MMDBImportDryRunRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_archive_triage(request_json: str = "{}") -> str:
    """Rank archive files from bounded source scans for later manifest inspection."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.archive_triage(ArchiveTriageRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_archive_compare(request_json: str) -> str:
    """Compare zip archives by internal member signatures without extracting them."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.archive_compare(ArchiveCompareRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_archive_duplicate_candidates(request_json: str = "{}") -> str:
    """Find same-name/same-size archive duplicate candidates and compare zip member signatures."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.archive_duplicate_candidates(ArchiveDuplicateCandidateRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_cleanup_evidence(request_json: str = "{}") -> str:
    """Build a non-destructive cleanup evidence ledger from duplicate and corpus evidence."""
    payload = json.loads(request_json or "{}")
    return json.dumps(source_universe.cleanup_evidence(CleanupEvidenceRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_cleanup_ledger(status: str = "candidate", limit: int = 100) -> str:
    """List durable cleanup ledger records."""
    return json.dumps({"cleanup_ledger": self_state.list_table("cleanup_ledger", status=status or None, limit=limit)}, indent=2)


@mcp.tool()
async def repo_kernel_workfront() -> str:
    """Return the balanced multi-lane repo-kernel workfront."""
    return json.dumps(workfront_report(), indent=2)


@mcp.tool()
async def repo_kernel_probe_module(name: str, mode: str = "static") -> str:
    """Run a bounded capability probe for one repo module."""
    return json.dumps(probe_runner.probe(name, mode=mode, include_search_examples=True), indent=2)


@mcp.tool()
async def repo_kernel_promote_plan(name: str, target: str = "CMPLX-PartsFactory") -> str:
    """Create a behavior-first promotion plan for one repo module."""
    return json.dumps(probe_runner.promotion_plan(name, target=target, include_probe=True), indent=2)


@mcp.tool()
async def repo_kernel_list_adapters() -> str:
    """List available safe repo-kernel module adapters."""
    return json.dumps(adapter_registry.list_adapters(), indent=2)


@mcp.tool()
async def repo_kernel_repo_unification_worklist(limit: int = 20, include_probe: bool = False) -> str:
    """Return a GitNexus-informed worklist for repo adapter unification."""
    return json.dumps(
        adapter_registry.unification_worklist(gitnexus=gitnexus_bridge, limit=limit, include_probe=include_probe),
        indent=2,
    )


@mcp.tool()
async def repo_kernel_adapter_slice_candidates(name: str, limit: int = 20) -> str:
    """Return bounded slice candidates for a noisy repo module before promotion."""
    return json.dumps(adapter_registry.slice_candidates(name, gitnexus=gitnexus_bridge, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_slice_candidate_matrix(
    modules_json: str = "[]",
    limit_per_module: int = 12,
    include_review: bool = False,
) -> str:
    """Return a system-grouped matrix of bounded repo slice candidates."""
    modules = json.loads(modules_json or "[]")
    return json.dumps(
        adapter_registry.slice_candidate_matrix(
            gitnexus=gitnexus_bridge,
            modules=modules or None,
            limit_per_module=limit_per_module,
            include_review=include_review,
        ),
        indent=2,
    )


@mcp.tool()
async def repo_kernel_slice_intake_plan(name: str, path: str) -> str:
    """Plan how a bounded repo slice would become a canonical API capability."""
    return json.dumps(adapter_registry.slice_intake_plan(name, path, gitnexus=gitnexus_bridge), indent=2)


@mcp.tool()
async def repo_kernel_global_system_slices(system: str = "code-execution") -> str:
    """List canonical slice capabilities exposed for a global system."""
    return json.dumps(adapter_registry.canonical_slice_registry(gitnexus=gitnexus_bridge, system=system), indent=2)


@mcp.tool()
async def repo_kernel_global_system_slice(system: str, slice_id: str) -> str:
    """Return one canonical slice summary and intake plan."""
    return json.dumps(adapter_registry.canonical_slice(system, slice_id, gitnexus=gitnexus_bridge), indent=2)


@mcp.tool()
async def repo_kernel_code_execution_octa64() -> str:
    """Return the named octa64 code-execution capability summary."""
    return json.dumps(adapter_registry.octa64_capability(gitnexus=gitnexus_bridge), indent=2)


@mcp.tool()
async def repo_kernel_code_execution_octa64_tree(max_depth: int = 2, limit: int = 100) -> str:
    """Return the read-only octa64 source tree through the CMPLXDevKit adapter."""
    return json.dumps(adapter_registry.octa64_tree(max_depth=max_depth, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_code_execution_octa64_file(path: str, max_bytes: int = 120000) -> str:
    """Read one allowlisted octa64 source file."""
    return json.dumps(adapter_registry.octa64_read_file(path, max_bytes=max_bytes), indent=2)


@mcp.tool()
async def repo_kernel_code_execution_octa64_call_plan(request_json: str = "{}") -> str:
    """Plan an octa64 operation without executing it."""
    payload = json.loads(request_json or "{}")
    return json.dumps(adapter_registry.octa64_call_plan(GlobalSystemCallPlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_validation_mcp_os() -> str:
    """Return the named MCP OS validation capability summary."""
    return json.dumps(adapter_registry.mcp_os_validation_capability(gitnexus=gitnexus_bridge), indent=2)


@mcp.tool()
async def repo_kernel_validation_mcp_os_tree(max_depth: int = 2, limit: int = 120) -> str:
    """Return the read-only MCP OS validation source tree through the CMPLXDevKit adapter."""
    return json.dumps(adapter_registry.mcp_os_validation_tree(max_depth=max_depth, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_validation_mcp_os_file(path: str, max_bytes: int = 160000) -> str:
    """Read one allowlisted MCP OS validation source file."""
    return json.dumps(adapter_registry.mcp_os_validation_read_file(path, max_bytes=max_bytes), indent=2)


@mcp.tool()
async def repo_kernel_validation_mcp_os_call_plan(request_json: str = "{}") -> str:
    """Plan an MCP OS validation operation without executing it."""
    payload = json.loads(request_json or "{}")
    return json.dumps(adapter_registry.mcp_os_validation_call_plan(GlobalSystemCallPlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_synthesis_cqe_modular() -> str:
    """Return the named CQE modular synthesis capability summary."""
    return json.dumps(adapter_registry.cqe_modular_capability(gitnexus=gitnexus_bridge), indent=2)


@mcp.tool()
async def repo_kernel_synthesis_cqe_modular_tree(max_depth: int = 2, limit: int = 80) -> str:
    """Return the read-only CQE modular source tree through the CMPLXDevKit adapter."""
    return json.dumps(adapter_registry.cqe_modular_tree(max_depth=max_depth, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_synthesis_cqe_modular_file(path: str, max_bytes: int = 80000) -> str:
    """Read one allowlisted CQE modular source file."""
    return json.dumps(adapter_registry.cqe_modular_read_file(path, max_bytes=max_bytes), indent=2)


@mcp.tool()
async def repo_kernel_synthesis_cqe_modular_call_plan(request_json: str = "{}") -> str:
    """Plan a CQE modular synthesis operation without executing it."""
    payload = json.loads(request_json or "{}")
    return json.dumps(adapter_registry.cqe_modular_call_plan(GlobalSystemCallPlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_knowledge_devkit_ingest() -> str:
    """Return the named DevKit knowledge-ingest capability summary."""
    return json.dumps(adapter_registry.devkit_ingest_capability(gitnexus=gitnexus_bridge), indent=2)


@mcp.tool()
async def repo_kernel_knowledge_devkit_ingest_tree(max_depth: int = 2, limit: int = 80) -> str:
    """Return the read-only DevKit ingest source tree through the CMPLXDevKit adapter."""
    return json.dumps(adapter_registry.devkit_ingest_tree(max_depth=max_depth, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_knowledge_devkit_ingest_file(path: str, max_bytes: int = 80000) -> str:
    """Read one allowlisted DevKit ingest source file."""
    return json.dumps(adapter_registry.devkit_ingest_read_file(path, max_bytes=max_bytes), indent=2)


@mcp.tool()
async def repo_kernel_knowledge_devkit_ingest_call_plan(request_json: str = "{}") -> str:
    """Plan a DevKit ingest operation without executing it."""
    payload = json.loads(request_json or "{}")
    return json.dumps(adapter_registry.devkit_ingest_call_plan(GlobalSystemCallPlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_mcp_local_os() -> str:
    """Return the named local MCP OS capability summary."""
    return json.dumps(adapter_registry.mcp_local_os_capability(gitnexus=gitnexus_bridge), indent=2)


@mcp.tool()
async def repo_kernel_mcp_local_os_tree(max_depth: int = 2, limit: int = 200) -> str:
    """Return the read-only local MCP OS source tree through the CMPLXDevKit adapter."""
    return json.dumps(adapter_registry.mcp_local_os_tree(max_depth=max_depth, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_mcp_local_os_file(path: str, max_bytes: int = 180000) -> str:
    """Read one allowlisted local MCP OS source file."""
    return json.dumps(adapter_registry.mcp_local_os_read_file(path, max_bytes=max_bytes), indent=2)


@mcp.tool()
async def repo_kernel_mcp_local_os_call_plan(request_json: str = "{}") -> str:
    """Plan a local MCP OS operation without executing it."""
    payload = json.loads(request_json or "{}")
    return json.dumps(adapter_registry.mcp_local_os_call_plan(GlobalSystemCallPlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_adapter_surfaces(name: str, limit: int = 500) -> str:
    """Return statically extracted API and MCP surfaces for a module adapter."""
    return json.dumps(surface_catalog.catalog(name, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_adapter_call(name: str, action: str, args_json: str = "{}") -> str:
    """Call a safe module adapter action. args_json must be a JSON object."""
    try:
        args = json.loads(args_json or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid args_json: {exc}") from exc
    req = AdapterCallRequest(action=action, args=args)
    return json.dumps(adapter_registry.call(name, req), indent=2)


@mcp.tool()
async def repo_kernel_registered_bundle(request_json: str = "{}") -> str:
    """Describe the current registered systems bundle wrapper."""
    payload = json.loads(request_json or "{}")
    return json.dumps(registered_bundle.describe(RegisteredBundleRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_registered_bundle_run(request_json: str = "{}") -> str:
    """Run one safe wrapper command across the selected registered systems."""
    payload = json.loads(request_json or "{}")
    return json.dumps(registered_bundle.run(RegisteredBundleRunRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_global_system(system: str = "mcp", modules_json: str = "[]") -> str:
    """Describe a global system API assembled from registered repo-local services."""
    modules = json.loads(modules_json or "[]")
    return json.dumps(global_systems.describe(system, modules=modules or None), indent=2)


@mcp.tool()
async def repo_kernel_global_location_map(system: str | None = None, modules_json: str = "[]") -> str:
    """Return canonical paths, repo-local roots, and hosted port evidence for global systems."""
    modules = json.loads(modules_json or "[]")
    return json.dumps(global_systems.location_map(system=system, modules=modules or None), indent=2)


@mcp.tool()
async def repo_kernel_global_coverage(modules_json: str = "[]", limit_unassigned: int = 200) -> str:
    """Report which repo routes, tools, and runtime targets are covered or still unassigned."""
    modules = json.loads(modules_json or "[]")
    return json.dumps(global_systems.coverage(modules=modules or None, limit_unassigned=limit_unassigned), indent=2)


@mcp.tool()
async def repo_kernel_global_port_plan(modules_json: str = "[]") -> str:
    """Plan port ownership and reassignment behind the repo-kernel global control layer."""
    modules = json.loads(modules_json or "[]")
    return json.dumps(global_systems.port_reassignment_plan(modules=modules or None), indent=2)


@mcp.tool()
async def repo_kernel_global_runtime_slices(
    modules_json: str = "[]",
    check_health: bool = False,
    timeout_seconds: float = 0.7,
    limit: int = 18,
) -> str:
    """Rank the next live Docker-backed global systems to route behind repo-kernel."""
    modules = json.loads(modules_json or "[]")
    return json.dumps(
        global_systems.runtime_slice_plan(
            modules=modules or None,
            check_health=check_health,
            timeout_seconds=timeout_seconds,
            limit=limit,
        ),
        indent=2,
    )


@mcp.tool()
async def repo_kernel_global_tool_workbook(check_health: bool = False, timeout_seconds: float = 0.7) -> str:
    """Return the live workbook of routed tools available through repo-kernel."""
    return json.dumps(global_systems.tool_workbook(check_health=check_health, timeout_seconds=timeout_seconds), indent=2)


@mcp.tool()
async def repo_kernel_global_state(check_health: bool = False, timeout_seconds: float = 0.7) -> str:
    """Return a compact, fast state summary of the global control layer."""
    return json.dumps(global_systems.compact_state(check_health=check_health, timeout_seconds=timeout_seconds), indent=2)


@mcp.tool()
async def repo_kernel_clean_system_image_plan() -> str:
    """Return the plan for turning gathered repo history into one clean governed system image."""
    return json.dumps(global_systems.clean_system_image_plan(), indent=2)


@mcp.tool()
async def repo_kernel_capability_registry() -> str:
    """Return the staged canonical capability registry for the clean system image."""
    return json.dumps(global_systems.capability_registry(), indent=2)


@mcp.tool()
async def repo_kernel_prototype_evidence() -> str:
    """Return bounded evidence from Claude's Unification Prototypes workspace."""
    return json.dumps(prototype_evidence.overview(), indent=2)


@mcp.tool()
async def repo_kernel_prototype_evidence_docs(limit: int = 50) -> str:
    """List harvested docs from Claude's prototype workspace as capability-claim evidence."""
    return json.dumps(prototype_evidence.docs(limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_prototype_evidence_bridges(limit: int = 50) -> str:
    """List prototype bridge-density evidence for cross-system routing priority."""
    return json.dumps(prototype_evidence.bridges(limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_prototype_evidence_search(query: str, limit: int = 20) -> str:
    """Search Claude prototype docs and claims as read-only knowledge evidence."""
    return json.dumps(prototype_evidence.search(query, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_prototype_evidence_read(path: str, max_bytes: int = 120000) -> str:
    """Read one bounded prototype evidence file by repo-relative path."""
    return json.dumps(prototype_evidence.read(PrototypeEvidenceReadRequest(path=path, max_bytes=max_bytes)), indent=2)


@mcp.tool()
async def repo_kernel_gitnexus_status(include_repos: bool = True, repo_limit: int = 20) -> str:
    """Return GitNexus API, indexed repo, and aggregate-report status."""
    return json.dumps(gitnexus_bridge.status(include_repos=include_repos, repo_limit=repo_limit), indent=2)


@mcp.tool()
async def repo_kernel_gitnexus_repos(limit: int = 100) -> str:
    """List GitNexus indexed repositories, sorted by graph size."""
    return json.dumps(gitnexus_bridge.repos(limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_gitnexus_graph_summary(repo: str, limit: int = 20) -> str:
    """Return a canned read-only GitNexus graph summary for one indexed repo."""
    return json.dumps(gitnexus_bridge.graph_summary(repo=repo, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_gitnexus_unification_hints(limit: int = 12) -> str:
    """Use GitNexus graph and report evidence to rank unification work candidates."""
    return json.dumps(gitnexus_bridge.unification_hints(limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_gitnexus_aggregate() -> str:
    """Summarize the local GitNexus historical report aggregate database."""
    return json.dumps(gitnexus_bridge.aggregate_summary(), indent=2)


@mcp.tool()
async def repo_kernel_gitnexus_aggregate_search(
    query: str | None = None,
    system: str | None = None,
    language: str | None = None,
    limit: int = 50,
) -> str:
    """Search local GitNexus historical report evidence before promotion work."""
    return json.dumps(
        gitnexus_bridge.aggregate_search(q=query, system=system, language=language, limit=limit),
        indent=2,
    )


@mcp.tool()
async def repo_kernel_global_query(request_json: str = "{}") -> str:
    """Run one read-only fanout query across routed global systems."""
    payload = json.loads(request_json or "{}")
    return json.dumps(global_systems.global_query(GlobalQueryRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_global_system_tools(system: str = "mcp", query: str | None = None, limit: int = 500) -> str:
    """List normalized tools behind a global system API."""
    return json.dumps(global_systems.tools(system, q=query, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_global_memory_upstreams(check_health: bool = False, timeout_seconds: float = 0.7) -> str:
    """Return the routed memory upstream contract behind /api/global/memory."""
    return json.dumps(
        global_systems.memory_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds),
        indent=2,
    )


@mcp.tool()
async def repo_kernel_global_memory_read(service: str, path: str = "", query_json: str = "{}") -> str:
    """Run an approved read-only request through the global memory controller."""
    query = json.loads(query_json or "{}")
    return json.dumps(global_systems.memory_read_proxy(service, path, query=query), indent=2)


@mcp.tool()
async def repo_kernel_global_geometry_upstreams(check_health: bool = False, timeout_seconds: float = 0.7) -> str:
    """Return the routed geometry upstream contract behind /api/global/geometry."""
    return json.dumps(
        global_systems.geometry_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds),
        indent=2,
    )


@mcp.tool()
async def repo_kernel_global_geometry_read(service: str, path: str = "", query_json: str = "{}") -> str:
    """Run an approved read-only request through the global geometry controller."""
    query = json.loads(query_json or "{}")
    return json.dumps(global_systems.geometry_read_proxy(service, path, query=query), indent=2)


@mcp.tool()
async def repo_kernel_global_operations_upstreams(check_health: bool = False, timeout_seconds: float = 0.7) -> str:
    """Return the routed operations upstream contract behind /api/global/operations."""
    return json.dumps(
        global_systems.operations_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds),
        indent=2,
    )


@mcp.tool()
async def repo_kernel_global_operations_read(service: str, path: str = "", query_json: str = "{}") -> str:
    """Run an approved read-only request through the global operations controller."""
    query = json.loads(query_json or "{}")
    return json.dumps(global_systems.operations_read_proxy(service, path, query=query), indent=2)


@mcp.tool()
async def repo_kernel_global_knowledge_upstreams(check_health: bool = False, timeout_seconds: float = 0.7) -> str:
    """Return the routed knowledge upstream contract behind /api/global/knowledge."""
    return json.dumps(
        global_systems.knowledge_routing_contract(check_health=check_health, timeout_seconds=timeout_seconds),
        indent=2,
    )


@mcp.tool()
async def repo_kernel_global_knowledge_read(service: str, path: str = "", query_json: str = "{}") -> str:
    """Run an approved read-only request through the global knowledge controller."""
    query = json.loads(query_json or "{}")
    return json.dumps(global_systems.knowledge_read_proxy(service, path, query=query), indent=2)


@mcp.tool()
async def repo_kernel_global_system_skills(system: str = "mcp", limit: int = 500) -> str:
    """List repo-defined skills associated with a global system API."""
    return json.dumps(global_systems.skills(system, limit=limit), indent=2)


@mcp.tool()
async def repo_kernel_global_system_call_plan(system: str = "mcp", request_json: str = "{}") -> str:
    """Plan a global system operation without executing live services."""
    payload = json.loads(request_json or "{}")
    return json.dumps(global_systems.call_plan(system, GlobalSystemCallPlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_runtime_topology(modules_json: str = "[]") -> str:
    """Return documented and compose-derived runtime ports for module adapters."""
    modules = json.loads(modules_json or "[]")
    return json.dumps(runtime_topology.all_topologies(modules=modules or None), indent=2)


@mcp.tool()
async def repo_kernel_compose_evidence(modules_json: str = "[]", recursive: bool = True, limit_per_module: int = 80) -> str:
    """Summarize compose files as preflight evidence, not launch commands."""
    modules = json.loads(modules_json or "[]")
    return json.dumps(
        runtime_topology.compose_evidence_all(
            modules=modules or None,
            recursive=recursive,
            limit_per_module=limit_per_module,
        ),
        indent=2,
    )


@mcp.tool()
async def repo_kernel_runtime_activation_plan(request_json: str = "{}") -> str:
    """Plan which repo services/ports to activate for a workflow without starting them."""
    payload = json.loads(request_json or "{}")
    return json.dumps(runtime_activation.plan(RuntimeActivationPlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_runtime_issues() -> str:
    """Return operational issues detected in runtime topology and activation plans."""
    return json.dumps(runtime_issues.report(), indent=2)


@mcp.tool()
async def repo_kernel_unified_workflows() -> str:
    """List AI workflow layers that can be unified across promoted modules."""
    return json.dumps(unified_workflows.list_workflows(), indent=2)


@mcp.tool()
async def repo_kernel_unified_route_plan(workflow: str, modules_json: str = "[]") -> str:
    """Return a health-first route plan for one unified AI workflow."""
    modules = json.loads(modules_json or "[]")
    return json.dumps(unified_workflows.route_plan(workflow, modules=modules or None), indent=2)


@mcp.tool()
async def repo_kernel_memory_capabilities() -> str:
    """Return the first unified memory API layer capabilities."""
    return json.dumps(memory_workflow.capabilities(), indent=2)


@mcp.tool()
async def repo_kernel_memory_query_plan(request_json: str = "{}") -> str:
    """Plan a unified memory query across live ports and static adapter surfaces."""
    payload = json.loads(request_json or "{}")
    return json.dumps(memory_workflow.query_plan(MemoryQueryRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_memory_runtime_preflight() -> str:
    """Return the focused memory runtime preflight checklist without starting services."""
    return json.dumps(memory_workflow.runtime_preflight(), indent=2)


@mcp.tool()
async def repo_kernel_memory_corpus_import_plan(request_json: str = "{}") -> str:
    """Plan a memory corpus import from archive evidence without extracting or writing databases."""
    payload = json.loads(request_json or "{}")
    return json.dumps(memory_workflow.corpus_import_plan(MemoryCorpusImportPlanRequest(**payload), source_universe), indent=2)


@mcp.tool()
async def repo_kernel_memory_mmdb_import_compatibility(request_json: str) -> str:
    """Compare a quarantined MMDB dry-run recipe against discovered live/static memory surfaces."""
    payload = json.loads(request_json or "{}")
    return json.dumps(memory_workflow.mmdb_import_compatibility(MMDBImportCompatibilityRequest(**payload), source_universe), indent=2)


@mcp.tool()
async def repo_kernel_mcp_tool_capabilities() -> str:
    """Return unified MCP tool capabilities across promoted repo modules."""
    return json.dumps(mcp_tools_workflow.capabilities(), indent=2)


@mcp.tool()
async def repo_kernel_mcp_tool_call_plan(request_json: str) -> str:
    """Plan a unified MCP tool call without executing it."""
    payload = json.loads(request_json or "{}")
    return json.dumps(mcp_tools_workflow.call_plan(MCPToolCallPlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_agent_orchestration_capabilities() -> str:
    """Return unified agent orchestration capabilities across promoted modules."""
    return json.dumps(agent_orchestration_workflow.capabilities(), indent=2)


@mcp.tool()
async def repo_kernel_agent_orchestration_plan(request_json: str = "{}") -> str:
    """Plan an agent orchestration operation without executing or spawning agents."""
    payload = json.loads(request_json or "{}")
    return json.dumps(agent_orchestration_workflow.plan(AgentOrchestrationPlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_knowledge_capabilities() -> str:
    """Return unified knowledge/search/retrieval capabilities across promoted modules."""
    return json.dumps(knowledge_workflow.capabilities(), indent=2)


@mcp.tool()
async def repo_kernel_knowledge_plan(request_json: str = "{}") -> str:
    """Plan a knowledge, corpus, search, or retrieval operation without indexing or writing."""
    payload = json.loads(request_json or "{}")
    return json.dumps(knowledge_workflow.plan(KnowledgePlanRequest(**payload)), indent=2)


@mcp.tool()
async def repo_kernel_knowledge_runtime_preflight() -> str:
    """Return knowledge workflow runtime hints and health without starting services."""
    return json.dumps(knowledge_workflow.runtime_preflight(), indent=2)


@mcp.tool()
async def repo_kernel_self_status() -> str:
    """Return durable builder self-state status, open issues, and next actions."""
    return json.dumps(self_state.status(), indent=2)


@mcp.tool()
async def repo_kernel_self_seed_current() -> str:
    """Seed durable builder self-state from current repo-kernel knowledge."""
    return json.dumps(seed_self_state(), indent=2)


@mcp.tool()
async def repo_kernel_self_next_actions(status: str = "open", limit: int = 20) -> str:
    """List durable next actions for future work."""
    return json.dumps({"next_actions": self_state.list_table("next_actions", status=status or None, limit=limit)}, indent=2)


@mcp.tool()
async def repo_kernel_self_session_brief() -> str:
    """Generate and return a future-session brief."""
    return json.dumps(self_state.generate_brief(), indent=2)


app.mount("/mcp", mcp.sse_app())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=int(os.environ.get("REPO_KERNEL_PORT", "8786")))
