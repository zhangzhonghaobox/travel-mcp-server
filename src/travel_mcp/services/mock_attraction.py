"""Mock attraction service for testing."""

from typing import Any, Dict, List, Optional

from travel_mcp.utils.cache import timed_cache


class MockAttractionService:
    """Mock attraction service providing fake tourist attraction data."""

    ATTRACTIONS: List[Dict[str, Any]] = [
        {
            "id": "a001",
            "name": "Great Wall of China",
            "city": "beijing",
            "tags": ["history", "landmark", " UNESCO"],
            "rating": 4.8,
            "reviews": 50000,
            "price": 45.00,
            "currency": "CNY",
            "description": "Ancient defensive wall stretching over 13,000 miles",
            "opening_hours": "07:30-17:30",
        },
        {
            "id": "a002",
            "name": "Forbidden City",
            "city": "beijing",
            "tags": ["history", "museum", "culture"],
            "rating": 4.7,
            "reviews": 35000,
            "price": 60.00,
            "currency": "CNY",
            "description": "Imperial palace complex from the Ming and Qing dynasties",
            "opening_hours": "08:30-17:00",
        },
        {
            "id": "a003",
            "name": "The Bund",
            "city": "shanghai",
            "tags": ["landmark", "viewing", "nightlife"],
            "rating": 4.6,
            "reviews": 28000,
            "price": 0.00,
            "currency": "CNY",
            "description": "Waterfront promenade with stunning skyline views",
            "opening_hours": "Open 24 hours",
        },
        {
            "id": "a004",
            "name": "Tokyo Tower",
            "city": "tokyo",
            "tags": ["landmark", "viewing", "romantic"],
            "rating": 4.5,
            "reviews": 22000,
            "price": 1200.00,
            "currency": "JPY",
            "description": "Iconic communications and observation tower",
            "opening_hours": "09:00-23:00",
        },
        {
            "id": "a005",
            "name": "Senso-ji Temple",
            "city": "tokyo",
            "tags": ["history", "culture", "spiritual"],
            "rating": 4.7,
            "reviews": 40000,
            "price": 0.00,
            "currency": "JPY",
            "description": "Ancient Buddhist temple in Asakusa",
            "opening_hours": "06:00-17:00",
        },
        {
            "id": "a006",
            "name": "Eiffel Tower",
            "city": "paris",
            "tags": ["landmark", "romantic", "viewing"],
            "rating": 4.8,
            "reviews": 80000,
            "price": 26.00,
            "currency": "EUR",
            "description": "Iconic iron lattice tower and symbol of Paris",
            "opening_hours": "09:30-23:45",
        },
        {
            "id": "a007",
            "name": "Louvre Museum",
            "city": "paris",
            "tags": ["art", "museum", "history"],
            "rating": 4.9,
            "reviews": 60000,
            "price": 17.00,
            "currency": "EUR",
            "description": "World's largest art museum housing the Mona Lisa",
            "opening_hours": "09:00-18:00",
        },
        {
            "id": "a008",
            "name": "Big Ben",
            "city": "london",
            "tags": ["landmark", "history", "architecture"],
            "rating": 4.7,
            "reviews": 45000,
            "price": 0.00,
            "currency": "GBP",
            "description": "Iconic clock tower at the Palace of Westminster",
            "opening_hours": "External viewing only",
        },
        {
            "id": "a009",
            "name": "Statue of Liberty",
            "city": "new york",
            "tags": ["landmark", "history", "culture"],
            "rating": 4.8,
            "reviews": 70000,
            "price": 24.00,
            "currency": "USD",
            "description": "Neoclassical sculpture gifted by France",
            "opening_hours": "08:30-16:00",
        },
        {
            "id": "a010",
            "name": "Central Park",
            "city": "new york",
            "tags": ["nature", "park", "relaxation"],
            "rating": 4.9,
            "reviews": 90000,
            "price": 0.00,
            "currency": "USD",
            "description": "Urban park spanning 843 acres in Manhattan",
            "opening_hours": "06:00-01:00",
        },
    ]

    @timed_cache(seconds=300)
    async def search_attractions(
        self, destination: str, tags: Optional[List[str]] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for attractions by destination and optional tags.

        Args:
            destination: Destination city
            tags: Optional list of interest tags
            limit: Maximum number of results

        Returns:
            List of matching attractions
        """
        dest_lower = destination.lower()
        results = []

        for attraction in self.ATTRACTIONS:
            if attraction["city"] == dest_lower:
                if tags:
                    # Check if any tag matches
                    attraction_tags_lower = [t.lower() for t in attraction["tags"]]
                    if any(tag.lower() in attraction_tags_lower for tag in tags):
                        results.append(attraction)
                else:
                    results.append(attraction)

        return results[:limit]
