from typing import Dict, Any, List, Optional
import copy

HOST = "host.docker.internal"

SNAP_FRAGMENT: Dict[str, Any] = {
    "snap": {
        "image": "cmplx/polyglot:5.0.0",
        "container_name": "cmplx-snap",
        "restart": "unless-stopped",
        "ports": ["8080:8080"],
        "environment": {
            "SERVICE": "snap",
            "CMPLX_SNAP_ENABLED": "true",
            "CMPLX_SECURITY_ENABLED": "true",
            "LOG_LEVEL": "info",
            "PYTHONPATH": "/app:/app/src",
        },
        "volumes": [
            "cmplx_data:/data",
        ],
        "networks": ["cmplx_network"],
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "40s",
        },
        "deploy": {
            "resources": {
                "limits": {"cpus": "2", "memory": "2G"},
                "reservations": {"cpus": "1", "memory": "1G"},
            }
        },
        "depends_on": ["redis"],
    }
}

UHP_FRAGMENT: Dict[str, Any] = {
    "uhp": {
        "image": "cmplx/polyglot:5.0.0",
        "container_name": "cmplx-uhp",
        "restart": "unless-stopped",
        "ports": ["8081:8081"],
        "environment": {
            "SERVICE": "uhp",
            "UHP_PORT": "8081",
            "LOG_LEVEL": "info",
            "PYTHONPATH": "/app:/app/src",
            "SNAP_URL": f"http://{HOST}:8080",
            "REDIS_URL": f"redis://{HOST}:6379/1",
        },
        "networks": ["cmplx_network"],
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:8081/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s",
        },
        "deploy": {
            "resources": {
                "limits": {"cpus": "2", "memory": "2G"},
                "reservations": {"cpus": "1", "memory": "1G"},
            }
        },
        "depends_on": ["snap", "redis"],
    }
}

TARPIT_FRAGMENT: Dict[str, Any] = {
    "tarpit": {
        "image": "cmplx/polyglot:5.0.0",
        "container_name": "cmplx-tarpit",
        "restart": "unless-stopped",
        "ports": ["8082:8082"],
        "environment": {
            "SERVICE": "tarpit",
            "TARPIT_PORT": "8082",
            "LOG_LEVEL": "info",
            "PYTHONPATH": "/app:/app/src",
            "UHP_URL": f"http://{HOST}:8081",
            "REDIS_URL": f"redis://{HOST}:6379/3",
        },
        "networks": ["cmplx_network"],
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:8082/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s",
        },
        "deploy": {
            "resources": {
                "limits": {"cpus": "2", "memory": "2G"},
                "reservations": {"cpus": "1", "memory": "1G"},
            }
        },
        "depends_on": ["uhp", "redis"],
    }
}

E6_FRAGMENT: Dict[str, Any] = {
    "e6": {
        "image": "cmplx/polyglot:5.0.0",
        "container_name": "cmplx-e6",
        "restart": "unless-stopped",
        "ports": ["8083:8083"],
        "environment": {
            "SERVICE": "e6",
            "E6_PORT": "8083",
            "LOG_LEVEL": "info",
            "PYTHONPATH": "/app:/app/src",
            "SNAP_URL": f"http://{HOST}:8080",
            "UHP_URL": f"http://{HOST}:8081",
            "TARPIT_URL": f"http://{HOST}:8082",
            "THINKTANK_URL": f"http://{HOST}:8084",
            "CLAW_URL": f"http://{HOST}:8085",
            "REDIS_URL": f"redis://{HOST}:6379/4",
        },
        "networks": ["cmplx_network"],
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:8083/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "40s",
        },
        "deploy": {
            "resources": {
                "limits": {"cpus": "2", "memory": "2G"},
                "reservations": {"cpus": "1", "memory": "1G"},
            }
        },
        "depends_on": ["snap", "uhp", "tarpit", "thinktank", "claw", "redis"],
    }
}

THINKTANK_FRAGMENT: Dict[str, Any] = {
    "thinktank": {
        "image": "cmplx/polyglot:5.0.0",
        "container_name": "cmplx-thinktank",
        "restart": "unless-stopped",
        "ports": ["8084:8084"],
        "environment": {
            "SERVICE": "thinktank",
            "THINKTANK_PORT": "8084",
            "THINKTANK_WORKERS": "24",
            "THINKTANK_MODE": "live",
            "LOG_LEVEL": "info",
            "PYTHONPATH": "/app:/app/src",
            "REDIS_URL": f"redis://{HOST}:6379/5",
        },
        "networks": ["cmplx_network"],
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:8084/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "60s",
        },
        "deploy": {
            "resources": {
                "limits": {"cpus": "4", "memory": "8G"},
                "reservations": {"cpus": "2", "memory": "4G"},
            }
        },
        "depends_on": ["redis"],
    }
}

CLAW_FRAGMENT: Dict[str, Any] = {
    "claw": {
        "image": "cmplx/polyglot:5.0.0",
        "container_name": "cmplx-claw",
        "restart": "unless-stopped",
        "ports": ["8085:8085"],
        "environment": {
            "SERVICE": "claw",
            "CLAW_PORT": "8085",
            "LOG_LEVEL": "info",
            "PYTHONPATH": "/app:/app/src",
            "THINKTANK_URL": f"http://{HOST}:8084",
            "REDIS_URL": f"redis://{HOST}:6379/2",
        },
        "networks": ["cmplx_network"],
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:8085/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s",
        },
        "deploy": {
            "resources": {
                "limits": {"cpus": "2", "memory": "4G"},
                "reservations": {"cpus": "1", "memory": "2G"},
            }
        },
        "depends_on": ["thinktank", "redis"],
    }
}

