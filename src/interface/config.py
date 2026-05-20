from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Settings:
    gateway_port: int = int(os.environ.get("GATEWAY_PORT", "8877"))
    host: str = os.environ.get("GATEWAY_HOST", "0.0.0.0")

    opencode_api_url: str = os.environ.get("OPENCODE_API_URL", "http://opencode-session:4096")
    opencode_username: str = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
    opencode_password: str = os.environ.get("OPENCODE_SERVER_PASSWORD", "")

    api_key: str = os.environ.get("GATEWAY_API_KEY", "")
    auth_disabled: bool = os.environ.get("GATEWAY_AUTH_DISABLED", "").lower() in ("1", "true", "yes")

    cors_origins: list[str] = field(default_factory=lambda: os.environ.get("GATEWAY_CORS_ORIGINS", "*").split(","))

    known_services: Dict[str, str] = field(default_factory=lambda: {
        "research": os.environ.get("RESEARCH_API_URL", "http://research-api:3000"),
        "manny": os.environ.get("MANNY_RUNTIME_URL", "http://manny-runtime:8870"),
        "manifold": os.environ.get("MANNY_MANIFOLD_URL", "http://manny-manifold-api:8840"),
        "mmdb": os.environ.get("MMDB_UNIFIED_URL", "http://mmdb-unified:8824"),
        "mdhg": os.environ.get("MDHG_UNIFIED_URL", "http://mdhg-unified:8825"),
        "snap": os.environ.get("SNAP_UNIFIED_URL", "http://snap-unified:8823"),
        "tarpit": os.environ.get("TARPIT_API_URL", "http://tarpit-api:8844"),
        "speedlight": os.environ.get("SPEEDLIGHT_API_URL", "http://speedlight-api:8843"),
        "aggregator": os.environ.get("DB_AGGREGATOR_URL", "http://db-aggregator-api:8815"),
        "pocket": os.environ.get("POCKET_MEMORY_URL", "http://pocket-memory-api:8816"),
        "agenthub": os.environ.get("AGENTHUB_URL", "http://agenthub-db-bridge:8817"),
        "unified": os.environ.get("CMPLX_UNIFIED_URL", "http://cmplx-unified-api:8851"),
        "gitnexus": os.environ.get("GITNEXUS_URL", "http://gitnexus-rebuild-server:4747"),
    })


settings = Settings()
