"""Tourist attraction search tool implementation."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from travel_mcp.tools.base import BaseTool, ToolExecutionContext
from travel_mcp.services.data_source import get_data_source


class TouristAttractionSearchInput(BaseModel):
    """Input schema for tourist attraction search tool."""

    destination: str = Field(..., description="Destination city or location")
    tags: Optional[List[str]] = Field(
        None, description="Interest tags to filter attractions (e.g., history, nature, food)"
    )
    limit: int = Field(
        default=10, ge=1, le=50, description="Maximum number of results to return"
    )


class TouristAttractionSearchTool(BaseTool):
    """Tool for searching tourist attractions."""

    name: str = "tourist_attraction_search"
    description: str = "Search for tourist attractions at a destination with filtering by interest tags."

    input_schema = {
        "type": "object",
        "properties": {
            "destination": {
                "type": "string",
                "description": "Destination city or location to search attractions",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Interest tags to filter attractions (e.g., history, nature, food)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (1-50, default 10)",
                "default": 10,
            },
        },
        "required": ["destination"],
    }

    async def execute(self, context: ToolExecutionContext) -> Dict[str, Any]:
        """Execute tourist attraction search."""
        destination = context.arguments.get("destination")
        tags = context.arguments.get("tags")
        limit = context.arguments.get("limit", 10)

        if not destination:
            return {
                "success": False,
                "error": "Destination parameter is required",
            }

        data_source = get_data_source()
        attraction_service = data_source.get_attraction_service()

        try:
            results = await attraction_service.search_attractions(destination, tags, limit)
            return {
                "success": True,
                "data": {
                    "attractions": results,
                    "count": len(results),
                    "destination": destination,
                    "tags": tags or [],
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
