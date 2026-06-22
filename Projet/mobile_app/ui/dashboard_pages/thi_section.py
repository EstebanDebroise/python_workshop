"""Thermal stress section: circular THI gauge, comfort zone, and alerts."""

from __future__ import annotations

import flet as ft

import theme
from i18n import t
from logic.thi_calculator import ThiCalculator
from logic.thi_result import ThiResult
from models import Weather
from ui.badge import Badge
from ui.base import WeatherSection
from ui.components import UIComponents


class ThiSection(WeatherSection):
    """Thermal stress card displaying THI gauge, comfort zone, and alerts.

    Implements :class:`WeatherSection`. The THI (Temperature Humidity Index)
    is recalculated with each measurement. The circular gauge, zone badge, and
    alert banners (danger only) are updated in-place. The alert zone is hidden
    by default and only appears in case of danger.
    """

    def __init__(self) -> None:
        """Prepare the circular gauge, zone labels, and hidden alert zone.

        Args:
            None.

        Returns:
            None — :meth:`build` must be called to get the Flet control.
        """
        self.badge = Badge("—", "ok")
        self._value = ft.Text("--", size=22, weight=ft.FontWeight.BOLD, color=theme.RED, text_align=ft.TextAlign.CENTER)
        self._ring = ft.ProgressRing(
            value=0,
            width=90,
            height=90,
            color=theme.RED,
            bgcolor="#F5E9E9",
            stroke_width=8,
        )
        self._status = ft.Text("—", size=15, weight=ft.FontWeight.BOLD, color=theme.RED)
        self._desc = ft.Text(t("thi_section", "waiting"), size=11, color=theme.MUTED)
        self._alert_zone = ft.Container(visible=False)

    def build(self) -> ft.Control:
        """Build the THI card with circular gauge, zone scale, and alert zone.

        The circular gauge displays the THI normalized over the range 50 to 90.
        The zone scale (Normal → Emergency) is represented by 5 colored segments.
        The alert zone (red banner + info banner) is invisible at startup.

        Args:
            None.

        Returns:
            ft.Control: White card containing the THI gauge, zone labels,
                colored scale, and conditional alert zone.
        """
        return UIComponents.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(t("thi_section", "title"), size=13, weight=ft.FontWeight.W_600),
                            self.badge.control,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        [
                            ft.Stack(
                                [
                                    self._ring,
                                    ft.Container(
                                        content=ft.Column(
                                            [
                                                self._value,
                                                ft.Text("THI", size=9, color=theme.MUTED, text_align=ft.TextAlign.CENTER),
                                            ],
                                            spacing=0,
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            alignment=ft.MainAxisAlignment.CENTER,
                                        ),
                                        width=90,
                                        height=90,
                                        alignment=ft.Alignment(0, 0),
                                    ),
                                ],
                                width=90,
                                height=90,
                            ),
                            ft.Column(
                                [
                                    self._status,
                                    self._desc,
                                    ft.Row(
                                        [
                                            ft.Container(expand=1, height=6, bgcolor=theme.GREEN_LIGHT, border_radius=2),
                                            ft.Container(expand=1, height=6, bgcolor=theme.GREEN_LIGHT, border_radius=2),
                                            ft.Container(expand=1, height=6, bgcolor=theme.AMBER, border_radius=2),
                                            ft.Container(expand=1, height=6, bgcolor=theme.ORANGE, border_radius=2),
                                            ft.Container(expand=1, height=6, bgcolor=theme.RED, border_radius=2),
                                        ],
                                        spacing=3,
                                    ),
                                    ft.Row(
                                        [
                                            ft.Text(t("thi_section", "zone_normal"), size=9, color=theme.MUTED),
                                            ft.Text(t("thi_section", "zone_alert"), size=9, color=theme.MUTED),
                                            ft.Text(t("thi_section", "zone_danger"), size=9, color=theme.MUTED),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),
                                ],
                                spacing=6,
                                expand=True,
                            ),
                        ],
                        spacing=14,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._alert_zone,
                ],
                spacing=12,
            )
        )

    def update(self, w: Weather) -> None:
        """Recalculate THI, update gauge, and show or hide danger alert.

        The THI is calculated via :meth:`ThiCalculator.result` from temperature
        and humidity. The gauge is normalized over the range [50, 90]. In the
        danger zone, two alert banners (red + info) appear in ``_alert_zone``.

        Args:
            w (Weather): The new weather measurement. The fields ``temperature_c``
                and ``humidity_pct`` are used for THI calculation.

        Returns:
            None — the Flet controls are modified in-place.
        """
        result: ThiResult = ThiCalculator.result(w.temperature_c, w.humidity_pct)
        color = UIComponents.COLOR_TOKENS[result.color_token]

        self._value.value = f"{result.value:.0f}"
        self._value.color = color
        self._ring.color = color
        self._ring.value = max(0.0, min(1.0, (result.value - 50) / 40))
        self._status.value = t("thi_section", f"{result.code}_label")
        self._status.color = color
        self._desc.value = t("thi_section", f"{result.code}_desc")
        self.badge.update(t("thi_section", f"{result.code}_badge"), result.kind)

        if result.kind == "danger":
            self._alert_zone.content = ft.Column(
                [
                    UIComponents.danger_alert(
                        ft.Icons.WARNING_AMBER,
                        t("thi_section", "danger_alert", value=f"{result.value:.0f}"),
                    ),
                    UIComponents.info_alert(
                        ft.Icons.NOTIFICATIONS_ACTIVE,
                        t("thi_section", "danger_info"),
                    ),
                ],
                spacing=6,
            )
            self._alert_zone.visible = True
        else:
            self._alert_zone.visible = False

    def reset(self) -> None:
        """Reset the THI gauge, comfort zone, and alert to waiting state.

        Args:
            None.

        Returns:
            None — the Flet controls are modified in-place.
        """
        self._value.value = "--"
        self._value.color = theme.RED
        self._ring.value = 0
        self._ring.color = theme.RED
        self._status.value = "—"
        self._status.color = theme.RED
        self._desc.value = t("thi_section", "waiting")
        self.badge.update("—", "ok")
        self._alert_zone.visible = False
