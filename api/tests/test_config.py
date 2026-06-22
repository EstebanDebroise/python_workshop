import os

from api import config


def test_kafka_bootstrap_default():
    """Verify that KAFKA_BOOTSTRAP has a default value."""
    assert config.KAFKA_BOOTSTRAP is not None
    assert ":" in config.KAFKA_BOOTSTRAP


def test_kafka_bootstrap_from_env():
    """Verify that KAFKA_BOOTSTRAP can be set via environment variables."""
    original = config.KAFKA_BOOTSTRAP
    try:
        os.environ["KAFKA_BOOTSTRAP"] = "kafka.test:9093"
        import importlib
        importlib.reload(config)
        assert config.KAFKA_BOOTSTRAP == "kafka.test:9093"
    finally:
        os.environ.pop("KAFKA_BOOTSTRAP", None)
        importlib.reload(config)


def test_kafka_bootstrap_fallback_to_broker():
    """Verify that KAFKA_BOOTSTRAP falls back to KAFKA_BROKER."""
    try:
        os.environ.pop("KAFKA_BOOTSTRAP", None)
        os.environ["KAFKA_BROKER"] = "broker.test:9094"
        import importlib
        importlib.reload(config)
        assert config.KAFKA_BOOTSTRAP == "broker.test:9094"
    finally:
        os.environ.pop("KAFKA_BROKER", None)
        import importlib
        importlib.reload(config)


def test_kafka_read_timeout_ms_default():
    """Verify that KAFKA_READ_TIMEOUT_MS has a default value."""
    assert isinstance(config.KAFKA_READ_TIMEOUT_MS, int)
    assert config.KAFKA_READ_TIMEOUT_MS > 0


def test_kafka_read_timeout_ms_from_env():
    """Verify that KAFKA_READ_TIMEOUT_MS can be set via environment variables."""
    try:
        os.environ["KAFKA_READ_TIMEOUT_MS"] = "5000"
        import importlib
        importlib.reload(config)
        assert config.KAFKA_READ_TIMEOUT_MS == 5000
    finally:
        os.environ.pop("KAFKA_READ_TIMEOUT_MS", None)
        import importlib
        importlib.reload(config)


def test_db_path_default():
    """Verify that DB_PATH has a default value."""
    assert config.DB_PATH is not None
    assert config.DB_PATH.endswith(".db")


def test_db_path_from_env():
    """Verify that DB_PATH can be set via environment variables."""
    try:
        os.environ["API_DB_PATH"] = "/tmp/custom.db"
        import importlib
        importlib.reload(config)
        assert config.DB_PATH == "/tmp/custom.db"
    finally:
        os.environ.pop("API_DB_PATH", None)
        import importlib
        importlib.reload(config)
