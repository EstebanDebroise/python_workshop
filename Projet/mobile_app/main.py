"""Météo Agri — point d'entrée Flet.

Orchestre :
  - la vue de configuration (ville + profil),
  - le client de l'API (polling périodique en arrière-plan),
  - la vue dashboard (4 sections).

L'application n'accède plus directement à Kafka : elle interroge l'API
intermédiaire (dossier ``api/``) qui lit Kafka et gère la base des lieux.
"""

from __future__ import annotations

import os
import re
import threading

import flet as ft
import requests

import theme
from logic.weather_notifier import WeatherNotifier
from api_client import ApiWeatherClient
from models import Weather
from ui.dashboard_pages.dashboard_view import DashboardView
from ui.conexion_pages.setup_view import SetupResult, SetupView

API_BASE = os.getenv("WEATHER_API_BASE", "http://localhost:8000")


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
        self.client: ApiWeatherClient | None = None
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
        """Callback de :class:`SetupView` : enregistre le lieu puis bascule sur le dashboard."""
        topic = re.sub(r"[^A-Za-z0-9_.\-]", "_", result.city.lower())
        self._register_location(result.city)
        self._show_dashboard(result.city, result.profile, topic)
        self._start_client(topic)

    def _show_dashboard(self, city: str, profile: str, topic: str) -> None:
        """Instancie le dashboard, remplace les contrôles et active le scroll."""
        self.dashboard = DashboardView(
            city, profile, topic, on_settings_save=self._on_settings_save
        )
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.controls.clear()
        self.page.add(self.dashboard.build())
        self.page.update()

    def _on_settings_save(self, city: str, profile: str) -> None:
        """Applique les nouveaux réglages : enregistre le lieu, met à jour le header, relance le client."""
        topic = re.sub(r"[^A-Za-z0-9_.\-]", "_", city.lower())
        self._register_location(city)
        if self.dashboard is not None:
            self.dashboard.header.update_info(city, profile, topic)
            self.page.update()
        self.prev_weather = None
        self._start_client(topic)

    def _start_client(self, topic: str) -> None:
        """Arrête l'éventuel client en cours et lance un client API sur le topic demandé."""
        if self.client is not None:
            self.client.stop()
        self.client = ApiWeatherClient(
            topic=topic,
            api_base=API_BASE,
            on_weather=self._on_new_weather,
            on_status=self._on_status,
        )
        self.client.start()

    def _register_location(self, city: str) -> None:
        """Demande à l'API d'enregistrer le lieu (ajout idempotent), sans bloquer l'UI.

        L'appel HTTP est lancé dans un thread daemon et toute erreur est ignorée :
        l'enregistrement du lieu ne doit jamais empêcher l'utilisateur d'accéder
        au dashboard si l'API est momentanément indisponible.
        """

        def _post() -> None:
            try:
                requests.post(
                    f"{API_BASE}/locations", json={"name": city}, timeout=10
                )
            except requests.RequestException:
                pass

        threading.Thread(target=_post, daemon=True).start()

    # ----- callbacks (exécutés dans le thread du client API) -----

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
