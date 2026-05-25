"""Modèle de données météo issu des messages Kafka."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Weather:
    """Représente une mesure météo instantanée publiée sur Kafka.

    Immuable (``frozen=True``) afin de pouvoir être stockée sans risque
    dans une file d'historique et partagée entre threads.
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
        """Construit une instance à partir du payload JSON Kafka brut.

        Les champs manquants ou ``null`` sont remplacés par des valeurs
        neutres (0 pour les numériques, chaîne vide pour les textes)
        pour éviter de propager des erreurs jusqu'à l'interface.
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
