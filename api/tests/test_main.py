"""Tests pour le module main (endpoints FastAPI)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.tests.conftest import create_location_out


@pytest.fixture
def client():
    """Fournit un client de test FastAPI."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests pour l'endpoint /health."""

    def test_health_returns_ok(self, client):
        """Vérifie que /health retourne status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_content_type(self, client):
        """Vérifie le content-type de /health."""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]


class TestWeatherEndpoint:
    """Tests pour l'endpoint /weather/{topic}."""

    @patch("api.main.reader.read_latest")
    def test_weather_returns_ok_status(self, mock_read, client):
        """Teste /weather avec un statut ok."""
        mock_read.return_value = {
            "status": "ok",
            "is_new": True,
            "offset": 100,
            "message": {"temp": 20},
            "detail": None,
        }

        response = client.get("/weather/paris")
        assert response.status_code == 200

        data = response.json()
        assert data["topic"] == "paris"
        assert data["status"] == "ok"
        assert data["is_new"] is True
        assert data["offset"] == 100
        assert data["message"]["temp"] == 20

    @patch("api.main.reader.read_latest")
    def test_weather_returns_empty_status(self, mock_read, client):
        """Teste /weather avec un statut empty."""
        mock_read.return_value = {
            "status": "empty",
            "is_new": False,
            "offset": None,
            "message": None,
            "detail": "Topic inconnu",
        }

        response = client.get("/weather/unknown")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "empty"
        assert data["detail"] == "Topic inconnu"

    @patch("api.main.reader.read_latest")
    def test_weather_returns_error_status(self, mock_read, client):
        """Teste /weather avec un statut error."""
        mock_read.return_value = {
            "status": "error",
            "is_new": False,
            "offset": None,
            "message": None,
            "detail": "Erreur Kafka",
        }

        response = client.get("/weather/paris")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "error"
        assert data["detail"] is not None

    @patch("api.main.reader.read_latest")
    def test_weather_is_new_false(self, mock_read, client):
        """Teste /weather avec is_new=False."""
        mock_read.return_value = {
            "status": "ok",
            "is_new": False,
            "offset": 99,
            "message": {"temp": 19},
            "detail": None,
        }

        response = client.get("/weather/paris")
        data = response.json()
        assert data["is_new"] is False

    @patch("api.main.reader.read_latest")
    def test_weather_reader_called_with_topic(self, mock_read, client):
        """Vérifie que le reader est appelé avec le bon topic."""
        mock_read.return_value = {
            "status": "ok",
            "is_new": True,
            "offset": 100,
            "message": {},
            "detail": None,
        }

        client.get("/weather/my_topic")
        mock_read.assert_called_once_with("my_topic")


