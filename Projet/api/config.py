"""Configuration de l'API : variables d'environnement et chemins de fichiers."""

from __future__ import annotations

import os
from pathlib import Path

# Adresse du broker Kafka. On accepte les deux noms de variable utilisés
# ailleurs dans le projet (KAFKA_BOOTSTRAP côté app, KAFKA_BROKER côté producer).
KAFKA_BOOTSTRAP: str = os.getenv(
    "KAFKA_BOOTSTRAP", os.getenv("KAFKA_BROKER", "localhost:9092")
)

# Délai maximal (en millisecondes) accordé à une lecture Kafka à la demande.
KAFKA_READ_TIMEOUT_MS: int = int(os.getenv("KAFKA_READ_TIMEOUT_MS", "3000"))

# Chemin du fichier SQLite des lieux. Par défaut, dans le dossier api/.
_DEFAULT_DB_PATH = Path(__file__).resolve().parent / "locations.db"
DB_PATH: str = os.getenv("API_DB_PATH", str(_DEFAULT_DB_PATH))
