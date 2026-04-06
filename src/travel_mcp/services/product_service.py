"""Real product API service."""

from typing import Any, Dict, List, Optional

import httpx

from travel_mcp.core.error_handler import ServiceUnavailableError, TimeoutError
from travel_mcp.utils.retry import retry_with_backoff


class ProductService:
    """Real product search service using external API (e.g., Taobao/JD)."""

    def __init__(self, api_key: str) -> None:
        """Initialize product service with API key."""
        self.api_key = api_key
        # Placeholder - in real implementation, use actual API
        self.base_url = "https://api.example.com/v1"
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def search_products(
        self, keywords: str, category: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for products using real API.

        Note: This is a placeholder implementation. In production,
        integrate with actual product APIs like Taobao, JD, etc.
        """
        # This would make actual API calls in production
        # For now, raise an error indicating real API is not implemented
        raise ServiceUnavailableError(
            "Real product API not configured. Set USE_MOCK_DATA=false and provide valid API key."
        )
