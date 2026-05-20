import time
import threading
from enum import Enum
from typing import Callable, Any


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5,
                 recovery_timeout: float = 30.0, half_open_max_calls: int = 3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0
        self._success_count = 0
        self._total_calls = 0
        self._total_failures = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state

    def __call__(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            current_state = self.state
            if current_state == CircuitState.OPEN:
                self._total_calls += 1
                self._total_failures += 1
                raise CircuitBreakerOpenError(self.name)

            if current_state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    self._total_calls += 1
                    self._total_failures += 1
                    raise CircuitBreakerOpenError(self.name, "half-open at capacity")
                self._half_open_calls += 1

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            self._success_count += 1
            self._total_calls += 1
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._half_open_calls = 0

    def _on_failure(self):
        with self._lock:
            self._total_calls += 1
            self._total_failures += 1
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

    def reset(self):
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._half_open_calls = 0

    def metrics(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "total_calls": self._total_calls,
                "total_failures": self._total_failures,
                "success_count": self._success_count,
                "success_rate": (self._success_count / max(self._total_calls, 1)) * 100,
            }


class CircuitBreakerOpenError(Exception):
    def __init__(self, service_name: str, detail: str = "circuit breaker is open"):
        self.service_name = service_name
        self.detail = detail
        super().__init__(f"Circuit breaker open for '{service_name}': {detail}")
