import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import tempfile


class ExecutionResult:
    def __init__(
        self,
        success: bool,
        services: List[str] = None,
        duration: float = 0,
        output: str = "",
        error: str = "",
        metadata: Dict[str, Any] = None,
    ):
        self.success = success
        self.services = services or []
        self.duration = duration
        self.output = output
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "services": self.services,
            "duration": self.duration,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"<ExecutionResult {status} services={len(self.services)} duration={self.duration:.2f}s>"


class ComposeLifecycleManager:
    HEALTH_CHECK_INTERVAL = 10
    HEALTH_CHECK_TIMEOUT = 300
    COMPOSE_PROJECT = "cmplx-on-demand"

    def __init__(self, compose_binary: str = "docker", work_dir: str = None):
        self.compose_binary = compose_binary
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self._current_compose_file = None
        self._active_services = []

    def execute(
        self,
        compose_yaml: str,
        controller_name: str,
        timeout: int = 300,
        wait_healthy: bool = True,
    ) -> ExecutionResult:
        start_time = time.time()

        try:
            compose_file = self.work_dir / "compose.yaml"
            compose_file.write_text(compose_yaml)
            self._current_compose_file = str(compose_file)

            compose_data = yaml_safe_load(compose_yaml)
            services = list(compose_data.get("services", {}).keys())
            self._active_services = services

            print(f"[{controller_name}] Pulling images...")
            result = self._run_compose(["pull"], timeout=60)
            if result.returncode != 0:
                return ExecutionResult(
                    success=False, error=f"Pull failed: {result.stderr}"
                )

            print(f"[{controller_name}] Starting services: {services}")
            result = self._run_compose(["up", "-d"], timeout=120)
            if result.returncode != 0:
                return ExecutionResult(
                    success=False,
                    services=services,
                    error=f"Start failed: {result.stderr}",
                )

            if wait_healthy:
                print(f"[{controller_name}] Waiting for services to be healthy...")
                healthy = self._wait_for_healthy(services, timeout)
                if not healthy:
                    self._run_compose(["ps"])
                    return ExecutionResult(
                        success=False,
                        services=services,
                        error="Services did not become healthy within timeout",
                    )

            duration = time.time() - start_time
            print(f"[{controller_name}] Services ready in {duration:.2f}s")

            return ExecutionResult(
                success=True,
                services=services,
                duration=duration,
                output=f"Services started: {', '.join(services)}",
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False, duration=duration, error=str(e)
            )

    def cleanup(self, compose_yaml: str = None, preserve_volumes: bool = False) -> bool:
        compose_file = compose_yaml or self._current_compose_file
        if not compose_file:
            print("No active compose to clean up")
            return True

        try:
            print("Stopping services...")
            self._run_compose(["down"])

            if not preserve_volumes:
                print("Removing volumes...")
                self._run_compose(["volumes", "rm", "-f"])

            self._active_services = []
            self._current_compose_file = None

            print("Cleanup complete")
            return True

        except Exception as e:
            print(f"Cleanup error: {e}")
            return False

    def preserve_config(
        self,
        compose_yaml: str,
        controller_name: str,
        result: ExecutionResult,
        registry_path: str = "composed_configs",
    ) -> Path:
        from .generator import ComposeGenerator

        gen = ComposeGenerator()

        metadata = {
            "controller": controller_name,
            "execution": result.to_dict(),
            "timestamp": datetime.now().isoformat(),
        }

        config_path = gen.save_config(controller_name, compose_yaml, metadata)
        print(f"Config saved to: {config_path}")
        return config_path

    def get_service_logs(self, service: str = None, lines: int = 100) -> str:
        cmd = ["logs", "--tail", str(lines)]
        if service:
            cmd.append(service)
        result = self._run_compose(cmd)
        return result.stdout + result.stderr

    def exec_in_service(self, service: str, command: List[str]) -> subprocess.CompletedProcess:
        cmd = ["exec", "-T", service] + command
        return self._run_compose(cmd)

    def _wait_for_healthy(self, services: List[str], timeout: int) -> bool:
        elapsed = 0
        while elapsed < timeout:
            result = self._run_compose(["ps", "--format", "json"])

            if result.returncode == 0 and result.stdout:
                try:
                    ps_output = []
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            ps_output.append(json.loads(line))

                    running = {
                        p.get("Service"): p.get("State") == "running"
                        for p in ps_output
                    }

                    health_ok = True
                    for svc in services:
                        if svc in running and running[svc]:
                            health = self._check_service_health(svc)
                            if health is not None and not health:
                                health_ok = False

                    if health_ok and all(running.values()):
                        return True

                except (json.JSONDecodeError, KeyError):
                    pass

            time.sleep(self.HEALTH_CHECK_INTERVAL)
            elapsed += self.HEALTH_CHECK_INTERVAL
            print(f"  Waiting... ({elapsed}s)")

        return False

    def _check_service_health(self, service: str) -> Optional[bool]:
        result = self._run_compose(
            ["inspect", service, "--format", "{{.State.Health.Status}}"]
        )

        if result.returncode != 0:
            return None

        status = result.stdout.strip()
        return status == "healthy"

    def _run_compose(self, args: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        cmd = [
            self.compose_binary,
            "compose",
            "-f",
            self._current_compose_file,
            "-p",
            self.COMPOSE_PROJECT,
        ] + args

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(self.work_dir),
        )


def yaml_safe_load(yaml_str: str) -> Dict[str, Any]:
    import yaml
    return yaml.safe_load(yaml_str)


class OnDemandRunner:
    def __init__(self):
        from .generator import ComposeGenerator

        self.generator = ComposeGenerator()
        self.lifecycle = ComposeLifecycleManager()

    def run_controller(
        self,
        controller_name: str,
        services: List[str],
        work_func: callable = None,
        preserve_config: bool = True,
    ) -> ExecutionResult:
        print(
            f"Generating compose for {controller_name} with services: {services}"
        )
        compose_yaml = self.generator.generate(controller_name, services)

        result = self.lifecycle.execute(compose_yaml, controller_name)

        if not result.success:
            print(f"Execution failed: {result.error}")
            return result

        if work_func:
            try:
                work_func(controller_name, result)
            except Exception as e:
                result.success = False
                result.error = str(e)
                print(f"Work function error: {e}")

        self.lifecycle.cleanup(compose_yaml)

        if preserve_config:
            self.lifecycle.preserve_config(compose_yaml, controller_name, result)

        return result