MCP_FRAGMENT: Dict[str, Any] = {
    "mcp": {
        "image": "cmplx/polyglot:5.0.0",
        "container_name": "cmplx-mcp",
        "restart": "unless-stopped",
        "ports": ["8086:8086"],
        "environment": {
            "SERVICE": "mcp",
            "MCP_PORT": "8086",
            "LOG_LEVEL": "info",
            "PYTHONPATH": "/app:/app/src",
            "SNAP_URL": f"http://{HOST}:8080",
            "UHP_URL": f"http://{HOST}:8081",
            "TARPIT_URL": f"http://{HOST}:8082",
            "E6_URL": f"http://{HOST}:8083",
            "THINKTANK_URL": f"http://{HOST}:8084",
            "CLAW_URL": f"http://{HOST}:8085",
            "REDIS_URL": f"redis://{HOST}:6379/6",
        },
        "networks": ["cmplx_network"],
        "healthcheck": {
            "test": ["CMD", "curl", "-f", "http://localhost:8086/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s",
        },
        "deploy": {
            "resources": {
                "limits": {"cpus": "2", "memory": "4G"},
                "reservations": {"cpus": "1", "memory": "2G"},
            }
        },
        "depends_on": ["snap", "uhp", "tarpit", "e6", "thinktank", "claw", "redis"],
    }
}

REDIS_FRAGMENT: Dict[str, Any] = {
    "redis": {
        "image": "redis:7-alpine",
        "container_name": "cmplx-redis",
        "restart": "unless-stopped",
        "ports": ["6379:6379"],
        "command": "redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru",
        "volumes": [
            "redis_data:/data",
        ],
        "networks": ["cmplx_network"],
        "healthcheck": {
            "test": ["CMD", "redis-cli", "ping"],
            "interval": "10s",
            "timeout": "3s",
            "retries": 3,
        },
        "deploy": {
            "resources": {
                "limits": {"cpus": "0.5", "memory": "512M"},
                "reservations": {"cpus": "0.25", "memory": "256M"},
            }
        },
    }
}

POSTGRES_FRAGMENT: Dict[str, Any] = {
    "postgres": {
        "image": "postgres:16-alpine",
        "container_name": "cmplx-postgres",
        "restart": "unless-stopped",
        "ports": ["5432:5432"],
        "environment": {
            "POSTGRES_USER": "cmplx",
            "POSTGRES_PASSWORD": "cmplx_secure_password_change_in_production",
            "POSTGRES_DB": "cmplx_1t",
            "POSTGRES_INITDB_ARGS": "--encoding=UTF8 --locale=en_US.UTF-8",
        },
        "volumes": [
            "postgres_data:/var/lib/postgresql/data",
        ],
        "networks": ["cmplx_network"],
        "healthcheck": {
            "test": ["CMD-SHELL", "pg_isready -U cmplx -d cmplx_1t"],
            "interval": "10s",
            "timeout": "5s",
            "retries": 5,
        },
        "deploy": {
            "resources": {
                "limits": {"cpus": "1", "memory": "1G"},
                "reservations": {"cpus": "0.5", "memory": "512M"},
            }
        },
    }
}

SERVICE_FRAGMENTS: Dict[str, Dict[str, Any]] = {
    "snap": SNAP_FRAGMENT,
    "uhp": UHP_FRAGMENT,
    "tarpit": TARPIT_FRAGMENT,
    "e6": E6_FRAGMENT,
    "thinktank": THINKTANK_FRAGMENT,
    "claw": CLAW_FRAGMENT,
    "mcp": MCP_FRAGMENT,
    "redis": REDIS_FRAGMENT,
    "postgres": POSTGRES_FRAGMENT,
}


class FragmentLoader:
    def __init__(self, master_image: str = "cmplx/polyglot:5.0.0"):
        self.master_image = master_image
        self._fragments = SERVICE_FRAGMENTS.copy()

    def get_fragment(self, service_name: str) -> Optional[Dict[str, Any]]:
        fragment = self._fragments.get(service_name)
        if fragment:
            inner = copy.deepcopy(fragment)
            for key in list(inner.keys()):
                inner = inner[key]
                break
            return self._substitute_image(inner)
        return None

    def get_fragments(self, service_names: List[str]) -> Dict[str, Dict[str, Any]]:
        result = {}
        for name in service_names:
            fragment = self.get_fragment(name)
            if fragment:
                result[name] = fragment
        return result

    def list_services(self) -> List[str]:
        return list(self._fragments.keys())

    def _substitute_image(self, fragment: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(fragment)

        def replace_image(d):
            if isinstance(d, dict):
                if "image" in d:
                    d["image"] = self.master_image
                for v in d.values():
                    replace_image(v)
            elif isinstance(d, list):
                for item in d:
                    replace_image(item)

        replace_image(result)
        return result

    def validate_dependencies(self, requested_services: List[str]) -> tuple[List[str], List[str]]:
        valid = []
        missing = []
        for service in requested_services:
            if service in self._fragments:
                valid.append(service)
            else:
                missing.append(service)
        return valid, missing

    def resolve_dependencies(self, service_names: List[str]) -> List[str]:
        resolved = []
        seen = set()

        def add_service(name: str):
            if name in seen:
                return
            seen.add(name)
            fragment = self._fragments.get(name)
            if fragment:
                deps = fragment.get("depends_on", [])
                for dep in deps:
                    add_service(dep)
            resolved.append(name)

        for service in service_names:
            add_service(service)
        return resolved
