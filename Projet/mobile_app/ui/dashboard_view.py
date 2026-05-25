"""Vue dashboard : header + 4 sections (météo, THI, confort, traitement)."""

from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Iterable

import flet as ft

import theme
from analytics import (
    PastureAlert,
    ThiResult,
    TreatmentSlot,
    icon_for_condition,
    pasture_alerts,
    thi_result,
    treatment_slots,
)
from models import Weather
from ui.components import (
    Badge,
    card,
    cold_alert,
    danger_alert,
    icon_name,
    info_alert,
    nav_item,
    section_label,
    stat_cell,
    sun_alert,
    warn_alert,
)
from ui.components import COLOR_TOKENS


# ----- Header -----

class HeaderSection:
    """Bandeau vert du haut : ville, profil et statut de connexion Kafka."""

    def __init__(self, city: str, profile: str, topic: str) -> None:
        """Mémorise les libellés ; prépare le ``Text`` de statut modifiable."""
        self.city = city
        self.profile = profile
        self.topic = topic
        self._status = ft.Text(
            f"Connexion au topic « {topic} »…",
            size=11, color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        )

    def build(self) -> ft.Control:
        """Construit l'arbre Flet du header (à insérer en haut du dashboard)."""
        return ft.Container(
            bgcolor=theme.GREEN,
            padding=ft.padding.only(left=20, right=20, top=20, bottom=20),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE), size=18),
                                    ft.Column(
                                        [
                                            ft.Text(self.city, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                            ft.Text(self.profile, size=12, color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE)),
                                        ],
                                        spacing=1,
                                    ),
                                ],
                                spacing=8,
                            ),
                            ft.Container(
                                ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE),
                                width=36, height=36, border_radius=18,
                                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                                alignment=ft.alignment.center,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        [
                            ft.Container(width=6, height=6, border_radius=3, bgcolor=theme.GREEN_LIGHT),
                            self._status,
                        ],
                        spacing=6,
                    ),
                ],
                spacing=12,
            ),
        )

    def set_status(self, text: str) -> None:
        """Met à jour le texte de statut (« Flux actif », erreur, …)."""
        self._status.value = text


# ----- Section météo actuelle -----

