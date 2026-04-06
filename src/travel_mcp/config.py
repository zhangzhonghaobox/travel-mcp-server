"""Configuration management for Travel MCP Server."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPServerConfig(BaseSettings):
    """Main configuration class for the Travel MCP Server."""

    # Server Identity
    server_name: str = Field(default="travel-mcp-server", description="Server name")
    version: str = Field(default="1.0.0", description="Server version")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, ge=1, le=65535, description="Port to bind to")

    # MCP Configuration
    mcp_host: str = Field(default="0.0.0.0", description="MCP host")
    mcp_port: int = Field(default=8000, ge=1, le=65535, description="MCP port")

    # Performance Configuration
    max_concurrent_requests: int = Field(
        default=100, ge=1, description="Maximum concurrent requests"
    )
    request_timeout: float = Field(
        default=30.0, ge=0.1, description="Request timeout in seconds"
    )

    # Data Source Configuration
    use_mock_data: bool = Field(
        default=True,
        description="Use mock data instead of real APIs",
    )

    # Real API Keys
    amap_api_key: str = Field(
        default="",
        description="Amap (Gaode) Maps API Key for real weather/location data",
    )
    weather_api_key: str = Field(
        default="",
        description="WeatherAPI Key for real weather data",
    )

    # Security Configuration
    api_key: str = Field(
        default="",
        description="API key for authenticating requests",
    )
    rate_limit_per_minute: int = Field(
        default=60, ge=1, description="Rate limit per minute per client"
    )

    # Monitoring Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    metrics_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TRAVEL_",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @property
    def api_key_enabled(self) -> bool:
        """Check if API key authentication is enabled."""
        return bool(self.api_key)


@lru_cache
def get_config() -> MCPServerConfig:
    """Get cached configuration instance."""
    return MCPServerConfig()
