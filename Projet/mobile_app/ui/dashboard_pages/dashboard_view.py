"""Vue dashboard : orchestrateur assemblant le header, les 4 sections et la navigation."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

import theme
from logic.notification_service import NotificationService
from models import Weather
from ui.base import Buildable
from ui.dashboard_pages.bottom_nav_section import BottomNavSection
from ui.components import UIComponents
from ui.dashboard_pages.current_weather_section import CurrentWeatherSection
from ui.dashboard_pages.header_section import HeaderSection
from ui.dashboard_pages.notifications_view import NotificationsView
from ui.dashboard_pages.pasture_section import PastureSection
from ui.dashboard_pages.settings_view import SettingsView
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

    Gère la navigation entre le dashboard, la page Alertes et la page de réglages
    via la barre inférieure. Expose :meth:`update_weather` et :meth:`set_status`
    pour les mises à jour en temps réel.
    """

    def __init__(
        self,
        city: str,
        profile: str,
        topic: str,
        notification_service: NotificationService,
        on_settings_save: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """Instancie chaque sous-section et prépare la zone de contenu permutable.

        Args:
            city (str): Nom de la ville affiché dans le header.
            profile (str): Profil utilisateur affiché en sous-titre du header.
            topic (str): Nom du topic Kafka pour la ligne de statut initiale.
            notification_service (NotificationService): Service partagé pilotant
                l'activation et l'envoi des notifications, fourni à la page Alertes.
            on_settings_save (Callable[[str, str], None] | None): Callback optionnel
                appelé avec ``(city, profile)`` quand l'utilisateur enregistre ses
                réglages. Permet à l'orchestrateur parent de relancer le consumer Kafka.

        Returns:
            None — :meth:`build` doit être appelé pour obtenir le contrôle Flet.
        """
        self._current_city = city
        self._current_profile = profile
        self._notification_service = notification_service
        self._on_settings_save_cb = on_settings_save

        self.header = HeaderSection(city, profile, topic)
        self.current = CurrentWeatherSection()
        self.thi = ThiSection()
        self.pasture = PastureSection()
        self.treatment = TreatmentSection()

        self._dashboard_ctrl = self._make_dashboard_content()
        self._body = ft.Container(
            bgcolor=theme.BG,
            padding=16,
            expand=True,
            content=self._dashboard_ctrl,
        )
        self._bottom_nav = BottomNavSection(
            on_dashboard=self._nav_to_dashboard,
            on_alerts=self._nav_to_alerts,
            on_settings=self._nav_to_settings,
        )

    def _make_dashboard_content(self) -> ft.Column:
        return ft.Column(
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
        )

    def _nav_to_dashboard(self) -> None:
        self._body.content = self._dashboard_ctrl
        self._body.update()

    def _nav_to_alerts(self) -> None:
        alerts = NotificationsView(self._notification_service)
        self._body.content = alerts.build()
        self._body.update()

    def _nav_to_settings(self) -> None:
        settings = SettingsView(self._current_city, self._current_profile, self._on_settings_saved)
        self._body.content = settings.build()
        self._body.update()

    def _on_settings_saved(self, city: str, profile: str) -> None:
        self._current_city = city
        self._current_profile = profile
        if self._on_settings_save_cb:
            self._on_settings_save_cb(city, profile)

    def build(self) -> ft.Control:
        """Assemble le header, la zone de contenu permutable et la barre de navigation.

        Args:
            Aucun.

        Returns:
            ft.Control: ``Column`` Flet complète (header + corps + nav) prête
                à être ajoutée à la page.
        """
        return ft.Column(
            [self.header.build(), self._body, self._bottom_nav.build()],
            spacing=0,
            expand=True,
        )

    def update_weather(self, w: Weather) -> None:
        """Propage une nouvelle mesure météo à chacune des quatre sections enfants.

        Args:
            w (Weather): La nouvelle mesure météo reçue depuis le consommateur Kafka.

        Returns:
            None
        """
        self.current.update(w)
        self.thi.update(w)
        self.pasture.update(w)
        self.treatment.update(w)

    def reset_data(self) -> None:
        """Réinitialise les quatre sections à leur état d'attente.

        Vide les données accumulées (historique, alertes, créneaux…) afin de ne pas
        afficher les mesures de l'ancien lieu après un changement de localisation.
        Le rafraîchissement réel à l'écran est déclenché par l'appelant via
        ``page.update()``.

        Args:
            Aucun.

        Returns:
            None
        """
        self.current.reset()
        self.thi.reset()
        self.pasture.reset()
        self.treatment.reset()

    def set_status(self, text: str) -> None:
        """Relaie un message de statut de connexion Kafka au header du dashboard.

        Args:
            text (str): Message de statut à afficher dans le bandeau supérieur.

        Returns:
            None
        """
        self.header.set_status(text)