class CurrentWeatherSection:
    """Carte « Météo actuelle » avec température, icône, chips et historique.

    Conserve en mémoire les ``HISTORY_LEN`` dernières mesures et les
    affiche sous forme de ruban en bas de la carte.
    """

    HISTORY_LEN = 7

    def __init__(self) -> None:
        """Initialise les contrôles et la file d'historique bornée."""
        self.history: deque[Weather] = deque(maxlen=self.HISTORY_LEN)

        self._temp = ft.Text("--°C", size=32, weight=ft.FontWeight.BOLD, color=theme.TEXT)
        self._desc = ft.Text("En attente…", size=12, color=theme.MUTED)
        self._icon = ft.Icon(ft.Icons.WB_SUNNY, color="#F59E0B", size=30)
        self._chip_hum = ft.Text("--%", size=11, color=theme.MUTED)
        self._chip_wind = ft.Text("-- m/s", size=11, color=theme.MUTED)
        self._chip_feel = ft.Text("--°C ressenti", size=11, color=theme.MUTED)
        self._history_cells: list[ft.Container] = []

    def build(self) -> ft.Control:
        """Construit la carte météo (en-tête principal + ruban historique)."""
        history_row = self._build_history_row()
        return card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                self._icon,
                                width=56, height=56, border_radius=14,
                                bgcolor="#FFF8E1", border=ft.border.all(1, "#FFE082"),
                                alignment=ft.alignment.center,
                            ),
                            ft.Column(
                                [
                                    self._temp,
                                    self._desc,
                                    ft.Row(
                                        [
                                            ft.Row([ft.Icon(ft.Icons.WATER_DROP, size=13, color=theme.MUTED), self._chip_hum], spacing=3),
                                            ft.Row([ft.Icon(ft.Icons.AIR, size=13, color=theme.MUTED), self._chip_wind], spacing=3),
                                            ft.Row([ft.Icon(ft.Icons.REMOVE_RED_EYE, size=13, color=theme.MUTED), self._chip_feel], spacing=3),
                                        ],
                                        spacing=10, wrap=True,
                                    ),
                                ],
                                spacing=3, expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=20, color=theme.BORDER),
                    ft.Text("Historique récent (7 dernières mesures)", size=10, color=theme.MUTED, weight=ft.FontWeight.W_500),
                    history_row,
                ],
                spacing=8,
            )
        )

    def _build_history_row(self) -> ft.Row:
        """Crée 7 cellules vides et conserve une référence pour les MAJ."""
        cells = []
        for _ in range(self.HISTORY_LEN):
            label = ft.Text("—", size=9, color=theme.MUTED, weight=ft.FontWeight.W_500)
            ico = ft.Icon(ft.Icons.WB_SUNNY, color="#F59E0B", size=18)
            hi = ft.Text("--°", size=13, weight=ft.FontWeight.W_600)
            cell = ft.Container(
                content=ft.Column([label, ico, hi], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=theme.BG, padding=ft.padding.symmetric(vertical=8, horizontal=4),
                border_radius=10, border=ft.border.all(1, theme.BORDER), expand=True,
            )
            cell.data = {"label": label, "icon": ico, "hi": hi}
            self._history_cells.append(cell)
            cells.append(cell)
        return ft.Row(cells, spacing=6)

    def update(self, w: Weather) -> None:
        """Met à jour la carte avec une nouvelle mesure et l'ajoute à l'historique."""
        self.history.append(w)
        self._temp.value = f"{w.temperature_c:.0f}°C"
        self._desc.value = f"{w.description.capitalize()} · {_pretty_ts(w.timestamp)}"

        icon, token = icon_for_condition(w.condition)
        self._icon.name = icon_name(icon)
        self._icon.color = COLOR_TOKENS[token]

        self._chip_hum.value = f"{w.humidity_pct}%"
        gust = f" (raf. {w.wind_gust_ms:.0f})" if w.wind_gust_ms else ""
        self._chip_wind.value = f"{w.wind_speed_ms:.1f} m/s{gust}"
        self._chip_feel.value = f"{w.feels_like_c:.0f}°C ressenti"

        self._refresh_history()

    def _refresh_history(self) -> None:
        """Reflète la file d'historique courante dans les cellules du ruban."""
        items = list(self.history)
        for i, cell in enumerate(self._history_cells):
            d = cell.data
            if i < len(items):
                w = items[i]
                d["label"].value = _hour_or_dash(w.timestamp)
                ico_name, token = icon_for_condition(w.condition)
                d["icon"].name = icon_name(ico_name)
                d["icon"].color = COLOR_TOKENS[token]
                d["hi"].value = f"{w.temperature_c:.0f}°"
            else:
                d["label"].value = "—"
                d["hi"].value = "--°"


# ----- Section THI -----

class ThiSection:
    """Carte « Stress thermique » : jauge THI, zone, description, alertes."""

    def __init__(self) -> None:
        """Prépare la jauge, les libellés et la zone d'alerte (initialement masquée)."""
        self.badge = Badge("—", "ok")
        self._value = ft.Text("--", size=22, weight=ft.FontWeight.BOLD, color=theme.RED)
        self._ring = ft.ProgressRing(value=0, width=90, height=90, color=theme.RED, bgcolor="#F5E9E9", stroke_width=8)
        self._status = ft.Text("—", size=15, weight=ft.FontWeight.BOLD, color=theme.RED)
        self._desc = ft.Text("En attente de données.", size=11, color=theme.MUTED)
        self._alert_zone = ft.Container(visible=False)

    def build(self) -> ft.Control:
        """Construit la carte THI complète (jauge circulaire + barème + alertes)."""
        return card(
            ft.Column(
                [
                    ft.Row(
                        [ft.Text("Indice THI Bétail", size=13, weight=ft.FontWeight.W_600), self.badge.control],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        [
                            ft.Stack(
                                [
                                    self._ring,
                                    ft.Container(
                                        content=ft.Column(
                                            [self._value, ft.Text("THI", size=9, color=theme.MUTED)],
                                            spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        ),
                                        width=90, height=90, alignment=ft.alignment.center,
                                    ),
                                ],
                                width=90, height=90,
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
                                            ft.Text("Normal", size=9, color=theme.MUTED),
                                            ft.Text("Alerte", size=9, color=theme.MUTED),
                                            ft.Text("Danger", size=9, color=theme.MUTED),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),
                                ],
                                spacing=6, expand=True,
                            ),
                        ],
                        spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._alert_zone,
                ],
                spacing=12,
            )
        )

    def update(self, w: Weather) -> None:
        """Recalcule le THI, met la jauge à jour et affiche l'alerte si danger."""
        result: ThiResult = thi_result(w.temperature_c, w.humidity_pct)
        color = COLOR_TOKENS[result.color_token]

        self._value.value = f"{result.value:.0f}"
        self._value.color = color
        self._ring.color = color
        self._ring.value = max(0.0, min(1.0, (result.value - 50) / 40))
        self._status.value = result.label
        self._status.color = color
        self._desc.value = result.description
        self.badge.update(result.label.split()[-1].upper(), result.kind)

        if result.kind == "danger":
            self._alert_zone.content = ft.Column(
                [
                    danger_alert(
                        ft.Icons.WARNING_AMBER,
                        f"Pic de chaleur détecté · ventilation des bâtiments recommandée (THI {result.value:.0f})",
                    ),
                    info_alert(
                        ft.Icons.NOTIFICATIONS_ACTIVE,
                        "Notification envoyée aux éleveurs · seuil danger franchi",
                    ),
                ],
                spacing=6,
            )
            self._alert_zone.visible = True
        else:
            self._alert_zone.visible = False


