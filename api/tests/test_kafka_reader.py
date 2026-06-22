"""Tests pour le module kafka_reader."""

from unittest.mock import MagicMock, patch

import pytest
from kafka.errors import KafkaError

from api.kafka_reader import KafkaReader


class TestKafkaReader:
    """Tests pour la classe KafkaReader."""

    def test_initialization(self):
        """Vérifie que l'initialisation stocke les paramètres."""
        reader = KafkaReader(bootstrap="kafka:9092", timeout_ms=5000)
        assert reader._bootstrap == "kafka:9092"
        assert reader._timeout_ms == 5000

    def test_initialization_with_defaults(self):
        """Vérifie que l'initialisation utilise les defaults."""
        reader = KafkaReader()
        assert reader._bootstrap is not None
        assert reader._timeout_ms > 0

    def test_initialization_creates_lock(self):
        """Vérifie que l'initialisation crée un lock."""
        reader = KafkaReader()
        assert reader._lock is not None

    def test_initialization_empty_last_ts(self):
        """Vérifie que _last_ts commence vide."""
        reader = KafkaReader()
        assert reader._last_ts == {}

    @patch("api.kafka_reader.KafkaConsumer")
    def test_read_latest_ok_status(self, mock_consumer_class):
        """Teste read_latest avec un statut ok."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        # Configure les mocks
        from kafka import TopicPartition
        tp = TopicPartition("paris", 0)
        mock_consumer.partitions_for_topic.return_value = {0}
        mock_consumer.end_offsets.return_value = {tp: 100}
        mock_consumer.beginning_offsets.return_value = {tp: 0}

        # Mock le record
        mock_record = MagicMock()
        mock_record.timestamp = 1000
        mock_record.offset = 100
        mock_record.value = {"temp": 20}

        reader = KafkaReader()
        reader._poll_last_record = lambda *args, **kwargs: mock_record

        result = reader.read_latest("paris")

        assert result["status"] == "ok"
        assert result["is_new"] is True
        assert result["offset"] == 100
        assert result["message"] == {"temp": 20}
        mock_consumer.close.assert_called()

    @patch("api.kafka_reader.KafkaConsumer")
    def test_read_latest_empty_topic(self, mock_consumer_class):
        """Teste read_latest avec un topic sans partitions."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer
        mock_consumer.partitions_for_topic.return_value = None

        reader = KafkaReader()
        result = reader.read_latest("unknown_topic")

        assert result["status"] == "empty"
        assert result["is_new"] is False
        assert result["offset"] is None
        assert result["message"] is None

    @patch("api.kafka_reader.KafkaConsumer")
    def test_read_latest_no_data_in_partitions(self, mock_consumer_class):
        """Teste read_latest quand les partitions n'ont pas de données."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        from kafka import TopicPartition
        tp = TopicPartition("paris", 0)
        mock_consumer.partitions_for_topic.return_value = {0}
        mock_consumer.end_offsets.return_value = {tp: 0}
        mock_consumer.beginning_offsets.return_value = {tp: 0}

        reader = KafkaReader()
        result = reader.read_latest("paris")

        assert result["status"] == "empty"

    @patch("api.kafka_reader.KafkaConsumer")
    def test_read_latest_timeout_no_record(self, mock_consumer_class):
        """Teste read_latest quand le timeout expire sans records."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        from kafka import TopicPartition
        tp = TopicPartition("paris", 0)
        mock_consumer.partitions_for_topic.return_value = {0}
        mock_consumer.end_offsets.return_value = {tp: 100}
        mock_consumer.beginning_offsets.return_value = {tp: 0}

        reader = KafkaReader()
        reader._poll_last_record = lambda *args, **kwargs: None

        result = reader.read_latest("paris")

        assert result["status"] == "empty"
        assert "délai" in result["detail"].lower()
        mock_consumer.close.assert_called()

    @patch("api.kafka_reader.KafkaConsumer")
    def test_read_latest_kafka_error(self, mock_consumer_class):
        """Teste read_latest avec une exception Kafka."""
        mock_consumer_class.side_effect = KafkaError("Connexion refusée")

        reader = KafkaReader()
        result = reader.read_latest("paris")

        assert result["status"] == "error"
        assert result["is_new"] is False
        assert result["offset"] is None
        assert result["message"] is None
        assert "Kafka" in result["detail"]

    @patch("api.kafka_reader.KafkaConsumer")
    def test_read_latest_closes_consumer_on_success(self, mock_consumer_class):
        """Vérifie que le consumer est fermé après un succès."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        from kafka import TopicPartition
        tp = TopicPartition("paris", 0)
        mock_consumer.partitions_for_topic.return_value = {0}
        mock_consumer.end_offsets.return_value = {tp: 100}
        mock_consumer.beginning_offsets.return_value = {tp: 0}

        mock_record = MagicMock()
        mock_record.timestamp = 1000
        mock_record.offset = 100
        mock_record.value = {}

        reader = KafkaReader()
        reader._poll_last_record = lambda *args, **kwargs: mock_record
        reader.read_latest("paris")

        mock_consumer.close.assert_called()

    @patch("api.kafka_reader.KafkaConsumer")
    def test_read_latest_closes_consumer_on_error(self, mock_consumer_class):
        """Vérifie que le consumer est fermé après une erreur."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer
        mock_consumer.partitions_for_topic.side_effect = KafkaError("Erreur")

        reader = KafkaReader()
        reader.read_latest("paris")

        mock_consumer.close.assert_called()

    @patch("api.kafka_reader.KafkaConsumer")
    def test_is_new_flag_first_read(self, mock_consumer_class):
        """Vérifie que is_new=True au premier appel."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        from kafka import TopicPartition
        tp = TopicPartition("topic1", 0)
        mock_consumer.partitions_for_topic.return_value = {0}
        mock_consumer.end_offsets.return_value = {tp: 100}
        mock_consumer.beginning_offsets.return_value = {tp: 0}

        mock_record = MagicMock()
        mock_record.timestamp = 1000
        mock_record.offset = 100
        mock_record.value = {}

        reader = KafkaReader()
        reader._poll_last_record = lambda *args, **kwargs: mock_record
        result = reader.read_latest("topic1")

        assert result["is_new"] is True

    @patch("api.kafka_reader.KafkaConsumer")
    def test_is_new_flag_subsequent_read_newer(self, mock_consumer_class):
        """Vérifie que is_new=True si le timestamp est plus récent."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        from kafka import TopicPartition
        tp = TopicPartition("topic1", 0)
        mock_consumer.partitions_for_topic.return_value = {0}
        mock_consumer.end_offsets.return_value = {tp: 100}
        mock_consumer.beginning_offsets.return_value = {tp: 0}

        reader = KafkaReader()

        # Premier appel
        mock_record1 = MagicMock()
        mock_record1.timestamp = 1000
        mock_record1.offset = 100
        mock_record1.value = {}

        reader._poll_last_record = lambda *args, **kwargs: mock_record1
        reader.read_latest("topic1")

        # Deuxième appel avec timestamp plus récent
        mock_record2 = MagicMock()
        mock_record2.timestamp = 2000
        mock_record2.offset = 101
        mock_record2.value = {}

        reader._poll_last_record = lambda *args, **kwargs: mock_record2
        result = reader.read_latest("topic1")

        assert result["is_new"] is True

    @patch("api.kafka_reader.KafkaConsumer")
    def test_is_new_flag_subsequent_read_same(self, mock_consumer_class):
        """Vérifie que is_new=False si le timestamp est identique."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        from kafka import TopicPartition
        tp = TopicPartition("topic1", 0)
        mock_consumer.partitions_for_topic.return_value = {0}
        mock_consumer.end_offsets.return_value = {tp: 100}
        mock_consumer.beginning_offsets.return_value = {tp: 0}

        reader = KafkaReader()

        mock_record1 = MagicMock()
        mock_record1.timestamp = 1000
        mock_record1.offset = 100
        mock_record1.value = {}

        reader._poll_last_record = lambda *args, **kwargs: mock_record1
        reader.read_latest("topic1")

        mock_record2 = MagicMock()
        mock_record2.timestamp = 1000
        mock_record2.offset = 100
        mock_record2.value = {}

        reader._poll_last_record = lambda *args, **kwargs: mock_record2
        result = reader.read_latest("topic1")

        assert result["is_new"] is False

    def test_empty_response_format(self):
        """Vérifie le format d'une réponse empty."""
        reader = KafkaReader()
        result = reader._empty("Test detail")

        assert result["status"] == "empty"
        assert result["is_new"] is False
        assert result["offset"] is None
        assert result["message"] is None
        assert result["detail"] == "Test detail"

    @patch("api.kafka_reader.KafkaConsumer")
    def test_read_latest_consumer_close_error_handled(self, mock_consumer_class):
        """Vérifie que les erreurs lors de la fermeture du consumer sont gérées."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer
        mock_consumer.close.side_effect = Exception("Erreur close")

        from kafka import TopicPartition
        tp = TopicPartition("paris", 0)
        mock_consumer.partitions_for_topic.return_value = {0}
        mock_consumer.end_offsets.return_value = {tp: 100}
        mock_consumer.beginning_offsets.return_value = {tp: 0}

        mock_record = MagicMock()
        mock_record.timestamp = 1000
        mock_record.offset = 100
        mock_record.value = {}

        reader = KafkaReader()
        reader._poll_last_record = lambda *args, **kwargs: mock_record

        # Ne doit pas lever d'exception
        result = reader.read_latest("paris")

        assert result["status"] == "ok"

    @patch("api.kafka_reader.KafkaConsumer")
    def test_thread_safety_with_lock(self, mock_consumer_class):
        """Vérifie que le lock est utilisé pour la sécurité des threads."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        from kafka import TopicPartition
        tp = TopicPartition("topic1", 0)
        mock_consumer.partitions_for_topic.return_value = {0}
        mock_consumer.end_offsets.return_value = {tp: 100}
        mock_consumer.beginning_offsets.return_value = {tp: 0}

        mock_record = MagicMock()
        mock_record.timestamp = 1000
        mock_record.offset = 100
        mock_record.value = {}

        reader = KafkaReader()
        reader._poll_last_record = lambda *args, **kwargs: mock_record
        result = reader.read_latest("topic1")

        # Vérifier que le dictionnaire a été mis à jour
        assert "topic1" in reader._last_ts
        assert reader._last_ts["topic1"] == 1000

    def test_poll_last_record_empty_dict(self):
        """Vérifie que _poll_last_record retourne None si pas de records."""
        reader = KafkaReader()
        mock_consumer = MagicMock()

        from kafka import TopicPartition
        tp = TopicPartition("test", 0)

        # Simule aucun record reçu
        latest = reader._poll_last_record(mock_consumer, [tp])

        assert latest is None

    def test_poll_last_record_returns_max_timestamp(self):
        """Vérifie que _poll_last_record retourne le record avec le plus grand timestamp."""
        reader = KafkaReader()

        record1 = MagicMock()
        record1.timestamp = 1000

        record2 = MagicMock()
        record2.timestamp = 2000

        from kafka import TopicPartition
        tp1 = TopicPartition("test", 0)
        tp2 = TopicPartition("test", 1)

        mock_consumer = MagicMock()
        # Poll retourne les records (simule 2 records reçus en un poll)
        mock_consumer.poll.return_value = {
            tp1: [record1],
            tp2: [record2]
        }

        latest = reader._poll_last_record(mock_consumer, [tp1, tp2])

        # Doit retourner le record avec le timestamp le plus élevé
        assert latest.timestamp == 2000
