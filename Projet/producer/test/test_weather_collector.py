import os
import sys
import sqlite3
import unittest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import weather_collector


class TestFetchKafkaTopics(unittest.TestCase):

    def test_no_database_url_returns_empty_list(self):
        # DATABASE_URL is not set → function prints an error and returns an empty list
        with patch.object(weather_collector, "DATABASE_URL", None):
            result = weather_collector.fetch_kafka_topics()
        self.assertEqual(result, [])

    def test_sqlite_prefix_is_stripped(self):
        # DATABASE_URL starts with "sqlite:///" → prefix is removed before connecting
        rows = [{"topic": "paris"}, {"topic": "london"}]
        with patch.object(weather_collector, "DATABASE_URL", "sqlite:///mydb.db"), \
             patch("weather_collector.sqlite3.connect") as mock_connect:
            mock_conn, mock_cursor = MagicMock(), MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = rows
            result = weather_collector.fetch_kafka_topics()

        mock_connect.assert_called_once_with("mydb.db")
        self.assertEqual(result, ["paris", "london"])

    def test_database_url_without_prefix_used_as_is(self):
        # DATABASE_URL has no sqlite:/// prefix → path is used directly as-is
        rows = [{"topic": "berlin"}]
        with patch.object(weather_collector, "DATABASE_URL", "mydb.db"), \
             patch("weather_collector.sqlite3.connect") as mock_connect:
            mock_conn, mock_cursor = MagicMock(), MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = rows
            result = weather_collector.fetch_kafka_topics()

        mock_connect.assert_called_once_with("mydb.db")
        self.assertEqual(result, ["berlin"])

    def test_sqlite_error_returns_empty_list(self):
        # sqlite3.Error raised during connect → function catches it and returns an empty list
        with patch.object(weather_collector, "DATABASE_URL", "mydb.db"), \
             patch("weather_collector.sqlite3.connect") as mock_connect:
            mock_connect.side_effect = sqlite3.Error("DB error")
            result = weather_collector.fetch_kafka_topics()

        self.assertEqual(result, [])

    def test_empty_table_returns_empty_list(self):
        # locations table exists but has no rows → returns an empty list
        with patch.object(weather_collector, "DATABASE_URL", "mydb.db"), \
             patch("weather_collector.sqlite3.connect") as mock_connect:
            mock_conn, mock_cursor = MagicMock(), MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []
            result = weather_collector.fetch_kafka_topics()

        self.assertEqual(result, [])

    def test_connection_closed_after_query(self):
        # verifies that the database connection is properly closed after the query
        with patch.object(weather_collector, "DATABASE_URL", "mydb.db"), \
             patch("weather_collector.sqlite3.connect") as mock_connect:
            mock_conn, mock_cursor = MagicMock(), MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []
            weather_collector.fetch_kafka_topics()

        mock_conn.close.assert_called_once()


class TestFetchWeather(unittest.TestCase):

    def _mock_response(self, json_data=None):
        mock_resp = MagicMock()
        mock_resp.json.return_value = json_data or {}
        return mock_resp

    def test_returns_json_on_success(self):
        # API responds with 200 → function returns the parsed JSON dict
        expected = {"weather": [{"main": "Clear"}]}
        with patch("weather_collector.requests.get", return_value=self._mock_response(expected)):
            result = weather_collector.fetch_weather(48.85, 2.35)
        self.assertEqual(result, expected)

    def test_raise_for_status_is_called(self):
        # verifies that raise_for_status() is always called to catch HTTP error codes
        mock_resp = self._mock_response()
        with patch("weather_collector.requests.get", return_value=mock_resp):
            weather_collector.fetch_weather(0.0, 0.0)
        mock_resp.raise_for_status.assert_called_once()

    def test_http_error_propagates(self):
        # raise_for_status() raises HTTPError (e.g. 404) → exception is not caught, it propagates to the caller
        import requests as req_lib
        mock_resp = self._mock_response()
        mock_resp.raise_for_status.side_effect = req_lib.HTTPError("404")
        with patch("weather_collector.requests.get", return_value=mock_resp):
            with self.assertRaises(req_lib.HTTPError):
                weather_collector.fetch_weather(0.0, 0.0)

    def test_request_params_contain_lat_lon_units(self):
        # verifies that lat, lon, units=metric and lang=fr are passed to the API request
        with patch("weather_collector.requests.get", return_value=self._mock_response()) as mock_get:
            weather_collector.fetch_weather(48.85, 2.35)

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["lat"], 48.85)
        self.assertEqual(params["lon"], 2.35)
        self.assertEqual(params["units"], "metric")
        self.assertEqual(params["lang"], "fr")

    def test_timeout_is_10_seconds(self):
        # verifies that the HTTP request uses a 10-second timeout to avoid hanging
        with patch("weather_collector.requests.get", return_value=self._mock_response()) as mock_get:
            weather_collector.fetch_weather(0.0, 0.0)

        self.assertEqual(mock_get.call_args.kwargs["timeout"], 10)


