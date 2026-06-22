"""Factory for reusable Flet components across the entire application."""

from __future__ import annotations

import flet as ft

import theme


class UIComponents:
    """Static factory for reusable Flet components.

    Groups all shared visual elements as static methods: cards, alert banners,
    stat cells, navigation items, and section labels. No instantiation needed.

    Class Attributes:
        COLOR_TOKENS (dict[str, str]): Semantic token → hexadecimal color mapping.
            Connects the business layer (analytics) to the UI layer without
            requiring the business logic to import Flet or know exact colors.
    """

    COLOR_TOKENS: dict[str, str] = {
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

    @staticmethod
    def icon_name(name: "str | ft.Icons") -> ft.Icons:
        """Convert a snake_case identifier to the corresponding ``ft.Icons`` member.

        Allows the business layer to manipulate neutral strings (e.g. ``wb_sunny``)
        without directly importing Flet. Also accepts an already-resolved ``ft.Icons``
        member, which is returned as-is.

        Args:
            name (str | ft.Icons): Icon name in snake_case (e.g. ``"wb_sunny"``,
                ``"home_work"``) or an ``ft.Icons`` member.

        Returns:
            ft.Icons: The corresponding Flet enumeration member.
        """
        if isinstance(name, str):
            return getattr(ft.Icons, name.upper())
        return name

    @staticmethod
    def section_label(text: str) -> ft.Text:
        """Create a section label in capitals with a subtle monospace subtitle style.

        Args:
            text (str): Label text. Will be automatically converted to uppercase.

        Returns:
            ft.Text: Styled text control (size 10, monospace, muted color),
                ready to be inserted before each dashboard section.
        """
        return ft.Text(
            text.upper(),
            size=10,
            weight=ft.FontWeight.W_600,
            color=theme.MUTED,
            font_family="monospace",
        )

    @staticmethod
    def card(content: ft.Control) -> ft.Container:
        """Wrap a control in the application's standard white card.

        Applies the white background, gray border, corner radius, and padding
        defined by the design system. Used by all dashboard sections.

        Args:
            content (ft.Control): The control or column to display inside the card.

        Returns:
            ft.Container: Card with white background (``theme.CARD``), gray border
                (``theme.BORDER``), 18 px rounded corners, and 16 px padding.
        """
        return ft.Container(
            content=content,
            bgcolor=theme.CARD,
            border_radius=18,
            padding=16,
            border=ft.Border.all(1, theme.BORDER),
        )

    @staticmethod
    def alert_strip(icon: str, text: str, fg: str, bg: str, border_color: str) -> ft.Container:
        """Create a fully parameterizable horizontal alert banner.

        Serves as the base building block for all specialized helpers
        (``cold_alert``, ``sun_alert``, ``warn_alert``, etc.) which delegate here,
        providing only the color triplet suited to their alert type.

        Args:
            icon (str): Flet icon identifier to display (e.g. ``ft.Icons.WARNING``).
            text (str): Alert message to display next to the icon.
            fg (str): Hexadecimal color applied to the icon and text.
            bg (str): Hexadecimal color for the banner background.
            border_color (str): Hexadecimal color for the banner border.

        Returns:
            ft.Container: Banner with icon, expanded text, colored background and border,
                10 px rounded corners.
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
            border=ft.Border.all(1, border_color),
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border_radius=10,
        )

    @staticmethod
    def cold_alert(icon: str, text: str) -> ft.Container:
        """Create a cold alert banner (shelter animals) with blue tones.

        Args:
            icon (str): Flet icon identifier to display.
            text (str): Alert message to display (e.g. "Shelter calves and lambs.").

        Returns:
            ft.Container: Light blue banner (``theme.SKY_PALE``) suited for cold alerts.
        """
        return UIComponents.alert_strip(icon, text, theme.SKY_DARK, theme.SKY_PALE, "#B3E5FC")

    @staticmethod
    def sun_alert(icon: str, text: str) -> ft.Container:
        """Create an intense sunlight alert banner (shade required) with yellow tones.

        Args:
            icon (str): Flet icon identifier to display.
            text (str): Alert message to display (e.g. "Shade required.").

        Returns:
            ft.Container: Pale yellow banner suited for maximum sun exposure alerts.
        """
        return UIComponents.alert_strip(icon, text, "#E65100", "#FFF9C4", "#FFF176")

    @staticmethod
    def warn_alert(icon: str, text: str) -> ft.Container:
        """Create a generic warning banner with amber tones.

        Args:
            icon (str): Flet icon identifier to display.
            text (str): Warning message to display.

        Returns:
            ft.Container: Pale amber banner (``theme.AMBER_PALE``) for warnings.
        """
        return UIComponents.alert_strip(icon, text, "#B45309", theme.AMBER_PALE, "#FDE68A")

    @staticmethod
    def danger_alert(icon: str, text: str) -> ft.Container:
        """Create a critical danger banner with red tones.

        Args:
            icon (str): Flet icon identifier to display.
            text (str): Danger message to display (e.g. "Ventilation required.").

        Returns:
            ft.Container: Pale red banner (``theme.RED_PALE``) for critical alerts.
        """
        return UIComponents.alert_strip(icon, text, theme.RED, theme.RED_PALE, "#FFCDD2")

    @staticmethod
    def info_alert(icon: str, text: str) -> ft.Container:
        """Create a subtle informational banner (push confirmation, etc.) with ochre tones.

        Args:
            icon (str): Flet icon identifier to display.
            text (str): Informational message to display.

        Returns:
            ft.Container: Light ochre banner (``#FFF8E1``) for confirmation messages.
        """
        return UIComponents.alert_strip(icon, text, "#92400E", "#FFF8E1", "#FFE082")

    @staticmethod
    def stat_cell(value_ctrl: ft.Text, unit: str, label: str) -> ft.Container:
        """Create a centered statistic cell displaying numeric value, unit, and label.

        The ``value_ctrl`` parameter is passed by reference so the owning section
        can update it in-place without rebuilding the cell.

        Args:
            value_ctrl (ft.Text): Text control containing the numeric value,
                created and managed by the calling section to allow updates.
            unit (str): Unit displayed small to the right of the value (e.g. ``"°C"``, ``"m/s"``).
            label (str): Descriptive label displayed below the value (e.g. ``"Actual Temperature"``).

        Returns:
            ft.Container: Gray cell (``theme.BG``) horizontally expandable,
                with rounded corners and center alignment.
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

    @staticmethod
    def nav_item(icon: str, label: str, active: bool) -> ft.Container:
        """Create a bottom navigation bar item with icon and label.

        Args:
            icon (str): Flet icon identifier to display (e.g. ``ft.Icons.DASHBOARD``).
            label (str): Textual label for the tab (e.g. ``"Dashboard"``).
            active (bool): If ``True``, the item is highlighted green (``theme.GREEN``);
                otherwise displayed in muted color (``theme.MUTED``).

        Returns:
            ft.Container: Navigation item centered and horizontally expandable,
                ready to be placed in a ``Row`` of the bottom bar.
        """
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
            alignment=ft.Alignment.CENTER,
        )
