"""Spraying and treatment section: evaluated time slots and legend."""

from __future__ import annotations

import flet as ft

import theme
from i18n import t
from logic.treatment_analyzer import TreatmentAnalyzer
from logic.treatment_slot import TreatmentSlot
from models import Weather
from ui.badge import Badge
from ui.base import WeatherSection
from ui.components import UIComponents


class TreatmentSection(WeatherSection):
    """Spraying card displaying 3 evaluated time slots and their legend.

    Implements :class:`WeatherSection`. The time slots (−2h / now / +3h) are
    recalculated with each new measurement via :func:`TreatmentAnalyzer.slots`.
    Each slot is displayed with a color code (optimal / risky / discouraged).
    The badge summarizes the number of slots deemed optimal.
    """

    def __init__(self) -> None:
        """Initialize the empty slot column and summary badge.

        Args:
            None.

        Returns:
            None — :meth:`build` must be called to get the Flet control.
        """
        self.badge = Badge("—", "ok")
        self._slots = ft.Column([], spacing=6)

    def build(self) -> ft.Control:
        """Build the card with title, dynamic slot list, and color legend.

        The ``_slots`` column is inserted empty; it will be filled by :meth:`update`.
        The legend (Optimal / Risky / Discouraged) is static.

        Args:
            None.

        Returns:
            ft.Control: White card with title, slot list, and legend.
        """
        return UIComponents.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                t("treatment_section", "title"),
                                size=13,
                                weight=ft.FontWeight.W_600,
                            ),
                            self.badge.control,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self._slots,
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Container(width=8, height=8, bgcolor=theme.GREEN_LIGHT, border_radius=4),
                                    ft.Text(t("treatment_section", "legend_optimal"), size=10, color=theme.MUTED),
                                ],
                                spacing=4,
                            ),
                            ft.Row(
                                [
                                    ft.Container(width=8, height=8, bgcolor=theme.AMBER, border_radius=4),
                                    ft.Text(t("treatment_section", "legend_risky"), size=10, color=theme.MUTED),
                                ],
                                spacing=4,
                            ),
                            ft.Row(
                                [
                                    ft.Container(width=8, height=8, bgcolor=theme.RED, border_radius=4),
                                    ft.Text(t("treatment_section", "legend_discouraged"), size=10, color=theme.MUTED),
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=14,
                    ),
                ],
                spacing=10,
            )
        )

    def update(self, w: Weather) -> None:
        """Recalculate the 3 spraying slots and update the summary badge.

        Delegates calculation to :func:`TreatmentAnalyzer.slots` then rebuilds
        the list of visual lines via :meth:`_render_slot`. The badge displays
        the number of optimal slots or "NONE" if no optimal slots are available.

        Args:
            w (Weather): The new weather measurement used as the basis for calculation.
                The fields ``wind_speed_ms``, ``rain_1h_mm``, and ``temperature_c``
                are used to evaluate each slot.

        Returns:
            None — the Flet controls are modified in-place.
        """
        slots = TreatmentAnalyzer.slots(w)
        self._slots.controls = [self._render_slot(s) for s in slots]
        ok_count = sum(1 for s in slots if s.status == "ok")
        if ok_count:
            self.badge.update(t("treatment_section", "badge_ok", count=ok_count), "ok")
        else:
            self.badge.update(t("treatment_section", "badge_none"), "danger")

    def reset(self) -> None:
        """Clear the slot list and reset the badge to waiting state.

        Args:
            None.

        Returns:
            None — the Flet controls are modified in-place.
        """
        self._slots.controls = []
        self.badge.update("—", "ok")

    @staticmethod
    def _render_slot(s: TreatmentSlot) -> ft.Container:
        """Build the visual line of a time slot with its color code.

        Background, border, and dot are determined by the slot status:
        ``"ok"`` → green, ``"warn"`` → amber, ``"no"`` → red.

        Args:
            s (TreatmentSlot): Time slot with its attributes: ``label`` (time range),
                ``wind`` (m/s), ``rain`` (mm), ``temp`` (°C), and ``status`` (ok/warn/no).

        Returns:
            ft.Container: Styled line containing the time label, weather indicators
                (wind, rain, temperature), and status dot.
        """
        styles = {
            "ok": (theme.GREEN_LIGHT, "#F0FDF4", "#BBF7D0"),
            "warn": (theme.AMBER, "#FFFBEB", "#FDE68A"),
            "no": (theme.RED, "#FEF2F2", "#FECACA"),
        }
        dot, bg, border = styles[s.status]
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(s.label, size=12, weight=ft.FontWeight.W_600, width=86),
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.AIR, size=13, color=theme.MUTED),
                                    ft.Text(f"{s.wind:.1f} m/s", size=10, color=theme.MUTED),
                                ],
                                spacing=3,
                            ),
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.WATER_DROP, size=13, color=theme.MUTED),
                                    ft.Text(f"{s.rain:.1f} mm", size=10, color=theme.MUTED),
                                ],
                                spacing=3,
                            ),
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.THERMOSTAT, size=13, color=theme.MUTED),
                                    ft.Text(f"{s.temp:.0f}°C", size=10, color=theme.MUTED),
                                ],
                                spacing=3,
                            ),
                        ],
                        spacing=8,
                        expand=True,
                    ),
                    ft.Container(width=8, height=8, bgcolor=dot, border_radius=4),
                ],
                spacing=10,
            ),
            bgcolor=bg,
            border=ft.Border.all(1, border),
            padding=ft.Padding.symmetric(horizontal=11, vertical=9),
            border_radius=10,
        )
