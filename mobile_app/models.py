"""Weather data model from Kafka messages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Weather:
    """Represents an instantaneous weather measurement published on Kafka.

    Immutable (``frozen=True``) so it can be safely stored
    in a history queue and shared between threads.
    """

    location: str
    country: str
    condition: str
    description: str
    temperature_c: float
    feels_like_c: float
    humidity_pct: int
    pressure_hpa: int
    wind_speed_ms: float
    wind_gust_ms: Optional[float]
    rain_1h_mm: Optional[float]
    snow_1h_mm: Optional[float]
    clouds_pct: int
    visibility_m: int
    timestamp: str

    @classmethod
    def from_message(cls, m: dict) -> "Weather":
        """Constructs an instance from raw Kafka JSON payload.

        Missing or ``null`` fields are replaced with neutral values
        (0 for numerics, empty string for text) to prevent errors
        from propagating to the UI.
        """
        w = m.get("weather", {})
        return cls(
            location=m.get("location", "—"),
            country=m.get("country", ""),
            condition=w.get("condition", "—"),
            description=w.get("description", ""),
            temperature_c=float(w.get("temperature_c", 0) or 0),
            feels_like_c=float(w.get("feels_like_c", 0) or 0),
            humidity_pct=int(w.get("humidity_pct", 0) or 0),
            pressure_hpa=int(w.get("pressure_hpa", 0) or 0),
            wind_speed_ms=float(w.get("wind_speed_ms", 0) or 0),
            wind_gust_ms=w.get("wind_gust_ms"),
            rain_1h_mm=w.get("rain_1h_mm"),
            snow_1h_mm=w.get("snow_1h_mm"),
            clouds_pct=int(w.get("clouds_pct", 0) or 0),
            visibility_m=int(w.get("visibility_m", 0) or 0),
            timestamp=m.get("timestamp", ""),
        )
