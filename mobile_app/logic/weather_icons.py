from __future__ import annotations


class WeatherIcons:

    ICONS: dict[str, tuple[str, str]] = {
        "rain": ("water_drop", "rain"),
        "drizzle": ("water_drop", "rain"),
        "snow": ("ac_unit", "snow"),
        "cloud": ("cloud", "cloud"),
        "storm": ("flash_on", "storm"),
        "thunder": ("flash_on", "storm"),
    }

    @staticmethod
    def for_condition(condition: str) -> tuple[str, str]:
        c = (condition or "").lower()
        for key, value in WeatherIcons.ICONS.items():
            if key in c:
                return value
        return ("wb_sunny", "sun")
