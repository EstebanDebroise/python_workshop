"""Settings page: modify city and livestock type."""

from __future__ import annotations

from typing import Callable

import flet as ft

import theme
from i18n import t
from ui.base import Buildable
from ui.components import UIComponents
from ui.language_selector import LanguageSelector


class SettingsView(Buildable):
    """Settings page allowing the user to modify city and profile.

    Implements :class:`Buildable`. Displays a card with a city text field and a
    profile dropdown menu. Triggers the ``on_save`` callback when validated.
    """

    def __init__(
        self,
        city: str,
        profile: str,
        on_save: Callable[[str, str], None],
        on_language_change: Callable[[], None] | None = None,
    ) -> None:
        """Prepare form controls with current values.

        Args:
            city (str): Currently configured city, pre-filled in the text field.
            profile (str): Code of the currently configured profile, pre-selected
                in the menu (e.g. ``"dairy"``).
            on_save (Callable[[str, str], None]): Callback called with ``(city, profile)``
                when validation is done. The caller is responsible for propagating the change.
            on_language_change (Callable[[], None] | None): Callback called after
                a language change, to rebuild the translated screen.

        Returns:
            None — :meth:`build` must be called to get the Flet control.
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
        """Build the settings page with the form card.

        Args:
            None.

        Returns:
            ft.Control: ``Column`` containing the section label and form card,
                following the same design as other dashboard sections.
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
        """Validate input and trigger the ``on_save`` callback.

        Displays an error message if the city is empty, otherwise calls
        ``on_save`` with the entered values and displays a confirmation.

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
