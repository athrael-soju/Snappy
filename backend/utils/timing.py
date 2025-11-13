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
    """Decorator to log function execution time on successful completion.

    Only logs when the function completes successfully. Exceptions are propagated
    without logging, allowing normal error handling to manage failures.

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

                result = await func(*args, **kwargs)
                duration_s = time.perf_counter() - start_time
                duration_ms = duration_s * 1000

                # Determine log level
                level = log_level
                if warn_threshold_ms and duration_ms > warn_threshold_ms:
                    level = logging.WARNING

                logger.log(
                    level,
                    "%s completed in %.2fs",
                    op_name,
                    duration_s,
                    extra={
                        "operation": op_name,
                        "duration_s": round(duration_s, 3),
                        "function": func.__name__,
                        "func_module": func.__module__,
                    },
                )

                return result

            return async_wrapper  # type: ignore[return-value]

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                op_name = operation or func.__name__
                start_time = time.perf_counter()

                result = func(*args, **kwargs)
                duration_s = time.perf_counter() - start_time
                duration_ms = duration_s * 1000

                # Determine log level
                level = log_level
                if warn_threshold_ms and duration_ms > warn_threshold_ms:
                    level = logging.WARNING

                logger.log(
                    level,
                    "%s completed in %.2fs",
                    op_name,
                    duration_s,
                    extra={
                        "operation": op_name,
                        "duration_s": round(duration_s, 3),
                        "function": func.__name__,
                        "func_module": func.__module__,
                    },
                )

                return result

            return sync_wrapper  # type: ignore[return-value]

    return decorator


# Add asyncio import
import asyncio


class PerformanceTimer:
    """Context manager for timing code blocks.

    Only logs on successful completion. Exceptions are propagated without logging.

    Example:
        with PerformanceTimer("process batch") as timer:
            process_images(batch)

        logger.info(f"Took {timer.duration_s:.2f}s")
    """

    def __init__(self, operation: str, log_on_exit: bool = True):
        """Initialize performance timer.

        Args:
            operation: Name of the operation being timed
            log_on_exit: If True, automatically log duration on successful exit
        """
        self.operation = operation
        self.log_on_exit = log_on_exit
        self.start_time: float = 0
        self.end_time: float = 0
        self.duration_s: float = 0
        self.duration_ms: float = 0  # Keep for backward compatibility

    def __enter__(self) -> "PerformanceTimer":
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timing and optionally log."""
        self.end_time = time.perf_counter()
        self.duration_s = self.end_time - self.start_time
        self.duration_ms = self.duration_s * 1000  # Keep for backward compatibility

        # Only log on successful completion
        if self.log_on_exit and exc_type is None:
            logger.debug(
                "%s completed in %.2fs",
                self.operation,
                self.duration_s,
                extra={
                    "operation": self.operation,
                    "duration_s": round(self.duration_s, 3),
                },
            )
