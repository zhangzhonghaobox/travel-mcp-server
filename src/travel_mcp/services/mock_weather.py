"""Mock weather service for testing."""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from travel_mcp.utils.cache import timed_cache


class MockWeatherService:
    """Mock weather service providing fake but realistic weather data."""

    # Sample cities with base temperatures
    CITIES_BASE_TEMP: Dict[str, Dict[str, Any]] = {
        "beijing": {"country": "China", "base_temp": 15, "condition": "Sunny"},
        "shanghai": {"country": "China", "base_temp": 18, "condition": "Cloudy"},
        "tokyo": {"country": "Japan", "base_temp": 16, "condition": "Partly Cloudy"},
        "paris": {"country": "France", "base_temp": 14, "condition": "Rainy"},
        "london": {"country": "UK", "base_temp": 12, "condition": "Overcast"},
        "new york": {"country": "USA", "base_temp": 15, "condition": "Sunny"},
        "los angeles": {"country": "USA", "base_temp": 22, "condition": "Sunny"},
        "sydney": {"country": "Australia", "base_temp": 20, "condition": "Clear"},
        "dubai": {"country": "UAE", "base_temp": 32, "condition": "Hot"},
        "singapore": {"country": "Singapore", "base_temp": 28, "condition": "Humid"},
    }

    CONDITIONS = [
        "Sunny",
        "Cloudy",
        "Partly Cloudy",
        "Rainy",
        "Stormy",
        "Snowy",
        "Foggy",
        "Windy",
        "Clear",
        "Overcast",
    ]

    @timed_cache(seconds=300)
    async def get_weather(
        self, city: str, date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get mock weather for a city.

        Args:
            city: City name (case-insensitive)
            date_str: Optional date in YYYY-MM-DD format

        Returns:
            Simulated weather data
        """
        city_lower = city.lower()
        city_data = self.CITIES_BASE_TEMP.get(city_lower)

        if city_data:
            base_temp = city_data["base_temp"]
            country = city_data["country"]
            base_condition = city_data["condition"]
        else:
            # Default for unknown cities
            base_temp = 20
            country = "Unknown"
            base_condition = "Sunny"

        # Add some variance based on date
        target_date = date_str or date.today().isoformat()
        date_hash = hash(target_date) % 10
        variance = date_hash - 5

        return {
            "city": city.title(),
            "country": country,
            "date": target_date,
            "temperature_c": base_temp + variance,
            "temperature_f": int((base_temp + variance) * 9 / 5 + 32),
            "feels_like_c": base_temp + variance - 2,
            "humidity": 50 + (date_hash * 5) % 40,
            "wind_kph": 10 + date_hash * 2,
            "condition": base_condition,
            "condition_icon": f"https://cdn.weatherapi.com/weather/64x64/day/116.png",
            "uv_index": 5 + date_hash % 5,
            "forecast": {
                "date": target_date,
                "max_temp_c": base_temp + variance + 5,
                "min_temp_c": base_temp + variance - 5,
                "avg_temp_c": base_temp + variance,
                "max_wind_kph": 15 + date_hash * 3,
                "total_precip_mm": date_hash * 2,
                "avg_humidity": 55 + date_hash * 3,
                "daily_chance_of_rain": min(80, date_hash * 10),
                "condition": base_condition,
            },
        }
