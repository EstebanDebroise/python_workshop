"""Application FastAPI : intermédiaire entre l'app mobile et Kafka.

Expose trois familles d'endpoints :
  - santé : ``GET /health`` ;
  - météo : ``GET /weather/{topic}`` — lit la dernière mesure d'un topic Kafka ;
  - lieux : ``POST /locations`` (ajout idempotent) et ``GET /locations`` (liste).

Lancement (depuis la racine du projet) :
    uvicorn api.main:app --reload
"""

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
    description="Intermédiaire entre l'application mobile et Kafka.",
    version="1.0.0",
    lifespan=lifespan,
)

# Dépendances applicatives instanciées une fois au démarrage du module.
db = LocationDB(config.DB_PATH)
reader = KafkaReader()


@app.get("/health")
def health() -> dict[str, str]:
    """Vérifie que l'API répond. Ne teste pas la connectivité Kafka."""
    return {"status": "ok"}


@app.get("/weather/{topic}", response_model=WeatherResponse)
def get_weather(topic: str) -> WeatherResponse:
    """Renvoie la dernière mesure météo disponible pour un topic.

    Lit Kafka à la demande : si une mesure plus récente que la précédente est
    disponible, elle est renvoyée avec ``is_new=True`` ; sinon la mesure du
    précédent offset est renvoyée avec ``is_new=False``. En l'absence totale de
    données, ``status`` vaut ``"empty"``.

    Args:
        topic (str): Nom du topic Kafka (typiquement la ville normalisée).

    Returns:
        WeatherResponse: Statut de lecture et, le cas échéant, le payload brut.
    """
    result = reader.read_latest(topic)
    return WeatherResponse(topic=topic, **result)


@app.post("/locations", response_model=LocationResult, status_code=201)
def add_location(payload: LocationIn) -> LocationResult:
    """Ajoute un lieu à la base s'il n'existe pas déjà (idempotent).

    Le topic est dérivé du nom si ``payload.topic`` n'est pas fourni. Si un lieu
    avec le même topic existe déjà, il est renvoyé tel quel sans duplication.

    Args:
        payload (LocationIn): Lieu à enregistrer (nom, topic optionnel, pays).

    Returns:
        LocationResult: Indique si le lieu a été créé et son enregistrement.

    Raises:
        HTTPException: 422 si le nom ne produit aucun topic valide.
    """
    topic = (payload.topic or normalize_topic(payload.name)).strip()
    if not topic:
        raise HTTPException(status_code=422, detail="Nom de lieu invalide.")
    created, location = db.add_if_absent(payload.name.strip(), topic, payload.country)
    return LocationResult(created=created, location=location)


@app.get("/locations", response_model=list[LocationOut])
def list_locations() -> list[LocationOut]:
    """Retourne la liste de tous les lieux enregistrés."""
    return db.all()
