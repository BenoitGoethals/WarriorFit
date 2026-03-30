import asyncio
import functools
import logging
import os
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Only enable benchmarking if ENV is 'development' or 'dev'
# You can adjust this check based on how you set your environment
IS_DEV = os.getenv("ENV", "development").lower() in (
    "development",
    "dev",
    "Test",
    "Testing",
)


def benchmark(func: Callable) -> Callable:
    """
    Decorator that logs the execution time of a function.
    Only active in development mode.
    """
    if not IS_DEV:
        return func

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()

        if asyncio.iscoroutinefunction(func):

            async def async_wrapper():
                try:
                    return await func(*args, **kwargs)
                finally:
                    duration = time.perf_counter() - start_time
                    logger.info(f"[BENCHMARK] Async '{func.__name__}': {duration:.4f}s")

            return async_wrapper()
        else:
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start_time
                logger.info(f"[BENCHMARK] '{func.__name__}': {duration:.4f}s")

    return wrapper
