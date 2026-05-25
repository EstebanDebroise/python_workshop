"""Vue dashboard : orchestrateur assemblant le header, les 4 sections et la navigation."""

from __future__ import annotations

import flet as ft

import theme
from models import Weather
from ui.base import Buildable
from ui.dashboard_pages.bottom_nav_section import BottomNavSection
from ui.components import UIComponents
from ui.dashboard_pages.current_weather_section import CurrentWeatherSection
from ui.dashboard_pages.header_section import HeaderSection
from ui.dashboard_pages.pasture_section import PastureSection
from ui.dashboard_pages.thi_section import ThiSection
from ui.dashboard_pages.treatment_section import TreatmentSection


class DashboardView(Buildable):
    """Orchestrateur principal de la vue dashboard.

    Agrège et coordonne cinq composants enfants :
    - :class:`HeaderSection` : bandeau supérieur (ville, profil, statut Kafka) ;
    - :class:`CurrentWeatherSection` : météo actuelle et historique ;
    - :class:`ThiSection` : jauge de stress thermique ;
    - :class:`PastureSection` : confort au pré ;
    - :class:`TreatmentSection` : créneaux de pulvérisation ;
    - :class:`BottomNavSection` : barre de navigation inférieure.

    Expose :meth:`build` pour construire l'arbre Flet initial, :meth:`update_weather`
    pour diffuser une nouvelle mesure à toutes les sections, et :meth:`set_status`
    pour relayer un message Kafka au header.
    """

    def __init__(self, city: str, profile: str, topic: str) -> None:
        """Instancie chaque sous-section dans l'ordre d'affichage du dashboard.

        Args:
            city (str): Nom de la ville affiché dans le header (ex. ``"Limoges"``).
            profile (str): Profil utilisateur affiché en sous-titre du header
                (ex. ``"Éleveur laitier"``).
            topic (str): Nom du topic Kafka utilisé pour la ligne de statut initiale
                (ex. ``"limoges"``).

        Returns:
            None — :meth:`build` doit être appelé pour obtenir le contrôle Flet.
        """
        self.header = HeaderSection(city, profile, topic)
        self.current = CurrentWeatherSection()
        self.thi = ThiSection()
        self.pasture = PastureSection()
        self.treatment = TreatmentSection()
        self._bottom_nav = BottomNavSection()

    def build(self) -> ft.Control:
        """Assemble le header, le corps scrollable et la barre de navigation inférieure.

        Le corps est une ``Column`` scrollable contenant les 4 sections précédées
        chacune d'un label de section. Le tout est encapsulé dans une ``Column``
        principale (expand=True) aux côtés du header et de la navigation.

        Args:
            Aucun.

        Returns:
            ft.Control: ``Column`` Flet complète (header + corps + nav) prête
                à être ajoutée à la page.
        """
        body = ft.Container(
            bgcolor=theme.BG,
            padding=16,
            content=ft.Column(
                [
                    UIComponents.section_label("Météo actuelle"),
                    self.current.build(),
                    UIComponents.section_label("Stress thermique"),
                    self.thi.build(),
                    UIComponents.section_label("Confort au pré"),
                    self.pasture.build(),
                    UIComponents.section_label("Fenêtre de traitement"),
                    self.treatment.build(),
                    ft.Container(height=8),
                ],
                spacing=10,
            ),
        )
        return ft.Column(
            [self.header.build(), body, self._bottom_nav.build()],
            spacing=0,
            expand=True,
        )

    def update_weather(self, w: Weather) -> None:
        """Propage une nouvelle mesure météo à chacune des quatre sections enfants.

        Appelle successivement :meth:`update` sur ``current``, ``thi``, ``pasture``
        et ``treatment``. Le header et la navigation ne sont pas mis à jour ici
        (ils n'ont pas de méthode ``update`` liée aux mesures météo).

        Args:
            w (Weather): La nouvelle mesure météo reçue depuis le consommateur Kafka.

        Returns:
            None
        """
        self.current.update(w)
        self.thi.update(w)
        self.pasture.update(w)
        self.treatment.update(w)

    def set_status(self, text: str) -> None:
        """Relaie un message de statut de connexion Kafka au header du dashboard.

        Args:
            text (str): Message de statut à afficher dans le bandeau supérieur
                (ex. ``"Flux actif · 14 mesures reçues"``, message d'erreur).

        Returns:
            None
        """
        self.header.set_status(text)
