"""Page de réglages : modification de la ville et du type d'élevage."""

from __future__ import annotations

from typing import Callable

import flet as ft

import theme
from i18n import t
from ui.base import Buildable
from ui.components import UIComponents
from ui.language_selector import LanguageSelector


class SettingsView(Buildable):
    """Page de réglages permettant à l'utilisateur de modifier sa ville et son profil.

    Implémente :class:`Buildable`. Affiche une carte avec un champ ville et un
    menu déroulant de profil. Déclenche le callback ``on_save`` lors de la validation.
    """

    def __init__(
        self,
        city: str,
        profile: str,
        on_save: Callable[[str, str], None],
        on_language_change: Callable[[], None] | None = None,
    ) -> None:
        """Prépare les contrôles du formulaire avec les valeurs actuelles.

        Args:
            city (str): Ville actuellement configurée, pré-remplie dans le champ texte.
            profile (str): Code du profil actuellement configuré, pré-sélectionné
                dans le menu (ex. ``"dairy"``).
            on_save (Callable[[str, str], None]): Callback appelé avec ``(city, profile)``
                lors de la validation. L'appelant est responsable de propager le changement.
            on_language_change (Callable[[], None] | None): Callback appelé après
                un changement de langue, pour reconstruire l'écran traduit.

        Returns:
            None — :meth:`build` doit être appelé pour obtenir le contrôle Flet.
        """
        self._on_save = on_save
        self._language = LanguageSelector(on_language_change or (lambda: None))
        self._city = ft.TextField(
            label=t("settings_view", "city_label"),
            value=city,
            border_color=theme.GREEN,
            focused_border_color=theme.GREEN,
        )
        self._profile = ft.Dropdown(
            label=t("settings_view", "profile_label"),
            options=[
                ft.dropdown.Option(key="dairy", text=t("common", "profile_dairy")),
                ft.dropdown.Option(key="meat", text=t("common", "profile_meat")),
                ft.dropdown.Option(key="poultry", text=t("common", "profile_poultry")),
                ft.dropdown.Option(key="crops", text=t("common", "profile_crops")),
            ],
            value=profile,
            border_color=theme.GREEN,
        )
        self._feedback = ft.Text("", size=12)

    def build(self) -> ft.Control:
        """Construit la page de réglages avec la carte de formulaire.

        Args:
            Aucun.

        Returns:
            ft.Control: ``Column`` contenant le label de section et la carte de formulaire,
                dans la même charte graphique que les autres sections du dashboard.
        """
        return ft.Column(
            [
                UIComponents.section_label(t("settings_view", "section_label")),
                UIComponents.card(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.LANGUAGE, color=theme.GREEN, size=18),
                                    ft.Text(
                                        t("settings_view", "language_title"),
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=theme.TEXT,
                                    ),
                                ],
                                spacing=8,
                            ),
                            self._language.build(),
                        ],
                        spacing=12,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                    )
                ),
                UIComponents.card(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.LOCATION_CITY, color=theme.GREEN, size=18),
                                    ft.Text(
                                        t("settings_view", "localisation_title"),
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=theme.TEXT,
                                    ),
                                ],
                                spacing=8,
                            ),
                            self._city,
                            ft.Container(height=4),
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.AGRICULTURE, color=theme.GREEN, size=18),
                                    ft.Text(
                                        t("settings_view", "farming_type_title"),
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=theme.TEXT,
                                    ),
                                ],
                                spacing=8,
                            ),
                            self._profile,
                            self._feedback,
                            ft.Container(height=4),
                            ft.Button(
                                t("settings_view", "save_button"),
                                icon=ft.Icons.SAVE,
                                on_click=lambda e: self._save(),
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
            spacing=10,
        )

    def _save(self) -> None:
        """Valide la saisie et déclenche le callback ``on_save``.

        Affiche un message d'erreur si la ville est vide, sinon appelle
        ``on_save`` avec les valeurs saisies et affiche une confirmation.

        Returns:
            None
        """
        city = (self._city.value or "").strip()
        if not city:
            self._feedback.value = t("settings_view", "empty_city_error")
            self._feedback.color = theme.RED
            self._feedback.update()
            return
        self._feedback.value = t("settings_view", "saved_confirm")
        self._feedback.color = theme.GREEN
        self._feedback.update()
        self._on_save(city, self._profile.value or "crops")