# ----- Section confort au pré -----

class PastureSection:
    """Carte « Ressenti & Pâturage » : 4 indicateurs + alertes confort animal."""

    def __init__(self) -> None:
        """Prépare la grille de statistiques et les bandeaux d'alerte cachés."""
        self.badge = Badge("—", "ok")
        self._temp = ft.Text("--", size=18, weight=ft.FontWeight.BOLD)
        self._feels = ft.Text("--", size=18, weight=ft.FontWeight.BOLD, color=theme.SKY_DARK)
        self._wind = ft.Text("--", size=18, weight=ft.FontWeight.BOLD)
        self._clouds = ft.Text("--", size=18, weight=ft.FontWeight.BOLD)
        self._feels_row = ft.Container(visible=False)
        self._alerts = ft.Column([], spacing=6)

    def build(self) -> ft.Control:
        """Construit la carte (titre + 4 cellules + ligne ressenti + alertes)."""
        return card(
            ft.Column(
                [
                    ft.Row(
                        [ft.Text("Ressenti & Pâturage", size=13, weight=ft.FontWeight.W_600), self.badge.control],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row([stat_cell(self._temp, "°C", "Température réelle"), stat_cell(self._feels, "°C", "Ressenti")], spacing=8),
                    ft.Row([stat_cell(self._wind, "m/s", "Vent"), stat_cell(self._clouds, "%", "Nuages")], spacing=8),
                    self._feels_row,
                    self._alerts,
                ],
                spacing=10,
            )
        )

    def update(self, w: Weather) -> None:
        """Met à jour les 4 indicateurs, la ligne ressenti et les alertes."""
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
                            ft.Text(f"Vent {wind_word} → ressenti {feels_diff:+.0f}°C", size=12, weight=ft.FontWeight.W_600),
                            ft.Text("Impact sur le confort animal", size=10, color=theme.MUTED),
                        ],
                        spacing=1, expand=True,
                    ),
                    ft.Text(f"{feels_diff:+.0f}°", size=16, weight=ft.FontWeight.BOLD, color=theme.SKY_DARK),
                ],
                spacing=8,
            )
            self._feels_row.bgcolor = theme.SOIL_PALE
            self._feels_row.padding = 8
            self._feels_row.border_radius = 10
            self._feels_row.visible = True
        else:
            self._feels_row.visible = False

        self._alerts.controls = list(_render_pasture_alerts(pasture_alerts(w)))
        if not self._alerts.controls:
            self.badge.update("OK", "ok")
        else:
            self.badge.update("VIGILANCE", "warn")


def _render_pasture_alerts(alerts: Iterable[PastureAlert]) -> Iterable[ft.Control]:
    """Transforme une liste d'alertes métier en contrôles Flet colorés."""
    for a in alerts:
        icon = icon_name(a.icon)
        if a.kind == "cold":
            yield cold_alert(icon, a.message)
        elif a.kind == "sun":
            yield sun_alert(icon, a.message)
        else:
            yield warn_alert(icon, a.message)


# ----- Section pulvérisation -----

