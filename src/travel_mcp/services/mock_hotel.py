"""Mock hotel service for testing."""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from travel_mcp.utils.cache import timed_cache


class MockHotelService:
    """Mock hotel service providing fake hotel data."""

    HOTELS: List[Dict[str, Any]] = [
        {
            "id": "h001",
            "name": "Grand Palace Hotel",
            "city": "beijing",
            "stars": 5,
            "rating": 4.8,
            "reviews": 2500,
            "base_price": 680.00,
            "amenities": ["wifi", "pool", "gym", "spa", "restaurant"],
            "location": "Dongcheng District",
        },
        {
            "id": "h002",
            "name": "City Center Inn",
            "city": "beijing",
            "stars": 3,
            "rating": 4.2,
            "reviews": 1200,
            "base_price": 280.00,
            "amenities": ["wifi", "restaurant", "parking"],
            "location": "Chaoyang District",
        },
        {
            "id": "h003",
            "name": "Shanghai Bund Hotel",
            "city": "shanghai",
            "stars": 5,
            "rating": 4.9,
            "reviews": 3200,
            "base_price": 850.00,
            "amenities": ["wifi", "pool", "gym", "spa", "restaurant", "bar"],
            "location": "Huangpu District",
        },
        {
            "id": "h004",
            "name": "River View Hotel",
            "city": "shanghai",
            "stars": 4,
            "rating": 4.5,
            "reviews": 1800,
            "base_price": 420.00,
            "amenities": ["wifi", "restaurant", "gym"],
            "location": "Pudong District",
        },
        {
            "id": "h005",
            "name": "Tokyo Imperial Hotel",
            "city": "tokyo",
            "stars": 5,
            "rating": 4.9,
            "reviews": 4000,
            "base_price": 1200.00,
            "amenities": ["wifi", "pool", "gym", "spa", "restaurant", "bar", "concierge"],
            "location": "Marunouchi",
        },
        {
            "id": "h006",
            "name": "Shinjuku Business Hotel",
            "city": "tokyo",
            "stars": 3,
            "rating": 4.1,
            "reviews": 950,
            "base_price": 350.00,
            "amenities": ["wifi", "restaurant"],
            "location": "Shinjuku",
        },
        {
            "id": "h007",
            "name": "Paris Ritz Hotel",
            "city": "paris",
            "stars": 5,
            "rating": 4.9,
            "reviews": 5000,
            "base_price": 1500.00,
            "amenities": ["wifi", "pool", "gym", "spa", "restaurant", "bar", "concierge"],
            "location": "Place Vendome",
        },
        {
            "id": "h008",
            "name": "Montmartre Inn",
            "city": "paris",
            "stars": 3,
            "rating": 4.3,
            "reviews": 1100,
            "base_price": 180.00,
            "amenities": ["wifi", "breakfast"],
            "location": "Montmartre",
        },
    ]

    def _calculate_nights(self, check_in: str, check_out: str) -> int:
        """Calculate number of nights from check-in and check-out dates."""
        try:
            d1 = datetime.strptime(check_in, "%Y-%m-%d")
            d2 = datetime.strptime(check_out, "%Y-%m-%d")
            nights = (d2 - d1).days
            return max(1, nights)
        except ValueError:
            return 1

    @timed_cache(seconds=300)
    async def search_hotels(
        self,
        city: str,
        check_in: str,
        check_out: str,
        guests: int = 1,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for hotels by city and dates.

        Args:
            city: City to search
            check_in: Check-in date YYYY-MM-DD
            check_out: Check-out date YYYY-MM-DD
            guests: Number of guests
            limit: Maximum results

        Returns:
            List of matching hotels with pricing
        """
        city_lower = city.lower()
        nights = self._calculate_nights(check_in, check_out)
        results = []

        for hotel in self.HOTELS:
            if hotel["city"] == city_lower:
                # Calculate price based on nights and guests
                price_variance = random.uniform(-50, 50)
                base = hotel["base_price"] + price_variance
                # Additional guest fee
                if guests > 2:
                    base *= 1.1
                total_price = base * nights

                result = hotel.copy()
                result["check_in"] = check_in
                result["check_out"] = check_out
                result["nights"] = nights
                result["guests"] = guests
                result["price_per_night"] = round(base, 2)
                result["total_price"] = round(total_price, 2)
                result["currency"] = "CNY" if city_lower in ["beijing", "shanghai"] else "USD"
                results.append(result)

        return results[:limit]
