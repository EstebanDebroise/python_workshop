"""Lecteur Kafka à la demande : récupère la dernière mesure d'un topic.

Contrairement au consumer en flux continu de l'application d'origine, ce lecteur
est interrogé ponctuellement par l'API. À chaque appel il se positionne sur le
dernier offset du topic, renvoie cette mesure, et indique si elle est plus récente
que la précédente déjà servie (sinon il s'agit de la donnée du précédent offset).
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any, Optional

from kafka import KafkaConsumer, TopicPartition
from kafka.errors import KafkaError

from api import config


class KafkaReader:
    """Lecture ponctuelle du dernier message d'un topic Kafka.

    Une nouvelle connexion ``KafkaConsumer`` est créée à chaque lecture (les
    consumers ne sont pas sûrs vis-à-vis des threads et les topics changent selon
    les lieux des utilisateurs). Un dictionnaire interne mémorise, par topic, le
    timestamp de la dernière mesure servie afin de calculer le drapeau ``is_new``.
    """

    def __init__(
        self,
        bootstrap: str = config.KAFKA_BOOTSTRAP,
        timeout_ms: int = config.KAFKA_READ_TIMEOUT_MS,
    ) -> None:
        """Mémorise les paramètres de connexion ; aucune connexion n'est ouverte ici.

        Args:
            bootstrap (str): Adresse ``host:port`` du broker Kafka.
            timeout_ms (int): Budget temps maximal d'une lecture (connexion + poll).

        Returns:
            None
        """
        self._bootstrap = bootstrap
        self._timeout_ms = timeout_ms
        self._lock = threading.Lock()
        self._last_ts: dict[str, int] = {}

    def read_latest(self, topic: str) -> dict[str, Any]:
        """Lit la dernière mesure disponible sur ``topic``.

        Se positionne sur le dernier offset de chaque partition, récupère le
        message correspondant et conserve le plus récent (par timestamp Kafka).
        S'il n'y a aucun message, renvoie un statut ``"empty"``. S'il n'y a rien
        de nouveau depuis la dernière lecture, renvoie tout de même la mesure du
        précédent offset avec ``is_new=False``.

        Args:
            topic (str): Nom du topic Kafka à interroger.

        Returns:
            dict[str, Any]: Dictionnaire avec les clés ``status`` (``"ok"`` /
                ``"empty"`` / ``"error"``), ``is_new`` (bool), ``offset``
                (int | None), ``message`` (dict | None) et ``detail`` (str | None).
                Directement dépliable dans un :class:`~api.schemas.WeatherResponse`.
        """
        consumer: Optional[KafkaConsumer] = None
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=self._bootstrap,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                enable_auto_commit=False,
                group_id=None,
            )
            partitions = consumer.partitions_for_topic(topic)
            if not partitions:
                return self._empty("Topic inconnu ou aucune donnée publiée.")

            tps = [TopicPartition(topic, p) for p in partitions]
            consumer.assign(tps)
            end_offsets = consumer.end_offsets(tps)
            begin_offsets = consumer.beginning_offsets(tps)

            seeked = [tp for tp in tps if end_offsets[tp] > begin_offsets[tp]]
            if not seeked:
                return self._empty("Le topic existe mais ne contient aucune mesure.")
            for tp in seeked:
                consumer.seek(tp, end_offsets[tp] - 1)

            last_record = self._poll_last_record(consumer, seeked)
            if last_record is None:
                return self._empty("Aucune mesure récupérée dans le délai imparti.")

            with self._lock:
                previous_ts = self._last_ts.get(topic)
                is_new = previous_ts is None or last_record.timestamp > previous_ts
                self._last_ts[topic] = last_record.timestamp

            return {
                "status": "ok",
                "is_new": is_new,
                "offset": last_record.offset,
                "message": last_record.value,
                "detail": None,
            }
        except KafkaError as exc:
            return {
                "status": "error",
                "is_new": False,
                "offset": None,
                "message": None,
                "detail": f"Erreur Kafka : {exc}",
            }
        finally:
            if consumer is not None:
                try:
                    consumer.close()
                except Exception:
                    pass

    def _poll_last_record(self, consumer: KafkaConsumer, seeked: list[TopicPartition]):
        """Interroge Kafka jusqu'à récupérer le dernier message de chaque partition.

        Boucle sur ``poll`` (par petits paquets) jusqu'à obtenir un message pour
        chaque partition positionnée ou jusqu'à expiration du délai, puis renvoie
        le message au timestamp le plus récent.

        Args:
            consumer (KafkaConsumer): Consumer déjà assigné et positionné.
            seeked (list[TopicPartition]): Partitions contenant au moins une mesure.

        Returns:
            Le ``ConsumerRecord`` le plus récent, ou ``None`` si rien n'a été lu.
        """
        deadline = time.monotonic() + self._timeout_ms / 1000.0
        latest_per_partition: dict[TopicPartition, Any] = {}
        while time.monotonic() < deadline and len(latest_per_partition) < len(seeked):
            batch = consumer.poll(timeout_ms=200, max_records=500)
            for tp, records in batch.items():
                if records:
                    latest_per_partition[tp] = records[-1]

        if not latest_per_partition:
            return None
        return max(latest_per_partition.values(), key=lambda r: r.timestamp)

    @staticmethod
    def _empty(detail: str) -> dict[str, Any]:
        """Construit une réponse de statut ``empty`` avec le détail fourni."""
        return {
            "status": "empty",
            "is_new": False,
            "offset": None,
            "message": None,
            "detail": detail,
        }
