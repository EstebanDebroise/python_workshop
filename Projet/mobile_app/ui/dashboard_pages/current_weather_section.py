"""Section météo actuelle : température principale, icône, chips et historique."""

from __future__ import annotations

from collections import deque
from datetime import datetime

import flet as ft

import theme
from analytics import icon_for_condition
from models import Weather
from ui.base import WeatherSection
from ui.components import UIComponents


class CurrentWeatherSection(WeatherSection):
    """Carte affichant la météo actuelle avec température, icône, chips et ruban historique.

    Implémente :class:`WeatherSection`. Conserve en mémoire les ``HISTORY_LEN``
    dernières mesures météo dans une file circulaire (``deque``) et les affiche
    sous forme de ruban de cellules en bas de la carte. Les cellules du ruban sont
    créées une seule fois lors du :meth:`build` puis mises à jour en place.

    Attribut de classe :
        HISTORY_LEN (int): Taille maximale de la file d'historique (7 par défaut).
    """

    HISTORY_LEN = 7

    def __init__(self) -> None:
        """Initialise les contrôles Flet internes et la file d'historique bornée.

        Tous les contrôles texte (température, description, chips) et l'icône
        sont créés ici avec des valeurs par défaut (``"--"``). Les cellules du
        ruban historique sont créées lors de :meth:`build`.

        Args:
            Aucun.

        Returns:
            None — :meth:`build` doit être appelé pour obtenir le contrôle Flet.
        """
        self.history: deque[Weather] = deque(maxlen=self.HISTORY_LEN)
        self._temp = ft.Text("--°C", size=32, weight=ft.FontWeight.BOLD, color=theme.TEXT)
        self._desc = ft.Text("En attente…", size=12, color=theme.MUTED)
        self._icon = ft.Icon(ft.Icons.WB_SUNNY, color="#F59E0B", size=30)
        self._chip_hum = ft.Text("--%", size=11, color=theme.MUTED)
        self._chip_wind = ft.Text("-- m/s", size=11, color=theme.MUTED)
        self._chip_feel = ft.Text("--°C ressenti", size=11, color=theme.MUTED)
        self._history_cells: list[ft.Container] = []

    def build(self) -> ft.Control:
        """Construit la carte météo complète avec en-tête principal et ruban d'historique.

        Crée les 7 cellules du ruban via :meth:`_build_history_row` et conserve
        leurs références pour les mises à jour ultérieures.

        Args:
            Aucun.

        Returns:
            ft.Control: Carte blanche contenant l'icône météo, la température principale,
                les chips (humidité, vent, ressenti) et le ruban des 7 dernières mesures.
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
                                border=ft.border.all(1, "#FFE082"),
                                alignment=ft.alignment.center,
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
                        "Historique récent (7 dernières mesures)",
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
        """Crée les 7 cellules vides du ruban historique et en conserve les références internes.

        Chaque cellule stocke ses sous-contrôles dans ``cell.data`` pour permettre
        les mises à jour en place sans reconstruire l'arbre.

        Args:
            Aucun.

        Returns:
            ft.Row: Ligne contenant les 7 cellules historiques initialisées à ``"—"`` / ``"--°"``.
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
                padding=ft.padding.symmetric(vertical=8, horizontal=4),
                border_radius=10,
                border=ft.border.all(1, theme.BORDER),
                expand=True,
            )
            cell.data = {"label": label, "icon": ico, "hi": hi}
            self._history_cells.append(cell)
            cells.append(cell)
        return ft.Row(cells, spacing=6)

    def update(self, w: Weather) -> None:
        """Met à jour la carte principale et ajoute la mesure à la file d'historique.

        Met à jour en place la température, la description, l'icône, les chips,
        puis rafraîchit le ruban d'historique via :meth:`_refresh_history`.

        Args:
            w (Weather): La nouvelle mesure météo à afficher. Ses champs ``temperature_c``,
                ``description``, ``condition``, ``humidity_pct``, ``wind_speed_ms``,
                ``wind_gust_ms``, ``feels_like_c`` et ``timestamp`` sont utilisés.

        Returns:
            None — les contrôles Flet sont modifiés en place.
        """
        self.history.append(w)
        self._temp.value = f"{w.temperature_c:.0f}°C"
        self._desc.value = f"{w.description.capitalize()} · {self._pretty_ts(w.timestamp)}"

        icon, token = icon_for_condition(w.condition)
        self._icon.name = UIComponents.icon_name(icon)
        self._icon.color = UIComponents.COLOR_TOKENS[token]

        self._chip_hum.value = f"{w.humidity_pct}%"
        gust = f" (raf. {w.wind_gust_ms:.0f})" if w.wind_gust_ms else ""
        self._chip_wind.value = f"{w.wind_speed_ms:.1f} m/s{gust}"
        self._chip_feel.value = f"{w.feels_like_c:.0f}°C ressenti"

        self._refresh_history()

    def _refresh_history(self) -> None:
        """Reflète l'état courant de la file d'historique dans les cellules du ruban.

        Parcourt les 7 cellules dans l'ordre d'insertion. Les cellules sans mesure
        correspondante (file pas encore pleine) sont réinitialisées aux valeurs vides.

        Args:
            Aucun.

        Returns:
            None — les cellules du ruban sont modifiées en place.
        """
        items = list(self.history)
        for i, cell in enumerate(self._history_cells):
            d = cell.data
            if i < len(items):
                w = items[i]
                d["label"].value = self._hour_or_dash(w.timestamp)
                ico_name, token = icon_for_condition(w.condition)
                d["icon"].name = UIComponents.icon_name(ico_name)
                d["icon"].color = UIComponents.COLOR_TOKENS[token]
                d["hi"].value = f"{w.temperature_c:.0f}°"
            else:
                d["label"].value = "—"
                d["hi"].value = "--°"

    @staticmethod
    def _pretty_ts(ts: str) -> str:
        """Formate un timestamp ISO en libellé lisible (ex. « Lundi 26 mai · 14:07 »).

        Args:
            ts (str): Timestamp au format ISO 8601 (ex. ``"2024-05-26T14:07:00Z"``).

        Returns:
            str: Libellé formaté et capitalisé, ou la chaîne d'origine si non parsable.
        """
        try:
            return (
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
                .strftime("%A %d %b · %H:%M")
                .capitalize()
            )
        except Exception:
            return ts

    @staticmethod
    def _hour_or_dash(ts: str) -> str:
        """Extrait l'heure au format ``HH:MM`` d'un timestamp ISO.

        Args:
            ts (str): Timestamp au format ISO 8601.

        Returns:
            str: Heure au format ``"HH:MM"`` (ex. ``"14:07"``),
                ou ``"—"`` si le timestamp n'est pas parsable.
        """
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%H:%M")
        except Exception:
            return "—"
