"""Section confort au pré : 4 indicateurs météo et alertes de pâturage."""

from __future__ import annotations

from typing import Iterable

import flet as ft

import theme
from mobile_app.logic.pasture_alert import PastureAlert
from mobile_app.logic.pasture_analyzer import PastureAnalyzer
from models import Weather
from ui.badge import Badge
from ui.base import WeatherSection
from ui.components import UIComponents


class PastureSection(WeatherSection):
    """Carte de confort au pré affichant 4 indicateurs et les alertes animales.

    Implémente :class:`WeatherSection`. Affiche température réelle, ressenti,
    vitesse du vent et couverture nuageuse dans une grille 2×2. Une ligne
    contextuelle apparaît quand l'écart ressenti/réel dépasse 2°C. Les alertes
    métier (froid, ensoleillement, canicule) sont rendues sous forme de bandeaux.
    Le badge indique le niveau global de vigilance (OK ou VIGILANCE).
    """

    def __init__(self) -> None:
        """Prépare la grille de statistiques et les conteneurs d'alertes initialement vides.

        Args:
            Aucun.

        Returns:
            None — :meth:`build` doit être appelé pour obtenir le contrôle Flet.
        """
        self.badge = Badge("—", "ok")
        self._temp = ft.Text("--", size=18, weight=ft.FontWeight.BOLD)
        self._feels = ft.Text("--", size=18, weight=ft.FontWeight.BOLD, color=theme.SKY_DARK)
        self._wind = ft.Text("--", size=18, weight=ft.FontWeight.BOLD)
        self._clouds = ft.Text("--", size=18, weight=ft.FontWeight.BOLD)
        self._feels_row = ft.Container(visible=False)
        self._alerts = ft.Column([], spacing=6)

    def build(self) -> ft.Control:
        """Construit la carte avec titre, grille 2×2, ligne ressenti et zone d'alertes.

        La ligne ressenti (``_feels_row``) et la colonne d'alertes (``_alerts``)
        sont insérées vides et seront remplies dynamiquement par :meth:`update`.

        Args:
            Aucun.

        Returns:
            ft.Control: Carte blanche avec grille de statistiques, ligne contextuelle
                et zone d'alertes de pâturage.
        """
        return UIComponents.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Ressenti & Pâturage", size=13, weight=ft.FontWeight.W_600),
                            self.badge.control,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        [
                            UIComponents.stat_cell(self._temp, "°C", "Température réelle"),
                            UIComponents.stat_cell(self._feels, "°C", "Ressenti"),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            UIComponents.stat_cell(self._wind, "m/s", "Vent"),
                            UIComponents.stat_cell(self._clouds, "%", "Nuages"),
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
        """Met à jour les 4 indicateurs, la ligne ressenti et les alertes de pâturage.

        Si l'écart entre ressenti et température réelle est ≥ 2°C, une ligne
        contextuelle est affichée. Les alertes métier sont recalculées via
        :func:`analytics.pasture_alerts` et rendues via :meth:`_render_pasture_alerts`.
        Le badge passe à VIGILANCE dès qu'au moins une alerte est présente.

        Args:
            w (Weather): La nouvelle mesure météo. Les champs ``temperature_c``,
                ``feels_like_c``, ``wind_speed_ms`` et ``clouds_pct`` sont utilisés.

        Returns:
            None — les contrôles Flet sont modifiés en place.
        """
        self._temp.value = f"{w.temperature_c:.0f}"
        self._feels.value = f"{w.feels_like_c:.0f}"
        self._wind.value = f"{w.wind_speed_ms:.1f}"
        self._clouds.value = f"{w.clouds_pct}"

        feels_diff = w.feels_like_c - w.temperature_c
        if abs(feels_diff) >= 2:
            wind_word = "fort" if w.wind_speed_ms >= 5 else "modéré"
            self._feels_row.content = ft.Row(
                [
                    ft.Icon(ft.Icons.AIR, color=theme.SOIL, size=18),
                    ft.Column(
                        [
                            ft.Text(
                                f"Vent {wind_word} → ressenti {feels_diff:+.0f}°C",
                                size=12,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text("Impact sur le confort animal", size=10, color=theme.MUTED),
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
            self.badge.update("OK", "ok")
        else:
            self.badge.update("VIGILANCE", "warn")

    @staticmethod
    def _render_pasture_alerts(alerts: Iterable[PastureAlert]) -> Iterable[ft.Control]:
        """Convertit une liste d'alertes métier en bandeaux Flet colorés selon leur type.

        Dispatche chaque alerte vers le helper visuel correspondant selon son ``kind`` :
        ``"cold"`` → bandeau bleu, ``"sun"`` → bandeau jaune, autre → bandeau ambre.

        Args:
            alerts (Iterable[PastureAlert]): Alertes issues de :func:`analytics.pasture_alerts`,
                chacune portant un ``icon``, un ``message`` et un ``kind``.

        Returns:
            Iterable[ft.Control]: Générateur de bandeaux Flet, un par alerte.
        """
        for a in alerts:
            icon = UIComponents.icon_name(a.icon)
            if a.kind == "cold":
                yield UIComponents.cold_alert(icon, a.message)
            elif a.kind == "sun":
                yield UIComponents.sun_alert(icon, a.message)
            else:
                yield UIComponents.warn_alert(icon, a.message)
