from __future__ import annotations

from typing import Optional

from models import Weather

import i18n
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
            msgs.append(i18n.t("messages", "thi_danger"))
        rain_prev = prev.rain_1h_mm or 0
        rain_now = curr.rain_1h_mm or 0
        if rain_now > 0 and rain_prev == 0:
            msgs.append(i18n.t("messages", "rain_started"))
        if curr.condition != prev.condition:
            msgs.append(i18n.t(
                "messages",
                "condition_change",
                prev=i18n.t("conditions", prev.condition),
                curr=i18n.t("conditions", curr.condition),
            ))
        return msgs
