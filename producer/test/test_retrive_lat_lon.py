import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import retrive_lat_lon


class TestGetCityCoordinates(unittest.TestCase):

    def _mock_nominatim(self, mock_cls, geocode_return):
        mock_geolocator = MagicMock()
        mock_cls.return_value = mock_geolocator
        mock_geolocator.geocode.return_value = geocode_return
        return mock_geolocator

    def test_city_found_returns_lat_lon_tuple(self):
        # geocode() returns a location → function returns (latitude, longitude) tuple
        mock_location = MagicMock()
        mock_location.latitude = 48.8566
        mock_location.longitude = 2.3522

        with patch("retrive_lat_lon.Nominatim") as mock_cls:
            self._mock_nominatim(mock_cls, mock_location)
            result = retrive_lat_lon.get_city_coordinates("Paris")

        self.assertEqual(result, (48.8566, 2.3522))

    def test_city_not_found_returns_none(self):
        # geocode() returns None (unknown city) → function returns None
        with patch("retrive_lat_lon.Nominatim") as mock_cls:
            self._mock_nominatim(mock_cls, None)
            result = retrive_lat_lon.get_city_coordinates("XyzInexistant999")

        self.assertIsNone(result)

    def test_geocode_exception_returns_none(self):
        # geocode() raises an exception (e.g. network error) → function catches it and returns None
        with patch("retrive_lat_lon.Nominatim") as mock_cls:
            mock_geolocator = MagicMock()
            mock_cls.return_value = mock_geolocator
            mock_geolocator.geocode.side_effect = Exception("Network error")

            result = retrive_lat_lon.get_city_coordinates("Paris")

        self.assertIsNone(result)

    def test_geocode_called_with_city_name(self):
        # verifies that geocode() is called with the exact city name passed to the function
        with patch("retrive_lat_lon.Nominatim") as mock_cls:
            geolocator = self._mock_nominatim(mock_cls, None)
            retrive_lat_lon.get_city_coordinates("Lyon")

        geolocator.geocode.assert_called_once_with("Lyon")

    def test_nominatim_user_agent(self):
        # verifies that Nominatim is instantiated with the expected user_agent string
        with patch("retrive_lat_lon.Nominatim") as mock_cls:
            self._mock_nominatim(mock_cls, None)
            retrive_lat_lon.get_city_coordinates("Paris")

        mock_cls.assert_called_once_with(user_agent="city_locator")

    def test_empty_city_name(self):
        # edge case: empty string as city name → geocode finds nothing, returns None
        with patch("retrive_lat_lon.Nominatim") as mock_cls:
            self._mock_nominatim(mock_cls, None)
            result = retrive_lat_lon.get_city_coordinates("")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