class TestFormatMessage(unittest.TestCase):

    def _full_raw(self):
        return {
            "name": "Paris",
            "sys": {"country": "FR"},
            "weather": [{"main": "Clear", "description": "ciel dégagé"}],
            "main": {
                "temp": 20.0,
                "feels_like": 19.0,
                "temp_min": 17.0,
                "temp_max": 22.0,
                "humidity": 60,
                "pressure": 1013,
            },
            "wind": {"speed": 5.0, "deg": 90, "gust": 7.5},
            "visibility": 10000,
            "clouds": {"all": 10},
            "rain": {"1h": 0.5},
            "snow": {"1h": 0.1},
        }

    def test_full_data_all_fields_mapped(self):
        # complete API response with all optional fields → all output fields are correctly mapped
        result = weather_collector.format_message(self._full_raw(), 48.85, 2.35)

        self.assertEqual(result["location"], "Paris")
        self.assertEqual(result["country"], "FR")
        self.assertEqual(result["coordinates"], {"lat": 48.85, "lon": 2.35})

        w = result["weather"]
        self.assertEqual(w["condition"], "Clear")
        self.assertEqual(w["description"], "ciel dégagé")
        self.assertEqual(w["temperature_c"], 20.0)
        self.assertEqual(w["feels_like_c"], 19.0)
        self.assertEqual(w["temp_min_c"], 17.0)
        self.assertEqual(w["temp_max_c"], 22.0)
        self.assertEqual(w["humidity_pct"], 60)
        self.assertEqual(w["pressure_hpa"], 1013)
        self.assertEqual(w["wind_speed_ms"], 5.0)
        self.assertEqual(w["wind_direction_deg"], 90)
        self.assertEqual(w["wind_gust_ms"], 7.5)
        self.assertEqual(w["visibility_m"], 10000)
        self.assertEqual(w["clouds_pct"], 10)
        self.assertEqual(w["rain_1h_mm"], 0.5)
        self.assertEqual(w["snow_1h_mm"], 0.1)

    def test_minimal_raw_optional_fields_are_none(self):
        # API response without wind/rain/snow/visibility/clouds → optional fields default to None
        raw = {
            "name": "",
            "weather": [{"main": "Rain", "description": "pluie"}],
            "main": {
                "temp": 10.0,
                "feels_like": 9.0,
                "temp_min": 8.0,
                "temp_max": 12.0,
                "humidity": 90,
                "pressure": 1005,
            },
        }
        result = weather_collector.format_message(raw, 0.0, 0.0)
        w = result["weather"]

        self.assertIsNone(w["wind_speed_ms"])
        self.assertIsNone(w["wind_direction_deg"])
        self.assertIsNone(w["wind_gust_ms"])
        self.assertIsNone(w["rain_1h_mm"])
        self.assertIsNone(w["snow_1h_mm"])
        self.assertIsNone(w["visibility_m"])
        self.assertIsNone(w["clouds_pct"])
        self.assertEqual(result["country"], "")
        self.assertEqual(result["location"], "")

    def test_timestamp_is_utc_iso_format(self):
        # verifies that the timestamp is in ISO 8601 format with UTC timezone (+00:00)
        result = weather_collector.format_message(self._full_raw(), 0, 0)
        self.assertIn("+00:00", result["timestamp"])

    def test_coordinates_embedded_correctly(self):
        # lat and lon passed to format_message are embedded verbatim in the output coordinates field
        result = weather_collector.format_message(self._full_raw(), -33.86, 151.21)
        self.assertEqual(result["coordinates"]["lat"], -33.86)
        self.assertEqual(result["coordinates"]["lon"], 151.21)

    def test_wind_partial_fields(self):
        # wind dict has only speed (no deg/gust) → missing sub-fields are None, speed is correctly set
        raw = self._full_raw()
        raw["wind"] = {"speed": 3.0}
        result = weather_collector.format_message(raw, 0, 0)
        w = result["weather"]
        self.assertEqual(w["wind_speed_ms"], 3.0)
        self.assertIsNone(w["wind_direction_deg"])
        self.assertIsNone(w["wind_gust_ms"])


class TestSendToKafka(unittest.TestCase):

    def _make_mock_producer(self):
        mock_producer = MagicMock()
        mock_future = MagicMock()
        mock_metadata = MagicMock()
        mock_metadata.topic = "test-topic"
        mock_metadata.partition = 0
        mock_metadata.offset = 42
        mock_future.get.return_value = mock_metadata
        mock_producer.send.return_value = mock_future
        return mock_producer, mock_future, mock_metadata

    def _sample_message(self, lat=48.85, lon=2.35):
        return {"coordinates": {"lat": lat, "lon": lon}, "data": "value"}

    def test_producer_send_called_with_topic_and_message(self):
        # verifies that producer.send() is called with the correct topic and full message dict
        mock_producer, mock_future, _ = self._make_mock_producer()
        with patch("weather_collector.KafkaProducer", return_value=mock_producer):
            weather_collector.send_to_kafka("paris", self._sample_message())

        mock_producer.send.assert_called_once()
        call_kwargs = mock_producer.send.call_args
        self.assertEqual(call_kwargs.args[0], "paris")
        self.assertEqual(call_kwargs.kwargs["value"], self._sample_message())

    def test_key_is_lat_comma_lon(self):
        # verifies that the Kafka message key is formatted as "lat,lon" from the coordinates
        mock_producer, _, _ = self._make_mock_producer()
        with patch("weather_collector.KafkaProducer", return_value=mock_producer):
            weather_collector.send_to_kafka("test", self._sample_message(10.0, 20.0))

        key = mock_producer.send.call_args.kwargs["key"]
        self.assertEqual(key, "10.0,20.0")

    def test_flush_called_with_timeout_10(self):
        # verifies that flush(timeout=10) is called to ensure the message is actually sent
        mock_producer, _, _ = self._make_mock_producer()
        with patch("weather_collector.KafkaProducer", return_value=mock_producer):
            weather_collector.send_to_kafka("paris", self._sample_message())

        mock_producer.flush.assert_called_once_with(timeout=10)

    def test_future_get_called_with_timeout_10(self):
        # verifies that future.get(timeout=10) is called to retrieve delivery confirmation
        mock_producer, mock_future, _ = self._make_mock_producer()
        with patch("weather_collector.KafkaProducer", return_value=mock_producer):
            weather_collector.send_to_kafka("paris", self._sample_message())

        mock_future.get.assert_called_once_with(timeout=10)


if __name__ == "__main__":
    unittest.main()
