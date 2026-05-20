from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from datetime import datetime
import yaml
import json
import hashlib

from .fragments import FragmentLoader, SERVICE_FRAGMENTS


class ComposeGenerator:
    DEFAULT_NETWORK = "cmplx_network"
    MASTER_IMAGE = "cmplx/polyglot:5.0.0"

    def __init__(
        self,
        master_image: str = MASTER_IMAGE,
        registry_path: str = "composed_configs",
    ):
        self.master_image = master_image
        self.registry_path = Path(registry_path)
        self.loader = FragmentLoader(master_image=self.master_image)
        self.fragments = SERVICE_FRAGMENTS.copy()

    def generate(
        self,
        controller_name: str,
        services: List[str],
        volumes: Dict[str, str] = None,
        environment: Dict[str, str] = None,
        resolve_deps: bool = True,
    ) -> str:
        valid_services, missing = self._validate_services(services)
        if missing:
            raise ValueError(f"Unknown services: {missing}")

        if resolve_deps:
            resolved = self._resolve_dependencies(valid_services)
        else:
            resolved = valid_services

        compose = self._build_compose(
            controller=controller_name,
            services=resolved,
            volumes=volumes,
            environment=environment,
        )

        return yaml.dump(compose, default_flow_style=False, sort_keys=False)

    def generate_file(
        self,
        controller_name: str,
        services: List[str],
        output_path: str = None,
        volumes: Dict[str, str] = None,
        environment: Dict[str, str] = None,
    ) -> Path:
        yaml_content = self.generate(
            controller_name, services, volumes, environment
        )

        if output_path:
            path = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d__%H%M%S")
            hash_suffix = hashlib.md5(
                f"{controller_name}{timestamp}".encode()
            ).hexdigest()[:6]
            path = self.registry_path / f"{controller_name}__{timestamp}__{hash_suffix}.yaml"

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml_content)
        return path

    def save_config(
        self,
        controller_name: str,
        compose_yaml: str,
        metadata: Dict[str, Any] = None,
    ) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d__%H%M%S")
        hash_suffix = hashlib.md5(compose_yaml.encode()).hexdigest()[:6]

        config_dir = self.registry_path / controller_name
        config_dir.mkdir(parents=True, exist_ok=True)

        config_path = config_dir / f"{timestamp}__{hash_suffix}.yaml"
        config_path.write_text(compose_yaml)

        if metadata:
            meta_path = config_dir / f"{timestamp}__{hash_suffix}.meta.json"
            meta_path.write_text(json.dumps(metadata, indent=2))

        return config_path

    def load_config(self, config_path: str) -> str:
        return Path(config_path).read_text()

    def list_configs(
        self, controller: str = None, include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        results = []

        if not self.registry_path.exists():
            return results

        if controller:
            search_dirs = [self.registry_path / controller]
        else:
            search_dirs = [p for p in self.registry_path.iterdir() if p.is_dir()]

        for config_dir in search_dirs:
            for yaml_file in config_dir.glob("*.yaml"):
                info = {
                    "path": str(yaml_file),
                    "name": yaml_file.name,
                    "controller": config_dir.name,
                    "created": datetime.fromtimestamp(
                        yaml_file.stat().st_mtime
                    ).isoformat(),
                }

                if include_metadata:
                    meta_path = yaml_file.with_suffix(".meta.json")
                    if meta_path.exists():
                        info["metadata"] = json.loads(meta_path.read_text())

                results.append(info)

        return sorted(results, key=lambda x: x["created"], reverse=True)

    def _validate_services(self, services: List[str]) -> tuple[List[str], List[str]]:
        available = self._get_available_services()
        valid = []
        missing = []
        for svc in services:
            if svc in available:
                valid.append(svc)
            else:
                missing.append(svc)
        return valid, missing

    def _get_available_services(self) -> Set[str]:
        return set(self.loader.list_services())

    def _resolve_dependencies(self, services: List[str]) -> List[str]:
        resolved = []
        seen = set()

        def add_service(name: str):
            if name in seen:
                return
            seen.add(name)
            fragment = self._get_fragment(name)
            if fragment:
                deps = fragment.get("depends_on", [])
                for dep in deps:
                    add_service(dep)
            resolved.append(name)

        for service in services:
            add_service(service)
        return resolved

    def _get_fragment(self, name: str) -> Dict[str, Any]:
        return self.loader.get_fragment(name) or {}

    def _build_compose(
        self,
        controller: str,
        services: List[str],
        volumes: Dict[str, str],
        environment: Dict[str, str],
    ) -> Dict[str, Any]:
        named_volumes = set()
        compose = {
            "version": "3.8",
            "services": {},
            "networks": {
                self.DEFAULT_NETWORK: {
                    "driver": "bridge",
                    "ipam": {
                        "config": [{"subnet": "172.20.0.0/16"}]
                    },
                }
            },
            "volumes": {},
        }

        for service_name in services:
            fragment = self._get_fragment(service_name)
            if fragment:
                service_def = self._prepare_service(
                    fragment, service_name, controller, volumes, environment
                )
                compose["services"][service_name] = service_def

                svc_volumes = service_def.get("volumes", [])
                for vol in svc_volumes:
                    if isinstance(vol, str) and ":" in vol:
                        vol_name = vol.split(":")[0]
                        named_volumes.add(vol_name)

        for vol_name in sorted(named_volumes):
            compose["volumes"][vol_name] = {"driver": "local"}

        return compose

    def _prepare_service(
        self,
        fragment: Dict[str, Any],
        service_name: str,
        controller: str,
        volumes: Dict[str, str],
        environment: Dict[str, str],
    ) -> Dict[str, Any]:
        import copy
        service = copy.deepcopy(fragment)

        if "container_name" in service:
            service["container_name"] = f"cmplx-{controller}-{service_name}"

        service["extra_hosts"] = ["host.docker.internal:host-gateway"]

        env = {}
        if "environment" in service:
            if isinstance(service["environment"], dict):
                env.update(service["environment"])

        if environment:
            env.update(environment)

        env["CONTROLLER"] = controller
        service["environment"] = env

        if volumes:
            svc_volumes = service.get("volumes", [])
            if isinstance(svc_volumes, list):
                for key, val in volumes.items():
                    svc_volumes.append(f"{key}:{val}")
                service["volumes"] = svc_volumes

        return service
