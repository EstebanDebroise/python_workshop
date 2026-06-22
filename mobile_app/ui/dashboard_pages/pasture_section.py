"""Pasture comfort section: 4 weather indicators and pasture alerts."""

from __future__ import annotations

from typing import Iterable

import flet as ft

import theme
from i18n import t
from logic.pasture_alert import PastureAlert
from logic.pasture_analyzer import PastureAnalyzer
from models import Weather
from ui.badge import Badge
from ui.base import WeatherSection
from ui.components import UIComponents


class PastureSection(WeatherSection):
    """Pasture comfort card displaying 4 indicators and animal alerts.

    Implements :class:`WeatherSection`. Displays actual temperature, feels-like,
    wind speed, and cloud coverage in a 2×2 grid. A contextual line appears when
    the feels-like/actual temperature gap exceeds 2°C. Business alerts (cold,
    sunshine, heat) are rendered as banners. The badge indicates overall alert level
    (OK or VIGILANCE).
    """

    def __init__(self) -> None:
        """Prepare the statistics grid and initially empty alert containers.

        Args:
            None.

        Returns:
            None — :meth:`build` must be called to get the Flet control.
        """
        self.badge = Badge("—", "ok")
        self._temp = ft.Text("--", size=18, weight=ft.FontWeight.BOLD)
        self._feels = ft.Text("--", size=18, weight=ft.FontWeight.BOLD, color=theme.SKY_DARK)
        self._wind = ft.Text("--", size=18, weight=ft.FontWeight.BOLD)
        self._clouds = ft.Text("--", size=18, weight=ft.FontWeight.BOLD)
        self._feels_row = ft.Container(visible=False)
        self._alerts = ft.Column([], spacing=6)

    def build(self) -> ft.Control:
        """Build the card with title, 2×2 grid, feels-like line, and alert zone.

        The feels-like line (``_feels_row``) and alert column (``_alerts``)
        are inserted empty and will be filled dynamically by :meth:`update`.

        Args:
            None.

        Returns:
            ft.Control: White card with statistics grid, contextual line,
                and pasture alert zone.
        """
        return UIComponents.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(t("pasture_section", "title"), size=13, weight=ft.FontWeight.W_600),
                            self.badge.control,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        [
                            UIComponents.stat_cell(self._temp, "°C", t("pasture_section", "stat_temp")),
                            UIComponents.stat_cell(self._feels, "°C", t("pasture_section", "stat_feels")),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            UIComponents.stat_cell(self._wind, "m/s", t("pasture_section", "stat_wind")),
                            UIComponents.stat_cell(self._clouds, "%", t("pasture_section", "stat_clouds")),
                        ],
                        spacing=8,
                    ),
                    self._feels_row,
                    self._alerts,
                ],
                spacing=10,
            )
        )

    def update(self, w: Weather) -> None:
        """Update the 4 indicators, feels-like line, and pasture alerts.

        If the gap between feels-like and actual temperature is ≥ 2°C, a contextual
        line is displayed. Business alerts are recalculated via :func:`PastureAnalyzer.alerts`
        and rendered via :meth:`_render_pasture_alerts`. The badge switches to VIGILANCE
        as soon as at least one alert is present.

        Args:
            w (Weather): The new weather measurement. The fields ``temperature_c``,
                ``feels_like_c``, ``wind_speed_ms``, and ``clouds_pct`` are used.

        Returns:
            None — the Flet controls are modified in-place.
        """
        self._temp.value = f"{w.temperature_c:.0f}"
        self._feels.value = f"{w.feels_like_c:.0f}"
        self._wind.value = f"{w.wind_speed_ms:.1f}"
        self._clouds.value = f"{w.clouds_pct}"

        feels_diff = w.feels_like_c - w.temperature_c
        if abs(feels_diff) >= 2:
            wind_word = t("pasture_section", "wind_strong" if w.wind_speed_ms >= 5 else "wind_moderate")
            self._feels_row.content = ft.Row(
                [
                    ft.Icon(ft.Icons.AIR, color=theme.SOIL, size=18),
                    ft.Column(
                        [
                            ft.Text(
                                t("pasture_section", "wind_impact", wind=wind_word, diff=f"{feels_diff:+.0f}"),
                                size=12,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(t("pasture_section", "comfort_impact"), size=10, color=theme.MUTED),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    ft.Text(
                        f"{feels_diff:+.0f}°",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=theme.SKY_DARK,
                    ),
                ],
                spacing=8,
            )
            self._feels_row.bgcolor = theme.SOIL_PALE
            self._feels_row.padding = 8
            self._feels_row.border_radius = 10
            self._feels_row.visible = True
        else:
            self._feels_row.visible = False

        self._alerts.controls = list(self._render_pasture_alerts(PastureAnalyzer.alerts(w)))
        if not self._alerts.controls:
            self.badge.update(t("pasture_section", "badge_ok"), "ok")
        else:
            self.badge.update(t("pasture_section", "badge_warning"), "warn")

    def reset(self) -> None:
        """Reset the 4 indicators, feels-like line, and alerts to waiting state.

        Args:
            None.

        Returns:
            None — the Flet controls are modified in-place.
        """
        self._temp.value = "--"
        self._feels.value = "--"
        self._wind.value = "--"
        self._clouds.value = "--"
        self._feels_row.visible = False
        self._alerts.controls = []
        self.badge.update("—", "ok")

    @staticmethod
    def _render_pasture_alerts(alerts: Iterable[PastureAlert]) -> Iterable[ft.Control]:
        """Convert a list of business alerts to colored Flet banners by type.

        Dispatch each alert to the corresponding visual helper based on its ``kind``:
        ``"cold"`` → blue banner, ``"sun"`` → yellow banner, other → amber banner.

        Args:
            alerts (Iterable[PastureAlert]): Alerts from :func:`PastureAnalyzer.alerts`,
                each carrying an ``icon``, a ``message``, and a ``kind``.

        Returns:
            Iterable[ft.Control]: Generator of Flet banners, one per alert.
        """
        for a in alerts:
            icon = UIComponents.icon_name(a.icon)
            message = t("pasture_section", a.code, **a.params)
            if a.kind == "cold":
                yield UIComponents.cold_alert(icon, message)
            elif a.kind == "sun":
                yield UIComponents.sun_alert(icon, message)
            else:
                yield UIComponents.warn_alert(icon, message)
