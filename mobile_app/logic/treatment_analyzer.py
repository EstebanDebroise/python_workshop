from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from models import Weather

from logic.treatment_slot import SlotStatus, TreatmentSlot


class TreatmentAnalyzer:

    @staticmethod
    def _slot_status(wind: float, rain: float, temp: float) -> SlotStatus:
        if wind >= 7 or rain >= 1 or temp >= 32:
            return "no"
        if wind >= 4 or rain >= 0.2 or temp >= 28:
            return "warn"
        return "ok"

    @staticmethod
    def slots(w: Weather, now: Optional[datetime] = None) -> list[TreatmentSlot]:
        base = (now or datetime.now()).replace(minute=0, second=0, microsecond=0)
        out: list[TreatmentSlot] = []
        for offset_h, wind_factor, extra_rain in [(-2, 0.5, 0.0), (0, 1.0, 0.0), (3, 0.7, w.rain_1h_mm or 0.0)]:
            start = base + timedelta(hours=offset_h)
            wind = w.wind_speed_ms * wind_factor
            rain = extra_rain
            temp = w.temperature_c
            out.append(TreatmentSlot(
                label=f"{start.strftime('%H:%M')}–{(start + timedelta(hours=2)).strftime('%H:%M')}",
                wind=wind, rain=rain, temp=temp,
                status=TreatmentAnalyzer._slot_status(wind, rain, temp),
            ))
        return out
