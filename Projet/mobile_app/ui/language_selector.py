"""Reusable language selector (startup screen and Settings page)."""

from __future__ import annotations

from typing import Callable

import flet as ft

import i18n
import theme
from ui.base import Buildable


class LanguageSelector(Buildable):
    """Dropdown menu to change the interface language.

    Implements :class:`Buildable`. Lists available languages (:func:`i18n.available`)
    and pre-selects the active language. When changed, updates the current language
    (:func:`i18n.set_language`, which persists it) then calls ``on_change``: the
    caller is responsible for rebuilding the current screen to reflect the new language.
    """

    def __init__(self, on_change: Callable[[], None], *, compact: bool = False) -> None:
        """Prepare the language dropdown menu.

        Args:
            on_change (Callable[[], None]): Callback called after language change.
                Must trigger the reconstruction of the current screen.
            compact (bool): If ``True``, display a narrow menu without label
                (suitable for a screen corner); otherwise a standard menu with label.
        """
        self._on_change = on_change
        self._compact = compact

    def build(self) -> ft.Control:
        """Build the language ``Dropdown`` pre-selected on the active language."""
        options = [
            ft.dropdown.Option(key=code, text=name)
            for code, name in i18n.available().items()
        ]
        return ft.Dropdown(
            label=None if self._compact else i18n.t("common", "language_label"),
            value=i18n.get_language(),
            options=options,
            on_select=self._changed,
            width=130 if self._compact else None,
            border_color=theme.GREEN,
            text_size=12 if self._compact else None,
        )

    def _changed(self, e: ft.ControlEvent) -> None:
        """Apply the chosen language then trigger screen reconstruction."""
        code = e.control.value
        if code and code != i18n.get_language():
            i18n.set_language(code)
            self._on_change()
