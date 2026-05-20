"""Probe the mounted CMPLXMCP runtime without editing the source repo."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    module_root = Path(os.environ.get("CMPLXMCP_MODULE", "/module")).resolve()
    sys.path.insert(0, str(module_root))

    result: dict[str, object] = {
        "module_root": str(module_root),
        "module_exists": module_root.is_dir(),
        "import_ok": False,
        "server_constructed": False,
        "transport": "stdio",
    }

    try:
        from server.server import CMPLXMCPServer

        result["import_ok"] = True
        server = CMPLXMCPServer(data_root=module_root)
        result["server_constructed"] = True
        result["server_type"] = type(server).__name__
        result["data_root"] = str(server.data_root)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    print(json.dumps(result, indent=2))
    return 0 if result["server_constructed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