class TreatmentSection:
    """Carte « Pulvérisation & Traitement » : créneaux horaires + légende."""

    def __init__(self) -> None:
        """Initialise le conteneur de créneaux (vide) et le badge récap."""
        self.badge = Badge("—", "ok")
        self._slots = ft.Column([], spacing=6)

    def build(self) -> ft.Control:
        """Construit la carte (en-tête, liste de créneaux, légende des points)."""
        return card(
            ft.Column(
                [
                    ft.Row(
                        [ft.Text("Pulvérisation & Traitement", size=13, weight=ft.FontWeight.W_600), self.badge.control],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self._slots,
                    ft.Row(
                        [
                            ft.Row([ft.Container(width=8, height=8, bgcolor=theme.GREEN_LIGHT, border_radius=4), ft.Text("Optimal", size=10, color=theme.MUTED)], spacing=4),
                            ft.Row([ft.Container(width=8, height=8, bgcolor=theme.AMBER, border_radius=4), ft.Text("Risqué", size=10, color=theme.MUTED)], spacing=4),
                            ft.Row([ft.Container(width=8, height=8, bgcolor=theme.RED, border_radius=4), ft.Text("Déconseillé", size=10, color=theme.MUTED)], spacing=4),
                        ],
                        spacing=14,
                    ),
                ],
                spacing=10,
            )
        )

    def update(self, w: Weather) -> None:
        """Recalcule les créneaux et rafraîchit le badge « X CRÉNEAU OK »."""
        slots = treatment_slots(w)
        self._slots.controls = [self._render_slot(s) for s in slots]
        ok_count = sum(1 for s in slots if s.status == "ok")
        if ok_count:
            self.badge.update(f"{ok_count} CRÉNEAU OK", "ok")
        else:
            self.badge.update("AUCUN", "danger")

    @staticmethod
    def _render_slot(s: TreatmentSlot) -> ft.Container:
        """Construit la ligne visuelle d'un créneau (label + chiffres + pastille)."""
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
                            ft.Row([ft.Icon(ft.Icons.AIR, size=13, color=theme.MUTED), ft.Text(f"{s.wind:.1f} m/s", size=10, color=theme.MUTED)], spacing=3),
                            ft.Row([ft.Icon(ft.Icons.WATER_DROP, size=13, color=theme.MUTED), ft.Text(f"{s.rain:.1f} mm", size=10, color=theme.MUTED)], spacing=3),
                            ft.Row([ft.Icon(ft.Icons.THERMOSTAT, size=13, color=theme.MUTED), ft.Text(f"{s.temp:.0f}°C", size=10, color=theme.MUTED)], spacing=3),
                        ],
                        spacing=8, expand=True,
                    ),
                    ft.Container(width=8, height=8, bgcolor=dot, border_radius=4),
                ],
                spacing=10,
            ),
            bgcolor=bg, border=ft.border.all(1, border),
            padding=ft.padding.symmetric(horizontal=11, vertical=9),
            border_radius=10,
        )


# ----- Bottom nav -----

def build_bottom_nav() -> ft.Control:
    """Construit la barre de navigation inférieure (4 onglets, Tableau actif)."""
    return ft.Container(
        bgcolor=theme.CARD,
        border=ft.border.only(top=ft.border.BorderSide(1, theme.BORDER)),
        padding=ft.padding.only(top=10, bottom=22),
        content=ft.Row(
            [
                nav_item(ft.Icons.DASHBOARD, "Tableau", True),
                nav_item(ft.Icons.SHOW_CHART, "Historique", False),
                nav_item(ft.Icons.NOTIFICATIONS, "Alertes", False),
                nav_item(ft.Icons.SETTINGS, "Réglages", False),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
    )


# ----- Vue orchestrateur -----

class DashboardView:
    """Orchestrateur de la vue dashboard : agrège header + 4 sections + nav.

    Expose deux opérations à l'application : :meth:`build` pour générer
    l'arbre Flet initial et :meth:`update_weather` pour diffuser une
    nouvelle mesure à toutes les sections enfants.
    """

    def __init__(self, city: str, profile: str, topic: str) -> None:
        """Instancie chaque sous-section dans l'ordre d'affichage."""
        self.header = HeaderSection(city, profile, topic)
        self.current = CurrentWeatherSection()
        self.thi = ThiSection()
        self.pasture = PastureSection()
        self.treatment = TreatmentSection()

    def build(self) -> ft.Control:
        """Assemble header + corps scrollable + navigation inférieure."""
        body = ft.Container(
            bgcolor=theme.BG,
            padding=16,
            content=ft.Column(
                [
                    section_label("Météo actuelle"),
                    self.current.build(),
                    section_label("Stress thermique"),
                    self.thi.build(),
                    section_label("Confort au pré"),
                    self.pasture.build(),
                    section_label("Fenêtre de traitement"),
                    self.treatment.build(),
                    ft.Container(height=8),
                ],
                spacing=10,
            ),
        )
        return ft.Column([self.header.build(), body, build_bottom_nav()], spacing=0, expand=True)

    def update_weather(self, w: Weather) -> None:
        """Propage la nouvelle mesure à chacune des quatre sections enfants."""
        self.current.update(w)
        self.thi.update(w)
        self.pasture.update(w)
        self.treatment.update(w)

    def set_status(self, text: str) -> None:
        """Relaie un message de statut au header (« Flux actif », erreurs…)."""
        self.header.set_status(text)


# ----- helpers locaux -----

def _pretty_ts(ts: str) -> str:
    """Formate un timestamp ISO en libellé lisible (« Lundi 26 mai · 14:07 »).

    Renvoie la chaîne d'origine si elle n'est pas parsable.
    """
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%A %d %b · %H:%M").capitalize()
    except Exception:
        return ts


def _hour_or_dash(ts: str) -> str:
    """Extrait ``HH:MM`` d'un timestamp ISO ; renvoie ``—`` en cas d'échec."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%H:%M")
    except Exception:
        return "—"
