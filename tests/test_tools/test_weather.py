"""Tests for weather tool."""

import pytest
from unittest.mock import AsyncMock, patch

from travel_mcp.tools.weather import WeatherQueryTool, WeatherQueryInput
from travel_mcp.tools.base import ToolExecutionContext


class TestWeatherQueryTool:
    """Test suite for WeatherQueryTool."""

    @pytest.fixture
    def tool(self) -> WeatherQueryTool:
        """Create weather tool instance."""
        return WeatherQueryTool()

    @pytest.fixture
    def context(self) -> ToolExecutionContext:
        """Create tool execution context."""
        return ToolExecutionContext(
            request_id="test-123",
            tool_name="weather_query",
            arguments={"city": "Beijing"},
        )

    @pytest.mark.asyncio
    async def test_tool_name(self, tool: WeatherQueryTool) -> None:
        """Test tool name is correct."""
        assert tool.name == "weather_query"

    @pytest.mark.asyncio
    async def test_tool_description(self, tool: WeatherQueryTool) -> None:
        """Test tool has description."""
        assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_input_schema(self, tool: WeatherQueryTool) -> None:
        """Test input schema structure."""
        assert "type" in tool.input_schema
        assert tool.input_schema["type"] == "object"
        assert "properties" in tool.input_schema
        assert "city" in tool.input_schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_with_city(self, tool: WeatherQueryTool, context: ToolExecutionContext) -> None:
        """Test execute with city parameter."""
        with patch("travel_mcp.tools.weather.get_data_source") as mock_ds:
            mock_service = AsyncMock()
            mock_service.get_weather.return_value = {
                "city": "Beijing",
                "temperature_c": 15,
                "condition": "Sunny",
            }
            mock_ds.return_value.get_weather_service.return_value = mock_service

            result = await tool.execute(context)

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["city"] == "Beijing"

    @pytest.mark.asyncio
    async def test_execute_missing_city(self, tool: WeatherQueryTool) -> None:
        """Test execute without city returns error."""
        context = ToolExecutionContext(
            request_id="test-123",
            tool_name="weather_query",
            arguments={},
        )

        result = await tool.execute(context)

        assert result["success"] is False
        assert "error" in result


class TestWeatherQueryInput:
    """Test suite for WeatherQueryInput model."""

    def test_valid_input(self) -> None:
        """Test valid input creation."""
        input_data = WeatherQueryInput(city="Shanghai")
        assert input_data.city == "Shanghai"
        assert input_data.date is None

    def test_input_with_date(self) -> None:
        """Test input with date."""
        input_data = WeatherQueryInput(city="Tokyo", date="2024-01-15")
        assert input_data.city == "Tokyo"
        assert input_data.date == "2024-01-15"
