"""Dashboard view: orchestrator assembling header, 4 sections, and navigation."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

import theme
from i18n import t
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
    """Main dashboard view orchestrator.

    Aggregates and coordinates five child components:
    - :class:`HeaderSection`: top banner (city, profile, Kafka status);
    - :class:`CurrentWeatherSection`: current weather and history;
    - :class:`ThiSection`: thermal stress gauge;
    - :class:`PastureSection`: pasture comfort;
    - :class:`TreatmentSection`: spraying time slots;
    - :class:`BottomNavSection`: bottom navigation bar.

    Manages navigation between dashboard, Alerts page, and Settings page
    via the bottom bar. Exposes :meth:`update_weather` and :meth:`set_status`
    for real-time updates.
    """

    def __init__(
        self,
        city: str,
        profile: str,
        topic: str,
        notification_service: NotificationService,
        on_settings_save: Optional[Callable[[str, str], None]] = None,
        on_language_change: Optional[Callable[[], None]] = None,
    ) -> None:
        """Instantiate each sub-section and prepare the swappable content area.

        Args:
            city (str): City name displayed in the header.
            profile (str): User profile displayed as header subtitle.
            topic (str): Kafka topic name for the initial status line.
            notification_service (NotificationService): Shared service controlling
                notification activation and delivery, provided to the Alerts page.
            on_settings_save (Callable[[str, str], None] | None): Optional callback
                called with ``(city, profile)`` when the user saves their settings.
                Allows the parent orchestrator to restart the Kafka consumer.

        Returns:
            None — :meth:`build` must be called to get the Flet control.
        """
        self._current_city = city
        self._current_profile = profile
        self._notification_service = notification_service
        self._on_settings_save_cb = on_settings_save
        self._on_language_change_cb = on_language_change

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
                UIComponents.section_label(t("dashboard_view", "current_weather")),
                self.current.build(),
                UIComponents.section_label(t("dashboard_view", "thermal_stress")),
                self.thi.build(),
                UIComponents.section_label(t("dashboard_view", "pasture_comfort")),
                self.pasture.build(),
                UIComponents.section_label(t("dashboard_view", "treatment_window")),
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
        settings = SettingsView(
            self._current_city,
            self._current_profile,
            self._on_settings_saved,
            on_language_change=self._on_language_change_cb,
        )
        self._body.content = settings.build()
        self._body.update()

    def _on_settings_saved(self, city: str, profile: str) -> None:
        self._current_city = city
        self._current_profile = profile
        if self._on_settings_save_cb:
            self._on_settings_save_cb(city, profile)

    def build(self) -> ft.Control:
        """Assemble the header, swappable content area, and navigation bar.

        Args:
            None.

        Returns:
            ft.Control: Complete Flet ``Column`` (header + body + nav) ready
                to be added to the page.
        """
        return ft.Column(
            [self.header.build(), self._body, self._bottom_nav.build()],
            spacing=0,
            expand=True,
        )

    def update_weather(self, w: Weather) -> None:
        """Propagate a new weather measurement to each of the four child sections.

        Args:
            w (Weather): The new weather measurement received from the Kafka consumer.

        Returns:
            None
        """
        self.current.update(w)
        self.thi.update(w)
        self.pasture.update(w)
        self.treatment.update(w)

    def reset_data(self) -> None:
        """Reset the four sections to their waiting state.

        Clear accumulated data (history, alerts, slots, etc.) to avoid displaying
        measurements from the old location after a location change. The actual
        screen refresh is triggered by the caller via ``page.update()``.

        Args:
            None.

        Returns:
            None
        """
        self.current.reset()
        self.thi.reset()
        self.pasture.reset()
        self.treatment.reset()

    def set_status(self, text: str) -> None:
        """Relay a Kafka connection status message to the dashboard header.

        Args:
            text (str): Status message to display in the top banner.

        Returns:
            None
        """
        self.header.set_status(text)
