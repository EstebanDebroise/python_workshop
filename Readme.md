# Agris App

## Goal of this project

The Goal of this project is to create an application to help the farmer to manage the weather.

2 main features :

- display some data like temp, rain or sun, ...

- calculate some indice to make advice

## Tools for this project

**python** : use for all code of this project

**docker** : used to containerize the broker, the Kafka UI, the API and the producer so they can run together with a single `docker compose up`

**OpenWeather** : the api to get the data (current weather endpoint, metric units)

**kafka** : message broker that decouples the producer from the mobile app — the producer publishes weather messages and the API reads them on demand

## Architecture overview

```
OpenWeatherMap API
       │  (HTTP)
       ▼
  [ producer ]  ──(Kafka topic)──►  [ broker ]  ◄──(read)──  [ api ]  ◄──(HTTP poll)──  [ mobile_app ]
                                        │
                                  [ kafka-ui ]  (monitoring, port 8080)
```

Data flow:
1. The **producer** asks the API which locations to watch, fetches current weather for each from OpenWeatherMap, and publishes a structured JSON message to the matching Kafka topic.
2. The **broker** (Apache Kafka in KRaft mode) stores the messages.
3. The **api** (FastAPI) exposes an HTTP interface used both by the mobile app (to read weather) and by the producer (to get the list of locations).
4. The **mobile_app** (Flet) polls the API in a background thread and updates the dashboard when a new measurement is available.

## Structure of the project

### mobile_app
Flet cross-platform application (desktop, web, Android/iOS).

Key files and folders:
- `main.py` — entry point, wires the setup screen → dashboard and manages the background API polling thread.
- `models.py` — immutable `Weather` dataclass built from raw Kafka JSON payloads.
- `api_client.py` — background thread that periodically calls `GET /weather/{topic}` and triggers UI callbacks.
- `logic/` — pure business logic, no UI dependency:
  - `thi_calculator.py` — Temperature-Humidity Index (THI) used to assess heat stress on livestock. Five levels: comfort / vigilance / alert / danger / emergency.
  - `pasture_analyzer.py` — generates grazing alerts (seek shelter from cold wind, provide shade in sun, hydration in heat, hypothermia risk).
  - `treatment_analyzer.py` — evaluates three treatment time slots (–2 h, now, +3 h) and marks each as ok / warn / no based on wind, rain and temperature.
  - `weather_notifier.py` — detects notable changes between two measurements (rain appearing, THI entering danger zone, condition change) and returns notification messages.
  - `notification_service.py` — sends Android system notifications via `plyer`; falls back to an in-app SnackBar on desktop/web.
- `ui/` — Flet widgets split into `conexion_pages/` (setup screen) and `dashboard_pages/` (main dashboard with header, weather cards, THI gauge, alerts, treatment slots).
- `i18n.py` + `langues/` — lightweight internationalisation (French / English).
- `theme.py` — shared colour palette.
- `config.example.json` — copy to `config.json` and set `api_base` to the API address (used when the `WEATHER_API_BASE` env var is absent, e.g. in an Android APK).

Environment variable:
| Variable | Default | Role |
|---|---|---|
| `WEATHER_API_BASE` | `http://ip_adress:8000` | Base URL of the intermediate API |

### api
FastAPI service acting as the bridge between the mobile app and Kafka.

Key files:
- `main.py` — FastAPI application with three endpoint families: health, weather, locations.
- `kafka_reader.py` — reads the latest message from a Kafka topic on demand and tracks the last-seen offset.
- `database.py` — SQLite repository (`locations.db`) for registered farm locations.
- `schemas.py` — Pydantic models and `normalize_topic()` helper (shared normalisation rule used by both the API and the mobile app).
- `config.py` — loads configuration from environment variables.

Endpoints:
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/weather/{topic}` | Latest weather message for a topic. Returns `is_new=true` if the offset advanced since the last call |
| POST | `/locations` | Register a farm location (idempotent — no duplicate if the topic already exists) |
| GET | `/locations` | List all registered locations |

Interactive docs auto-generated at `/docs` when the API is running.

Environment variables:
| Variable | Default | Role |
|---|---|---|
| `KAFKA_BOOTSTRAP` | `ip_adress:9092` | Kafka broker address |
| `KAFKA_READ_TIMEOUT_MS` | `5000` | Time budget for a Kafka read (ms) |
| `API_DB_PATH` | `api/locations.db` | Path to the SQLite file |

### producer
Python script that runs once (or on a schedule) to collect and publish weather data.

Key files:
- `manager.py` — entry point: fetches the topic list from the API, resolves coordinates for each, fetches weather from OpenWeatherMap, and publishes to Kafka.
- `weather_collector.py` — OpenWeatherMap HTTP client and Kafka publisher. Formats raw API responses into a structured JSON message (timestamp, coordinates, location, country, full weather payload).
- `retrive_lat_lon.py` — resolves a city name to (lat, lon) coordinates using `geopy`.

Environment variables (copy `env_example` to `.env`):
| Variable | Role |
|---|---|
| `OPENWEATHER_API_KEY` | Your OpenWeatherMap API key |
| `API_URL` | URL of the intermediate API |
| `OPENWEATHER_URL` | OpenWeatherMap current weather endpoint URL |
| `KAFKA_BROKER` | Kafka broker address (overridden to `broker:29092` inside Docker) |

## Test
Tests are located in `api/tests/` and cover the API layer.

Run them from the project root:
```bash
pip install -r api/requirements.txt
pytest api/tests/
```

With coverage report:
```bash
pytest api/tests/ --cov=api --cov-report=term-missing
```

Test files:
- `test_main.py` — endpoint integration tests (health, weather, locations)
- `test_database.py` — SQLite repository unit tests
- `test_kafka_reader.py` — Kafka reader unit tests (mocked broker)
- `test_schemas.py` — Pydantic schema and `normalize_topic` tests
- `test_config.py` — configuration loading tests

## how to deploy this project

### Prerequisites
- Docker and Docker Compose
- An OpenWeatherMap API key (free tier is sufficient)

### 1. Configure environment files

For the API, copy `api/env_example` to `api/.env` and fill in the values:
```
KAFKA_READ_TIMEOUT_MS=5000
API_DB_PATH=/data/locations.db
```

For the producer, copy `producer/env_example` to `producer/.env` and fill in:
```
OPENWEATHER_API_KEY=your_key_here
API_URL=http://ip_adress:8000
OPENWEATHER_URL=https://api.openweathermap.org/data/2.5/weather
KAFKA_BROKER=broker:29092
```

### 2. Start the infrastructure

From the project root:
```bash
docker compose up -d
```

This starts four services:
- `broker` — Apache Kafka (KRaft mode, port 9092)
- `kafka-ui` — Kafka web UI at http://ip_adress:8080
- `api` — FastAPI service at http://ip_adress:8000
- `producer` — set up cron to run each 5 minutes and file kafka broker with new data



### 5. Start the mobile app

```bash
cd mobile_app
flet build apk --split-per-abi
```
and install the apk on your machine, I use waydroid so the command is :
```bash
waydroid app install build/apk/mobile_app-x86_64.apk
```

Make sure `WEATHER_API_BASE` points to the running API 