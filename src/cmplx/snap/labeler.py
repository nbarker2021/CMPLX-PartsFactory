"""
SNAPLabeler — exhaustive rule-based labeler.

Adapted directly from `cmplx_pending/snap/SNAPLabeler.py` (4-variant
union, 11 methods, 5 conflicts resolved). The original used module-
level logger calls and inline imports; the version here is a clean
dataclass-friendly implementation that runs without external deps.

Builtin rules cover:
  - structural: class / function / module / string / dict / numeric / list
  - domain: e8, leech, morsr, morphonic, quorum, thinktank, governance,
    geometric, conservation (regex-keyed against text)
  - quality: documented (has __doc__), typed (has __annotations__)
  - risk: uses_exec, uses_subprocess, needs_review (when ctx.tested is False)
"""
from __future__ import annotations

import inspect
import re
from typing import Any, Optional

from .label import LabelRule, SNAPLabel


_DOMAIN_PATTERNS = {
    "e8":           re.compile(r"\be8\b|e8_lattice|e8lattice", re.I),
    "leech":        re.compile(r"\bleech\b|leech_lattice", re.I),
    "morsr":        re.compile(r"\bmorsr\b", re.I),
    "morphonic":    re.compile(r"morphon|morphonic|mglc", re.I),
    "quorum":       re.compile(r"\bquorum\b", re.I),
    "thinktank":    re.compile(r"think.?tank", re.I),
    "governance":   re.compile(r"governance|digital.?root|witness", re.I),
    "geometric":    re.compile(r"geometric|lattice|weyl|niemeier", re.I),
    "conservation": re.compile(r"conservation|delta.?phi|entropy", re.I),
}


class SNAPLabeler:
    """Apply every registered rule to every item.

    >>> labeler = SNAPLabeler()
    >>> label = labeler.label("class Foo:", key="foo.py")
    >>> "string" in label.structural
    True
    """

    name: str = "snap_labeler"

    def __init__(self) -> None:
        self._rules: list[LabelRule] = []
        self._label_cache: dict[str, SNAPLabel] = {}
        self._register_builtins()

    # ── Public API ────────────────────────────────────────────────────

    def add_rule(self, rule: LabelRule) -> None:
        self._rules.append(rule)

    def clear_cache(self) -> None:
        self._label_cache.clear()

    def get_cached(self, key: str) -> Optional[SNAPLabel]:
        return self._label_cache.get(key)

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def label(self, item: Any, key: str = "", context: Optional[dict] = None) -> SNAPLabel:
        """Apply every rule (in priority order) to `item`; return label."""
        ctx = context or {}
        result = SNAPLabel(item_key=key or str(id(item)))
        for rule in sorted(self._rules, key=lambda r: r.priority):
            try:
                if rule.matcher(item, ctx):
                    self._apply_rule(result, rule)
            except Exception:
                # Buggy rules don't crash the labeler; they just no-op.
                pass
        self._label_cache[result.item_key] = result
        return result

    def label_batch(
        self,
        items: list[Any],
        keys: Optional[list[str]] = None,
    ) -> list[SNAPLabel]:
        keys = keys or [str(i) for i in range(len(items))]
        return [self.label(it, k) for it, k in zip(items, keys)]

    def query_by_label(self, label: str) -> list[SNAPLabel]:
        """Return all cached labels containing `label` in any dimension."""
        return [sl for sl in self._label_cache.values() if sl.has(label)]

    def register_dynamic_label(self, snap_key: str, label: str) -> SNAPLabel:
        """Mint a user/ingest label for a snap_key not covered by rules."""
        key = f"dynamic:{snap_key}:{label}"
        result = SNAPLabel(item_key=key)
        result.semantic.add(label.strip().lower())
        result.custom.setdefault("snap_key", set()).add(snap_key)
        self._label_cache[key] = result
        return result

    # ── Internals ─────────────────────────────────────────────────────

    @staticmethod
    def _apply_rule(label: SNAPLabel, rule: LabelRule) -> None:
        dim = rule.dimension
        if dim.startswith("custom:"):
            key = dim.split(":", 1)[1]
            label.custom.setdefault(key, set()).update(rule.labels)
            return
        target = getattr(label, dim, None)
        if isinstance(target, set):
            target.update(rule.labels)

    def _register_builtins(self) -> None:
        add = self.add_rule

        # Structural
        add(LabelRule("is_class", "structural", ["class"],
                      lambda it, _: inspect.isclass(it)))
        add(LabelRule("is_function", "structural", ["function"],
                      lambda it, _: callable(it) and not inspect.isclass(it)))
        add(LabelRule("is_module", "structural", ["module"],
                      lambda it, _: inspect.ismodule(it)))
        add(LabelRule("is_string", "structural", ["string", "text"],
                      lambda it, _: isinstance(it, str)))
        add(LabelRule("is_dict", "structural", ["dict", "mapping"],
                      lambda it, _: isinstance(it, dict)))
        add(LabelRule("is_numeric", "structural", ["numeric"],
                      lambda it, _: isinstance(it, (int, float))
                                    and not isinstance(it, bool)))
        add(LabelRule("is_list", "structural", ["list", "sequence"],
                      lambda it, _: isinstance(it, (list, tuple))))

        # Domain (regex over text or stringified item)
        for domain_name, pattern in _DOMAIN_PATTERNS.items():
            add(LabelRule(
                name=f"domain_{domain_name}",
                dimension="domain",
                labels=[domain_name],
                matcher=_make_domain_matcher(pattern),
            ))

        # Quality
        add(LabelRule("has_docstring", "quality", ["documented"],
                      lambda it, _: callable(it) and bool(getattr(it, "__doc__", None))))
        add(LabelRule("has_type_hints", "quality", ["typed"],
                      lambda it, _: callable(it) and bool(getattr(it, "__annotations__", {}))))

        # Risk
        add(LabelRule("exec_usage", "risk",
                      ["security_relevant", "uses_exec"],
                      lambda it, _: isinstance(it, str)
                                    and ("exec(" in it or "eval(" in it)))
        add(LabelRule("subprocess_usage", "risk",
                      ["security_relevant", "uses_subprocess"],
                      lambda it, _: isinstance(it, str) and "subprocess" in it))
        add(LabelRule("untested_context", "risk", ["needs_review"],
                      lambda _, ctx: ctx.get("tested") is False))


def _make_domain_matcher(pattern: re.Pattern):
    def _match(item, ctx):
        text = ctx.get("text", "") or (item if isinstance(item, str) else "")
        return bool(pattern.search(str(text)))
    return _match
