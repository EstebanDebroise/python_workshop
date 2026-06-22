"""Notification service: activation preference + device delivery.

Centralizes all notification logic in the application:

- remembers if the user has **enabled** notifications (persistent preference
  via ``page.client_storage``);
- exposes :meth:`notify` which, when notifications are enabled, sends a real
  Android system notification (via ``plyer``) and, if not available, falls back
  to an in-app SnackBar (desktop/web/package without ``plyer``).

The business layer (``WeatherNotifier``) and orchestrator (``main.py``) only
know this interface: they call :meth:`notify` without worrying about the
platform or availability of ``plyer``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import flet as ft

try:  # ``plyer`` is only present on mobile device/package.
    from plyer import notification as _plyer_notification
except Exception:  # pragma: no cover - depends on the execution environment
    _plyer_notification = None


class NotificationService:
    """Single source of truth for "notifications enabled" state and delivery.

    A single instance is created by the orchestrator and shared between the
    Alerts page (:class:`NotificationsView`, which modifies the state) and the
    polling loop (which calls :meth:`notify` for each detected alert).
    """

    STORAGE_KEY = "notifications_enabled"
    APP_NAME = "Météo Agri"

    def __init__(self, page: ft.Page, enabled_default: bool = False) -> None:
        """Store the page and reload the persisted preference.

        Args:
            page (ft.Page): Flet page, used for the fallback SnackBar.
            enabled_default (bool): Default value if no preference has been
                recorded yet. ``False``: the user must explicitly enable
                notifications from the Alerts tab.
        """
        self.page = page
        self._enabled = self._load(enabled_default)

    @staticmethod
    def _pref_file() -> Path:
        """Path to the preference file in the application data folder.

        ``flet run`` exports ``FLET_APP_STORAGE_DATA`` to a writable directory
        (including on Android). In its absence (tests, direct execution), falls back
        to the user's home directory.
        """
        base = os.getenv("FLET_APP_STORAGE_DATA") or os.path.expanduser("~")
        return Path(base) / "meteo_agri_prefs.json"

    # ----- persistent preference -----

    @property
    def enabled(self) -> bool:
        """Indicate if the user has enabled notifications."""
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        """Update the state and persist it for future sessions.

        Args:
            value (bool): New desired state (``True`` = notifications active).
        """
        self._enabled = bool(value)
        try:
            self._pref_file().write_text(
                json.dumps({self.STORAGE_KEY: self._enabled})
            )
        except Exception:
            # Lack of writable storage (some web/test contexts) must never prevent
            # activation for the current session.
            pass

    def _load(self, default: bool) -> bool:
        try:
            data = json.loads(self._pref_file().read_text())
            stored = data.get(self.STORAGE_KEY)
        except Exception:
            stored = None
        return default if stored is None else bool(stored)

    # ----- delivery -----

    def notify(self, title: str, message: str) -> None:
        """Send a notification if enabled, otherwise do nothing.

        First tries a real system notification (Android via ``plyer``);
        if it fails or ``plyer`` is not available, falls back to an in-app SnackBar
        to maintain visible feedback on desktop and web.

        Args:
            title (str): Notification title (e.g. ``"Weather Agri"``).
            message (str): Notification body (the alert message).
        """
        if not self._enabled:
            return
        if not self._send_native(title, message):
            self._send_snackbar(message)

    def _send_native(self, title: str, message: str) -> bool:
        """Try a system notification via ``plyer``; return ``True`` if successful."""
        if _plyer_notification is None:
            return False
        try:
            _plyer_notification.notify(
                title=title,
                message=message,
                app_name=self.APP_NAME,
                timeout=10,
            )
            return True
        except Exception:
            return False

    def _send_snackbar(self, message: str) -> None:
        """Display a red SnackBar; silently ignore any Flet errors."""
        try:
            import theme

            snack = ft.SnackBar(ft.Text(message), bgcolor=theme.RED, open=True)
            self.page.overlay.append(snack)
            self.page.update()
        except Exception:
            pass
