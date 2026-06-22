"""Écran de configuration initiale : saisie de la ville et du profil utilisateur."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import flet as ft

import theme
from i18n import t
from ui.base import Buildable
from ui.components import UIComponents
from ui.language_selector import LanguageSelector


@dataclass
class SetupResult:
    """Données collectées par l'écran de configuration et transmises à l'orchestrateur.

    Attributs :
        city (str): Nom de la ville saisi par l'utilisateur, non normalisé.
            La normalisation en topic Kafka est effectuée par l'appelant.
        profile (str): Profil utilisateur sélectionné dans le menu déroulant
            (ex. ``"Éleveur laitier"``, ``"Agriculteur"``).
    """

    city: str
    profile: str


class SetupView(Buildable):
    """Vue de configuration initiale de l'application.

    Implémente :class:`Buildable`. Affiche un formulaire centré composé d'un
    champ texte pour la ville et d'un menu déroulant pour le profil. Déclenche
    le callback ``on_submit`` avec un :class:`SetupResult` lors de la validation.

    La vue est passive : elle ne gère ni Kafka ni la navigation entre écrans.
    Elle se contente de valider la saisie minimale (ville non vide) et de
    remonter les données à l'orchestrateur (:class:`WeatherApp`).
    """

    def __init__(
        self,
        on_submit: Callable[[SetupResult], None],
        on_language_change: Callable[[], None] | None = None,
    ) -> None:
        """Prépare les contrôles du formulaire sans les attacher à la page.

        Args:
            on_submit (Callable[[SetupResult], None]): Callback appelé lors de la
                validation du formulaire. Reçoit un :class:`SetupResult` contenant
                la ville et le profil saisis. L'appelant est responsable de la
                transition vers le dashboard.
            on_language_change (Callable[[], None] | None): Callback appelé après
                un changement de langue, pour que l'orchestrateur reconstruise
                l'écran dans la nouvelle langue.

        Returns:
            None — :meth:`build` doit être appelé pour obtenir le contrôle Flet.
        """
        self.on_submit = on_submit
        self._language = LanguageSelector(on_language_change or (lambda: None), compact=True)
        self._city = ft.TextField(
            label=t("setup_view", "city_label"),
            hint_text=t("setup_view", "city_hint"),
            autofocus=True,
            on_submit=lambda e: self._submit(),
            border_color=theme.GREEN,
            focused_border_color=theme.GREEN,
        )
        self._profile = ft.Dropdown(
            label=t("setup_view", "profile_label"),
            options=[
                ft.dropdown.Option(key="dairy", text=t("common", "profile_dairy")),
                ft.dropdown.Option(key="meat", text=t("common", "profile_meat")),
                ft.dropdown.Option(key="poultry", text=t("common", "profile_poultry")),
                ft.dropdown.Option(key="crops", text=t("common", "profile_crops")),
            ],
            value="dairy",
            border_color=theme.GREEN,
        )
        self._error = ft.Text("", color=theme.RED, size=12)

    def build(self) -> ft.Control:
        """Construit l'arbre Flet complet de l'écran de configuration.

        Produit une page centrée avec le logo, le sous-titre de l'application
        et la carte de formulaire (ville + profil + bouton Démarrer).

        Args:
            Aucun.

        Returns:
            ft.Control: ``Container`` expansif avec fond gris (``theme.BG``),
                centré horizontalement, contenant le logo et le formulaire de saisie.
        """
        return ft.Container(
            expand=True,
            bgcolor=theme.BG,
            padding=24,
            content=ft.Column(
                [
                    ft.Row(
                        [self._language.build()],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Container(height=20),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.AGRICULTURE, color=theme.GREEN, size=36),
                            ft.Text(
                                "Météo Agri",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=theme.GREEN,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    ft.Text(
                        t("setup_view", "subtitle"),
                        size=13,
                        color=theme.MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    UIComponents.card(
                        ft.Column(
                            [
                                ft.Text(t("setup_view", "config_title"), size=14, weight=ft.FontWeight.W_600),
                                ft.Text(
                                    t("setup_view", "config_note"),
                                    size=11,
                                    color=theme.MUTED,
                                ),
                                ft.Container(height=4),
                                self._city,
                                self._profile,
                                self._error,
                                ft.Container(height=4),
                                ft.Button(
                                    t("setup_view", "start_button"),
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
        """Valide la saisie et transmet le résultat via le callback ``on_submit``.

        Vérifie que le champ ville n'est pas vide. En cas d'erreur, affiche un
        message en place et interrompt la soumission. En cas de succès, appelle
        ``on_submit`` avec le :class:`SetupResult` construit à partir des valeurs
        saisies. Le profil par défaut est ``"Agriculteur"`` si rien n'est sélectionné.

        Args:
            Aucun.

        Returns:
            None — appelle ``on_submit`` en cas de succès, met à jour ``_error`` sinon.
        """
        city = (self._city.value or "").strip()
        if not city:
            self._error.value = t("setup_view", "empty_city_error")
            self._error.update()
            return
        self.on_submit(SetupResult(city=city, profile=self._profile.value or "crops"))
