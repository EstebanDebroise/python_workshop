"""Tests pour le module database."""

import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from api.database import LocationDB
from api.schemas import LocationOut


class TestLocationDB:
    """Tests pour la classe LocationDB."""

    @pytest.fixture
    def db(self):
        """Crée une DB temporaire pour chaque test."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        db = LocationDB(path)
        yield db
        Path(path).unlink(missing_ok=True)

    def test_initialization_creates_table(self, db):
        """Vérifie que le constructeur crée la table."""
        conn = sqlite3.connect(db._path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='locations'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_add_if_absent_new_location(self, db):
        """Ajoute un nouveau lieu et vérifie created=True."""
        created, location = db.add_if_absent("Paris", "paris", "France")
        assert created is True
        assert location.name == "Paris"
        assert location.topic == "paris"
        assert location.country == "France"
        assert location.id is not None
        assert location.created_at is not None

    def test_add_if_absent_duplicate(self, db):
        """Ajoute un lieu dupliqué et vérifie created=False."""
        created1, loc1 = db.add_if_absent("Paris", "paris", "France")
        created2, loc2 = db.add_if_absent("Paris_v2", "paris", "France")
        assert created1 is True
        assert created2 is False
        assert loc1.id == loc2.id

    def test_add_if_absent_without_country(self, db):
        """Ajoute un lieu sans pays."""
        created, location = db.add_if_absent("Lyon", "lyon")
        assert created is True
        assert location.country is None

    def test_add_if_absent_strips_whitespace(self, db):
        """Vérifie que les espaces sont supprimés."""
        created, location = db.add_if_absent("  Paris  ", "  paris  ", "  France  ")
        assert location.name == "Paris"
        assert location.topic == "paris"
        assert location.country == "France"

    def test_add_if_absent_multiple_different_locations(self, db):
        """Ajoute plusieurs lieux différents."""
        paris_created, paris = db.add_if_absent("Paris", "paris")
        lyon_created, lyon = db.add_if_absent("Lyon", "lyon")
        assert paris_created is True
        assert lyon_created is True
        assert paris.id != lyon.id

    def test_all_empty_database(self, db):
        """Retourne une liste vide quand la DB est vide."""
        locations = db.all()
        assert locations == []

    def test_all_returns_all_locations(self, db):
        """Retourne tous les lieux en ordre de création."""
        db.add_if_absent("Paris", "paris")
        db.add_if_absent("Lyon", "lyon")
        db.add_if_absent("Marseille", "marseille")

        locations = db.all()
        assert len(locations) == 3
        assert locations[0].name == "Paris"
        assert locations[1].name == "Lyon"
        assert locations[2].name == "Marseille"

    def test_all_ordered_by_created_at(self, db):
        """Vérifie que les lieux sont triés par date de création."""
        created1, loc1 = db.add_if_absent("Paris", "paris")
        created2, loc2 = db.add_if_absent("Lyon", "lyon")

        locations = db.all()
        assert len(locations) == 2
        # Vérifier l'ordre chronologique
        assert locations[0].created_at <= locations[1].created_at

    def test_row_to_out_conversion(self, db):
        """Vérifie la conversion d'une ligne en LocationOut."""
        created, location = db.add_if_absent("Paris", "paris", "France")
        assert isinstance(location, LocationOut)
        assert location.id > 0
        assert location.name == "Paris"
        assert location.topic == "paris"
        assert location.country == "France"

    def test_add_if_absent_country_none_stored_correctly(self, db):
        """Vérifie que country=None est stocké et récupéré correctement."""
        created, location = db.add_if_absent("Anonymous", "anonymous", None)

        # Récupère depuis la DB
        all_locs = db.all()
        assert len(all_locs) == 1
        assert all_locs[0].country is None

    def test_concurrent_access_simulation(self, db):
        """Simule un accès concurrent (deux ajouts du même lieu)."""
        # Cela teste la contrainte UNIQUE du topic
        created1, loc1 = db.add_if_absent("Place 1", "paris")
        created2, loc2 = db.add_if_absent("Place 2", "paris")

        assert created1 is True
        assert created2 is False
        assert loc1.id == loc2.id

    def test_created_at_is_iso_format(self, db):
        """Vérifie que created_at est au format ISO."""
        created, location = db.add_if_absent("Paris", "paris")
        # Tenter de parser l'ISO format
        dt = datetime.fromisoformat(location.created_at)
        assert isinstance(dt, datetime)

    def test_add_multiple_with_special_characters(self, db):
        """Ajoute des lieux avec des caractères spéciaux."""
        created1, loc1 = db.add_if_absent("Côte-d'Ivoire", "côte-d'ivoire")
        created2, loc2 = db.add_if_absent("São Paulo", "são_paulo")

        assert created1 is True
        assert created2 is True
        assert len(db.all()) == 2
