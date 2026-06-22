"""Sélecteur de langue réutilisable (écran de démarrage et page Réglages)."""

from __future__ import annotations

from typing import Callable

import flet as ft

import i18n
import theme
from ui.base import Buildable


class LanguageSelector(Buildable):
    """Menu déroulant permettant de changer la langue de l'interface.

    Implémente :class:`Buildable`. Liste les langues disponibles
    (:func:`i18n.available`) et présélectionne la langue active. Lors d'un
    changement, met à jour la langue courante (:func:`i18n.set_language`, qui
    la persiste) puis appelle ``on_change`` : l'appelant est responsable de
    reconstruire l'écran courant pour refléter la nouvelle langue.
    """

    def __init__(self, on_change: Callable[[], None], *, compact: bool = False) -> None:
        """Prépare le menu déroulant des langues.

        Args:
            on_change (Callable[[], None]): Callback appelé après changement de
                langue. Doit déclencher la reconstruction de l'écran courant.
            compact (bool): Si ``True``, affiche un menu étroit sans libellé
                (adapté à un coin d'écran) ; sinon un menu standard avec libellé.
        """
        self._on_change = on_change
        self._compact = compact

    def build(self) -> ft.Control:
        """Construit le ``Dropdown`` des langues présélectionné sur la langue active."""
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
        """Applique la langue choisie puis déclenche la reconstruction de l'écran."""
        code = e.control.value
        if code and code != i18n.get_language():
            i18n.set_language(code)
            self._on_change()
