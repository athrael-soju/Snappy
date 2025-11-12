"""Performance timing utilities for backend services."""

import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def log_execution_time(
    operation: str | None = None,
    log_level: int = logging.DEBUG,
    warn_threshold_ms: float | None = None,
) -> Callable[[F], F]:
    """Decorator to log function execution time.

    Args:
        operation: Custom operation name (defaults to function name)
        log_level: Log level for normal execution (default: DEBUG)
        warn_threshold_ms: If set, log as WARNING if duration exceeds this value

    Example:
        @log_execution_time("embed images")
        async def embed_images(images: List[Image]) -> List[Tensor]:
            ...

        @log_execution_time(warn_threshold_ms=1000)
        def slow_operation():
            ...
    """

    def decorator(func: F) -> F:
        # Handle both sync and async functions
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                op_name = operation or func.__name__
                start_time = time.perf_counter()

                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000

                    # Determine log level
                    level = log_level
                    if warn_threshold_ms and duration_ms > warn_threshold_ms:
                        level = logging.WARNING

                    logger.log(
                        level,
                        "%s completed in %.2fms",
                        op_name,
                        duration_ms,
                        extra={
                            "operation": op_name,
                            "duration_ms": round(duration_ms, 2),
                            "function": func.__name__,
                            "func_module": func.__module__,
                        },
                    )

                    return result
                except Exception as e:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    logger.error(
                        "%s failed after %.2fms: %s",
                        op_name,
                        duration_ms,
                        str(e),
                        extra={
                            "operation": op_name,
                            "duration_ms": round(duration_ms, 2),
                            "function": func.__name__,
                            "func_module": func.__module__,
                            "error": str(e),
                        },
                        exc_info=True,
                    )
                    raise

            return async_wrapper  # type: ignore[return-value]

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                op_name = operation or func.__name__
                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000

                    # Determine log level
                    level = log_level
                    if warn_threshold_ms and duration_ms > warn_threshold_ms:
                        level = logging.WARNING

                    logger.log(
                        level,
                        "%s completed in %.2fms",
                        op_name,
                        duration_ms,
                        extra={
                            "operation": op_name,
                            "duration_ms": round(duration_ms, 2),
                            "function": func.__name__,
                            "func_module": func.__module__,
                        },
                    )

                    return result
                except Exception as e:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    logger.error(
                        "%s failed after %.2fms: %s",
                        op_name,
                        duration_ms,
                        str(e),
                        extra={
                            "operation": op_name,
                            "duration_ms": round(duration_ms, 2),
                            "function": func.__name__,
                            "func_module": func.__module__,
                            "error": str(e),
                        },
                        exc_info=True,
                    )
                    raise

            return sync_wrapper  # type: ignore[return-value]

    return decorator


# Add asyncio import
import asyncio


class PerformanceTimer:
    """Context manager for timing code blocks.

    Example:
        with PerformanceTimer("process batch") as timer:
            process_images(batch)

        logger.info(f"Took {timer.duration_ms}ms")
    """

    def __init__(self, operation: str, log_on_exit: bool = True):
        """Initialize performance timer.

        Args:
            operation: Name of the operation being timed
            log_on_exit: If True, automatically log duration on exit
        """
        self.operation = operation
        self.log_on_exit = log_on_exit
        self.start_time: float = 0
        self.end_time: float = 0
        self.duration_ms: float = 0

    def __enter__(self) -> "PerformanceTimer":
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timing and optionally log."""
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000

        if self.log_on_exit:
            if exc_type is None:
                logger.debug(
                    "%s completed in %.2fms",
                    self.operation,
                    self.duration_ms,
                    extra={
                        "operation": self.operation,
                        "duration_ms": round(self.duration_ms, 2),
                    },
                )
            else:
                logger.error(
                    "%s failed after %.2fms: %s",
                    self.operation,
                    self.duration_ms,
                    str(exc_val),
                    extra={
                        "operation": self.operation,
                        "duration_ms": round(self.duration_ms, 2),
                        "error": str(exc_val),
                    },
                    exc_info=True,
                )
