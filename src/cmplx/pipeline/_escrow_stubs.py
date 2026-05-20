"""Stubs so escrow ChainRunner imports resolve without full Manny pipeline tree."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class Station:
    def __init__(self, name: str, brain: Any) -> None:
        self.name = name
        self.brain = brain


@dataclass
class Item:
    payload: Dict[str, Any]


@dataclass
class TaskConfig:
    name: str = "default"


def get_brain_spec(name: str) -> Dict[str, str]:
    return {"station": name}


def get_brain(spec: Dict[str, str]) -> object:
    return object()


def task_config_for(name: str) -> TaskConfig:
    return TaskConfig(name=name)
