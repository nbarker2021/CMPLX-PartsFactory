"""
SNAPLabel + SNAPRole + LabelRule — the dimensional labeling primitives.

`SNAPLabel` carries five dimensions of labels (structural, semantic,
quality, risk, domain) plus a custom map. The original canonical was a
Frankenstein merge (an Enum that was also a dataclass); split here
into clean concerns:

  - `SNAPRole` is the enum of process roles (INPUT/OUTPUT/TRANSFORM/...).
  - `SNAPLabel` is the dataclass with the dimensional label sets.
  - `LabelRule` is the named, prioritized rule a `SNAPLabeler` applies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Process roles (from the original canonical's enum half)
# ---------------------------------------------------------------------------

class SNAPRole(str, Enum):
    """The role an atom plays in a SNAP pipeline."""
    INPUT = "input"
    OUTPUT = "output"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    PERSIST = "persist"
    TRANSMIT = "transmit"
    RECEIVE = "receive"
    ORCHESTRATE = "orchestrate"


# ---------------------------------------------------------------------------
# SNAPLabel — five-dimensional label set
# ---------------------------------------------------------------------------

@dataclass
class SNAPLabel:
    """The multi-dimensional label set attached to a single item.

    Five built-in dimensions + a `custom` open-ended map. Labels are
    `set[str]`; `all_labels` returns their flat union.
    """
    item_key: str = ""
    structural: set[str] = field(default_factory=set)
    semantic: set[str] = field(default_factory=set)
    quality: set[str] = field(default_factory=set)
    risk: set[str] = field(default_factory=set)
    domain: set[str] = field(default_factory=set)
    custom: dict[str, set[str]] = field(default_factory=dict)

    @property
    def all_labels(self) -> set[str]:
        out: set[str] = set()
        out |= self.structural
        out |= self.semantic
        out |= self.quality
        out |= self.risk
        out |= self.domain
        for v in self.custom.values():
            out |= v
        return out

    def has(self, label: str) -> bool:
        return label in self.all_labels

    def to_dict(self) -> dict:
        return {
            "item_key": self.item_key,
            "structural": sorted(self.structural),
            "semantic": sorted(self.semantic),
            "quality": sorted(self.quality),
            "risk": sorted(self.risk),
            "domain": sorted(self.domain),
            "custom": {k: sorted(v) for k, v in self.custom.items()},
        }


# ---------------------------------------------------------------------------
# LabelRule — the unit of registration in a SNAPLabeler
# ---------------------------------------------------------------------------

@dataclass
class LabelRule:
    """A rule the labeler can apply to an item.

    - `name`: stable id (for logging / debugging).
    - `dimension`: which `SNAPLabel` field the rule writes to. Use
      `"custom:<key>"` to write into `SNAPLabel.custom[<key>]`.
    - `labels`: the label strings to add when the matcher fires.
    - `matcher(item, ctx) -> bool`: deciding predicate.
    - `priority`: lower = runs earlier (deterministic ordering).
    """
    name: str
    dimension: str
    labels: list[str]
    matcher: Callable[[Any, dict], bool]
    priority: int = 100
