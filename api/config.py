from __future__ import annotations

import os
from pathlib import Path

KAFKA_BOOTSTRAP: str = os.getenv("KAFKA_BROKER")

# Timeout lecture for Kafka consumer in milliseconds. Default is 3000 ms.
KAFKA_READ_TIMEOUT_MS: int = int(os.getenv("KAFKA_READ_TIMEOUT_MS"))

# Database path for SQLite. This can be set via the environment variable API_DB_PATH.
DB_PATH: str = os.getenv("API_DB_PATH")
