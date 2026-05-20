"""
cmplx.tools — external scientific instruments and composite tool framework.

Manus toolkit (30-domain manifold adapters) lives under ``manus/``.
Composite execution receipts under ``composite/``.
"""

from .manus import CMPLXToolRegistry, load_manifest_v3
from .provider import ManusToolsProvider
from .wire import get_manus_tools, register_default_toolkit

__all__ = [
    "CMPLXToolRegistry",
    "load_manifest_v3",
    "ManusToolsProvider",
    "register_default_toolkit",
    "get_manus_tools",
]
