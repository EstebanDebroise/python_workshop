"""Section stress thermique : jauge THI circulaire, zone et alertes."""

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
    """Carte de stress thermique affichant la jauge THI, la zone de confort et les alertes.

    Implémente :class:`WeatherSection`. Le THI (Temperature Humidity Index) est
    recalculé à chaque mesure. La jauge circulaire, le badge de zone et les
    bandeaux d'alerte (danger uniquement) sont mis à jour en place.
    La zone d'alerte est masquée par défaut et n'apparaît qu'en cas de danger.
    """

    def __init__(self) -> None:
        """Prépare la jauge circulaire, les libellés de zone et la zone d'alerte cachée.

        Args:
            Aucun.

        Returns:
            None — :meth:`build` doit être appelé pour obtenir le contrôle Flet.
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
        """Construit la carte THI avec jauge circulaire, barème de zones et zone d'alertes.

        La jauge circulaire affiche le THI normalisé sur une plage de 50 à 90.
        Le barème (Normal → Urgence) est représenté par 5 segments colorés.
        La zone d'alertes (bandeau rouge + bandeau info) est invisible au démarrage.

        Args:
            Aucun.

        Returns:
            ft.Control: Carte blanche contenant la jauge THI, les libellés de zone,
                le barème coloré et la zone d'alertes conditionnelle.
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
        """Recalcule le THI, met à jour la jauge et affiche ou masque l'alerte danger.

        Le THI est calculé via :meth:`ThiCalculator.result` à partir de la température
        et de l'humidité. La jauge est normalisée sur la plage [50, 90]. En zone
        danger, deux bandeaux d'alerte (rouge + info) apparaissent dans ``_alert_zone``.

        Args:
            w (Weather): La nouvelle mesure météo. Les champs ``temperature_c``
                et ``humidity_pct`` sont utilisés pour le calcul THI.

        Returns:
            None — les contrôles Flet sont modifiés en place.
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
        """Remet la jauge THI, la zone de confort et l'alerte à leur état d'attente.

        Args:
            Aucun.

        Returns:
            None — les contrôles Flet sont modifiés en place.
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
