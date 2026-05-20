"""
Composite Tool Base Class
==========================

All composite tools inherit from ``CompositeTool``.  A composite tool
aggregates operations from multiple unified families and exposes them
through a single, governed interface.

Design principles (from S13 HANDOFF):
- Tool-first execution: try registry before custom logic
- Receipt chains: every execution is logged with a receipt
- Guardrails: type checks, dimension checks, family compatibility
- Self-improving: performance metrics feed back into tier scoring
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger("cmplx.composite_tools.base_tool")


# ---------------------------------------------------------------------------
# Receipt system
# ---------------------------------------------------------------------------

@dataclass
class ToolReceipt:
    """Execution receipt for a single composite tool call."""

    receipt_id: str = field(default_factory=lambda: str(uuid.uuid4())[:16])
    tool_code: str = ""
    tool_name: str = ""
    family_used: str = ""
    operation_used: str = ""
    tier_used: str = ""
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    input_hash: str = ""
    output_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finalize(self, success: bool, error: Optional[str] = None) -> None:
        self.completed_at = time.time()
        self.duration_ms = (self.completed_at - self.started_at) * 1000
        self.success = success
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _hash_payload(payload: Any) -> str:
    """Compute a short hash of any JSON-serializable payload."""
    try:
        raw = json.dumps(payload, sort_keys=True, default=str)
    except Exception:
        raw = str(payload)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------

class GuardrailError(ValueError):
    """Raised when a composite tool guardrail check fails."""


def check_type(value: Any, expected_type: type, name: str = "input") -> None:
    """Assert that *value* is an instance of *expected_type*."""
    if not isinstance(value, expected_type):
        raise GuardrailError(
            f"Guardrail failed: '{name}' expected {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )


def check_dimension(vector: Any, expected_dim: int, name: str = "vector") -> None:
    """Assert that *vector* has the expected number of dimensions."""
    try:
        import numpy as np
        arr = np.asarray(vector)
        if arr.shape[-1] != expected_dim:
            raise GuardrailError(
                f"Guardrail failed: '{name}' expected last dim={expected_dim}, "
                f"got shape={arr.shape}"
            )
    except ImportError:
        pass  # Skip dimension check if numpy unavailable


# ---------------------------------------------------------------------------
# Base composite tool
# ---------------------------------------------------------------------------

class CompositeTool(ABC):
    """
    Abstract base class for all composite tools.

    Subclasses must implement ``TOOL_CODE``, ``TOOL_NAME``,
    ``FAMILIES``, and ``execute()``.
    """

    TOOL_CODE: str = ""          # e.g. "COMP-GEO-001"
    TOOL_NAME: str = ""          # e.g. "composite_embed"
    CATEGORY: str = ""           # e.g. "GEOMETRIC_OPERATIONS"
    FAMILIES: Sequence[str] = () # Primary families this tool uses
    GUARDRAILS: Sequence[str] = ("type_check",)

    def __init__(self) -> None:
        self._logger = logging.getLogger(
            f"cmplx.composite_tools.{self.CATEGORY.lower()}.{self.TOOL_NAME}"
        )
        self._receipts: List[ToolReceipt] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the composite tool, generating a receipt."""
        receipt = ToolReceipt(
            tool_code=self.TOOL_CODE,
            tool_name=self.TOOL_NAME,
            input_hash=_hash_payload(kwargs),
        )
        try:
            result = self.execute(*args, **kwargs)
            receipt.output_hash = _hash_payload(result)
            receipt.finalize(success=True)
            return result
        except Exception as exc:
            receipt.finalize(success=False, error=str(exc))
            raise
        finally:
            self._receipts.append(receipt)
            self._logger.debug(
                "Receipt %s: success=%s, duration=%.1fms",
                receipt.receipt_id,
                receipt.success,
                receipt.duration_ms or 0,
            )

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Implement the composite tool logic here."""
        ...

    # ------------------------------------------------------------------
    # Registry-driven execution helper
    # ------------------------------------------------------------------

    def _registry_execute(self, tool_code: str, min_tier: str = "ACCEPTABLE", **kwargs: Any) -> Any:
        """
        Execute *tool_code* via the alternative registry.

        Falls back through tiers until one succeeds.
        """
        from .alternative_registry import registry
        return registry.execute(tool_code, min_tier=min_tier, **kwargs)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def info(self) -> Dict[str, Any]:
        return {
            "tool_code": self.TOOL_CODE,
            "tool_name": self.TOOL_NAME,
            "category": self.CATEGORY,
            "families": list(self.FAMILIES),
            "guardrails": list(self.GUARDRAILS),
        }

    def receipts(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._receipts]

    def last_receipt(self) -> Optional[Dict[str, Any]]:
        return self._receipts[-1].to_dict() if self._receipts else None
