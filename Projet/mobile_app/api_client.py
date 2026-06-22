from __future__ import annotations

import threading
from typing import Callable, Optional

import requests

import i18n
from models import Weather


class ApiWeatherClient:
    """Periodically queries the API to retrieve the latest measurement of a topic.

    Runs in a dedicated daemon thread and relays each new measurement via
    ``on_weather`` and state changes via ``on_status``. The class does not
    depend on Flet or Kafka: it only knows about HTTP API.
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
        """Stores parameters; polling starts at :meth:`start`.

        Args:
            topic (str): Topic to query (normalized city name).
            api_base (str): Base URL of the API (ex. ``"http://localhost:8000"``).
            on_weather (Callable[[Weather], None]): Called for each new measurement
                (offset different from previous).
            on_status (Callable[[str], None]): Called to inform the UI of state
                (connection, waiting for data, error).
            interval_s (float): Interval between two queries, in seconds.
            timeout_s (float): Maximum delay for an HTTP request, in seconds.

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
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        self.on_status(i18n.t("messages", "status_connecting", topic=self.topic))
        while not self._stop.is_set():
            self._poll_once()
            # ``wait`` allows reactive shutdown without waiting for the interval to complete.
            self._stop.wait(self.interval_s)

    def _poll_once(self) -> None:
        try:
            resp = requests.get(
                f"{self.api_base}/weather/{self.topic}", timeout=self.timeout_s
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            self.on_status(i18n.t("messages", "status_unreachable", error=exc))
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
            self.on_status(i18n.t("messages", "status_active", offset=offset))
        elif status == "empty":
            self.on_status(i18n.t("messages", "status_waiting", topic=self.topic))
        else:
            self.on_status(i18n.t("messages", "status_error", detail=data.get("detail") or "unknown"))
