"""Composants Flet réutilisables (carte, badge, bannière d'alerte, etc.)."""

from __future__ import annotations

import flet as ft

import theme

# Mapping token couleur → couleur hex (utilisé par analytics → UI)
COLOR_TOKENS = {
    "green": theme.GREEN,
    "amber": theme.AMBER,
    "orange": theme.ORANGE,
    "red": theme.RED,
    "darkred": "#7f0000",
    "sun": "#F59E0B",
    "rain": theme.SKY_DARK,
    "snow": theme.SKY_DARK,
    "cloud": "#78909C",
    "storm": "#5C6BC0",
}


def icon_name(name: str) -> str:
    """Convertit un identifiant snake_case en attribut ``ft.Icons``.

    Permet à la couche métier de manipuler des chaînes neutres
    (« home_work ») sans importer Flet.
    """
    return getattr(ft.Icons, name.upper())


def section_label(text: str) -> ft.Text:
    """Petit libellé de section en capitales, style sous-titre discret."""
    return ft.Text(
        text.upper(),
        size=10,
        weight=ft.FontWeight.W_600,
        color=theme.MUTED,
        font_family="monospace",
    )


def card(content: ft.Control) -> ft.Container:
    """Wrappe un contrôle dans la carte blanche standard de l'app."""
    return ft.Container(
        content=content,
        bgcolor=theme.CARD,
        border_radius=18,
        padding=16,
        border=ft.border.all(1, theme.BORDER),
    )


class Badge:
    """Pastille colorée dont le texte et la couleur peuvent évoluer.

    Encapsule le ``Container`` Flet sous-jacent pour masquer la palette
    aux appelants : ils manipulent uniquement un ``kind`` sémantique
    (``ok``, ``warn``, ``danger``).
    """

    def __init__(self, text: str = "—", kind: str = "ok") -> None:
        """Construit le badge avec un libellé et un ``kind`` initiaux."""
        bg, fg = theme.BADGE_PALETTE[kind]
        self._label = ft.Text(text, size=10, weight=ft.FontWeight.W_500, color=fg)
        self.control = ft.Container(
            content=self._label,
            bgcolor=bg,
            padding=ft.padding.symmetric(horizontal=9, vertical=3),
            border_radius=20,
        )

    def update(self, text: str, kind: str) -> None:
        """Modifie le texte et la couleur en fonction d'un nouveau ``kind``."""
        bg, fg = theme.BADGE_PALETTE[kind]
        self._label.value = text
        self._label.color = fg
        self.control.bgcolor = bg


def alert_strip(icon: str, text: str, fg: str, bg: str, border_color: str) -> ft.Container:
    """Bandeau d'alerte horizontal (icône + texte) totalement paramétrable.

    Les helpers spécialisés (``cold_alert`` etc.) délèguent ici en
    fournissant simplement le triplet de couleurs adapté.
    """
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, color=fg, size=16),
                ft.Text(text, size=11, color=fg, weight=ft.FontWeight.W_500, expand=True),
            ],
            spacing=8,
        ),
        bgcolor=bg,
        border=ft.border.all(1, border_color),
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        border_radius=10,
    )


def cold_alert(icon: str, text: str) -> ft.Container:
    """Bandeau d'alerte « froid / abriter les animaux » (tons bleus)."""
    return alert_strip(icon, text, theme.SKY_DARK, theme.SKY_PALE, "#B3E5FC")


def sun_alert(icon: str, text: str) -> ft.Container:
    """Bandeau d'alerte « ensoleillement / ombre » (tons jaunes)."""
    return alert_strip(icon, text, "#E65100", "#FFF9C4", "#FFF176")


def warn_alert(icon: str, text: str) -> ft.Container:
    """Bandeau d'avertissement générique (tons ambre)."""
    return alert_strip(icon, text, "#B45309", theme.AMBER_PALE, "#FDE68A")


def danger_alert(icon: str, text: str) -> ft.Container:
    """Bandeau de danger (tons rouges) pour les alertes critiques."""
    return alert_strip(icon, text, theme.RED, theme.RED_PALE, "#FFCDD2")


def info_alert(icon: str, text: str) -> ft.Container:
    """Bandeau informatif sobre (tons ocres), p.ex. confirmation push."""
    return alert_strip(icon, text, "#92400E", "#FFF8E1", "#FFE082")


def stat_cell(value_ctrl: ft.Text, unit: str, label: str) -> ft.Container:
    """Cellule statistique « grosse valeur + unité + libellé » centrée.

    ``value_ctrl`` est passé tel quel pour qu'il puisse être mis à jour
    en place par la section qui le possède.
    """
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [value_ctrl, ft.Text(unit, size=10, color=theme.MUTED)],
                    spacing=2,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Text(label, size=9, color=theme.MUTED),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=theme.BG,
        padding=10,
        border_radius=10,
        expand=True,
    )


def nav_item(icon: str, label: str, active: bool) -> ft.Container:
    """Item de barre de navigation inférieure ; ``active`` colore en vert."""
    color = theme.GREEN if active else theme.MUTED
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icon, color=color, size=22),
                ft.Text(
                    label,
                    size=9,
                    color=color,
                    weight=ft.FontWeight.W_500 if active else ft.FontWeight.W_400,
                ),
            ],
            spacing=3,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
        alignment=ft.alignment.center,
    )
