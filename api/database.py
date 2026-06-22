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
    """
    SQLite repository for the locations table.

    Encapsulates all persistence for locations. Each operation opens its own connection to be thread-safe. Uniqueness is enforced by a ``UNIQUE`` constraint on the ``topic``,
    which makes insertions idempotent.
    """

    def __init__(self, path: str) -> None:
        """Store the database file path and create the table if needed.

        Args:
            path (str): Path to the SQLite file (created if it does not exist).

        Returns:
            None
        """
        self._path = path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """Opens a SQLite connection with column access by name."""
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Creates the ``locations`` table if it does not already exist."""
        conn = self._connect()
        try:
            conn.executescript(_SCHEMA)
        finally:
            conn.close()

    def add_if_absent(
        self, name: str, topic: str, country: str | None = None
    ) -> tuple[bool, LocationOut]:
        """Inserts a location if it does not already exist (identified by its topic).

        Args:
            name (str): Name of the location.
            topic (str): Normalized topic serving as uniqueness key.
            country (str | None): Optional country.

        Returns:
            tuple[bool, LocationOut]: ``(created, location)`` where ``created`` is
                ``True`` if a new row was inserted, ``False`` if the location
                already existed. ``location`` is the resulting record.
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
        """Returns all registered locations, sorted by creation date.

        Returns:
            list[LocationOut]: The complete list of locations.
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
        """Converts a SQLite row to :class:`LocationOut`."""
        return LocationOut(
            id=row["id"],
            name=row["name"],
            topic=row["topic"],
            country=row["country"],
            created_at=row["created_at"],
        )
