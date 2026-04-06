"""Retry utilities with exponential backoff."""

import asyncio
import functools
from typing import Any, Callable, TypeVar, Type

from travel_mcp.core.error_handler import TimeoutError as TravelTimeoutError

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retriable_exceptions: tuple = (Exception,),
):
    """
    Decorator that retries an async function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
        retriable_exceptions: Tuple of exceptions to retry on

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retriable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    # Add jitter
                    import random
                    delay *= 0.5 + random.random()

                    if isinstance(e, TravelTimeoutError):
                        # Shorter retry for timeout errors
                        delay = min(delay, 5.0)

                    await asyncio.sleep(delay)

            # All retries exhausted
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class RetryPolicy:
    """
    Configurable retry policy for API calls.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
    ) -> None:
        """Initialize retry policy."""
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        import random
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        return delay * (0.5 + random.random())

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry policy."""
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt == self.max_retries:
                    break

                delay = self.calculate_delay(attempt)
                await asyncio.sleep(delay)

        if last_exception:
            raise last_exception
        raise RuntimeError("Retry policy exhausted without result or exception")
