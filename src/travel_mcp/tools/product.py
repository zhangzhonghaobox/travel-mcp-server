"""Product search tool implementation."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from travel_mcp.tools.base import BaseTool, ToolExecutionContext
from travel_mcp.services.data_source import get_data_source


class ProductSearchInput(BaseModel):
    """Input schema for product search tool."""

    keywords: str = Field(..., description="Search keywords for products")
    category: Optional[str] = Field(
        None, description="Product category to filter by"
    )
    limit: int = Field(
        default=10, ge=1, le=50, description="Maximum number of results to return"
    )


class ProductSearchTool(BaseTool):
    """Tool for searching travel-related products."""

    name: str = "product_search"
    description: str = "Search for travel-related products such as luggage, adapters, travel pillows, etc."

    input_schema = {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "string",
                "description": "Search keywords for products",
            },
            "category": {
                "type": "string",
                "description": "Product category to filter by (optional)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (1-50, default 10)",
                "default": 10,
            },
        },
        "required": ["keywords"],
    }

    async def execute(self, context: ToolExecutionContext) -> Dict[str, Any]:
        """Execute product search."""
        keywords = context.arguments.get("keywords")
        category = context.arguments.get("category")
        limit = context.arguments.get("limit", 10)

        if not keywords:
            return {
                "success": False,
                "error": "Keywords parameter is required",
            }

        data_source = get_data_source()
        product_service = data_source.get_product_service()

        try:
            results = await product_service.search_products(keywords, category, limit)
            return {
                "success": True,
                "data": {
                    "products": results,
                    "count": len(results),
                    "keywords": keywords,
                    "category": category,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
