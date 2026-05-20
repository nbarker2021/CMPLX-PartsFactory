"""Runtime path helpers for keeping generated state out of the source tree."""
from __future__ import annotations

import os
from pathlib import Path


def runtime_root() -> Path:
    """Return the local runtime root for generated CMPLX-PartsFactory state."""
    configured = os.environ.get("CMPLX_RUNTIME_DIR")
    if configured:
        return Path(configured)
    if os.name == "nt":
        return Path("D:/PartsFactory/runtime/CMPLX-PartsFactory")
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / (
        "cmplx-partsfactory"
    )


def runtime_path(*parts: str) -> Path:
    """Build a path under the runtime root."""
    return runtime_root().joinpath(*parts)


__all__ = ["runtime_root", "runtime_path"]
