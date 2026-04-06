"""Tests for product tool."""

import pytest
from unittest.mock import AsyncMock, patch

from travel_mcp.tools.product import ProductSearchTool, ProductSearchInput
from travel_mcp.tools.base import ToolExecutionContext


class TestProductSearchTool:
    """Test suite for ProductSearchTool."""

    @pytest.fixture
    def tool(self) -> ProductSearchTool:
        """Create product search tool instance."""
        return ProductSearchTool()

    @pytest.fixture
    def context(self) -> ToolExecutionContext:
        """Create tool execution context."""
        return ToolExecutionContext(
            request_id="test-456",
            tool_name="product_search",
            arguments={"keywords": "pillow"},
        )

    @pytest.mark.asyncio
    async def test_tool_name(self, tool: ProductSearchTool) -> None:
        """Test tool name is correct."""
        assert tool.name == "product_search"

    @pytest.mark.asyncio
    async def test_tool_description(self, tool: ProductSearchTool) -> None:
        """Test tool has description."""
        assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_input_schema(self, tool: ProductSearchTool) -> None:
        """Test input schema structure."""
        assert "type" in tool.input_schema
        assert tool.input_schema["type"] == "object"
        assert "properties" in tool.input_schema
        assert "keywords" in tool.input_schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_with_keywords(self, tool: ProductSearchTool, context: ToolExecutionContext) -> None:
        """Test execute with keywords."""
        with patch("travel_mcp.tools.product.get_data_source") as mock_ds:
            mock_service = AsyncMock()
            mock_service.search_products.return_value = [
                {"id": "p001", "name": "Travel Pillow", "price": 29.99}
            ]
            mock_ds.return_value.get_product_service.return_value = mock_service

            result = await tool.execute(context)

        assert result["success"] is True
        assert "data" in result
        assert "products" in result["data"]
        assert len(result["data"]["products"]) == 1

    @pytest.mark.asyncio
    async def test_execute_missing_keywords(self, tool: ProductSearchTool) -> None:
        """Test execute without keywords returns error."""
        context = ToolExecutionContext(
            request_id="test-456",
            tool_name="product_search",
            arguments={},
        )

        result = await tool.execute(context)

        assert result["success"] is False
        assert "error" in result


class TestProductSearchInput:
    """Test suite for ProductSearchInput model."""

    def test_valid_input(self) -> None:
        """Test valid input creation."""
        input_data = ProductSearchInput(keywords="luggage")
        assert input_data.keywords == "luggage"
        assert input_data.category is None
        assert input_data.limit == 10

    def test_input_with_all_params(self) -> None:
        """Test input with all parameters."""
        input_data = ProductSearchInput(
            keywords="adapter",
            category="electronics",
            limit=20,
        )
        assert input_data.keywords == "adapter"
        assert input_data.category == "electronics"
        assert input_data.limit == 20

    def test_limit_validation(self) -> None:
        """Test limit parameter validation."""
        with pytest.raises(Exception):
            ProductSearchInput(keywords="test", limit=100)  # Over max
