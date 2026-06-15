"""Base de données SQLite des lieux suivis par les utilisateurs."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from api.schemas import LocationOut

_SCHEMA = """
CREATE TABLE IF NOT EXISTS locations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    topic      TEXT    NOT NULL UNIQUE,
    country    TEXT,
    created_at TEXT    NOT NULL
);
"""


class LocationDB:
    """Dépôt SQLite pour la table des lieux.

    Encapsule toute la persistance des lieux. Chaque opération ouvre sa propre
    connexion afin d'être sûre vis-à-vis des threads (FastAPI exécute les routes
    synchrones dans un pool de threads). L'unicité est garantie par une contrainte
    ``UNIQUE`` sur le ``topic``, ce qui permet un ajout idempotent.
    """

    def __init__(self, path: str) -> None:
        """Mémorise le chemin du fichier et crée la table si nécessaire.

        Args:
            path (str): Chemin du fichier SQLite (créé s'il n'existe pas).

        Returns:
            None
        """
        self._path = path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """Ouvre une connexion SQLite avec accès aux colonnes par nom."""
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Crée la table ``locations`` si elle n'existe pas déjà."""
        conn = self._connect()
        try:
            conn.executescript(_SCHEMA)
        finally:
            conn.close()

    def add_if_absent(
        self, name: str, topic: str, country: str | None = None
    ) -> tuple[bool, LocationOut]:
        """Insère un lieu s'il n'existe pas déjà (identifié par son topic).

        Args:
            name (str): Nom du lieu.
            topic (str): Topic normalisé servant de clé d'unicité.
            country (str | None): Pays optionnel.

        Returns:
            tuple[bool, LocationOut]: ``(created, location)`` où ``created`` vaut
                ``True`` si une nouvelle ligne a été insérée, ``False`` si le lieu
                existait déjà. ``location`` est l'enregistrement résultant.
        """
        conn = self._connect()
        try:
            existing = conn.execute(
                "SELECT * FROM locations WHERE topic = ?", (topic,)
            ).fetchone()
            if existing is not None:
                return False, self._row_to_out(existing)

            created_at = datetime.now(timezone.utc).isoformat()
            name = name.strip()
            topic = topic.strip()
            country = country.strip() if country else None
            cursor = conn.execute(
                "INSERT INTO locations (name, topic, country, created_at) "
                "VALUES (?, ?, ?, ?)",
                (name, topic, country, created_at),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM locations WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return True, self._row_to_out(row)
        finally:
            conn.close()

    def all(self) -> list[LocationOut]:
        """Retourne tous les lieux enregistrés, triés par date de création.

        Returns:
            list[LocationOut]: La liste complète des lieux.
        """
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM locations ORDER BY created_at ASC"
            ).fetchall()
            return [self._row_to_out(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def _row_to_out(row: sqlite3.Row) -> LocationOut:
        """Convertit une ligne SQLite en :class:`LocationOut`."""
        return LocationOut(
            id=row["id"],
            name=row["name"],
            topic=row["topic"],
            country=row["country"],
            created_at=row["created_at"],
        )
