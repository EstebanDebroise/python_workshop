"""Badge component: colored pill with dynamic text and color."""

from __future__ import annotations

import flet as ft

import theme


class Badge:
    """Colored pill with dynamically evolving label and color.

    Wraps a Flet ``Container`` exposing only a semantic ``kind`` (``ok``, ``warn``,
    ``danger``) rather than raw hexadecimal colors. The palette is resolved from
    :data:`theme.BADGE_PALETTE`.

    Public Attributes:
        control (ft.Container): The underlying Flet control, to be inserted in the
            parent hierarchy. Do not recreate this control — modify via :meth:`update`.
    """

    def __init__(self, text: str = "—", kind: str = "ok") -> None:
        """Create the badge with an initial label and category.

        Args:
            text (str): Initial textual label displayed in the badge.
                        Default: ``"—"``.
            kind (str): Semantic category among ``"ok"``, ``"warn"``, ``"danger"``.
                        Determines the background and text colors.
                        Default: ``"ok"``.

        Returns:
            None — the Flet control is immediately available via ``self.control``.
        """
        bg, fg = theme.BADGE_PALETTE[kind]
        self._label = ft.Text(text, size=10, weight=ft.FontWeight.W_500, color=fg)
        self.control = ft.Container(
            content=self._label,
            bgcolor=bg,
            padding=ft.Padding.symmetric(horizontal=9, vertical=3),
            border_radius=20,
        )

    def update(self, text: str, kind: str) -> None:
        """Update the badge label and colors according to a new ``kind``.

        The Flet control is modified in-place. The caller must then call
        ``page.update()`` for the change to become visible on screen.

        Args:
            text (str): New label to display in the badge.
            kind (str): New category among ``"ok"``, ``"warn"``, ``"danger"``.
                        Determines the new background and text colors.

        Returns:
            None
        """
        bg, fg = theme.BADGE_PALETTE[kind]
        self._label.value = text
        self._label.color = fg
        self.control.bgcolor = bg
