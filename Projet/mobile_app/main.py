"""Weather Agri — Flet entry point.

Orchestrates:
  - the configuration view (city + profile),
  - the API client (periodic polling in background),
  - the dashboard view (4 sections).

The application no longer accesses Kafka directly: it queries the
intermediate API (``api/`` folder) which reads Kafka and manages locations.
"""

from __future__ import annotations

import json
import os
import re
import threading

import flet as ft
import requests

import theme
from logic.notification_service import NotificationService
from logic.weather_notifier import WeatherNotifier
from api_client import ApiWeatherClient
from models import Weather
from ui.dashboard_pages.dashboard_view import DashboardView
from ui.conexion_pages.setup_view import SetupResult, SetupView

def _load_api_base() -> str:
    """Determines the API URL without hardcoding it in the source.

    Priority order:
      1. ``WEATHER_API_BASE`` environment variable (convenient for PC development);
      2. ``api_base`` key from ``config.json`` file located next to this script
         (embedded in the APK at build time, ignored by git);
      3. ``http://localhost:8000`` as a fallback.

    The ``config.json`` file is intentionally outside the repository: copy
    ``config.example.json`` and provide the actual API address.
    """
    env = os.getenv("WEATHER_API_BASE")
    if env:
        return env
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        with open(config_path, encoding="utf-8") as fh:
            value = json.load(fh).get("api_base")
            if value:
                return value
    except (OSError, ValueError):
        pass
    return "http://localhost:8000"


API_BASE = _load_api_base()


class WeatherApp:
    """Main controller: chains setup → dashboard and manages Kafka.

    Keeps the last measurement to compare with each new value and
    trigger change notifications. All layout is delegated to
    :class:`SetupView` then :class:`DashboardView`.
    """

    def __init__(self, page: ft.Page) -> None:
        """Configures the Flet page and displays the initial input screen."""
        self.page = page
        self.prev_weather: Weather | None = None
        self.dashboard: DashboardView | None = None
        self.client: ApiWeatherClient | None = None
        self.notifications = NotificationService(page)
        # État de l'écran courant, pour pouvoir le reconstruire lors d'un
        # changement de langue. ``None`` tant que rien n'est affiché.
        self._screen: str | None = None
        self._screen_args: tuple = ()
        self._configure_page()
        self._show_setup()

    def _configure_page(self) -> None:
        """Applies global page settings (title, background, theme)."""
        self.page.title = "Météo Agri"
        self.page.bgcolor = theme.BG
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT

    def _show_setup(self) -> None:
        """Displays the configuration screen and disables global scrolling."""
        self._screen = "setup"
        self._screen_args = ()
        self.page.scroll = None
        setup = SetupView(
            on_submit=self._on_setup_submitted,
            on_language_change=self._rebuild_current,
        )
        self.page.controls.clear()
        self.page.add(setup.build())
        self.page.update()

    def _on_setup_submitted(self, result: SetupResult) -> None:
        """Callback from :class:`SetupView`: registers the location then switches to dashboard."""
        topic = re.sub(r"[^A-Za-z0-9_.\-]", "_", result.city.lower())
        self._register_location(result.city)
        self._show_dashboard(result.city, result.profile, topic)
        self._start_client(topic)

    def _show_dashboard(self, city: str, profile: str, topic: str) -> None:
        """Instantiates the dashboard, replaces controls and enables scrolling."""
        self._screen = "dashboard"
        self._screen_args = (city, profile, topic)
        self.dashboard = DashboardView(
            city,
            profile,
            topic,
            notification_service=self.notifications,
            on_settings_save=self._on_settings_save,
            on_language_change=self._rebuild_current,
        )
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.controls.clear()
        self.page.add(self.dashboard.build())
        self.page.update()

    def _rebuild_current(self) -> None:
        """Reconstruit l'écran courant dans la langue active.

        Appelé après un changement de langue depuis le sélecteur. Sur le
        dashboard, réapplique la dernière mesure connue (``prev_weather``) pour
        ne pas perdre l'affichage en attendant le prochain relevé. Le client
        d'API n'est pas redémarré : seule l'interface est reconstruite.
        """
        if self._screen == "setup":
            self._show_setup()
        elif self._screen == "dashboard":
            city, profile, topic = self._screen_args
            self._show_dashboard(city, profile, topic)
            if self.dashboard is not None and self.prev_weather is not None:
                self.dashboard.update_weather(self.prev_weather)
                self.page.update()

    def _on_settings_save(self, city: str, profile: str) -> None:
        """Applies new settings when location changes.

        Registers the new location with the API, updates the header, clears
        the old location's displayed data (``reset_data``) then restarts the API
        client on the new topic — which immediately triggers a request to
        fetch the correct data.
        """
        topic = re.sub(r"[^A-Za-z0-9_.\-]", "_", city.lower())
        self._screen_args = (city, profile, topic)
        self._register_location(city)
        self.prev_weather = None
        if self.dashboard is not None:
            self.dashboard.header.update_info(city, profile, topic)
            self.dashboard.reset_data()
            self.page.update()
        self._start_client(topic)

    def _start_client(self, topic: str) -> None:
        """Stops any running client and starts a new API client for the requested topic."""
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
        """Requests the API to register the location (idempotent add) without blocking the UI.

        The HTTP call is made in a daemon thread and any error is ignored:
        location registration must never prevent the user from accessing
        the dashboard if the API is temporarily unavailable.
        """

        def _post() -> None:
            try:
                requests.post(
                    f"{API_BASE}/locations", json={"name": city}, timeout=10
                )
            except requests.RequestException:
                pass

        threading.Thread(target=_post, daemon=True).start()

    # ----- callbacks (executed in the API client thread) -----

    def _dispatch_ui(self, apply) -> None:
        """Runs a UI mutation on Flet's event loop thread.

        The API client callbacks run in a background polling thread. In Flet
        0.85 a ``page.update()`` issued from another thread enqueues the patch
        but never wakes the loop's send task, so the client is never
        refreshed. ``page.run_task`` marshals the work onto the loop thread
        (via ``asyncio.run_coroutine_threadsafe``), which makes both the
        control mutations and the ``page.update()`` take effect.
        """

        async def _runner() -> None:
            apply()

        try:
            self.page.run_task(_runner)
        except Exception:
            # No active session/loop yet (e.g. shutting down): drop silently.
            pass

    def _on_status(self, text: str) -> None:
        """Relays a Kafka status message to the dashboard header."""
        if self.dashboard is None:
            return

        def apply() -> None:
            self.dashboard.set_status(text)
            self.page.update()

        self._dispatch_ui(apply)

    def _on_new_weather(self, w: Weather) -> None:
        """Updates the dashboard and emits change notifications.

        Alert messages are delegated to :class:`NotificationService`, which
        only emits a notification (Android system or fallback SnackBar) if
        the user has enabled them in the Alerts tab. Polling runs in
        a daemon thread: alerts are thus evaluated continuously, regardless of
        which page is displayed.
        """
        if self.dashboard is None:
            return

        # Pure logic (no UI access) can stay on the polling thread.
        messages = WeatherNotifier.change_notifications(self.prev_weather, w)
        self.prev_weather = w

        def apply() -> None:
            self.dashboard.update_weather(w)
            for msg in messages:
                self.notifications.notify("Météo Agri", msg)
            self.page.update()

        self._dispatch_ui(apply)

    @staticmethod
    def main(page: ft.Page) -> None:
        """Entry point called by ``ft.run`` for each user session."""
        WeatherApp(page)


if __name__ == "__main__":
    ft.run(WeatherApp.main)
