"""Schémas Pydantic des requêtes/réponses de l'API et utilitaire de normalisation."""

from __future__ import annotations

import re
from typing import Any, Optional

from pydantic import BaseModel, Field


def normalize_topic(name: str) -> str:
    """Normalise un nom de lieu en nom de topic Kafka.

    Reprend exactement la règle appliquée côté application mobile : minuscules,
    et remplacement de tout caractère non alphanumérique (hors ``_ . -``) par ``_``.
    Garantit qu'un même lieu produit toujours le même topic des deux côtés.

    Args:
        name (str): Nom de lieu brut saisi par l'utilisateur (ex. ``"Saint-Lô"``).

    Returns:
        str: Topic normalisé (ex. ``"saint-lô"`` → ``"saint-l_"``).
    """
    return re.sub(r"[^A-Za-z0-9_.\-]", "_", name.strip().lower())


class LocationIn(BaseModel):
    """Corps de requête pour l'ajout d'un lieu à la base de données.

    Attributs :
        name (str): Nom du lieu (ville de la ferme), non vide.
        topic (str | None): Topic Kafka associé. S'il est absent, il est dérivé
            automatiquement de ``name`` via :func:`normalize_topic`.
        country (str | None): Code ou nom de pays optionnel.
    """

    name: str = Field(..., min_length=1)
    topic: Optional[str] = None
    country: Optional[str] = None


class LocationOut(BaseModel):
    """Représentation d'un lieu tel que stocké en base et renvoyé par l'API."""

    id: int
    name: str
    topic: str
    country: Optional[str] = None
    created_at: str


class LocationResult(BaseModel):
    """Résultat d'un ajout de lieu : indique s'il a été créé ou s'il existait déjà.

    Attributs :
        created (bool): ``True`` si le lieu vient d'être inséré, ``False`` s'il
            était déjà présent (aucune duplication n'est faite).
        location (LocationOut): Le lieu correspondant en base.
    """

    created: bool
    location: LocationOut


class WeatherResponse(BaseModel):
    """Réponse de l'endpoint météo.

    Attributs :
        topic (str): Topic interrogé.
        status (str): ``"ok"`` (donnée disponible), ``"empty"`` (aucune donnée sur
            le topic) ou ``"error"`` (problème de lecture Kafka).
        is_new (bool): ``True`` si la mesure renvoyée est plus récente que la
            dernière déjà servie pour ce topic ; ``False`` si c'est la donnée du
            précédent offset (rien de nouveau).
        offset (int | None): Offset Kafka de la mesure renvoyée.
        message (dict | None): Payload brut de la mesure (format identique à celui
            publié par le producer), directement exploitable par l'app mobile.
        detail (str | None): Message d'explication en cas de ``status`` non ``ok``.
    """

    topic: str
    status: str
    is_new: bool = False
    offset: Optional[int] = None
    message: Optional[dict[str, Any]] = None
    detail: Optional[str] = None
