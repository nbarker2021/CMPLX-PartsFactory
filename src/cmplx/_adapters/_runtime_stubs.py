"""Minimal stubs for escrow controllers that referenced ``runtime.*``."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class ControllerContext:
    def __init__(
        self,
        workspace: Path,
        run_id: str,
        run_dir: Path,
        step_id: str = "step-0",
    ) -> None:
        self.workspace = workspace
        self.run_id = run_id
        self.run_dir = run_dir
        self.step_id = step_id


class BaseController:
    name = "base"

    def run(self, ctx: ControllerContext, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


def canon_artifacts(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return list(specs)
