"""Tests pour le module schemas."""

import pytest
from pydantic import ValidationError

from api.schemas import (
    LocationIn,
    LocationOut,
    LocationResult,
    WeatherResponse,
    normalize_topic,
)


class TestNormalizeTopic:
    """Tests pour la fonction normalize_topic."""

    def test_normalize_lowercase(self):
        """Vérifie que le topic est converti en minuscules."""
        assert normalize_topic("PARIS") == "paris"

    def test_normalize_with_accents(self):
        """Vérifie que les accents sont remplacés par underscore."""
        assert normalize_topic("Saint-Lô") == "saint-l_"

    def test_normalize_spaces_to_underscore(self):
        """Vérifie que les espaces sont remplacés par underscore."""
        assert normalize_topic("New York") == "new_york"

    def test_normalize_special_chars(self):
        """Vérifie que les caractères spéciaux sont remplacés."""
        assert normalize_topic("Paris@2024") == "paris_2024"

    def test_normalize_preserves_dash_dot_underscore(self):
        """Vérifie que - . _ sont conservés."""
        assert normalize_topic("paris_france-2024.test") == "paris_france-2024.test"

    def test_normalize_strips_whitespace(self):
        """Vérifie que les espaces aux extrémités sont supprimés."""
        assert normalize_topic("  PARIS  ") == "paris"

    def test_normalize_empty_after_strip(self):
        """Vérifie le comportement avec une string vide après strip."""
        assert normalize_topic("   ") == ""

    def test_normalize_special_chars_comprehensive(self):
        """Teste une variété de caractères spéciaux."""
        assert normalize_topic("Côte-d'Ivoire") == "c_te-d_ivoire"
        assert normalize_topic("São Paulo") == "s_o_paulo"
        assert normalize_topic("Zürich!@#$%^&*()") == "z_rich__________"


class TestLocationIn:
    """Tests pour le schéma LocationIn."""

    def test_location_in_minimal(self):
        """Crée une LocationIn avec le minimum requis."""
        loc = LocationIn(name="Paris")
        assert loc.name == "Paris"
        assert loc.topic is None
        assert loc.country is None

    def test_location_in_with_all_fields(self):
        """Crée une LocationIn avec tous les champs."""
        loc = LocationIn(name="Paris", topic="paris", country="France")
        assert loc.name == "Paris"
        assert loc.topic == "paris"
        assert loc.country == "France"

    def test_location_in_empty_name_fails(self):
        """Vérifie que le nom ne peut pas être vide."""
        with pytest.raises(ValidationError):
            LocationIn(name="")

    def test_location_in_whitespace_only_name_is_accepted(self):
        """Pydantic accepte les espaces, donc ce test vérifie l'acceptance."""
        # Note: min_length=1 requiert au moins 1 caractère, les espaces comptent
        loc = LocationIn(name="   ")
        assert loc.name == "   "


class TestLocationOut:
    """Tests pour le schéma LocationOut."""

    def test_location_out_creation(self):
        """Crée une LocationOut avec tous les champs."""
        loc = LocationOut(
            id=1,
            name="Paris",
            topic="paris",
            country="France",
            created_at="2024-01-01T00:00:00+00:00"
        )
        assert loc.id == 1
        assert loc.name == "Paris"
        assert loc.topic == "paris"
        assert loc.country == "France"

    def test_location_out_without_country(self):
        """Crée une LocationOut sans pays."""
        loc = LocationOut(
            id=1,
            name="Paris",
            topic="paris",
            created_at="2024-01-01T00:00:00+00:00"
        )
        assert loc.country is None


class TestLocationResult:
    """Tests pour le schéma LocationResult."""

    def test_location_result_created_true(self):
        """Crée un LocationResult avec created=True."""
        loc_out = LocationOut(
            id=1,
            name="Paris",
            topic="paris",
            created_at="2024-01-01T00:00:00+00:00"
        )
        result = LocationResult(created=True, location=loc_out)
        assert result.created is True
        assert result.location.id == 1

    def test_location_result_created_false(self):
        """Crée un LocationResult avec created=False."""
        loc_out = LocationOut(
            id=2,
            name="Lyon",
            topic="lyon",
            created_at="2024-01-01T00:00:00+00:00"
        )
        result = LocationResult(created=False, location=loc_out)
        assert result.created is False
        assert result.location.name == "Lyon"


class TestWeatherResponse:
    """Tests pour le schéma WeatherResponse."""

    def test_weather_response_ok_with_message(self):
        """Crée une réponse météo avec statut ok."""
        msg = {"temperature": 20.5, "humidity": 60}
        resp = WeatherResponse(
            topic="paris",
            status="ok",
            is_new=True,
            offset=100,
            message=msg
        )
        assert resp.topic == "paris"
        assert resp.status == "ok"
        assert resp.is_new is True
        assert resp.offset == 100
        assert resp.message == msg
        assert resp.detail is None

    def test_weather_response_empty(self):
        """Crée une réponse météo avec statut empty."""
        resp = WeatherResponse(
            topic="unknown",
            status="empty",
            detail="Topic inconnu"
        )
        assert resp.status == "empty"
        assert resp.is_new is False
        assert resp.offset is None
        assert resp.message is None
        assert resp.detail == "Topic inconnu"

    def test_weather_response_error(self):
        """Crée une réponse météo avec statut error."""
        resp = WeatherResponse(
            topic="paris",
            status="error",
            detail="Erreur Kafka : connection refused"
        )
        assert resp.status == "error"
        assert resp.detail is not None

    def test_weather_response_is_new_false(self):
        """Crée une réponse weathere avec is_new=False."""
        resp = WeatherResponse(
            topic="paris",
            status="ok",
            is_new=False,
            offset=99,
            message={}
        )
        assert resp.is_new is False
