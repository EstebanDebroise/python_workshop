"""Page Alertes : activation des notifications de changement météo."""

from __future__ import annotations

import flet as ft

import theme
from i18n import t
from logic.notification_service import NotificationService
from ui.base import Buildable
from ui.components import UIComponents


class NotificationsView(Buildable):
    """Page permettant d'activer/désactiver les notifications d'alerte météo.

    Implémente :class:`Buildable`. Affiche un interrupteur relié au
    :class:`NotificationService` partagé : son état est persistant et pilote
    l'envoi des notifications système déclenchées par la boucle de polling.
    """

    #: Icône + clé de traduction des changements météo surveillés (affichés à titre informatif).
    MONITORED = [
        (ft.Icons.THERMOSTAT, "monitored_thi"),
        (ft.Icons.WATER_DROP, "monitored_rain"),
        (ft.Icons.CLOUD, "monitored_condition"),
    ]

    def __init__(self, service: NotificationService) -> None:
        """Prépare l'interrupteur à partir de l'état courant du service.

        Args:
            service (NotificationService): Service partagé qui mémorise la
                préférence d'activation et émet les notifications.
        """
        self._service = service
        self._switch = ft.Switch(
            value=service.enabled,
            active_color=theme.GREEN,
            on_change=self._on_toggle,
        )
        self._status = ft.Text(
            self._status_text(service.enabled),
            size=12,
            color=theme.GREEN if service.enabled else theme.MUTED,
        )

    def _status_text(self, enabled: bool) -> str:
        return t("notifications_view", "enabled_status" if enabled else "disabled_status")

    def _on_toggle(self, e: ft.ControlEvent) -> None:
        """Persiste le nouvel état et met à jour le texte de statut."""
        enabled = bool(self._switch.value)
        self._service.set_enabled(enabled)
        self._status.value = self._status_text(enabled)
        self._status.color = theme.GREEN if enabled else theme.MUTED
        self._status.update()

    def _monitored_rows(self) -> list[ft.Control]:
        return [
            ft.Row(
                [
                    ft.Icon(icon, color=theme.GREEN, size=16),
                    ft.Text(t("notifications_view", key), size=12, color=theme.TEXT, expand=True),
                ],
                spacing=8,
            )
            for icon, key in self.MONITORED
        ]

    def build(self) -> ft.Control:
        """Construit la page Alertes (interrupteur + liste des alertes surveillées).

        Returns:
            ft.Control: ``Column`` reprenant la charte des autres sections
                (label de section + cartes blanches).
        """
        toggle_card = UIComponents.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.NOTIFICATIONS_ACTIVE,
                                        color=theme.GREEN,
                                        size=18,
                                    ),
                                    ft.Text(
                                        t("notifications_view", "title"),
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=theme.TEXT,
                                    ),
                                ],
                                spacing=8,
                            ),
                            self._switch,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self._status,
                ],
                spacing=8,
            )
        )

        info_card = UIComponents.card(
            ft.Column(
                [
                    ft.Text(
                        t("notifications_view", "monitored_title"),
                        size=13,
                        weight=ft.FontWeight.W_600,
                        color=theme.TEXT,
                    ),
                    *self._monitored_rows(),
                    ft.Container(height=2),
                    ft.Text(
                        t("notifications_view", "info_text"),
                        size=11,
                        color=theme.MUTED,
                    ),
                ],
                spacing=10,
            )
        )

        return ft.Column(
            [
                UIComponents.section_label(t("notifications_view", "section_label")),
                toggle_card,
                info_card,
            ],
            spacing=10,
        )
