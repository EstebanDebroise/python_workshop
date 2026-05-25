"""Section pulvérisation et traitement : créneaux horaires évalués et légende."""

from __future__ import annotations

import flet as ft

import theme
from mobile_app.logic.treatment_analyzer import TreatmentAnalyzer
from mobile_app.logic.treatment_slot import TreatmentSlot
from models import Weather
from ui.badge import Badge
from ui.base import WeatherSection
from ui.components import UIComponents


class TreatmentSection(WeatherSection):
    """Carte de pulvérisation affichant 3 créneaux horaires évalués et leur légende.

    Implémente :class:`WeatherSection`. Les créneaux (−2h / maintenant / +3h)
    sont recalculés à chaque nouvelle mesure via :func:`analytics.treatment_slots`.
    Chaque créneau est affiché avec un code couleur (optimal / risqué / déconseillé).
    Le badge récapitule le nombre de créneaux jugés optimaux.
    """

    def __init__(self) -> None:
        """Initialise la colonne de créneaux vide et le badge récapitulatif.

        Args:
            Aucun.

        Returns:
            None — :meth:`build` doit être appelé pour obtenir le contrôle Flet.
        """
        self.badge = Badge("—", "ok")
        self._slots = ft.Column([], spacing=6)

    def build(self) -> ft.Control:
        """Construit la carte avec titre, liste de créneaux dynamique et légende des couleurs.

        La colonne ``_slots`` est insérée vide ; elle sera remplie par :meth:`update`.
        La légende (Optimal / Risqué / Déconseillé) est statique.

        Args:
            Aucun.

        Returns:
            ft.Control: Carte blanche avec le titre, la liste des créneaux et la légende.
        """
        return UIComponents.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "Pulvérisation & Traitement",
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
                                    ft.Text("Optimal", size=10, color=theme.MUTED),
                                ],
                                spacing=4,
                            ),
                            ft.Row(
                                [
                                    ft.Container(width=8, height=8, bgcolor=theme.AMBER, border_radius=4),
                                    ft.Text("Risqué", size=10, color=theme.MUTED),
                                ],
                                spacing=4,
                            ),
                            ft.Row(
                                [
                                    ft.Container(width=8, height=8, bgcolor=theme.RED, border_radius=4),
                                    ft.Text("Déconseillé", size=10, color=theme.MUTED),
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
        """Recalcule les 3 créneaux de pulvérisation et met à jour le badge récapitulatif.

        Délègue le calcul à :func:`analytics.treatment_slots` puis reconstruit
        la liste des lignes visuelles via :meth:`_render_slot`. Le badge affiche
        le nombre de créneaux optimaux ou « AUCUN » si aucun n'est disponible.

        Args:
            w (Weather): La nouvelle mesure météo servant de base au calcul.
                Les champs ``wind_speed_ms``, ``rain_1h_mm`` et ``temperature_c``
                sont utilisés pour évaluer chaque créneau.

        Returns:
            None — les contrôles Flet sont modifiés en place.
        """
        slots = TreatmentAnalyzer.slots(w)
        self._slots.controls = [self._render_slot(s) for s in slots]
        ok_count = sum(1 for s in slots if s.status == "ok")
        if ok_count:
            self.badge.update(f"{ok_count} CRÉNEAU OK", "ok")
        else:
            self.badge.update("AUCUN", "danger")

    @staticmethod
    def _render_slot(s: TreatmentSlot) -> ft.Container:
        """Construit la ligne visuelle d'un créneau avec son code couleur.

        Le fond, la bordure et la pastille sont déterminés par le statut du créneau :
        ``"ok"`` → vert, ``"warn"`` → ambre, ``"no"`` → rouge.

        Args:
            s (TreatmentSlot): Créneau horaire avec ses attributs : ``label`` (plage horaire),
                ``wind`` (m/s), ``rain`` (mm), ``temp`` (°C) et ``status`` (ok/warn/no).

        Returns:
            ft.Container: Ligne stylisée contenant le label horaire, les indicateurs
                météo (vent, pluie, température) et la pastille de statut.
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
            border=ft.border.all(1, border),
            padding=ft.padding.symmetric(horizontal=11, vertical=9),
            border_radius=10,
        )
