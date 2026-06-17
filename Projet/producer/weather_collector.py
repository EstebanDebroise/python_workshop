#!/usr/bin/env python3
"""
Fetches current weather data for given coordinates and publishes to Kafka.
Usage: python weather_collector.py <lat> <lon>
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import KafkaError

from retrive_lat_lon import get_city_coordinates

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

def fetch_kafka_topics() -> list:
    """Récupère la liste des villes demandé à l'aide de la bdd"""
    if not DATABASE_URL:
        print("[ERREUR] Variable d'environnement DATABASE_URL manquante.", file=sys.stderr)
        return []

    db_path = DATABASE_URL
    if db_path.startswith("sqlite:///"):
        db_path = db_path[10:]

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT topic FROM locations")
        rows = cursor.fetchall()
        topics = [row["topic"] for row in rows]
        conn.close()
        return topics
    except sqlite3.Error as e:
        print(f"[ERREUR] Base de données : {e}", file=sys.stderr)
        return []


def fetch_weather(lat: float, lon: float) -> dict:
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
        f"[OK] Message envoyé → topic={record_metadata.topic} "
        f"partition={record_metadata.partition} offset={record_metadata.offset}"
    )
   

def fetch_weather_mock(lat: float, lon: float) -> dict:
    return {
        "timestamp": "2026-05-24T14:36:11.823271+00:00",
        "coordinates": {
            "lat": 48.8566,
            "lon": 2.0
        },
        "location": "Chavenay",
        "country": "FR",
        "weather": {
            "condition": "Clear",
            "description": "ciel dégagé",
            "temperature_c": 30.78,
            "feels_like_c": 30.63,
            "temp_min_c": 29.66,
            "temp_max_c": 32.27,
            "humidity_pct": 40,
            "pressure_hpa": 1028,
            "wind_speed_ms": 4.63,
            "wind_direction_deg": 40,
            "wind_gust_ms": None,
            "visibility_m": 10000,
            "clouds_pct": 0,
            "rain_1h_mm": None,
            "snow_1h_mm": None
        }
        }


def main():
    if not OPENWEATHER_API_KEY:
        print("[ERREUR] Variable d'environnement OPENWEATHER_API_KEY manquante.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Collecteur météo → Kafka")
    parser.add_argument("lat", type=float, help="Latitude (ex: 48.8566)")
    parser.add_argument("lon", type=float, help="Longitude (ex: 2.3522)")
    args = parser.parse_args()

    if not (-90 <= args.lat <= 90):
        print("[ERREUR] Latitude invalide, doit être entre -90 et 90.", file=sys.stderr)
        sys.exit(1)
    if not (-180 <= args.lon <= 180):
        print("[ERREUR] Longitude invalide, doit être entre -180 et 180.", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Récupération météo pour lat={args.lat}, lon={args.lon} ...")

    try:
        raw_data = fetch_weather_mock(args.lat, args.lon)
    except requests.HTTPError as e:
        print(f"[ERREUR] API OpenWeatherMap : {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"[ERREUR] Réseau : {e}", file=sys.stderr)
        sys.exit(1)

    message = raw_data
    #message = format_message(raw_data, args.lat, args.lon)
    print(f"[INFO] Données formatées : {json.dumps(message, indent=2, ensure_ascii=False)}")

    try:
        send_to_kafka("weather_data", message)
    except KafkaError as e:
        print(f"[ERREUR] Kafka : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    #main()
    pass
