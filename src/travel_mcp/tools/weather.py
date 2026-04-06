"""Weather query tool implementation."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from travel_mcp.tools.base import BaseTool, ToolExecutionContext
from travel_mcp.services.data_source import get_data_source


class WeatherQueryInput(BaseModel):
    """Input schema for weather query tool."""

    city: str = Field(..., description="City name to query weather for")
    date: Optional[str] = Field(
        None, description="Date to query in YYYY-MM-DD format, defaults to today"
    )


class WeatherQueryTool(BaseTool):
    """Tool for querying weather information."""

    name: str = "weather_query"
    description: str = "Query weather forecast for a city. Returns temperature, humidity, and conditions."

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name to query weather for",
            },
            "date": {
                "type": "string",
                "description": "Date to query in YYYY-MM-DD format, defaults to today",
            },
        },
        "required": ["city"],
    }

    async def execute(self, context: ToolExecutionContext) -> Dict[str, Any]:
        """Execute weather query."""
        city = context.arguments.get("city")
        date = context.arguments.get("date")

        if not city:
            return {
                "success": False,
                "error": "City parameter is required",
            }

        data_source = get_data_source()
        weather_service = data_source.get_weather_service()

        try:
            result = await weather_service.get_weather(city, date)
            return {
                "success": True,
                "data": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
