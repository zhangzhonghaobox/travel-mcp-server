"""Caching utilities."""

import asyncio
import functools
import time
from typing import Any, Callable, Optional, TypeVar

from cachetools import TTLCache

T = TypeVar("T")


def timed_cache(seconds: int = 300, maxsize: int = 128):
    """
    Decorator that caches async function results for a specified time.

    Args:
        seconds: Time to cache results in seconds (default 5 minutes)
        maxsize: Maximum number of cached results

    Returns:
        Decorated function with caching
    """
    cache: TTLCache = TTLCache(maxsize=maxsize, ttl=seconds)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Create cache key from args and kwargs
            key = (args, tuple(sorted(kwargs.items())))

            # Check cache
            if key in cache:
                return cache[key]

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache[key] = result
            return result

        # Add cache clear method
        wrapper.clear_cache = cache.clear  # type: ignore
        return wrapper

    return decorator


class AsyncCache:
    """
    Simple async-aware cache implementation.
    """

    def __init__(self, ttl: int = 300, maxsize: int = 100) -> None:
        """
        Initialize async cache.

        Args:
            ttl: Time to live in seconds
            maxsize: Maximum number of entries
        """
        self._cache: dict = {}
        self._timestamps: dict = {}
        self._locks: dict = {}
        self._ttl = ttl
        self._maxsize = maxsize
        self._global_lock = asyncio.Lock()

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if key in self._cache:
            # Check if expired
            if time.time() - self._timestamps.get(key, 0) < self._ttl:
                return self._cache[key]
            # Expired, remove
            await self.delete(key)
        return default

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        async with self._global_lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self._maxsize and key not in self._cache:
                oldest_key = min(self._timestamps, key=self._timestamps.get)
                await self.delete(oldest_key)

            self._cache[key] = value
            self._timestamps[key] = time.time()

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._global_lock:
            self._cache.clear()
            self._timestamps.clear()
