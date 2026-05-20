"""
CMPLX Flow State
================

Pydantic-based state models for workflow flows.
Provides a base FlowState that tracks execution metadata,
plus helpers for structured/unstructured state management.

Usage:
    from cmplx_toolkit.workflow import FlowState

    class MyState(FlowState):
        hypothesis: str = ""
        results: list = []
        score: float = 0.0

    flow = MyFlow(state=MyState(hypothesis="test"))
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback: use dataclass-like base if pydantic not installed
    from dataclasses import dataclass
    from dataclasses import field as _field

    class BaseModel:
        """Minimal BaseModel stand-in when pydantic is unavailable."""
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            # Set defaults for annotations not in kwargs
            for k, v in getattr(self.__class__, '__annotations__', {}).items():
                if k not in kwargs:
                    default = getattr(self.__class__, k, None)
                    setattr(self, k, default)

        def model_dump(self):
            return {k: getattr(self, k) for k in self.__annotations__}

        def model_dump_json(self, indent=None):
            return json.dumps(self.model_dump(), indent=indent, default=str)

        @classmethod
        def model_validate(cls, data):
            return cls(**data)

    def Field(default=None, **kwargs):
        return default


class FlowState(BaseModel):
    """
    Base state model for CMPLXFlow instances.

    Subclass this with your domain-specific fields. The base provides
    execution tracking metadata that the flow engine manages automatically.

    Attributes:
        flow_id: Unique identifier for this flow execution.
        flow_name: Name of the flow class.
        current_step: Name of the step currently executing.
        completed_steps: Steps that have finished.
        errors: Accumulated error messages.
        started_at: ISO timestamp of flow start.
        updated_at: ISO timestamp of last state update.
        metadata: Arbitrary key-value metadata.
    """
    flow_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    flow_name: str = ""
    current_step: str = ""
    completed_steps: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    # -- Convenience methods --------------------------------------------------

    def mark_step_started(self, step_name: str) -> None:
        """Record that a step has begun."""
        self.current_step = step_name
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_step_completed(self, step_name: str) -> None:
        """Record that a step has finished."""
        if step_name not in self.completed_steps:
            self.completed_steps.append(step_name)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_error(self, message: str) -> None:
        """Append an error."""
        self.errors.append(message)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def is_complete(self) -> bool:
        """True if no current step is executing (flow finished or idle)."""
        return self.current_step == "" and len(self.completed_steps) > 0

    # -- Persistence ----------------------------------------------------------

    def save(self, path: Optional[Path] = None) -> Path:
        """
        Save state to JSON file.

        Args:
            path: File path. Defaults to cmplx_data/flows/{flow_id}.json

        Returns:
            Path where state was saved.
        """
        if path is None:
            path = Path("cmplx_data") / "flows" / f"{self.flow_id}.json"
        if isinstance(path, str):
            path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path) -> "FlowState":
        """
        Load state from JSON file.

        Args:
            path: Path to JSON state file.

        Returns:
            Restored FlowState instance.
        """
        if isinstance(path, str):
            path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.model_validate(data)


class UnstructuredState(FlowState):
    """
    Flow state that allows arbitrary key-value storage.

    Use this when you don't want to define a Pydantic model up front.
    Access data via state.data dict.
    """
    data: Dict[str, Any] = Field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
