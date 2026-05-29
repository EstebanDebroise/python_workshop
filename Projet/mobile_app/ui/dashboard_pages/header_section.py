"""Section header du dashboard : bandeau vert supérieur."""

from __future__ import annotations

import flet as ft

import theme
from ui.base import Buildable


class HeaderSection(Buildable):
    """Bandeau vert supérieur affichant la ville, le profil utilisateur et le statut Kafka.

    Implémente :class:`Buildable`. Le statut de connexion Kafka peut être mis à jour
    dynamiquement via :meth:`set_status` sans reconstruire toute la section,
    ce qui permet d'afficher en temps réel « Flux actif », les erreurs, etc.
    """

    def __init__(self, city: str, profile: str, topic: str) -> None:
        """Mémorise les libellés fixes et prépare le contrôle texte de statut modifiable.

        Args:
            city (str): Nom de la ville affiché en grand dans l'en-tête
                (ex. ``"Limoges"``).
            profile (str): Profil de l'utilisateur affiché en sous-titre
                (ex. ``"Éleveur laitier"``).
            topic (str): Nom du topic Kafka affiché dans la ligne de statut initiale
                (ex. ``"limoges"``).

        Returns:
            None — :meth:`build` doit être appelé pour obtenir le contrôle Flet.
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
            profile,
            size=12,
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        )
        self._status = ft.Text(
            f"Connexion au topic « {topic} »…",
            size=11,
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
        )

    def build(self) -> ft.Control:
        """Construit l'arbre Flet complet du bandeau supérieur.

        Produit un ``Container`` vert contenant sur une ligne : icône de localisation,
        nom de ville, profil et avatar ; et sur une deuxième ligne : point de statut
        et texte de connexion Kafka.

        Args:
            Aucun.

        Returns:
            ft.Control: ``Container`` vert (``theme.GREEN``) prêt à être inséré
                en haut du dashboard.
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
        """Met à jour le texte de statut de connexion Kafka en place.

        Modifie directement la valeur du contrôle ``_status`` sans reconstruire
        le header. L'appelant doit appeler ``page.update()`` pour que le
        changement soit visible à l'écran.

        Args:
            text (str): Nouveau message de statut à afficher
                (ex. ``"Flux actif · 14 mesures reçues"``, message d'erreur).

        Returns:
            None
        """
        self._status.value = text

    def update_info(self, city: str, profile: str, topic: str) -> None:
        """Met à jour la ville, le profil et le topic affichés dans le header.

        Modifie les contrôles texte en place. L'appelant doit appeler
        ``page.update()`` pour que les changements soient visibles.

        Args:
            city (str): Nouveau nom de ville.
            profile (str): Nouveau profil utilisateur.
            topic (str): Nouveau topic Kafka pour la ligne de statut.

        Returns:
            None
        """
        self.city = city
        self.profile = profile
        self.topic = topic
        self._city_text.value = city
        self._profile_text.value = profile
        self._status.value = f"Connexion au topic « {topic} »…"