class TestAddLocationEndpoint:
    """Tests pour l'endpoint POST /locations."""

    @patch("api.main.db.add_if_absent")
    def test_add_location_new(self, mock_add, client):
        """Teste l'ajout d'un nouveau lieu."""
        location = create_location_out(name="Paris", topic="paris", country="France")
        mock_add.return_value = (True, location)

        response = client.post(
            "/locations",
            json={"name": "Paris", "country": "France"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created"] is True
        assert data["location"]["name"] == "Paris"

    @patch("api.main.db.add_if_absent")
    def test_add_location_existing(self, mock_add, client):
        """Teste l'ajout d'un lieu déjà existant."""
        location = create_location_out(name="Paris", topic="paris", country="France")
        mock_add.return_value = (False, location)

        response = client.post(
            "/locations",
            json={"name": "Paris", "country": "France"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created"] is False

    def test_add_location_empty_name_fails(self, client):
        """Teste que l'ajout avec un nom vide échoue."""
        response = client.post(
            "/locations",
            json={"name": ""}
        )

        assert response.status_code == 422

    @patch("api.main.db.add_if_absent")
    def test_add_location_with_explicit_topic(self, mock_add, client):
        """Teste l'ajout avec un topic explicite."""
        location = create_location_out(name="Paris", topic="custom_topic", country=None)
        mock_add.return_value = (True, location)

        response = client.post(
            "/locations",
            json={"name": "Paris", "topic": "custom_topic"}
        )

        assert response.status_code == 201
        # Vérifier que le custom topic est utilisé
        mock_add.assert_called_once()
        call_args = mock_add.call_args
        assert call_args[0][1] == "custom_topic"

    @patch("api.main.db.add_if_absent")
    def test_add_location_topic_normalized(self, mock_add, client):
        """Teste que le topic est normalisé si pas explicite."""
        location = create_location_out(name="Paris France", topic="paris_france", country=None)
        mock_add.return_value = (True, location)

        response = client.post(
            "/locations",
            json={"name": "Paris France"}
        )

        assert response.status_code == 201
        # Le topic doit être normalisé
        call_args = mock_add.call_args
        assert call_args[0][1] == "paris_france"

    def test_add_location_only_whitespace_topic_fails(self, client):
        """Teste que l'ajout avec un topic explicite vide échoue."""
        response = client.post(
            "/locations",
            json={"name": "Paris", "topic": "   "}
        )

        assert response.status_code == 422
        data = response.json()
        assert "invalide" in data["detail"].lower()

    @patch("api.main.db.add_if_absent")
    def test_add_location_without_country(self, mock_add, client):
        """Teste l'ajout sans spécifier le pays."""
        location = create_location_out(name="Paris", topic="paris", country=None)
        mock_add.return_value = (True, location)

        response = client.post(
            "/locations",
            json={"name": "Paris"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["location"]["country"] is None

    @patch("api.main.db.add_if_absent")
    def test_add_location_strips_whitespace(self, mock_add, client):
        """Teste que les espaces sont supprimés du nom."""
        location = create_location_out(name="Paris", topic="paris", country=None)
        mock_add.return_value = (True, location)

        response = client.post(
            "/locations",
            json={"name": "  Paris  "}
        )

        assert response.status_code == 201
        # Vérifier que les espaces ont été supprimés
        call_args = mock_add.call_args
        assert call_args[0][0] == "Paris"


class TestListLocationsEndpoint:
    """Tests pour l'endpoint GET /locations."""

    @patch("api.main.db.all")
    def test_list_locations_empty(self, mock_all, client):
        """Teste le listing quand aucun lieu n'existe."""
        mock_all.return_value = []

        response = client.get("/locations")
        assert response.status_code == 200
        assert response.json() == []

    @patch("api.main.db.all")
    def test_list_locations_multiple(self, mock_all, client):
        """Teste le listing avec plusieurs lieux."""
        locations = [
            create_location_out(id=1, name="Paris", topic="paris"),
            create_location_out(id=2, name="Lyon", topic="lyon"),
        ]
        mock_all.return_value = locations

        response = client.get("/locations")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Paris"
        assert data[1]["name"] == "Lyon"

    @patch("api.main.db.all")
    def test_list_locations_format(self, mock_all, client):
        """Teste que le format de réponse est correct."""
        locations = [create_location_out(id=1, name="Paris", topic="paris")]
        mock_all.return_value = locations

        response = client.get("/locations")
        data = response.json()

        assert len(data) > 0
        location = data[0]
        assert "id" in location
        assert "name" in location
        assert "topic" in location
        assert "created_at" in location


class TestIntegrationEndpoints:
    """Tests d'intégration entre les endpoints."""

    @patch("api.main.db.add_if_absent")
    @patch("api.main.db.all")
    def test_add_then_list(self, mock_all, mock_add, client):
        """Teste l'ajout suivi du listing."""
        new_location = create_location_out(
            id=1, name="Paris", topic="paris", country="France"
        )

        mock_add.return_value = (True, new_location)
        mock_all.return_value = [new_location]

        # Ajouter un lieu
        add_response = client.post(
            "/locations",
            json={"name": "Paris", "country": "France"}
        )
        assert add_response.status_code == 201

        # Lister les lieux
        list_response = client.get("/locations")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1
