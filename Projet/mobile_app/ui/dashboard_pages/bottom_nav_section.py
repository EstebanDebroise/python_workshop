"""Bottom navigation section: fixed bar with 4 tabs."""

from __future__ import annotations

from typing import Callable

import flet as ft

import theme
from i18n import t
from ui.base import Buildable
from ui.components import UIComponents


class BottomNavSection(Buildable):
    """Fixed bottom navigation bar with 4 tabs.

    Implements :class:`Buildable`. The tabs "Dashboard", "Alerts", and
    "Settings" are functional and trigger the provided callbacks. Only
    the History tab remains visually present but is not functional.
    """

    def __init__(
        self,
        on_dashboard: Callable[[], None],
        on_alerts: Callable[[], None],
        on_settings: Callable[[], None],
    ) -> None:
        """Prepare active tab controls with their icon/text references.

        Args:
            on_dashboard (Callable[[], None]): Callback triggered on click
                of the "Dashboard" tab.
            on_alerts (Callable[[], None]): Callback triggered on click
                of the "Alerts" tab.
            on_settings (Callable[[], None]): Callback triggered on click
                of the "Settings" tab.

        Returns:
            None — :meth:`build` must be called to get the Flet control.
        """
        self._on_dashboard = on_dashboard
        self._on_alerts = on_alerts
        self._on_settings = on_settings

        self._icons: dict[str, ft.Icon] = {
            "dashboard": ft.Icon(ft.Icons.DASHBOARD, color=theme.GREEN, size=22),
            "alerts": ft.Icon(ft.Icons.NOTIFICATIONS, color=theme.MUTED, size=22),
            "settings": ft.Icon(ft.Icons.SETTINGS, color=theme.MUTED, size=22),
        }
        self._texts: dict[str, ft.Text] = {
            "dashboard": ft.Text(
                t("bottom_nav_section", "dashboard"), size=9, color=theme.GREEN, weight=ft.FontWeight.W_500
            ),
            "alerts": ft.Text(
                t("bottom_nav_section", "alerts"), size=9, color=theme.MUTED, weight=ft.FontWeight.W_400
            ),
            "settings": ft.Text(
                t("bottom_nav_section", "settings"), size=9, color=theme.MUTED, weight=ft.FontWeight.W_400
            ),
        }

    def set_active(self, tab: str) -> None:
        """Update the color and weight of active/inactive tabs.

        Args:
            tab (str): Tab identifier to activate (``"dashboard"``,
                ``"alerts"``, or ``"settings"``).

        Returns:
            None
        """
        for key in ("dashboard", "alerts", "settings"):
            color = theme.GREEN if key == tab else theme.MUTED
            weight = ft.FontWeight.W_500 if key == tab else ft.FontWeight.W_400
            self._icons[key].color = color
            self._texts[key].color = color
            self._texts[key].weight = weight
            self._icons[key].update()
            self._texts[key].update()

    def _clickable_nav_item(self, tab: str, on_click: Callable) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [self._icons[tab], self._texts[tab]],
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.Alignment.CENTER,
            on_click=on_click,
        )

    def build(self) -> ft.Control:
        """Build the navigation bar with its 4 horizontally aligned items.

        The "Dashboard", "Alerts", and "Settings" tabs are clickable and update
        their active state. Only the History tab is displayed but inert.

        Returns:
            ft.Control: White ``Container`` with top border and 4 navigation items.
        """

        def on_dashboard_click(_: ft.ControlEvent) -> None:
            self.set_active("dashboard")
            self._on_dashboard()

        def on_alerts_click(_: ft.ControlEvent) -> None:
            self.set_active("alerts")
            self._on_alerts()

        def on_settings_click(_: ft.ControlEvent) -> None:
            self.set_active("settings")
            self._on_settings()

        return ft.Container(
            bgcolor=theme.CARD,
            border=ft.Border.only(top=ft.BorderSide(1, theme.BORDER)),
            padding=ft.Padding.only(top=10, bottom=22),
            content=ft.Row(
                [
                    self._clickable_nav_item("dashboard", on_dashboard_click),
                    UIComponents.nav_item(ft.Icons.SHOW_CHART, t("bottom_nav_section", "history"), False),
                    self._clickable_nav_item("alerts", on_alerts_click),
                    self._clickable_nav_item("settings", on_settings_click),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
        )
