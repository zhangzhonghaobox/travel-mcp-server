"""Real weather API service using Amap/WeatherAPI."""

from datetime import date
from typing import Any, Dict, Optional

import httpx

from travel_mcp.core.error_handler import ServiceUnavailableError, TimeoutError
from travel_mcp.utils.retry import retry_with_backoff


class WeatherService:
    """Real weather service using external API."""

    def __init__(self, api_key: str) -> None:
        """Initialize weather service with API key."""
        self.api_key = api_key
        self.base_url = "https://api.weatherapi.com/v1"
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def get_weather(
        self, city: str, date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get weather for a city from real API.

        Args:
            city: City name
            date_str: Optional date in YYYY-MM-DD format

        Returns:
            Weather data including temperature, humidity, conditions
        """
        try:
            query = f"{city}"
            if date_str:
                query = f"{city}/{date_str}"

            url = f"{self.base_url}/forecast.json"
            params = {
                "key": self.api_key,
                "q": city,
                "days": 1 if date_str else 3,
                "aqi": "no",
                "alerts": "no",
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return self._parse_weather_response(data, date_str)

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Weather API timeout for city {city}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ServiceUnavailableError("Invalid weather API key")
            elif e.response.status_code == 403:
                raise ServiceUnavailableError("Weather API access forbidden")
            raise ServiceUnavailableError(f"Weather API error: {e.response.status_code}")
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to fetch weather: {str(e)}")

    def _parse_weather_response(
        self, data: Dict[str, Any], date_str: Optional[str]
    ) -> Dict[str, Any]:
        """Parse API response into standardized format."""
        location = data.get("location", {})
        current = data.get("current", {})
        forecast = data.get("forecast", {}).get("forecastday", [{}])[0]

        return {
            "city": location.get("name"),
            "country": location.get("country"),
            "date": date_str or date.today().isoformat(),
            "temperature_c": current.get("temp_c"),
            "temperature_f": current.get("temp_f"),
            "feels_like_c": current.get("feelslike_c"),
            "humidity": current.get("humidity"),
            "wind_kph": current.get("wind_kph"),
            "condition": current.get("condition", {}).get("text"),
            "condition_icon": current.get("condition", {}).get("icon"),
            "uv_index": current.get("uv"),
            "forecast": {
                "date": forecast.get("date"),
                "max_temp_c": forecast.get("day", {}).get("maxtemp_c"),
                "min_temp_c": forecast.get("day", {}).get("mintemp_c"),
                "avg_temp_c": forecast.get("day", {}).get("avgtemp_c"),
                "max_wind_kph": forecast.get("day", {}).get("maxwind_kph"),
                "total_precip_mm": forecast.get("day", {}).get("totalprecip_mm"),
                "avg_humidity": forecast.get("day", {}).get("avghumidity"),
                "daily_chance_of_rain": forecast.get("day", {}).get("daily_chance_of_rain"),
                "condition": forecast.get("day", {}).get("condition", {}).get("text"),
            },
        }
