from __future__ import annotations

from typing import Optional

from models import Weather

from logic.thi_calculator import ThiCalculator


class WeatherNotifier:

    @staticmethod
    def change_notifications(prev: Optional[Weather], curr: Weather) -> list[str]:
        if prev is None:
            return []
        msgs: list[str] = []
        thi_prev = ThiCalculator.compute(prev.temperature_c, prev.humidity_pct)
        thi_now = ThiCalculator.compute(curr.temperature_c, curr.humidity_pct)
        if thi_now >= 79 > thi_prev:
            msgs.append("Stress thermique : zone danger atteinte (THI)")
        rain_prev = prev.rain_1h_mm or 0
        rain_now = curr.rain_1h_mm or 0
        if rain_now > 0 and rain_prev == 0:
            msgs.append("Pluie en cours — pulvérisation à reporter")
        if curr.condition != prev.condition:
            msgs.append(f"Changement de temps : {prev.condition} → {curr.condition}")
        return msgs
