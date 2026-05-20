import time
import logging
from typing import Any, Callable

logger = logging.getLogger("mesh.errors")


class MeshError(Exception):
    def __init__(self, message: str, service: str = "", endpoint: str = "",
                 status_code: int = 500, details: dict | None = None):
        self.message = message
        self.service = service
        self.endpoint = endpoint
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error": self.message,
            "service": self.service,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "details": self.details,
        }


class ServiceUnavailableError(MeshError):
    def __init__(self, service: str, endpoint: str = "",
                 details: dict | None = None):
        super().__init__(
            f"Service '{service}' is unavailable",
            service=service, endpoint=endpoint,
            status_code=503, details=details,
        )





class TimeoutError(MeshError):
    def __init__(self, service: str, endpoint: str = "",
                 timeout: float = 0.0, details: dict | None = None):
        super().__init__(
            f"Request to '{service}/{endpoint}' timed out after {timeout}s",
            service=service, endpoint=endpoint,
            status_code=504, details={"timeout": timeout, **(details or {})},
        )


class RetryExhaustedError(MeshError):
    def __init__(self, service: str, endpoint: str = "",
                 attempts: int = 0, last_error: str = "",
                 details: dict | None = None):
        super().__init__(
            f"Request to '{service}/{endpoint}' failed after {attempts} retries: {last_error}",
            service=service, endpoint=endpoint,
            status_code=503, details={"attempts": attempts, "last_error": last_error, **(details or {})},
        )


def retry(max_attempts: int = 3, base_delay: float = 0.5,
          backoff: float = 2.0, retryable_exceptions: tuple = (Exception,)):
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exc = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (backoff ** attempt)
                        logger.debug("Retry %d/%d for %s after %.2fs: %s",
                                     attempt + 1, max_attempts, func.__name__, delay, e)
                        time.sleep(delay)
            raise RetryExhaustedError(
                service=kwargs.get("service", ""),
                endpoint=kwargs.get("endpoint", ""),
                attempts=max_attempts,
                last_error=str(last_exc),
            ) from last_exc
        return wrapper
    return decorator


def fallback(primary: Callable, fallback_func: Callable,
             on_exceptions: tuple = (Exception,)) -> Any:
    try:
        return primary()
    except on_exceptions as e:
        logger.warning("Primary failed, using fallback: %s", e)
        return fallback_func()
