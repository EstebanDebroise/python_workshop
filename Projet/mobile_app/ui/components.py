"""Fabrique de composants Flet réutilisables pour l'ensemble de l'application."""

from __future__ import annotations

import flet as ft

import theme


class UIComponents:
    """Fabrique statique de composants Flet réutilisables.

    Regroupe sous forme de méthodes statiques tous les éléments visuels partagés :
    cartes, bandeaux d'alerte, cellules statistiques, items de navigation et
    labels de section. Aucune instanciation n'est nécessaire.

    Attribut de classe :
        COLOR_TOKENS (dict[str, str]): Mapping token sémantique → couleur hexadécimale.
            Relie la couche métier (analytics) à la couche UI sans que la logique
            métier n'ait besoin d'importer Flet ou de connaître les couleurs exactes.
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
        """Convertit un identifiant snake_case en membre ``ft.Icons`` correspondant.

        Permet à la couche métier de manipuler des chaînes neutres (ex. ``wb_sunny``)
        sans importer Flet directement. Accepte aussi un membre ``ft.Icons`` déjà
        résolu, qui est alors renvoyé tel quel.

        Args:
            name (str | ft.Icons): Nom de l'icône en snake_case (ex. ``"wb_sunny"``,
                ``"home_work"``) ou un membre ``ft.Icons``.

        Returns:
            ft.Icons: Le membre d'énumération Flet correspondant.
        """
        if isinstance(name, str):
            return getattr(ft.Icons, name.upper())
        return name

    @staticmethod
    def section_label(text: str) -> ft.Text:
        """Crée un libellé de section en capitales, style sous-titre discret et monospace.

        Args:
            text (str): Texte du libellé. Sera automatiquement converti en majuscules.

        Returns:
            ft.Text: Contrôle texte stylisé (taille 10, monospace, couleur atténuée),
                prêt à être inséré avant chaque section du dashboard.
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
        """Enveloppe un contrôle dans la carte blanche standard de l'application.

        Applique le fond blanc, la bordure grise, le rayon de coin et le padding
        définis par la charte graphique. Utilisé par toutes les sections du dashboard.

        Args:
            content (ft.Control): Le contrôle ou la colonne à afficher à l'intérieur
                de la carte.

        Returns:
            ft.Container: Carte avec fond blanc (``theme.CARD``), bordure grise
                (``theme.BORDER``), coins arrondis à 18 px et padding de 16 px.
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
        """Crée un bandeau d'alerte horizontal entièrement paramétrable.

        Sert de brique de base pour tous les helpers spécialisés
        (``cold_alert``, ``sun_alert``, ``warn_alert``, etc.) qui délèguent ici
        en ne fournissant que le triplet de couleurs adapté à leur type d'alerte.

        Args:
            icon (str): Identifiant Flet de l'icône à afficher (ex. ``ft.Icons.WARNING``).
            text (str): Message d'alerte à afficher à côté de l'icône.
            fg (str): Couleur hexadécimale appliquée à l'icône et au texte.
            bg (str): Couleur hexadécimale du fond du bandeau.
            border_color (str): Couleur hexadécimale de la bordure du bandeau.

        Returns:
            ft.Container: Bandeau avec icône, texte expansif, fond et bordure colorés,
                coins arrondis à 10 px.
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
        """Crée un bandeau d'alerte froid (abriter les animaux), tons bleus.

        Args:
            icon (str): Identifiant Flet de l'icône à afficher.
            text (str): Message d'alerte à afficher (ex. "Abriter veaux et agneaux.").

        Returns:
            ft.Container: Bandeau bleu clair (``theme.SKY_PALE``) adapté aux alertes de froid.
        """
        return UIComponents.alert_strip(icon, text, theme.SKY_DARK, theme.SKY_PALE, "#B3E5FC")

    @staticmethod
    def sun_alert(icon: str, text: str) -> ft.Container:
        """Crée un bandeau d'alerte ensoleillement intense (ombre requise), tons jaunes.

        Args:
            icon (str): Identifiant Flet de l'icône à afficher.
            text (str): Message d'alerte à afficher (ex. "Ombre obligatoire.").

        Returns:
            ft.Container: Bandeau jaune pâle adapté aux alertes d'ensoleillement maximal.
        """
        return UIComponents.alert_strip(icon, text, "#E65100", "#FFF9C4", "#FFF176")

    @staticmethod
    def warn_alert(icon: str, text: str) -> ft.Container:
        """Crée un bandeau d'avertissement générique, tons ambre.

        Args:
            icon (str): Identifiant Flet de l'icône à afficher.
            text (str): Message d'avertissement à afficher.

        Returns:
            ft.Container: Bandeau ambre pâle (``theme.AMBER_PALE``) pour avertissements.
        """
        return UIComponents.alert_strip(icon, text, "#B45309", theme.AMBER_PALE, "#FDE68A")

    @staticmethod
    def danger_alert(icon: str, text: str) -> ft.Container:
        """Crée un bandeau de danger critique, tons rouges.

        Args:
            icon (str): Identifiant Flet de l'icône à afficher.
            text (str): Message de danger à afficher (ex. "Ventilation requise.").

        Returns:
            ft.Container: Bandeau rouge pâle (``theme.RED_PALE``) pour alertes critiques.
        """
        return UIComponents.alert_strip(icon, text, theme.RED, theme.RED_PALE, "#FFCDD2")

    @staticmethod
    def info_alert(icon: str, text: str) -> ft.Container:
        """Crée un bandeau informatif sobre (confirmation push, etc.), tons ocres.

        Args:
            icon (str): Identifiant Flet de l'icône à afficher.
            text (str): Message informatif à afficher.

        Returns:
            ft.Container: Bandeau ocre clair (``#FFF8E1``) pour messages de confirmation.
        """
        return UIComponents.alert_strip(icon, text, "#92400E", "#FFF8E1", "#FFE082")

    @staticmethod
    def stat_cell(value_ctrl: ft.Text, unit: str, label: str) -> ft.Container:
        """Crée une cellule statistique centrée affichant valeur numérique, unité et libellé.

        Le paramètre ``value_ctrl`` est passé par référence afin que la section
        propriétaire puisse le mettre à jour en place sans reconstruire la cellule.

        Args:
            value_ctrl (ft.Text): Contrôle texte contenant la valeur numérique,
                créé et géré par la section appelante pour permettre les mises à jour.
            unit (str): Unité affichée en petit à droite de la valeur (ex. ``"°C"``, ``"m/s"``).
            label (str): Libellé descriptif affiché sous la valeur (ex. ``"Température réelle"``).

        Returns:
            ft.Container: Cellule grise (``theme.BG``) extensible horizontalement,
                avec coins arrondis et alignement centré.
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
        """Crée un item de barre de navigation inférieure avec icône et libellé.

        Args:
            icon (str): Identifiant Flet de l'icône à afficher (ex. ``ft.Icons.DASHBOARD``).
            label (str): Libellé textuel de l'onglet (ex. ``"Tableau"``).
            active (bool): Si ``True``, l'item est mis en surbrillance verte (``theme.GREEN``) ;
                sinon il est affiché en couleur atténuée (``theme.MUTED``).

        Returns:
            ft.Container: Item de navigation centré et extensible horizontalement,
                prêt à être placé dans une ``Row`` de la barre inférieure.
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
