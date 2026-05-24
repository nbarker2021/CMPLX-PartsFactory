"""Core economic types — state, requests, and enums."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

RESOURCE_KEYS = [
    "cpu_ms",
    "gpu_ms",
    "ram_mb_s",
    "io_mb",
    "net_mb",
    "tokens",
    "embed_ops",
    "hash_ops",
    "store_ops",
]


class CommissionStatus(str, Enum):
    OPEN = "open"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISPUTED = "disputed"


class ItemType(str, Enum):
    BRAIN = "brain"
    LABEL_SET = "label_set"
    TRAINING_DATA = "training_data"


@dataclass
class BalanceSheet:
    debt: float = 0.0
    interest: float = 0.02
    credit_limit: float = 200.0
    in_default: bool = False


@dataclass
class EconomyState:
    resources: Dict[str, float] = field(
        default_factory=lambda: {k: 1000.0 for k in RESOURCE_KEYS}
    )
    prices: Dict[str, float] = field(
        default_factory=lambda: {k: 1.0 for k in RESOURCE_KEYS}
    )
    market_temp: float = 0.2
    supply_chain: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "tokens": ["cpu_ms", "ram_mb_s"],
            "embed_ops": ["gpu_ms", "ram_mb_s"],
            "hash_ops": ["cpu_ms", "io_mb"],
            "store_ops": ["io_mb", "net_mb"],
            "cpu_ms": [],
            "gpu_ms": [],
            "ram_mb_s": [],
            "io_mb": [],
            "net_mb": [],
        }
    )


@dataclass
class Commission:
    commission_id: str
    requester: str
    task: str
    reward: float
    status: CommissionStatus = CommissionStatus.OPEN
    snap_labels: List[str] = field(default_factory=list)
    deadline_hours: float = 24.0


@dataclass
class Listing:
    listing_id: str
    seller_id: str
    item_type: ItemType
    price: float
    per_call: bool = False
    subscription: bool = False
    revenue_share: float = 0.0
