"""Dashboard header section: top green banner."""

from __future__ import annotations

import flet as ft

import theme
from i18n import t
from ui.base import Buildable


def _profile_label(profile: str) -> str:
    """Translate a profile code (e.g. ``"dairy"``) to a displayable label."""
    return t("common", f"profile_{profile}")


class HeaderSection(Buildable):
    """Top green banner displaying city, user profile, and Kafka connection status.

    Implements :class:`Buildable`. The Kafka connection status can be updated
    dynamically via :meth:`set_status` without rebuilding the entire section,
    allowing real-time display of "Active Feed", errors, etc.
    """

    def __init__(self, city: str, profile: str, topic: str) -> None:
        """Store fixed labels and prepare the modifiable status text control.

        Args:
            city (str): City name displayed large in the header
                (e.g. ``"Limoges"``).
            profile (str): User profile displayed as subtitle
                (e.g. ``"Dairy Farmer"``).
            topic (str): Kafka topic name displayed in the initial status line
                (e.g. ``"limoges"``).

        Returns:
            None — :meth:`build` must be called to get the Flet control.
        """
        self.city = city
        self.profile = profile
        self.topic = topic
        self._city_text = ft.Text(
            city,
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )
        self._profile_text = ft.Text(
            _profile_label(profile),
            size=12,
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        )
        self._status = ft.Text(
            t("header_section", "connecting", topic=topic),
            size=11,
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        )

    def build(self) -> ft.Control:
        """Build the complete Flet tree for the top banner.

        Produces a green ``Container`` containing on one line: location icon,
        city name, profile, and avatar; and on a second line: status dot
        and Kafka connection text.

        Args:
            None.

        Returns:
            ft.Control: Green ``Container`` (``theme.GREEN``) ready to be inserted
                at the top of the dashboard.
        """
        return ft.Container(
            bgcolor=theme.GREEN,
            padding=ft.Padding.only(left=20, right=20, top=20, bottom=20),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.LOCATION_ON,
                                        color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                                        size=18,
                                    ),
                                    ft.Column(
                                        [
                                            self._city_text,
                                            self._profile_text,
                                        ],
                                        spacing=1,
                                    ),
                                ],
                                spacing=8,
                            ),
                            ft.Container(
                                ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE),
                                width=36,
                                height=36,
                                border_radius=18,
                                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                                alignment=ft.Alignment.CENTER,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                width=6,
                                height=6,
                                border_radius=3,
                                bgcolor=theme.GREEN_LIGHT,
                            ),
                            self._status,
                        ],
                        spacing=6,
                    ),
                ],
                spacing=12,
            ),
        )

    def set_status(self, text: str) -> None:
        """Update the Kafka connection status text in-place.

        Directly modifies the ``_status`` control value without rebuilding the
        header. The caller must call ``page.update()`` for the change to become
        visible on screen.

        Args:
            text (str): New status message to display
                (e.g. ``"Active Feed · 14 measurements received"``, error message).

        Returns:
            None
        """
        self._status.value = text

    def update_info(self, city: str, profile: str, topic: str) -> None:
        """Update the city, profile, and topic displayed in the header.

        Modifies the text controls in-place. The caller must call
        ``page.update()`` for the changes to become visible.

        Args:
            city (str): New city name.
            profile (str): New user profile.
            topic (str): New Kafka topic for the status line.

        Returns:
            None
        """
        self.city = city
        self.profile = profile
        self.topic = topic
        self._city_text.value = city
        self._profile_text.value = _profile_label(profile)
        self._status.value = t("header_section", "connecting", topic=topic)
