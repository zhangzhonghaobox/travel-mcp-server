"""Flight search tool implementation."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from travel_mcp.tools.base import BaseTool, ToolExecutionContext
from travel_mcp.services.data_source import get_data_source


class FlightSearchInput(BaseModel):
    """Input schema for flight search tool."""

    origin: str = Field(..., description="Origin city or airport code")
    destination: str = Field(..., description="Destination city or airport code")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(
        None, description="Return date in YYYY-MM-DD format for round trip"
    )
    passengers: int = Field(default=1, ge=1, le=9, description="Number of passengers")
    limit: int = Field(
        default=10, ge=1, le=50, description="Maximum number of results to return"
    )


class FlightSearchTool(BaseTool):
    """Tool for searching flights."""

    name: str = "flight_search"
    description: str = "Search for flights between two locations with date and passenger information."

    input_schema = {
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "Origin city or airport code (e.g., PEK, LAX)",
            },
            "destination": {
                "type": "string",
                "description": "Destination city or airport code (e.g., SHA, TYO)",
            },
            "departure_date": {
                "type": "string",
                "description": "Departure date in YYYY-MM-DD format",
            },
            "return_date": {
                "type": "string",
                "description": "Return date in YYYY-MM-DD format for round trip (optional)",
            },
            "passengers": {
                "type": "integer",
                "description": "Number of passengers (1-9, default 1)",
                "default": 1,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (1-50, default 10)",
                "default": 10,
            },
        },
        "required": ["origin", "destination", "departure_date"],
    }

    async def execute(self, context: ToolExecutionContext) -> Dict[str, Any]:
        """Execute flight search."""
        origin = context.arguments.get("origin")
        destination = context.arguments.get("destination")
        departure = context.arguments.get("departure_date")
        return_date = context.arguments.get("return_date")
        passengers = context.arguments.get("passengers", 1)
        limit = context.arguments.get("limit", 10)

        if not origin or not destination or not departure:
            return {
                "success": False,
                "error": "Origin, destination, and departure_date are required",
            }

        data_source = get_data_source()
        flight_service = data_source.get_flight_service()

        try:
            results = await flight_service.search_flights(
                origin, destination, departure, return_date, passengers, limit
            )
            return {
                "success": True,
                "data": {
                    "flights": results,
                    "count": len(results),
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure,
                    "return_date": return_date,
                    "passengers": passengers,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
