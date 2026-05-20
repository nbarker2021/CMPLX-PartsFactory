"""
ManusToolsProvider — wires the 30-instrument registry into the morphon mesh.

Register on the ``engine`` port alongside ``CQEProvider`` (composition) or
call ``cmplx.tools.wire.register_default_toolkit()`` at startup.
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from cmplx.tools.composite.base_tool import ToolReceipt, _hash_payload
from cmplx.tools.manus import CMPLXToolRegistry, load_manifest_v3

_INSTRUMENT_DIR = Path(__file__).resolve().parent / "manus" / "instruments"
_NAME_TO_MODULE = {
    p.stem: f"cmplx.tools.manus.instruments.{p.stem}"
    for p in _INSTRUMENT_DIR.glob("*.py")
    if p.name != "__init__.py"
}


def _snake_to_class(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


class ManusToolsProvider:
    """Adapt domain data to three rails and optionally run instrument classes."""

    name = "manus_tools"

    def __init__(self, registry: Optional[CMPLXToolRegistry] = None) -> None:
        self.registry = registry or CMPLXToolRegistry()
        self._manifest = load_manifest_v3()
        self._instruments: dict[str, Any] = {}

    def list_tools(self) -> List[dict]:
        return list(self._manifest.get("tools", []))

    def adapt(self, tool_key: str, data: Dict[str, Any]) -> Dict[str, np.ndarray]:
        return self.registry.adapt(tool_key, data)

    def adapt_to_24d(self, tool_key: str, data: Dict[str, Any]) -> np.ndarray:
        rails = self.adapt(tool_key, data)
        return np.concatenate([rails["alpha"], rails["beta"], rails["gamma"]])

    def get_instrument(self, module_stem: str) -> Any:
        """Lazy-load ``ProteinFoldMorphon`` etc. from ``instruments/<stem>.py``."""
        if module_stem in self._instruments:
            return self._instruments[module_stem]
        mod_name = _NAME_TO_MODULE.get(module_stem)
        if not mod_name:
            raise KeyError(f"unknown instrument module: {module_stem}")
        mod = importlib.import_module(mod_name)
        cls_name = _snake_to_class(module_stem)
        if hasattr(mod, cls_name):
            inst = getattr(mod, cls_name)()
        else:
            # fallback: first class ending in Morphon or Tool
            for attr in dir(mod):
                if attr.endswith(("Morphon", "Tool", "Classifier", "Detector")):
                    if isinstance(getattr(mod, attr), type):
                        inst = getattr(mod, attr)()
                        break
            else:
                raise AttributeError(f"no instrument class in {mod_name}")
        self._instruments[module_stem] = inst
        return inst

    def run_instrument(
        self,
        module_stem: str,
        method: str,
        *args: Any,
        **kwargs: Any,
    ) -> tuple[Any, ToolReceipt]:
        """Call ``analyze_sequence`` (etc.) with a composite receipt."""
        receipt = ToolReceipt(
            tool_code=module_stem,
            tool_name=module_stem,
            family_used="manus",
            operation_used=method,
        )
        receipt.input_hash = _hash_payload({"args": args, "kwargs": kwargs})
        try:
            inst = self.get_instrument(module_stem)
            fn = getattr(inst, method)
            out = fn(*args, **kwargs)
            receipt.output_hash = _hash_payload(out if isinstance(out, dict) else str(out)[:500])
            receipt.finalize(True)
            return out, receipt
        except Exception as exc:
            receipt.finalize(False, str(exc))
            raise

    def health(self) -> dict:
        return {
            "ok": True,
            "service": self.name,
            "tools_in_manifest": len(self.list_tools()),
            "instruments_on_disk": len(_NAME_TO_MODULE),
            "adapters_registered": len(self.registry._adapters_by_domain),
        }
