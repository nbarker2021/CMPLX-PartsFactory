"""
Load escrowed AGRM refactored reference (MDHG sweep controller) when present on disk.

Does not import the broken composed ``routing/agrm/AGRMController.py``.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Optional

_CACHED: Optional[ModuleType] = None
_LOAD_ERROR: Optional[str] = None

_DEFAULT_CANDIDATES = (
    Path(r"D:/PartsFactory/CMPLX-PartsFactory/staging/by-family/agrm/mdhg_hierarchy/53e25b8d_AGRM_refactored.py"),
    Path(
        r"D:/PartsFactory/work/attractor-assembly/corpus-visible/roots"
        r"/unification-prototypes/_extracted_variants/agrm/AGRM_refactored"
        r"/53e25b8d_AGRM_refactored.py"
    ),
)


def refactored_path() -> Optional[Path]:
    env = os.environ.get("AGRM_REFACTORED_PATH", "").strip()
    if env:
        p = Path(env)
        return p if p.is_file() else None
    for candidate in _DEFAULT_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def load_refactored_module(*, force: bool = False) -> Optional[ModuleType]:
    """Import the single-file refactored build; cache per process."""
    global _CACHED, _LOAD_ERROR
    if _CACHED is not None and not force:
        return _CACHED
    path = refactored_path()
    if path is None:
        _LOAD_ERROR = "refactored module path not found"
        return None
    try:
        spec = importlib.util.spec_from_file_location("cmplx_agrm_refactored", path)
        if spec is None or spec.loader is None:
            _LOAD_ERROR = "spec_from_file_location failed"
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _CACHED = mod
        _LOAD_ERROR = None
        return mod
    except Exception as exc:  # noqa: BLE001
        _LOAD_ERROR = str(exc)
        _CACHED = None
        return None


def refactored_status() -> dict[str, Any]:
    path = refactored_path()
    mod = _CACHED or (load_refactored_module() if path else None)
    return {
        "path": str(path) if path else None,
        "loaded": mod is not None,
        "error": _LOAD_ERROR,
        "has_AGRMController": bool(mod and hasattr(mod, "AGRMController")),
        "has_MDHGHashTable": bool(mod and hasattr(mod, "MDHGHashTable")),
    }


def run_mdhg_sweep_probe(*, sweeps: int = 1, n: int = 200, seed: int = 0) -> dict[str, Any]:
    """Optional bench hook — MDHG table sweeps, not geographic TSP."""
    mod = load_refactored_module()
    if mod is None:
        return {"status": "unavailable", "error": _LOAD_ERROR}
    ctrl_cls = getattr(mod, "AGRMController", None)
    if ctrl_cls is None:
        return {"status": "unavailable", "error": "AGRMController missing in refactored module"}
    ctrl = ctrl_cls()
    stats = ctrl.run_sweeps(sweeps=sweeps, n=n, seed=seed)
    return {"status": "ok", "mode": "mdhg_sweep", "sweeps": sweeps, "n": n, "stats": stats}
