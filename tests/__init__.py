"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from travel_mcp.config import get_config, MCPServerConfig
from travel_mcp.main import create_app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def config() -> MCPServerConfig:
    """Get test configuration."""
    return get_config()


@pytest.fixture
def app():
    """Create test application."""
    return create_app()


@pytest.fixture
def client(app) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_api_key() -> str:
    """Mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def auth_headers(mock_api_key: str) -> dict:
    """Authentication headers for testing."""
    return {"x-api-key": mock_api_key}


@pytest_asyncio.fixture
async def mock_weather_data() -> dict:
    """Mock weather data for testing."""
    return {
        "city": "Beijing",
        "country": "China",
        "date": "2024-01-15",
        "temperature_c": 15,
        "temperature_f": 59,
        "feels_like_c": 13,
        "humidity": 65,
        "wind_kph": 12,
        "condition": "Sunny",
        "uv_index": 5,
    }


@pytest_asyncio.fixture
async def mock_product_data() -> list:
    """Mock product data for testing."""
    return [
        {
            "id": "p001",
            "name": "Travel Neck Pillow",
            "category": "accessories",
            "price": 29.99,
            "rating": 4.5,
        }
    ]
