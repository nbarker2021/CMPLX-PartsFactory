"""
Rule library loader — YAML token / language / shell rules.

Libraries merge additively; later files override same-named filters.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from .shell_config import ShellConfig
from .token_index.language import LanguageFilter, REGISTRY, any_filter

logger = logging.getLogger(__name__)

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


@dataclass
class RuleLibraryBundle:
    version: str = "1"
    token_rules: dict[str, Any] = field(default_factory=dict)
    language_filters: dict[str, LanguageFilter] = field(default_factory=dict)
    shell_config: Optional[ShellConfig] = None
    source_paths: list[str] = field(default_factory=list)


class RuleLibraryLoader:
    """Load and merge rule libraries from ``data/rule_libs/`` trees."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else Path("data/rule_libs")

    def merge(self, *paths: str | Path) -> RuleLibraryBundle:
        bundle = RuleLibraryBundle()
        bundle.language_filters["any"] = any_filter()

        for path in paths:
            p = Path(path)
            if p.is_dir():
                for yaml_file in sorted(p.rglob("*.yaml")):
                    self._load_file(yaml_file, bundle)
            elif p.is_file():
                self._load_file(p, bundle)
            else:
                logger.warning("rule lib path missing: %s", p)

        if bundle.shell_config is None:
            shell_path = self.root / "shell" / "morphon_shell.yaml"
            if shell_path.is_file():
                self._load_file(shell_path, bundle)

        return bundle

    def list_libraries(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted(str(p) for p in self.root.rglob("*.yaml"))

    def validate(self, *paths: str | Path) -> list[str]:
        errors: list[str] = []
        targets = list(paths) if paths else [self.root]
        for path in targets:
            p = Path(path)
            files = sorted(p.rglob("*.yaml")) if p.is_dir() else [p]
            for f in files:
                if not f.is_file():
                    errors.append(f"missing: {f}")
                    continue
                try:
                    data = self._read_yaml(f)
                    errors.extend(self._validate_doc(data, f))
                except Exception as exc:
                    errors.append(f"{f}: {exc}")
        return errors

    def _load_file(self, path: Path, bundle: RuleLibraryBundle) -> None:
        data = self._read_yaml(path)
        bundle.source_paths.append(str(path))
        bundle.version = str(data.get("version", bundle.version))

        kind = data.get("kind", self._infer_kind(path))
        if kind == "language":
            filt = self._parse_language(data)
            bundle.language_filters[filt.name] = filt
        elif kind == "token":
            bundle.token_rules.update(data.get("rules", {}))
        elif kind == "shell":
            bundle.shell_config = self._parse_shell(data)
        else:
            logger.debug("unknown rule kind %s in %s", kind, path)

    @staticmethod
    def _infer_kind(path: Path) -> str:
        parent = path.parent.name
        if parent in ("token", "language", "shell"):
            return parent
        return str(path.stem)

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        if yaml is None:
            raise RuntimeError("PyYAML required for rule libraries (pip install pyyaml)")
        with path.open(encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
        if not isinstance(doc, dict):
            raise ValueError(f"expected mapping in {path}")
        return doc

    @staticmethod
    def _parse_language(data: dict[str, Any]) -> LanguageFilter:
        name = str(data.get("name", "custom"))
        common = frozenset(str(x).lower() for x in data.get("common_bigrams", []))
        forbidden = frozenset(str(x).lower() for x in data.get("forbidden_bigrams", []))
        min_common = int(data.get("min_common", 1))
        return LanguageFilter(
            name=name,
            common_bigrams=common,
            forbidden_bigrams=forbidden,
            min_common=min_common,
        )

    @staticmethod
    def _parse_shell(data: dict[str, Any]) -> ShellConfig:
        cfg = data.get("config", data)
        return ShellConfig(
            max_arity=int(cfg.get("max_arity", 8)),
            bond_separator=str(cfg.get("bond_separator", "|")),
            gate_mode=str(cfg.get("gate_mode", "govern")),
            language=str(cfg.get("language", "any")),
        )

    @staticmethod
    def _validate_doc(data: dict[str, Any], path: Path) -> list[str]:
        errors: list[str] = []
        if "kind" not in data and "name" not in data and "config" not in data:
            errors.append(f"{path}: missing kind/name/config")
        kind = data.get("kind", "")
        if kind == "language" and "name" not in data:
            errors.append(f"{path}: language rule requires name")
        return errors


def apply_language_filters(bundle: RuleLibraryBundle) -> None:
    """Register merged language filters into the global REGISTRY."""
    for name, filt in bundle.language_filters.items():
        REGISTRY[name] = filt


def filters_from_paths(*lib_paths: str | Path) -> dict[str, LanguageFilter]:
    loader = RuleLibraryLoader()
    bundle = loader.merge(*lib_paths) if lib_paths else loader.merge(loader.root)
    apply_language_filters(bundle)
    return dict(bundle.language_filters)


__all__ = [
    "RuleLibraryBundle",
    "RuleLibraryLoader",
    "apply_language_filters",
    "filters_from_paths",
]
