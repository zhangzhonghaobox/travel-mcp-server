"""Rate limiting middleware."""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional

from travel_mcp.config import get_config
from travel_mcp.core.error_handler import RateLimitExceededError


@dataclass
class RateLimitEntry:
    """Entry for tracking request rates."""

    timestamps: list = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RateLimiter:
    """
    Sliding window rate limiter implementation.
    """

    def __init__(self, requests_per_minute: Optional[int] = None) -> None:
        """Initialize rate limiter."""
        self.config = get_config()
        self.window_size = 60  # 1 minute window
        self.max_requests = requests_per_minute or self.config.rate_limit_per_minute
        self._entries: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)

    def _cleanup_old_entries(self, entry: RateLimitEntry, current_time: float) -> None:
        """Remove timestamps outside the current window."""
        cutoff = current_time - self.window_size
        entry.timestamps = [ts for ts in entry.timestamps if ts > cutoff]

    async def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client is within rate limits.

        Args:
            client_id: Unique identifier for the client

        Returns:
            True if request is allowed

        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        entry = self._entries[client_id]
        current_time = time.time()

        async with entry.lock:
            self._cleanup_old_entries(entry, current_time)

            if len(entry.timestamps) >= self.max_requests:
                oldest = entry.timestamps[0]
                wait_time = self.window_size - (current_time - oldest)
                raise RateLimitExceededError(
                    f"Rate limit exceeded. Try again in {wait_time:.1f} seconds.",
                    details={
                        "limit": self.max_requests,
                        "window_seconds": self.window_size,
                        "retry_after": int(wait_time) + 1,
                    },
                )

            entry.timestamps.append(current_time)
            return True

    async def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client in current window."""
        entry = self._entries[client_id]
        current_time = time.time()

        async with entry.lock:
            self._cleanup_old_entries(entry, current_time)
            return max(0, self.max_requests - len(entry.timestamps))

    async def reset(self, client_id: str) -> None:
        """Reset rate limit for a client."""
        entry = self._entries[client_id]
        async with entry.lock:
            entry.timestamps.clear()


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
