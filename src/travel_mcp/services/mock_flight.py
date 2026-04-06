"""Mock flight service for testing."""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from travel_mcp.utils.cache import timed_cache


class MockFlightService:
    """Mock flight service providing fake flight data."""

    AIRLINES: List[Dict[str, str]] = [
        {"code": "CA", "name": "Air China"},
        {"code": "MU", "name": "China Eastern"},
        {"code": "CZ", "name": "China Southern"},
        {"code": "AA", "name": "American Airlines"},
        {"code": "UA", "name": "United Airlines"},
        {"code": "DL", "name": "Delta Air Lines"},
        {"code": "BA", "name": "British Airways"},
        {"code": "LH", "name": "Lufthansa"},
        {"code": "AF", "name": "Air France"},
        {"code": "EK", "name": "Emirates"},
    ]

    AIRPORTS: Dict[str, Dict[str, str]] = {
        "PEK": {"city": "beijing", "name": "Beijing Capital International"},
        "SHA": {"city": "shanghai", "name": "Shanghai Hongqiao International"},
        "PVG": {"city": "shanghai", "name": "Shanghai Pudong International"},
        "NRT": {"city": "tokyo", "name": "Narita International"},
        "HND": {"city": "tokyo", "name": "Tokyo Haneda"},
        "CDG": {"city": "paris", "name": "Charles de Gaulle"},
        "ORY": {"city": "paris", "name": "Orly"},
        "LHR": {"city": "london", "name": "Heathrow"},
        "JFK": {"city": "new york", "name": "John F. Kennedy International"},
        "LAX": {"city": "los angeles", "name": "Los Angeles International"},
    }

    def _get_airport_info(self, code: str) -> Dict[str, str]:
        """Get airport info by code."""
        return self.AIRPORTS.get(code.upper(), {"city": "unknown", "name": code})

    def _find_airport_by_city(self, city_or_code: str) -> Optional[str]:
        """Find airport code for a city or return the code if it's an airport."""
        city_lower = city_or_code.lower()
        # Check if it's an airport code
        if city_or_code.upper() in self.AIRPORTS:
            return city_or_code.upper()
        # Search by city name
        for code, info in self.AIRPORTS.items():
            if info["city"] == city_lower:
                return code
        return None

    def _generate_flight_number(self, airline_code: str) -> str:
        """Generate a realistic flight number."""
        return f"{airline_code}{random.randint(100, 9999)}"

    def _generate_time(self, base_hour: int, variance: int = 2) -> str:
        """Generate a departure/arrival time."""
        hour = (base_hour + random.randint(-variance, variance)) % 24
        minute = random.choice([0, 15, 30, 45])
        return f"{hour:02d}:{minute:02d}"

    @timed_cache(seconds=300)
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        passengers: int = 1,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for flights between origin and destination.

        Args:
            origin: Origin city or airport code
            destination: Destination city or airport code
            departure_date: Departure date YYYY-MM-DD
            return_date: Optional return date for round trip
            passengers: Number of passengers
            limit: Maximum results

        Returns:
            List of matching flights with pricing
        """
        origin_code = self._find_airport_by_city(origin)
        dest_code = self._find_airport_by_city(destination)

        if not origin_code or not dest_code:
            return []

        origin_info = self._get_airport_info(origin_code)
        dest_info = self._get_airport_info(dest_code)

        # Calculate flight duration based on route (simplified)
        duration_hours = 2 + random.randint(0, 8)
        base_price = 300 + duration_hours * 80

        # Add some variance
        price_multiplier = random.uniform(0.8, 1.5)

        results = []
        num_flights = min(limit, 6)

        for _ in range(num_flights):
            airline = random.choice(self.AIRLINES)
            depart_hour = random.randint(6, 22)

            depart_time = self._generate_time(depart_hour)
            # Parse departure date and calculate arrival
            try:
                dep_dt = datetime.strptime(f"{departure_date} {depart_time}", "%Y-%m-%d %H:%M")
                arr_dt = dep_dt + timedelta(hours=duration_hours)
                arr_time = arr_dt.strftime("%H:%M")
                arr_date = arr_dt.strftime("%Y-%m-%d")
            except ValueError:
                arr_time = self._generate_time(depart_hour + duration_hours)
                arr_date = departure_date

            flight = {
                "flight_number": self._generate_flight_number(airline["code"]),
                "airline": airline["name"],
                "airline_code": airline["code"],
                "origin": {
                    "code": origin_code,
                    "city": origin_info["city"],
                    "airport": origin_info["name"],
                },
                "destination": {
                    "code": dest_code,
                    "city": dest_info["city"],
                    "airport": dest_info["name"],
                },
                "departure_date": departure_date,
                "departure_time": depart_time,
                "arrival_date": arr_date,
                "arrival_time": arr_time,
                "duration_hours": duration_hours,
                "stops": random.choice([0, 1, 1, 2]),
                "price_per_person": round(base_price * price_multiplier, 2),
                "total_price": round(base_price * price_multiplier * passengers, 2),
                "currency": "USD",
                "seats_available": random.randint(1, 50),
                "class": random.choice(["economy", "economy", "business", "first"]),
            }

            if return_date:
                # Generate return flight
                return_airline = random.choice(self.AIRLINES)
                return_depart_hour = random.randint(6, 20)
                return_depart_time = self._generate_time(return_depart_hour)
                return_duration = duration_hours + random.randint(-1, 2)

                try:
                    ret_dt = datetime.strptime(f"{return_date} {return_depart_time}", "%Y-%m-%d %H:%M")
                    ret_arr_dt = ret_dt + timedelta(hours=return_duration)
                    return_arr_time = ret_arr_dt.strftime("%H:%M")
                    return_arr_date = ret_arr_dt.strftime("%Y-%m-%d")
                except ValueError:
                    return_arr_time = self._generate_time(return_depart_hour + return_duration)
                    return_arr_date = return_date

                flight["return_flight"] = {
                    "flight_number": self._generate_flight_number(return_airline["code"]),
                    "airline": return_airline["name"],
                    "airline_code": return_airline["code"],
                    "origin": {
                        "code": dest_code,
                        "city": dest_info["city"],
                        "airport": dest_info["name"],
                    },
                    "destination": {
                        "code": origin_code,
                        "city": origin_info["city"],
                        "airport": origin_info["name"],
                    },
                    "departure_date": return_date,
                    "departure_time": return_depart_time,
                    "arrival_date": return_arr_date,
                    "arrival_time": return_arr_time,
                    "duration_hours": return_duration,
                    "stops": flight["stops"],
                }
                # Round trip pricing
                flight["total_price"] = round(flight["total_price"] * 1.8, 2)
                flight["trip_type"] = "round_trip"
            else:
                flight["trip_type"] = "one_way"

            results.append(flight)

        return results
