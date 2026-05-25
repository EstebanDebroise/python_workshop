"""Météo Agri — point d'entrée Flet.

Orchestre :
  - la vue de configuration (ville + profil),
  - le consumer Kafka (thread d'arrière-plan),
  - la vue dashboard (4 sections).
"""

from __future__ import annotations

import os
import re

import flet as ft

import theme
from logic.weather_notifier import WeatherNotifier
from kafka_client import WeatherConsumer
from models import Weather
from ui.dashboard_pages.dashboard_view import DashboardView
from ui.conexion_pages.setup_view import SetupResult, SetupView

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")


class WeatherApp:
    """Contrôleur principal : enchaîne setup → dashboard et pilote Kafka.

    Conserve la dernière mesure pour comparer chaque nouvelle valeur et
    déclencher les notifications de changement. Toute la mise en page
    est déléguée à :class:`SetupView` puis :class:`DashboardView`.
    """

    def __init__(self, page: ft.Page) -> None:
        """Configure la page Flet et affiche l'écran de saisie initial."""
        self.page = page
        self.prev_weather: Weather | None = None
        self.dashboard: DashboardView | None = None
        self.consumer: WeatherConsumer | None = None
        self._configure_page()
        self._show_setup()

    def _configure_page(self) -> None:
        """Applique les réglages globaux de la page (titre, fond, thème)."""
        self.page.title = "Météo Agri"
        self.page.bgcolor = theme.BG
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT

    def _show_setup(self) -> None:
        """Affiche l'écran de configuration et bloque le scroll global."""
        self.page.scroll = None
        setup = SetupView(on_submit=self._on_setup_submitted)
        self.page.controls.clear()
        self.page.add(setup.build())
        self.page.update()

    def _on_setup_submitted(self, result: SetupResult) -> None:
        """Callback de :class:`SetupView` : normalise le topic puis bascule sur le dashboard."""
        topic = re.sub(r"[^A-Za-z0-9_.\-]", "_", result.city.lower())
        self._show_dashboard(result.city, result.profile, topic)
        self._start_consumer(topic)

    def _show_dashboard(self, city: str, profile: str, topic: str) -> None:
        """Instancie le dashboard, remplace les contrôles et active le scroll."""
        self.dashboard = DashboardView(city, profile, topic)
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.controls.clear()
        self.page.add(self.dashboard.build())
        self.page.update()

    def _start_consumer(self, topic: str) -> None:
        """Crée et lance le :class:`WeatherConsumer` lié au topic demandé."""
        self.consumer = WeatherConsumer(
            topic=topic,
            bootstrap=KAFKA_BOOTSTRAP,
            on_weather=self._on_new_weather,
            on_status=self._on_status,
        )
        self.consumer.start()

    # ----- callbacks Kafka (exécutés dans le thread consumer) -----

    def _on_status(self, text: str) -> None:
        """Relaie un message de statut Kafka au header du dashboard."""
        if self.dashboard is None:
            return
        self.dashboard.set_status(text)
        self.page.update()

    def _on_new_weather(self, w: Weather) -> None:
        """Met à jour le dashboard et émet les notifications de changement."""
        if self.dashboard is None:
            return
        self.dashboard.update_weather(w)
        for msg in WeatherNotifier.change_notifications(self.prev_weather, w):
            self._notify(msg)
        self.prev_weather = w
        self.page.update()

    def _notify(self, message: str) -> None:
        """Affiche une SnackBar rouge ; ignore silencieusement toute erreur Flet."""
        try:
            self.page.open(ft.SnackBar(ft.Text(message), bgcolor=theme.RED))
        except Exception:
            pass

    @staticmethod
    def main(page: ft.Page) -> None:
        """Point d'entrée appelé par ``ft.app`` pour chaque session utilisateur."""
        WeatherApp(page)


if __name__ == "__main__":
    ft.app(target=WeatherApp.main)
