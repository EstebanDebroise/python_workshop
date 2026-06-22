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
                "cold_shelter",
                "cold",
                {"feels": f"{feels_diff:+.0f}"},
            ))
        if w.temperature_c >= 25 and w.clouds_pct <= 10 and w.wind_speed_ms <= 1:
            alerts.append(PastureAlert("wb_sunny", "sun_shade", "sun"))
        if w.temperature_c >= 30:
            alerts.append(PastureAlert("local_drink", "heat_water", "warn"))
        if w.temperature_c <= 5 and w.wind_speed_ms >= 4:
            alerts.append(PastureAlert("ac_unit", "cold_hypothermia", "cold"))
        return alerts
