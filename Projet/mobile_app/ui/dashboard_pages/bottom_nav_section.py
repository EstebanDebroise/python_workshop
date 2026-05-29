"""Section de navigation inférieure : barre fixe avec 4 onglets."""

from __future__ import annotations

from typing import Callable

import flet as ft

import theme
from ui.base import Buildable
from ui.components import UIComponents


class BottomNavSection(Buildable):
    """Barre de navigation inférieure fixe comportant 4 onglets.

    Implémente :class:`Buildable`. Les onglets « Tableau », « Alertes » et
    « Réglages » sont fonctionnels et déclenchent les callbacks fournis. Seul
    l'onglet Historique reste visuellement présent mais non fonctionnel.
    """

    def __init__(
        self,
        on_dashboard: Callable[[], None],
        on_alerts: Callable[[], None],
        on_settings: Callable[[], None],
    ) -> None:
        """Prépare les contrôles des onglets actifs avec leurs refs d'icône/texte.

        Args:
            on_dashboard (Callable[[], None]): Callback déclenché lors du clic
                sur l'onglet « Tableau ».
            on_alerts (Callable[[], None]): Callback déclenché lors du clic
                sur l'onglet « Alertes ».
            on_settings (Callable[[], None]): Callback déclenché lors du clic
                sur l'onglet « Réglages ».

        Returns:
            None — :meth:`build` doit être appelé pour obtenir le contrôle Flet.
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
                "Tableau", size=9, color=theme.GREEN, weight=ft.FontWeight.W_500
            ),
            "alerts": ft.Text(
                "Alertes", size=9, color=theme.MUTED, weight=ft.FontWeight.W_400
            ),
            "settings": ft.Text(
                "Réglages", size=9, color=theme.MUTED, weight=ft.FontWeight.W_400
            ),
        }

    def set_active(self, tab: str) -> None:
        """Met à jour la couleur et le poids des onglets actifs/inactifs.

        Args:
            tab (str): Identifiant de l'onglet à activer (``"dashboard"``,
                ``"alerts"`` ou ``"settings"``).

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
            alignment=ft.alignment.center,
            on_click=on_click,
        )

    def build(self) -> ft.Control:
        """Construit la barre de navigation avec ses 4 items alignés horizontalement.

        Les onglets « Tableau », « Alertes » et « Réglages » sont cliquables et
        mettent à jour leur état actif. Seul l'onglet Historique est affiché mais inerte.

        Returns:
            ft.Control: ``Container`` blanc avec bordure supérieure et 4 items de navigation.
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
            border=ft.border.only(top=ft.border.BorderSide(1, theme.BORDER)),
            padding=ft.padding.only(top=10, bottom=22),
            content=ft.Row(
                [
                    self._clickable_nav_item("dashboard", on_dashboard_click),
                    UIComponents.nav_item(ft.Icons.SHOW_CHART, "Historique", False),
                    self._clickable_nav_item("alerts", on_alerts_click),
                    self._clickable_nav_item("settings", on_settings_click),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
        )
