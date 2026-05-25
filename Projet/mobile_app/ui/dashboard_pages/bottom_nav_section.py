"""Section de navigation inférieure : barre fixe avec 4 onglets."""

from __future__ import annotations

import flet as ft

import theme
from ui.base import Buildable
from ui.components import UIComponents


class BottomNavSection(Buildable):
    """Barre de navigation inférieure fixe comportant 4 onglets.

    Implémente :class:`Buildable`. La section est entièrement statique :
    elle ne réagit pas aux mesures météo et n'a pas de méthode ``update``.
    Seul l'onglet « Tableau » est marqué actif par défaut ; les autres
    onglets (Historique, Alertes, Réglages) sont actuellement non fonctionnels.
    """

    def build(self) -> ft.Control:
        """Construit la barre de navigation avec ses 4 items alignés horizontalement.

        Produit un ``Container`` blanc avec une bordure supérieure, contenant
        une ``Row`` de 4 items de navigation créés via :meth:`UIComponents.nav_item`.
        L'onglet « Tableau » est le seul marqué actif (``active=True``).

        Args:
            Aucun.

        Returns:
            ft.Control: ``Container`` blanc (``theme.CARD``) avec bordure supérieure
                et 4 items de navigation espacés uniformément.
        """
        return ft.Container(
            bgcolor=theme.CARD,
            border=ft.border.only(top=ft.border.BorderSide(1, theme.BORDER)),
            padding=ft.padding.only(top=10, bottom=22),
            content=ft.Row(
                [
                    UIComponents.nav_item(ft.Icons.DASHBOARD, "Tableau", True),
                    UIComponents.nav_item(ft.Icons.SHOW_CHART, "Historique", False),
                    UIComponents.nav_item(ft.Icons.NOTIFICATIONS, "Alertes", False),
                    UIComponents.nav_item(ft.Icons.SETTINGS, "Réglages", False),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
        )
