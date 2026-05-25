from __future__ import annotations

from models import Weather

from logic.pasture_alert import PastureAlert


class PastureAnalyzer:

    @staticmethod
    def alerts(w: Weather) -> list[PastureAlert]:
        alerts: list[PastureAlert] = []
        feels_diff = w.feels_like_c - w.temperature_c
        if feels_diff <= -3 and w.wind_speed_ms >= 5:
            alerts.append(PastureAlert(
                "home_work",
                f"Vent fort → ressenti {feels_diff:+.0f}°C. Abriter veaux et agneaux.",
                "cold",
            ))
        if w.temperature_c >= 25 and w.clouds_pct <= 10 and w.wind_speed_ms <= 1:
            alerts.append(PastureAlert(
                "wb_sunny",
                "Ciel dégagé + air immobile → ensoleillement maximal. Ombre obligatoire.",
                "sun",
            ))
        if w.temperature_c >= 30:
            alerts.append(PastureAlert(
                "local_drink",
                "Chaleur élevée : doubler les points d'eau du troupeau.",
                "warn",
            ))
        if w.temperature_c <= 5 and w.wind_speed_ms >= 4:
            alerts.append(PastureAlert(
                "ac_unit",
                "Froid + vent : risque hypothermie pour les jeunes.",
                "cold",
            ))
        return alerts
