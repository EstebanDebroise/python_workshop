"""Client HTTP interrogeant l'API Météo Agri (intermédiaire vers Kafka).

Remplace l'accès direct à Kafka : au lieu de consommer un flux, l'application
interroge périodiquement l'API REST. L'interface (callbacks ``on_weather`` /
``on_status``, méthodes :meth:`start` / :meth:`stop`) est volontairement
identique à celle de l'ancien ``WeatherConsumer`` pour que l'orchestrateur n'ait
quasiment pas à changer.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

import requests

from models import Weather


class ApiWeatherClient:
    """Interroge périodiquement l'API pour récupérer la dernière mesure d'un topic.

    Tourne dans un thread daemon dédié et relaie chaque nouvelle mesure via
    ``on_weather`` et les changements d'état via ``on_status``. La classe ne
    dépend ni de Flet ni de Kafka : elle ne connaît que l'API HTTP.
    """

    def __init__(
        self,
        topic: str,
        api_base: str,
        on_weather: Callable[[Weather], None],
        on_status: Callable[[str], None],
        interval_s: float = 10.0,
        timeout_s: float = 10.0,
    ) -> None:
        """Mémorise les paramètres ; le polling démarre à :meth:`start`.

        Args:
            topic (str): Topic à interroger (ville normalisée).
            api_base (str): URL de base de l'API (ex. ``"http://localhost:8000"``).
            on_weather (Callable[[Weather], None]): Appelé pour chaque mesure
                nouvelle (offset différent du précédent).
            on_status (Callable[[str], None]): Appelé pour informer l'UI de l'état
                (connexion, attente de données, erreur).
            interval_s (float): Intervalle entre deux interrogations, en secondes.
            timeout_s (float): Délai maximal d'une requête HTTP, en secondes.

        Returns:
            None
        """
        self.topic = topic
        self.api_base = api_base.rstrip("/")
        self.on_weather = on_weather
        self.on_status = on_status
        self.interval_s = interval_s
        self.timeout_s = timeout_s
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_offset: Optional[int] = None

    def start(self) -> None:
        """Démarre le thread daemon qui interroge l'API en boucle."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Demande l'arrêt de la boucle de polling."""
        self._stop.set()

    def _run(self) -> None:
        """Boucle de polling : interroge l'API puis attend l'intervalle."""
        self.on_status(f"Connexion à l'API pour « {self.topic} »…")
        while not self._stop.is_set():
            self._poll_once()
            # ``wait`` permet un arrêt réactif sans attendre la fin de l'intervalle.
            self._stop.wait(self.interval_s)

    def _poll_once(self) -> None:
        """Effectue une interrogation et relaie le résultat via les callbacks."""
        try:
            resp = requests.get(
                f"{self.api_base}/weather/{self.topic}", timeout=self.timeout_s
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            self.on_status(f"API injoignable : {exc}")
            return

        status = data.get("status")
        if status == "ok" and data.get("message"):
            offset = data.get("offset")
            if offset != self._last_offset:
                self._last_offset = offset
                try:
                    self.on_weather(Weather.from_message(data["message"]))
                except Exception:
                    pass
            self.on_status(f"Flux actif via API · offset {offset}")
        elif status == "empty":
            self.on_status(f"En attente de données sur « {self.topic} »…")
        else:
            self.on_status(f"Erreur API : {data.get('detail') or 'inconnue'}")
