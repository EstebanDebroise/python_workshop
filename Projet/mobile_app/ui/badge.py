"""Composant Badge : pastille colorée à texte et couleur dynamiques."""

from __future__ import annotations

import flet as ft

import theme


class Badge:
    """Pastille colorée dont le libellé et la couleur évoluent dynamiquement.

    Encapsule un ``Container`` Flet en exposant uniquement un ``kind`` sémantique
    (``ok``, ``warn``, ``danger``) plutôt que des couleurs hexadécimales brutes.
    La palette est résolue à partir de :data:`theme.BADGE_PALETTE`.

    Attributs publics :
        control (ft.Container): Le contrôle Flet sous-jacent, à insérer dans la
            hiérarchie parente. Ne pas recréer ce contrôle — modifier via :meth:`update`.
    """

    def __init__(self, text: str = "—", kind: str = "ok") -> None:
        """Crée la pastille avec un libellé et une catégorie initiaux.

        Args:
            text (str): Libellé textuel initial affiché dans la pastille.
                        Défaut : ``"—"``.
            kind (str): Catégorie sémantique parmi ``"ok"``, ``"warn"``, ``"danger"``.
                        Détermine les couleurs du fond et du texte.
                        Défaut : ``"ok"``.

        Returns:
            None — le contrôle Flet est disponible immédiatement via ``self.control``.
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
        """Met à jour le libellé et les couleurs du badge selon un nouveau ``kind``.

        Le contrôle Flet est modifié en place. L'appelant doit ensuite appeler
        ``page.update()`` pour que le changement soit visible à l'écran.

        Args:
            text (str): Nouveau libellé à afficher dans la pastille.
            kind (str): Nouvelle catégorie parmi ``"ok"``, ``"warn"``, ``"danger"``.
                        Détermine les nouvelles couleurs de fond et de texte.

        Returns:
            None
        """
        bg, fg = theme.BADGE_PALETTE[kind]
        self._label.value = text
        self._label.color = fg
        self.control.bgcolor = bg
