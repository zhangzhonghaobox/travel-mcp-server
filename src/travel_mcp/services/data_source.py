"""Data source switcher for mock vs real API."""

from functools import lru_cache
from typing import TYPE_CHECKING

from travel_mcp.config import get_config

if TYPE_CHECKING:
    from travel_mcp.services.weather_service import WeatherService
    from travel_mcp.services.mock_weather import MockWeatherService
    from travel_mcp.services.product_service import ProductService
    from travel_mcp.services.mock_product import MockProductService
    from travel_mcp.services.mock_attraction import MockAttractionService
    from travel_mcp.services.mock_hotel import MockHotelService
    from travel_mcp.services.mock_flight import MockFlightService


class DataSource:
    """
    Factory class that provides either mock or real services based on configuration.
    """

    def __init__(self) -> None:
        """Initialize data source with configuration."""
        self.config = get_config()

    def get_weather_service(self) -> "WeatherService | MockWeatherService":
        """Get weather service based on use_mock_data setting."""
        if self.config.use_mock_data:
            from travel_mcp.services.mock_weather import MockWeatherService
            return MockWeatherService()
        else:
            from travel_mcp.services.weather_service import WeatherService
            return WeatherService(
                api_key=self.config.amap_api_key or self.config.weather_api_key
            )

    def get_product_service(self) -> "ProductService | MockProductService":
        """Get product service based on use_mock_data setting."""
        if self.config.use_mock_data:
            from travel_mcp.services.mock_product import MockProductService
            return MockProductService()
        else:
            from travel_mcp.services.product_service import ProductService
            return ProductService(api_key=self.config.amap_api_key)

    def get_attraction_service(self) -> "MockAttractionService":
        """Get attraction service (mock only for now)."""
        from travel_mcp.services.mock_attraction import MockAttractionService
        return MockAttractionService()

    def get_hotel_service(self) -> "MockHotelService":
        """Get hotel service (mock only for now)."""
        from travel_mcp.services.mock_hotel import MockHotelService
        return MockHotelService()

    def get_flight_service(self) -> "MockFlightService":
        """Get flight service (mock only for now)."""
        from travel_mcp.services.mock_flight import MockFlightService
        return MockFlightService()


@lru_cache
def get_data_source() -> DataSource:
    """Get cached data source instance."""
    return DataSource()
