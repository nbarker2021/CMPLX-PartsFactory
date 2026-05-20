"""ArtifactScanner — discover and fingerprint every Python file in the yard."""

from __future__ import annotations

import ast
import hashlib
import os
import pathlib
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class ArtifactRecord:
    """One discovered file with all metadata needed for canonicalization."""

    artifact_id: str          # SHA-256 of (path + content)
    rel_path: str             # Path relative to yard root
    abs_path: str             # Absolute path on disk
    basename: str             # Filename only
    size_bytes: int
    lines: int
    content_hash: str         # SHA-256 of raw content
    ast_hash: str             # SHA-256 of normalized AST
    top_level: str            # JSON list of (type, name) tuples
    repo_tag: str             # Which repo this came from
    scan_batch: str           # ISO timestamp of scan


class _ASTNormalizer(ast.NodeTransformer):
    """Strip variable names, literals, and docstrings to get structural identity."""

    def visit_Name(self, node: ast.Name) -> ast.Name:
        return ast.Name(id="_", ctx=node.ctx)

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        if isinstance(node.value, str):
            return ast.Constant(value="")
        if isinstance(node.value, (int, float)):
            return ast.Constant(value=0)
        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        return ast.arg(arg="_", annotation=None, type_comment=None)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node.body = [s for s in node.body if not isinstance(s, ast.Expr) or
                     not isinstance(s.value, ast.Constant) or
                     not isinstance(s.value.value, str)]
        return self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef


def _ast_hash(source: str) -> str:
    """Return SHA-256 of normalized AST dump."""
    try:
        tree = ast.parse(source)
        norm = _ASTNormalizer()
        tree = norm.visit(tree)
        ast.fix_missing_locations(tree)
        dump = ast.dump(tree, include_attributes=False)
        return hashlib.sha256(dump.encode()).hexdigest()
    except SyntaxError:
        return "INVALID_SYNTAX"
    except Exception:
        return "AST_ERROR"


def _top_level_defs(source: str) -> str:
    """JSON-like string of top-level class/function names."""
    try:
        tree = ast.parse(source)
        defs = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                defs.append(("class", node.name))
            elif isinstance(node, ast.FunctionDef):
                defs.append(("def", node.name))
            elif isinstance(node, ast.AsyncFunctionDef):
                defs.append(("async_def", node.name))
        return str(defs)
    except Exception:
        return "[]"


class ArtifactScanner:
    """Walks the creative yard and yields ArtifactRecords."""

    SKIP_DIRS = {
        ".git", ".opencode", "__pycache__", "node_modules",
        ".venv", "venv", "dist", "build", ".pytest_cache",
    }

    def __init__(self, yard_root: str, repo_tags: dict[str, str] | None = None):
        self.yard_root = pathlib.Path(yard_root).resolve()
        # repo_tags maps absolute-path-prefix -> tag name
        self.repo_tags = repo_tags or {}
        self.batch_id = __import__("datetime").datetime.utcnow().isoformat()

    def _tag_for(self, abs_path: pathlib.Path) -> str:
        p = str(abs_path)
        for prefix, tag in sorted(self.repo_tags.items(), key=lambda x: -len(x[0])):
            if p.startswith(prefix):
                return tag
        return "unknown"

    def scan(self) -> Iterator[ArtifactRecord]:
        for root, dirs, files in os.walk(self.yard_root):
            # Prune skip directories
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                abs_p = pathlib.Path(root) / fname
                rel_p = abs_p.relative_to(self.yard_root)
                content = abs_p.read_text(encoding="utf-8", errors="replace")
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                artifact_id = hashlib.sha256(
                    (str(rel_p) + content_hash).encode()
                ).hexdigest()
                yield ArtifactRecord(
                    artifact_id=artifact_id,
                    rel_path=str(rel_p).replace("\\", "/"),
                    abs_path=str(abs_p).replace("\\", "/"),
                    basename=fname,
                    size_bytes=len(content.encode()),
                    lines=content.count("\n") + 1,
                    content_hash=content_hash,
                    ast_hash=_ast_hash(content),
                    top_level=_top_level_defs(content),
                    repo_tag=self._tag_for(abs_p),
                    scan_batch=self.batch_id,
                )

    def scan_single_repo(self, repo_path: str, tag: str) -> Iterator[ArtifactRecord]:
        """Override tags for a single repo walk."""
        old_tags = self.repo_tags
        self.repo_tags = {str(pathlib.Path(repo_path).resolve()): tag}
        yield from self.scan()
        self.repo_tags = old_tags
