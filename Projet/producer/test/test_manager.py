import contextlib
import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import manager


class TestMain(unittest.TestCase):

    def _run_main(self, topics, coord_map, weather_return=None, formatted_return=None):
        weather_return = weather_return or {"weather": [{"main": "Clear"}]}
        formatted_return = formatted_return or {"coordinates": {"lat": 0.0, "lon": 0.0}}

        with patch("manager.fetch_kafka_topics", return_value=topics), \
             patch("manager.get_city_coordinates", side_effect=lambda t: coord_map.get(t)), \
             patch("manager.fetch_weather", return_value=weather_return), \
             patch("manager.format_message", return_value=formatted_return), \
             patch("manager.send_to_kafka") as mock_send:
            manager.main()

        return mock_send

    # --- alert threshold ---

    def test_more_than_10_topics_prints_alert_to_stderr(self):
        # more than 10 topics → an [ALERT] warning is printed to stderr
        topics = [str(i) for i in range(11)]
        stderr = io.StringIO()
        with patch("manager.fetch_kafka_topics", return_value=topics), \
             patch("manager.get_city_coordinates", return_value=None), \
             contextlib.redirect_stderr(stderr):
            manager.main()

        self.assertIn("[ALERT]", stderr.getvalue())

    def test_exactly_10_topics_no_alert(self):
        # exactly 10 topics (boundary value) → no alert is printed
        topics = [str(i) for i in range(10)]
        stderr = io.StringIO()
        with patch("manager.fetch_kafka_topics", return_value=topics), \
             patch("manager.get_city_coordinates", return_value=None), \
             contextlib.redirect_stderr(stderr):
            manager.main()

        self.assertNotIn("[ALERT]", stderr.getvalue())

    def test_fewer_than_10_topics_no_alert(self):
        # fewer than 10 topics → no alert is printed to stderr
        topics = ["paris", "london"]
        stderr = io.StringIO()
        with patch("manager.fetch_kafka_topics", return_value=topics), \
             patch("manager.get_city_coordinates", return_value=None), \
             contextlib.redirect_stderr(stderr):
            manager.main()

        self.assertNotIn("[ALERT]", stderr.getvalue())

    # --- coordinates None → error ---

    def test_coordinates_none_prints_error_to_stderr(self):
        # get_city_coordinates returns None → [ERROR] with the city name is printed to stderr, weather is not fetched
        topics = ["unknowncity"]
        stderr = io.StringIO()
        with patch("manager.fetch_kafka_topics", return_value=topics), \
             patch("manager.get_city_coordinates", return_value=None), \
             patch("manager.fetch_weather") as mock_weather, \
             contextlib.redirect_stderr(stderr):
            manager.main()

        self.assertIn("[ERROR]", stderr.getvalue())
        self.assertIn("unknowncity", stderr.getvalue())
        mock_weather.assert_not_called()

    # --- coordinates (None, None) → skips weather ---

    def test_coordinates_tuple_with_none_values_skips_weather(self):
        # coordinates returned as (None, None) → weather fetch and send are both skipped
        with patch("manager.fetch_kafka_topics", return_value=["badcity"]), \
             patch("manager.get_city_coordinates", return_value=(None, None)), \
             patch("manager.fetch_weather") as mock_weather, \
             patch("manager.send_to_kafka") as mock_send:
            manager.main()

        mock_weather.assert_not_called()
        mock_send.assert_not_called()

    def test_coordinates_with_none_lat_skips_weather(self):
        # latitude is None while longitude is valid → weather fetch is skipped
        with patch("manager.fetch_kafka_topics", return_value=["badcity"]), \
             patch("manager.get_city_coordinates", return_value=(None, 2.35)), \
             patch("manager.fetch_weather") as mock_weather:
            manager.main()

        mock_weather.assert_not_called()

    def test_coordinates_with_none_lon_skips_weather(self):
        # longitude is None while latitude is valid → weather fetch is skipped
        with patch("manager.fetch_kafka_topics", return_value=["badcity"]), \
             patch("manager.get_city_coordinates", return_value=(48.85, None)), \
             patch("manager.fetch_weather") as mock_weather:
            manager.main()

        mock_weather.assert_not_called()

    # --- happy path ---

    def test_valid_coordinates_calls_fetch_weather(self):
        # valid coordinates returned → fetch_weather is called with the correct lat and lon
        with patch("manager.fetch_kafka_topics", return_value=["paris"]), \
             patch("manager.get_city_coordinates", return_value=(48.85, 2.35)), \
             patch("manager.fetch_weather", return_value={}) as mock_weather, \
             patch("manager.format_message", return_value={"coordinates": {"lat": 48.85, "lon": 2.35}}), \
             patch("manager.send_to_kafka"):
            manager.main()

        mock_weather.assert_called_once_with(48.85, 2.35)

    def test_valid_coordinates_calls_format_and_send(self):
        # happy path: weather data is fetched, formatted, then sent to Kafka with the correct topic
        weather_data = {"weather": [{"main": "Clear"}]}
        formatted = {"coordinates": {"lat": 48.85, "lon": 2.35}}

        with patch("manager.fetch_kafka_topics", return_value=["paris"]), \
             patch("manager.get_city_coordinates", return_value=(48.85, 2.35)), \
             patch("manager.fetch_weather", return_value=weather_data), \
             patch("manager.format_message", return_value=formatted) as mock_fmt, \
             patch("manager.send_to_kafka") as mock_send:
            manager.main()

        mock_fmt.assert_called_once_with(weather_data, 48.85, 2.35)
        mock_send.assert_called_once_with("paris", formatted)

    def test_multiple_valid_topics_all_sent(self):
        # multiple topics with valid coordinates → send_to_kafka is called once per topic
        coord_map = {"paris": (48.85, 2.35), "london": (51.5, -0.12)}
        mock_send = self._run_main(["paris", "london"], coord_map)
        self.assertEqual(mock_send.call_count, 2)

    # --- edge cases ---

    def test_empty_topics_list_no_processing(self):
        # fetch_kafka_topics returns an empty list → no coordinates lookup or weather fetch happens
        with patch("manager.fetch_kafka_topics", return_value=[]), \
             patch("manager.get_city_coordinates") as mock_coords:
            manager.main()

        mock_coords.assert_not_called()

    def test_mixed_topics_valid_and_invalid(self):
        # one topic with valid coordinates, one without → only the valid one is sent, error logged for the other
        coord_map = {"paris": (48.85, 2.35), "nowhere": None}
        stderr = io.StringIO()

        with patch("manager.fetch_kafka_topics", return_value=["paris", "nowhere"]), \
             patch("manager.get_city_coordinates", side_effect=lambda t: coord_map.get(t)), \
             patch("manager.fetch_weather", return_value={}), \
             patch("manager.format_message", return_value={"coordinates": {"lat": 48.85, "lon": 2.35}}), \
             patch("manager.send_to_kafka") as mock_send, \
             contextlib.redirect_stderr(stderr):
            manager.main()

        mock_send.assert_called_once()
        self.assertIn("[ERROR]", stderr.getvalue())
        self.assertIn("nowhere", stderr.getvalue())

    def test_11_topics_with_mixed_results(self):
        # 11 topics all with None coordinates → both the [ALERT] and [ERROR] messages appear in stderr
        topics = [str(i) for i in range(11)]
        coord_map = {t: None for t in topics}
        stderr = io.StringIO()

        with patch("manager.fetch_kafka_topics", return_value=topics), \
             patch("manager.get_city_coordinates", side_effect=lambda t: coord_map.get(t)), \
             contextlib.redirect_stderr(stderr):
            manager.main()

        output = stderr.getvalue()
        self.assertIn("[ALERT]", output)
        self.assertIn("[ERROR]", output)


if __name__ == "__main__":
    unittest.main()
