"""Écran de saisie initial : ville + profil utilisateur."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import flet as ft

import theme
from ui.components import card


@dataclass
class SetupResult:
    """Données collectées par l'écran de configuration."""

    city: str
    profile: str


class SetupView:
    """Vue de configuration initiale de l'application.

    Affiche un formulaire centré (ville + profil) et déclenche le
    callback ``on_submit`` avec un :class:`SetupResult` quand l'utilisateur
    valide. La vue est passive : elle ne gère pas Kafka ni la navigation,
    elle se contente de remonter la saisie à l'orchestrateur.
    """

    def __init__(self, on_submit: Callable[[SetupResult], None]) -> None:
        """Prépare les contrôles ; ne les attache pas encore à la page."""
        self.on_submit = on_submit
        self._city = ft.TextField(
            label="Ville",
            hint_text="ex. Limoges",
            autofocus=True,
            on_submit=lambda e: self._submit(),
            border_color=theme.GREEN,
            focused_border_color=theme.GREEN,
        )
        self._profile = ft.Dropdown(
            label="Profil",
            options=[
                ft.dropdown.Option("Éleveur laitier"),
                ft.dropdown.Option("Éleveur viande"),
                ft.dropdown.Option("Aviculteur"),
                ft.dropdown.Option("Agriculteur"),
            ],
            value="Éleveur laitier",
            border_color=theme.GREEN,
        )
        self._error = ft.Text("", color=theme.RED, size=12)

    def build(self) -> ft.Control:
        """Construit et renvoie l'arbre Flet de la vue (à ajouter à la page)."""
        return ft.Container(
            expand=True,
            bgcolor=theme.BG,
            padding=24,
            content=ft.Column(
                [
                    ft.Container(height=60),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.AGRICULTURE, color=theme.GREEN, size=36),
                            ft.Text("Météo Agri", size=28, weight=ft.FontWeight.BOLD, color=theme.GREEN),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    ft.Text(
                        "Tableau de bord météo dédié aux agriculteurs et éleveurs",
                        size=13, color=theme.MUTED, text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    card(
                        ft.Column(
                            [
                                ft.Text("Configuration", size=14, weight=ft.FontWeight.W_600),
                                ft.Text(
                                    "Le topic Kafka utilisé portera le nom de la ville.",
                                    size=11, color=theme.MUTED,
                                ),
                                ft.Container(height=4),
                                self._city,
                                self._profile,
                                self._error,
                                ft.Container(height=4),
                                ft.ElevatedButton(
                                    "Démarrer",
                                    icon=ft.Icons.PLAY_ARROW,
                                    on_click=lambda e: self._submit(),
                                    bgcolor=theme.GREEN,
                                    color=ft.Colors.WHITE,
                                    width=200,
                                    height=44,
                                ),
                            ],
                            spacing=12,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _submit(self) -> None:
        """Valide la saisie puis transmet le résultat via ``on_submit``.

        Affiche une erreur en place si le champ ville est vide ; sinon
        n'effectue aucun nettoyage particulier (la normalisation du
        nom de topic est faite par l'appelant).
        """
        city = (self._city.value or "").strip()
        if not city:
            self._error.value = "Saisissez le nom de votre ville."
            self._error.update()
            return
        self.on_submit(SetupResult(city=city, profile=self._profile.value or "Agriculteur"))
