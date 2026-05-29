"""Service de notifications : préférence d'activation + envoi sur l'appareil.

Centralise toute la logique de notification de l'application :

- mémorise si l'utilisateur a **activé** les notifications (préférence
  persistante via ``page.client_storage``) ;
- expose :meth:`notify` qui, lorsque les notifications sont activées, émet une
  vraie notification système Android (via ``plyer``) et, à défaut, une SnackBar
  in-app comme repli (bureau / web / paquet sans ``plyer``).

La couche métier (``WeatherNotifier``) et l'orchestrateur (``main.py``) ne
connaissent que cette interface : ils appellent :meth:`notify` sans se soucier
de la plateforme ni de la disponibilité de ``plyer``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import flet as ft

try:  # ``plyer`` n'est présent que sur l'appareil / le paquet mobile.
    from plyer import notification as _plyer_notification
except Exception:  # pragma: no cover - dépend de l'environnement d'exécution
    _plyer_notification = None


class NotificationService:
    """Source de vérité unique de l'état « notifications activées » et de l'envoi.

    Une seule instance est créée par l'orchestrateur et partagée entre la page
    Alertes (:class:`NotificationsView`, qui modifie l'état) et la boucle de
    polling (qui appelle :meth:`notify` à chaque alerte détectée).
    """

    STORAGE_KEY = "notifications_enabled"
    APP_NAME = "Météo Agri"

    def __init__(self, page: ft.Page, enabled_default: bool = False) -> None:
        """Mémorise la page et recharge la préférence persistée.

        Args:
            page (ft.Page): Page Flet, utilisée pour la SnackBar de repli.
            enabled_default (bool): Valeur par défaut si aucune préférence n'a
                encore été enregistrée. ``False`` : l'utilisateur doit activer
                explicitement les notifications depuis l'onglet Alertes.
        """
        self.page = page
        self._enabled = self._load(enabled_default)

    @staticmethod
    def _pref_file() -> Path:
        """Chemin du fichier de préférence dans le dossier de données de l'app.

        ``flet run`` exporte ``FLET_APP_STORAGE_DATA`` vers un répertoire
        inscriptible (y compris sur Android). En son absence (tests, exécution
        directe), on retombe sur le dossier personnel de l'utilisateur.
        """
        base = os.getenv("FLET_APP_STORAGE_DATA") or os.path.expanduser("~")
        return Path(base) / "meteo_agri_prefs.json"

    # ----- préférence persistante -----

    @property
    def enabled(self) -> bool:
        """Indique si l'utilisateur a activé les notifications."""
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        """Met à jour l'état et le persiste pour les prochaines sessions.

        Args:
            value (bool): Nouvel état souhaité (``True`` = notifications actives).
        """
        self._enabled = bool(value)
        try:
            self._pref_file().write_text(
                json.dumps({self.STORAGE_KEY: self._enabled})
            )
        except Exception:
            # L'absence de stockage inscriptible (certains contextes web/test) ne
            # doit jamais empêcher l'activation pour la session courante.
            pass

    def _load(self, default: bool) -> bool:
        try:
            data = json.loads(self._pref_file().read_text())
            stored = data.get(self.STORAGE_KEY)
        except Exception:
            stored = None
        return default if stored is None else bool(stored)

    # ----- envoi -----

    def notify(self, title: str, message: str) -> None:
        """Émet une notification si elles sont activées, sinon ne fait rien.

        Tente d'abord une vraie notification système (Android via ``plyer``) ;
        en cas d'échec ou d'absence de ``plyer``, retombe sur une SnackBar in-app
        afin de conserver un retour visible sur bureau et web.

        Args:
            title (str): Titre de la notification (ex. ``"Météo Agri"``).
            message (str): Corps de la notification (le message d'alerte).
        """
        if not self._enabled:
            return
        if not self._send_native(title, message):
            self._send_snackbar(message)

    def _send_native(self, title: str, message: str) -> bool:
        """Tente une notification système via ``plyer`` ; retourne ``True`` si OK."""
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
        """Affiche une SnackBar rouge ; ignore silencieusement toute erreur Flet."""
        try:
            import theme

            snack = ft.SnackBar(ft.Text(message), bgcolor=theme.RED, open=True)
            self.page.overlay.append(snack)
            self.page.update()
        except Exception:
            pass
