# API Météo Agri

API FastAPI servant d'intermédiaire entre l'application mobile et Kafka.

Elle évite que l'application n'accède directement à Kafka : l'app interroge
l'API en HTTP, et l'API se charge de lire Kafka et de gérer la base des lieux.

## Rôle

- **Lecture météo à la demande** : `GET /weather/{topic}` lit le dernier message
  du topic. S'il y a une nouvelle mesure depuis le dernier appel, elle est
  renvoyée avec `is_new=true` ; sinon la mesure du précédent offset est renvoyée
  avec `is_new=false`. Aucune donnée sur le topic ⇒ `status="empty"`.
- **Base des lieux** : `POST /locations` enregistre le lieu de la ferme d'un
  utilisateur (au moment du setup ou d'un changement de réglages). L'ajout est
  idempotent : un lieu déjà présent (même topic) n'est pas dupliqué.

## Endpoints

| Méthode | Chemin              | Description                                       |
|---------|---------------------|---------------------------------------------------|
| GET     | `/health`           | Vérifie que l'API répond.                         |
| GET     | `/weather/{topic}`  | Dernière mesure météo du topic.                   |
| POST    | `/locations`        | Ajoute un lieu (idempotent). Corps : `LocationIn`.|
| GET     | `/locations`        | Liste tous les lieux enregistrés.                 |

Documentation interactive auto-générée sur `/docs` une fois l'API lancée.

## Installation

```bash
pip install -r api/requirements.txt
```

## Lancement

Depuis la **racine du projet** (pour que le package `api` soit importable) :

```bash
uvicorn api.main:app --reload
```

L'API écoute par défaut sur `http://localhost:8000`.

## Configuration (variables d'environnement)

| Variable                | Défaut                  | Rôle                                     |
|-------------------------|-------------------------|------------------------------------------|
| `KAFKA_BOOTSTRAP`       | `localhost:9092`        | Adresse du broker Kafka.                 |
| `KAFKA_READ_TIMEOUT_MS` | `3000`                  | Budget temps d'une lecture Kafka.        |
| `API_DB_PATH`           | `api/locations.db`      | Chemin du fichier SQLite des lieux.      |

Côté application mobile, la variable `WEATHER_API_BASE`
(défaut `http://localhost:8000`) indique où joindre cette API.

## Base de données

SQLite (module standard `sqlite3`), fichier `api/locations.db` créé
automatiquement. Table `locations` : `id`, `name`, `topic` (unique),
`country`, `created_at`.
