# Météo Agri — App Flet

Tableau de bord mobile pour agriculteurs qui consomme le topic Kafka `weather_data`.

## Installation

```bash
cd mobile_app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Lancement

Assurez‑vous que Kafka tourne (`docker compose up -d` à la racine) et que
le producteur publie sur `weather_data`.

```bash
# Bureau (fenêtre native)
python main.py

# Navigateur
flet run --web main.py

# Émulateur mobile (Android/iOS) via Flet
flet run --android main.py
```

Variables d'environnement :

- `KAFKA_BOOTSTRAP` (def. `localhost:9092`)
- `KAFKA_TOPIC` (def. `weather_data`)

## Fonctionnement

- **Dashboard** : température, ressenti, humidité, vent (+ rafales), pluie,
  pression, nuages — mis à jour à chaque message Kafka.
- **Notifications** : une bannière rouge + snackbar s'affiche quand
  `detect_alerts` repère un changement notable :
  - apparition de pluie / neige / précipitations,
  - changement de condition (`Clear` → `Clouds`…),
  - chute de température ≥ 3 °C,
  - rafales ≥ 15 m/s en hausse.
