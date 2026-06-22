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
- **Onglet Alertes** : un interrupteur permet d'**activer les notifications**.
  La préférence est persistée (`page.client_storage`) et survit au redémarrage.
- **Notifications** : lorsqu'elles sont activées, chaque changement notable
  détecté par `WeatherNotifier.change_notifications` déclenche une notification :
  - stress thermique (THI en zone danger),
  - apparition de pluie (pulvérisation à reporter),
  - changement de condition (`Clear` → `Clouds`…).

  Le `NotificationService` (`logic/notification_service.py`) envoie une **vraie
  notification système Android** via `plyer` ; sur bureau / web (ou si `plyer`
  est absent) il retombe sur une SnackBar in-app.

### Notifications Android & arrière-plan

- L'interrogation de l'API tourne dans un **thread daemon** (`ApiWeatherClient`) :
  tant que le processus de l'app est vivant, les données continuent d'être
  demandées et les alertes évaluées — y compris quand on quitte l'onglet
  Dashboard ou que l'app passe brièvement en arrière-plan.
- **Limite à connaître** : Android peut *geler* le processus d'une app mise en
  arrière-plan prolongé. Pour garantir un polling permanent écran éteint, il faut
  un **foreground service** Android, que Flet 0.25 n'expose pas nativement. La
  solution implémentée ici couvre le cas « app active / récemment minimisée ».
- Lors du packaging (`flet build apk`), pensez à déclarer la permission
  `POST_NOTIFICATIONS` (Android 13+) pour que les notifications `plyer`
  s'affichent.
