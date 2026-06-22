"""Current weather section: main temperature, icon, chips, and history."""

from __future__ import annotations

from collections import deque
from datetime import datetime

import flet as ft

import theme
from i18n import t, tr_list
from logic.weather_icons import WeatherIcons
from models import Weather
from ui.base import WeatherSection
from ui.components import UIComponents


class CurrentWeatherSection(WeatherSection):
    """Card displaying current weather with temperature, icon, chips, and history ribbon.

    Implements :class:`WeatherSection`. Stores the last ``HISTORY_LEN`` weather
    measurements in a circular queue (``deque``) and displays them as a ribbon
    of cells at the bottom of the card. The ribbon cells are created once during
    :meth:`build` and then updated in-place.

    Class Attributes:
        HISTORY_LEN (int): Maximum size of the history queue (7 by default).
    """

    HISTORY_LEN = 7

    def __init__(self) -> None:
        """Initialize internal Flet controls and bounded history queue.

        All text controls (temperature, description, chips) and the icon are
        created here with default values (``"--"``). The history ribbon cells
        are created during :meth:`build`.

        Args:
            None.

        Returns:
            None — :meth:`build` must be called to get the Flet control.
        """
        self.history: deque[Weather] = deque(maxlen=self.HISTORY_LEN)
        self._temp = ft.Text("--°C", size=32, weight=ft.FontWeight.BOLD, color=theme.TEXT)
        self._desc = ft.Text(t("current_weather_section", "waiting"), size=12, color=theme.MUTED)
        self._icon = ft.Icon(ft.Icons.WB_SUNNY, color="#F59E0B", size=30)
        self._chip_hum = ft.Text("--%", size=11, color=theme.MUTED)
        self._chip_wind = ft.Text("-- m/s", size=11, color=theme.MUTED)
        self._chip_feel = ft.Text(t("current_weather_section", "feels_chip", v="--"), size=11, color=theme.MUTED)
        self._history_cells: list[ft.Container] = []

    def build(self) -> ft.Control:
        """Build the complete weather card with main header and history ribbon.

        Creates the 7 ribbon cells via :meth:`_build_history_row` and keeps
        their references for future updates.

        Args:
            None.

        Returns:
            ft.Control: White card containing the weather icon, main temperature,
                chips (humidity, wind, feels-like), and the ribbon of the last 7 measurements.
        """
        history_row = self._build_history_row()
        return UIComponents.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                self._icon,
                                width=56,
                                height=56,
                                border_radius=14,
                                bgcolor="#FFF8E1",
                                border=ft.Border.all(1, "#FFE082"),
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column(
                                [
                                    self._temp,
                                    self._desc,
                                    ft.Row(
                                        [
                                            ft.Row(
                                                [
                                                    ft.Icon(ft.Icons.WATER_DROP, size=13, color=theme.MUTED),
                                                    self._chip_hum,
                                                ],
                                                spacing=3,
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Icon(ft.Icons.AIR, size=13, color=theme.MUTED),
                                                    self._chip_wind,
                                                ],
                                                spacing=3,
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Icon(ft.Icons.REMOVE_RED_EYE, size=13, color=theme.MUTED),
                                                    self._chip_feel,
                                                ],
                                                spacing=3,
                                            ),
                                        ],
                                        spacing=10,
                                        wrap=True,
                                    ),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=20, color=theme.BORDER),
                    ft.Text(
                        t("current_weather_section", "history_title"),
                        size=10,
                        color=theme.MUTED,
                        weight=ft.FontWeight.W_500,
                    ),
                    history_row,
                ],
                spacing=8,
            )
        )

    def _build_history_row(self) -> ft.Row:
        """Create the 7 empty history ribbon cells and keep internal references.

        Each cell stores its sub-controls in ``cell.data`` to allow in-place
        updates without rebuilding the tree.

        Args:
            None.

        Returns:
            ft.Row: Row containing 7 history cells initialized to ``"—"`` / ``"--°"``.
        """
        cells = []
        for _ in range(self.HISTORY_LEN):
            label = ft.Text("—", size=9, color=theme.MUTED, weight=ft.FontWeight.W_500)
            ico = ft.Icon(ft.Icons.WB_SUNNY, color="#F59E0B", size=18)
            hi = ft.Text("--°", size=13, weight=ft.FontWeight.W_600)
            cell = ft.Container(
                content=ft.Column(
                    [label, ico, hi],
                    spacing=3,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=theme.BG,
                padding=ft.Padding.symmetric(vertical=8, horizontal=4),
                border_radius=10,
                border=ft.Border.all(1, theme.BORDER),
                expand=True,
            )
            cell.data = {"label": label, "icon": ico, "hi": hi}
            self._history_cells.append(cell)
            cells.append(cell)
        return ft.Row(cells, spacing=6)

    def update(self, w: Weather) -> None:
        """Update the main card and add the measurement to the history queue.

        Updates in-place the temperature, description, icon, chips, then refreshes
        the history ribbon via :meth:`_refresh_history`.

        Args:
            w (Weather): The new weather measurement to display. Its fields ``temperature_c``,
                ``description``, ``condition``, ``humidity_pct``, ``wind_speed_ms``,
                ``wind_gust_ms``, ``feels_like_c``, and ``timestamp`` are used.

        Returns:
            None — the Flet controls are modified in-place.
        """
        self.history.append(w)
        self._temp.value = f"{w.temperature_c:.0f}°C"

        icon, token = WeatherIcons.for_condition(w.condition)
        self._icon.icon = UIComponents.icon_name(icon)
        self._icon.color = UIComponents.COLOR_TOKENS[token]

        # The API description is free text in a language imposed by the API; instead,
        # display the translated label of the weather token (derived from the condition,
        # like the icon) to stay consistent with the UI language.
        self._desc.value = f"{t('conditions', 'token_' + token)} · {self._pretty_ts(w.timestamp)}"

        self._chip_hum.value = f"{w.humidity_pct}%"
        gust = t("current_weather_section", "gust", v=f"{w.wind_gust_ms:.0f}") if w.wind_gust_ms else ""
        self._chip_wind.value = f"{w.wind_speed_ms:.1f} m/s{gust}"
        self._chip_feel.value = t("current_weather_section", "feels_chip", v=f"{w.feels_like_c:.0f}")

        self._refresh_history()

    def reset(self) -> None:
        """Clear the history and reset the weather card to waiting state.

        Args:
            None.

        Returns:
            None — the Flet controls are modified in-place.
        """
        self.history.clear()
        self._temp.value = "--°C"
        self._desc.value = t("current_weather_section", "waiting")
        self._icon.icon = UIComponents.icon_name(ft.Icons.WB_SUNNY)
        self._icon.color = "#F59E0B"
        self._chip_hum.value = "--%"
        self._chip_wind.value = "-- m/s"
        self._chip_feel.value = t("current_weather_section", "feels_chip", v="--")
        self._refresh_history()

    def _refresh_history(self) -> None:
        """Reflect the current state of the history queue in the ribbon cells.

        Iterates through the 7 cells in insertion order. Cells without a
        corresponding measurement (queue not yet full) are reset to empty values.

        Args:
            None.

        Returns:
            None — the ribbon cells are modified in-place.
        """
        items = list(self.history)
        for i, cell in enumerate(self._history_cells):
            d = cell.data
            if i < len(items):
                w = items[i]
                d["label"].value = self._hour_or_dash(w.timestamp)
                ico_name, token = WeatherIcons.for_condition(w.condition)
                d["icon"].icon = UIComponents.icon_name(ico_name)
                d["icon"].color = UIComponents.COLOR_TOKENS[token]
                d["hi"].value = f"{w.temperature_c:.0f}°"
            else:
                d["label"].value = "—"
                d["icon"].icon = UIComponents.icon_name(ft.Icons.WB_SUNNY)
                d["icon"].color = "#F59E0B"
                d["hi"].value = "--°"

    @staticmethod
    def _pretty_ts(ts: str) -> str:
        """Format an ISO timestamp into a readable and localized label.

        Day and month names come from the ``datetime`` namespace to follow the
        active language (e.g. "Monday 26 May · 14:07", "lunes 26 may. · 14:07").

        Args:
            ts (str): Timestamp in ISO 8601 format (e.g. ``"2024-05-26T14:07:00Z"``).

        Returns:
            str: Formatted and localized label, or the original string if not parseable.
        """
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return ts
        weekdays = tr_list("datetime", "weekdays")
        months = tr_list("datetime", "months")
        weekday = weekdays[dt.weekday()] if len(weekdays) == 7 else dt.strftime("%A")
        month = months[dt.month - 1] if len(months) == 12 else dt.strftime("%b")
        return f"{weekday.capitalize()} {dt.strftime('%d')} {month} · {dt.strftime('%H:%M')}"

    @staticmethod
    def _hour_or_dash(ts: str) -> str:
        """Extract the time in ``HH:MM`` format from an ISO timestamp.

        Args:
            ts (str): Timestamp in ISO 8601 format.

        Returns:
            str: Time in ``"HH:MM"`` format (e.g. ``"14:07"``),
                or ``"—"`` if the timestamp is not parseable.
        """
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%H:%M")
        except Exception:
            return "—"
