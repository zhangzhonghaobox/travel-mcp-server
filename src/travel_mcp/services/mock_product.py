"""Mock product service for testing."""

import random
from typing import Any, Dict, List, Optional

from travel_mcp.utils.cache import timed_cache


class MockProductService:
    """Mock product service providing fake travel product data."""

    PRODUCTS: List[Dict[str, Any]] = [
        {
            "id": "p001",
            "name": "Premium Travel Neck Pillow",
            "category": "accessories",
            "price": 29.99,
            "rating": 4.5,
            "reviews": 1234,
            "description": "Memory foam neck pillow for comfortable travel",
        },
        {
            "id": "p002",
            "name": "Universal Travel Adapter",
            "category": "electronics",
            "price": 39.99,
            "rating": 4.7,
            "reviews": 892,
            "description": "Works in 150+ countries with USB-C fast charging",
        },
        {
            "id": "p003",
            "name": "Lightweight Carry-On Luggage",
            "category": "luggage",
            "price": 149.99,
            "rating": 4.3,
            "reviews": 567,
            "description": "Hard shell spinner wheels 20-inch carry-on",
        },
        {
            "id": "p004",
            "name": "Travel Toiletry Bag",
            "category": "accessories",
            "price": 24.99,
            "rating": 4.6,
            "reviews": 2100,
            "description": "Hanging toiletry organizer with multiple pockets",
        },
        {
            "id": "p005",
            "name": "Portable WiFi Hotspot",
            "category": "electronics",
            "price": 89.99,
            "rating": 4.2,
            "reviews": 445,
            "description": "Global portable WiFi for up to 5 devices",
        },
        {
            "id": "p006",
            "name": "Travel First Aid Kit",
            "category": "safety",
            "price": 34.99,
            "rating": 4.8,
            "reviews": 1800,
            "description": "Comprehensive 100-piece medical kit",
        },
        {
            "id": "p007",
            "name": "Noise Cancelling Headphones",
            "category": "electronics",
            "price": 199.99,
            "rating": 4.9,
            "reviews": 3200,
            "description": "Premium ANC headphones for long flights",
        },
        {
            "id": "p008",
            "name": "Packing Cubes Set",
            "category": "luggage",
            "price": 32.99,
            "rating": 4.4,
            "reviews": 1500,
            "description": "6-piece compression packing cube set",
        },
        {
            "id": "p009",
            "name": "Travel Shoes Bag",
            "category": "luggage",
            "price": 18.99,
            "rating": 4.1,
            "reviews": 678,
            "description": "Waterproof shoe bag for keeping luggage clean",
        },
        {
            "id": "p010",
            "name": "World Travel Guide Book",
            "category": "books",
            "price": 24.99,
            "rating": 4.3,
            "reviews": 890,
            "description": "Comprehensive travel guide with maps and tips",
        },
    ]

    @timed_cache(seconds=300)
    async def search_products(
        self, keywords: str, category: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for products by keywords and optional category.

        Args:
            keywords: Search keywords
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of matching products
        """
        keywords_lower = keywords.lower()
        results = []

        for product in self.PRODUCTS:
            # Check if keywords match name or description
            if keywords_lower in product["name"].lower() or keywords_lower in product["description"].lower():
                if category is None or product["category"] == category:
                    # Add some variance to prices
                    price_variance = random.uniform(-5, 5)
                    result = product.copy()
                    result["price"] = round(product["price"] + price_variance, 2)
                    results.append(result)

            # Also check category matches directly
            elif category and keywords_lower == category.lower():
                if product["category"] == category:
                    result = product.copy()
                    result["price"] = round(product["price"] + random.uniform(-5, 5), 2)
                    results.append(result)

        return results[:limit]
