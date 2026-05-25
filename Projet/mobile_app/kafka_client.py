"""Encapsulation du consumer Kafka dans un thread d'arrière-plan."""

from __future__ import annotations

import json
import threading
from typing import Callable, Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from models import Weather


class WeatherConsumer:
    """Consumer Kafka non bloquant pour les messages météo.

    Tourne dans un thread daemon dédié et délègue le traitement de
    chaque message à deux callbacks (``on_weather`` / ``on_status``)
    fournis par l'appelant, afin que la classe ne dépende ni de Flet
    ni d'une interface graphique.
    """

    def __init__(
        self,
        topic: str,
        bootstrap: str,
        on_weather: Callable[[Weather], None],
        on_status: Callable[[str], None],
    ) -> None:
        """Mémorise les paramètres ; la connexion est différée à :meth:`start`.

        ``on_weather`` est appelé pour chaque message valide et
        ``on_status`` pour informer l'UI de l'état (connexion réussie,
        erreur). Les deux sont invoqués depuis le thread consumer.
        """
        self.topic = topic
        self.bootstrap = bootstrap
        self.on_weather = on_weather
        self.on_status = on_status
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._consumer: Optional[KafkaConsumer] = None

    def start(self) -> None:
        """Démarre le thread daemon qui consomme le topic en boucle."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Demande l'arrêt et ferme proprement le consumer sous-jacent."""
        self._stop.set()
        if self._consumer is not None:
            try:
                self._consumer.close()
            except Exception:
                pass

    def _run(self) -> None:
        """Boucle interne du thread : connexion puis itération sur les messages.

        En cas d'échec de connexion, signale l'erreur via ``on_status``
        et se termine. Les messages mal formés sont ignorés silencieusement
        pour éviter d'interrompre le flux.
        """
        try:
            self._consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=True,
                group_id=f"flet-{self.topic}",
            )
        except KafkaError as exc:
            self.on_status(f"Erreur Kafka : {exc}")
            return

        self.on_status(f"Flux Kafka actif · topic « {self.topic} »")

        for msg in self._consumer:
            if self._stop.is_set():
                break
            try:
                self.on_weather(Weather.from_message(msg.value))
            except Exception:
                continue
