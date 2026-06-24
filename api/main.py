from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from api import config
from api.database import LocationDB
from api.kafka_reader import KafkaReader
from api.schemas import (
    LocationIn,
    LocationOut,
    LocationResult,
    WeatherResponse,
    normalize_topic,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] ========================================")
    print("[INFO]  Météo Agri API starting up...")
    print(f"[INFO]  Kafka broker : {config.KAFKA_BOOTSTRAP}")
    print(f"[INFO]  Database     : {config.DB_PATH}")
    print("[INFO] ========================================")
    yield
    print("[INFO] API shutting down.")


app = FastAPI(
    title="Météo Agri — API",
    description="Middleware between the mobile app and Kafka.",
    version="1.0.0",
    lifespan=lifespan,
)

# Application dependencies instantiated once at module startup.
db = LocationDB(config.DB_PATH)
reader = KafkaReader()


@app.get("/health")
def health() -> dict[str, str]:
    """Checks that the API is responding. Does not test Kafka connectivity."""
    return {"status": "ok"}


@app.get("/weather/{topic}", response_model=WeatherResponse)
def get_weather(topic: str) -> WeatherResponse:
    """Return the latest available weather measurement for a topic.

    Reads Kafka on demand: if a measurement newer than the previous one is
    available, it is returned with ``is_new=True``; otherwise the measurement
    from the previous offset is returned with ``is_new=False``. If no data is
    available at all, ``status`` is ``"empty"``.

    Args:
        topic (str): Kafka topic name (typically the normalized city).

    Returns:
        WeatherResponse: Read status and, if applicable, the raw payload.
    """
    result = reader.read_latest(topic)
    return WeatherResponse(topic=topic, **result)


@app.post("/locations", response_model=LocationResult, status_code=201)
def add_location(payload: LocationIn) -> LocationResult:
    """Add a location to the database if it does not already exist (idempotent).

    The topic is derived from the name if ``payload.topic`` is not provided. If a
    location with the same topic already exists, it is returned as-is without
    duplication.

    Args:
        payload (LocationIn): Location to save (name, optional topic, country).

    Returns:
        LocationResult: Indicates whether the location was created and its record.

    Raises:
        HTTPException: 422 if the name does not produce a valid topic.
    """
    topic = (payload.topic or normalize_topic(payload.name)).strip()
    if not topic:
        raise HTTPException(status_code=422, detail="Nom de lieu invalide.")
    created, location = db.add_if_absent(payload.name.strip(), topic, payload.country)
    return LocationResult(created=created, location=location)


@app.get("/locations", response_model=list[LocationOut])
def list_locations() -> list[LocationOut]:
    """Returns the list of all registered locations."""
    return db.all()
