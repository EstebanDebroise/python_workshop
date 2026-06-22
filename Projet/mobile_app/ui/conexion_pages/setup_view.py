"""Initial setup screen: enter city and user profile."""

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
    """Data collected by the setup screen and transmitted to the orchestrator.

    Attributes:
        city (str): City name entered by the user, not normalized.
            Normalization to Kafka topic is performed by the caller.
        profile (str): User profile selected from the dropdown menu
            (e.g. ``"Dairy Farmer"``, ``"Crop Farmer"``).
    """

    city: str
    profile: str


class SetupView(Buildable):
    """Initial application setup view.

    Implements :class:`Buildable`. Displays a centered form with a text field
    for the city and a dropdown menu for the profile. Triggers the ``on_submit``
    callback with a :class:`SetupResult` when validated.

    The view is passive: it handles neither Kafka nor navigation between screens.
    It simply validates minimal input (non-empty city) and passes the data to
    the orchestrator (:class:`WeatherApp`).
    """

    def __init__(
        self,
        on_submit: Callable[[SetupResult], None],
        on_language_change: Callable[[], None] | None = None,
    ) -> None:
        """Prepare form controls without attaching them to the page.

        Args:
            on_submit (Callable[[SetupResult], None]): Callback called when the form
                is validated. Receives a :class:`SetupResult` containing the entered
                city and profile. The caller is responsible for transitioning to the
                dashboard.
            on_language_change (Callable[[], None] | None): Callback called after
                a language change, so the orchestrator can rebuild the screen in the
                new language.

        Returns:
            None — :meth:`build` must be called to get the Flet control.
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
        """Build the complete Flet tree for the setup screen.

        Produces a centered page with the logo, application subtitle,
        and form card (city + profile + Start button).

        Args:
            None.

        Returns:
            ft.Control: Expandable ``Container`` with gray background (``theme.BG``),
                horizontally centered, containing the logo and input form.
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
        """Validate input and transmit the result via the ``on_submit`` callback.

        Verifies that the city field is not empty. On error, displays a message
        in-place and stops submission. On success, calls ``on_submit`` with the
        :class:`SetupResult` built from the entered values. The default profile is
        ``"crops"`` if nothing is selected.

        Args:
            None.

        Returns:
            None — calls ``on_submit`` on success, updates ``_error`` otherwise.
        """
        city = (self._city.value or "").strip()
        if not city:
            self._error.value = t("setup_view", "empty_city_error")
            self._error.update()
            return
        self.on_submit(SetupResult(city=city, profile=self._profile.value or "crops"))
