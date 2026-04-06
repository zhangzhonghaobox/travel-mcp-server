"""Hotel search tool implementation."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from travel_mcp.tools.base import BaseTool, ToolExecutionContext
from travel_mcp.services.data_source import get_data_source


class HotelSearchInput(BaseModel):
    """Input schema for hotel search tool."""

    city: str = Field(..., description="City to search hotels in")
    check_in_date: str = Field(..., description="Check-in date in YYYY-MM-DD format")
    check_out_date: str = Field(..., description="Check-out date in YYYY-MM-DD format")
    guests: int = Field(default=1, ge=1, le=10, description="Number of guests")
    limit: int = Field(
        default=10, ge=1, le=50, description="Maximum number of results to return"
    )


class HotelSearchTool(BaseTool):
    """Tool for searching hotels."""

    name: str = "hotel_search"
    description: str = "Search for hotels in a city with check-in/out dates and guest count."

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City to search hotels in",
            },
            "check_in_date": {
                "type": "string",
                "description": "Check-in date in YYYY-MM-DD format",
            },
            "check_out_date": {
                "type": "string",
                "description": "Check-out date in YYYY-MM-DD format",
            },
            "guests": {
                "type": "integer",
                "description": "Number of guests (1-10, default 1)",
                "default": 1,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (1-50, default 10)",
                "default": 10,
            },
        },
        "required": ["city", "check_in_date", "check_out_date"],
    }

    async def execute(self, context: ToolExecutionContext) -> Dict[str, Any]:
        """Execute hotel search."""
        city = context.arguments.get("city")
        check_in = context.arguments.get("check_in_date")
        check_out = context.arguments.get("check_out_date")
        guests = context.arguments.get("guests", 1)
        limit = context.arguments.get("limit", 10)

        if not city or not check_in or not check_out:
            return {
                "success": False,
                "error": "City, check_in_date, and check_out_date are required",
            }

        data_source = get_data_source()
        hotel_service = data_source.get_hotel_service()

        try:
            results = await hotel_service.search_hotels(city, check_in, check_out, guests, limit)
            return {
                "success": True,
                "data": {
                    "hotels": results,
                    "count": len(results),
                    "city": city,
                    "check_in": check_in,
                    "check_out": check_out,
                    "guests": guests,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
