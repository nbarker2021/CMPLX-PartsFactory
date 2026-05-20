"""Start CMPLXMCP through its direct server package as a stdio MCP server."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


async def main() -> None:
    module_root = Path(os.environ.get("CMPLXMCP_MODULE", "/module")).resolve()
    sys.path.insert(0, str(module_root))

    from server.server import CMPLXMCPServer

    server = CMPLXMCPServer(data_root=module_root)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
