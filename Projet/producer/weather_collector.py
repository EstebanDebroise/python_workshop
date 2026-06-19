import json
import os
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import KafkaError

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
API_URL = os.getenv("API_URL")
OPENWEATHER_URL = os.getenv("OPENWEATHER_URL")

def fetch_kafka_topics() -> list:
    """Get the list of Kafka topics from the API.

    Interroge l'endpoint ``GET /locations`` de l'API au lieu d'accéder
    directement à la base de données.

    Returns:
        list: A list of Kafka topic names.
    """
    try:
        response = requests.get(f"{API_URL}/locations", timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return [data.get("name")] if data.get("name") else []
        return [location.get("name") for location in data if isinstance(location, dict) and location.get("name")]
    except requests.RequestException as e:
        print(f"[ERREUR] Impossible de récupérer les topics depuis l'API : {e}", file=sys.stderr)
        return []


def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch weather data from OpenWeatherMap API for given latitude and longitude.
    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
    Returns:
        dict: Weather data in JSON format.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "fr",
    }
    response = requests.get(OPENWEATHER_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def format_message(raw: dict, lat: float, lon: float) -> dict:
    """Format the raw weather data into a structured message.
    Args:
        raw (dict): Raw weather data from OpenWeatherMap API.
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
    Returns:
        dict: Formatted weather data.
    """
    wind = raw.get("wind", {})
    rain = raw.get("rain", {})
    snow = raw.get("snow", {})

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "coordinates": {"lat": lat, "lon": lon},
        "location": raw.get("name", ""),
        "country": raw.get("sys", {}).get("country", ""),
        "weather": {
            "condition": raw["weather"][0]["main"],
            "description": raw["weather"][0]["description"],
            "temperature_c": raw["main"]["temp"],
            "feels_like_c": raw["main"]["feels_like"],
            "temp_min_c": raw["main"]["temp_min"],
            "temp_max_c": raw["main"]["temp_max"],
            "humidity_pct": raw["main"]["humidity"],
            "pressure_hpa": raw["main"]["pressure"],
            "wind_speed_ms": wind.get("speed"),
            "wind_direction_deg": wind.get("deg"),
            "wind_gust_ms": wind.get("gust"),
            "visibility_m": raw.get("visibility"),
            "clouds_pct": raw.get("clouds", {}).get("all"),
            "rain_1h_mm": rain.get("1h"),
            "snow_1h_mm": snow.get("1h"),
        },
    }


def send_to_kafka(topic: str, message: dict) -> None:
    """Send a message to a Kafka topic.
    Args:
        topic (str): The Kafka topic to send the message to.
        message (dict): The message to send.
    """
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
    )

    key = f"{message['coordinates']['lat']},{message['coordinates']['lon']}"

    future = producer.send(topic, key=key, value=message)
    producer.flush(timeout=10)

    record_metadata = future.get(timeout=10)
    print(
        f"[OK] message sent → topic={record_metadata.topic} "
        f"partition={record_metadata.partition} offset={record_metadata.offset}"
    )


if __name__ == "__main__":
    #main()
    pass
