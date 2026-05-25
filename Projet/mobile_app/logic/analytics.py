"""Logique métier pure : calculs THI, alertes pâturage, créneaux traitement.

Aucune dépendance Flet — ces fonctions sont testables unitairement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Optional

from models import Weather

ZoneKind = Literal["ok", "warn", "danger"]
SlotStatus = Literal["ok", "warn", "no"]
PastureKind = Literal["cold", "sun", "warn"]


# ---------- THI ----------

@dataclass(frozen=True)
class ThiResult:
    """Résultat enrichi du calcul THI.

    Regroupe la valeur numérique, l'étiquette d'affichage, un token
    couleur (résolu côté UI), une description destinée à l'éleveur et
    la catégorie ``kind`` utilisée pour colorer les badges.
    """

    value: float
    label: str
    color_token: str
    description: str
    kind: ZoneKind


def compute_thi(temp_c: float, humidity_pct: float) -> float:
    """Calcule l'indice THI (Temperature Humidity Index) pour le bétail.

    Formule de référence (NRC) utilisée en élevage :
    ``THI = T_f − (0.55 − 0.0055·RH) · (T_f − 58)`` avec ``T_f`` en
    Fahrenheit et ``RH`` en pourcentage.
    """
    t_f = 1.8 * temp_c + 32
    return t_f - (0.55 - 0.0055 * humidity_pct) * (t_f - 58)


def thi_result(temp_c: float, humidity_pct: float) -> ThiResult:
    """Calcule le THI puis le classe dans une des cinq zones bétail.

    Les seuils (68 / 72 / 79 / 84) correspondent aux paliers usuels :
    confort, vigilance, alerte, danger, urgence.
    """
    thi = compute_thi(temp_c, humidity_pct)
    if thi < 68:
        return ThiResult(thi, "Zone confort", "green", "Conditions normales. Pas de stress thermique.", "ok")
    if thi < 72:
        return ThiResult(thi, "Zone vigilance", "amber", "Léger stress. Surveiller l'abreuvement.", "warn")
    if thi < 79:
        return ThiResult(thi, "Zone alerte", "orange", "Stress modéré : production en baisse. Ombre & eau.", "warn")
    if thi < 84:
        return ThiResult(thi, "Zone danger", "red", "Stress sévère. Ventilation, brumisation requises.", "danger")
    return ThiResult(thi, "Zone urgence", "darkred", "Risque mortel. Action immédiate obligatoire.", "danger")


# ---------- pâturage ----------

@dataclass(frozen=True)
class PastureAlert:
    """Alerte de confort au pré générée à partir d'un :class:`Weather`."""

    icon: str
    message: str
    kind: PastureKind


def pasture_alerts(w: Weather) -> list[PastureAlert]:
    """Évalue les conditions de pâturage et renvoie les alertes pertinentes.

    Couvre quatre situations : vent + ressenti froid (abriter les jeunes),
    ciel dégagé sans vent par chaleur (ombre obligatoire), forte chaleur
    (multiplier les points d'eau) et froid + vent (risque hypothermie).
    """
    alerts: list[PastureAlert] = []
    feels_diff = w.feels_like_c - w.temperature_c
    if feels_diff <= -3 and w.wind_speed_ms >= 5:
        alerts.append(PastureAlert(
            "home_work",
            f"Vent fort → ressenti {feels_diff:+.0f}°C. Abriter veaux et agneaux.",
            "cold",
        ))
    if w.temperature_c >= 25 and w.clouds_pct <= 10 and w.wind_speed_ms <= 1:
        alerts.append(PastureAlert(
            "wb_sunny",
            "Ciel dégagé + air immobile → ensoleillement maximal. Ombre obligatoire.",
            "sun",
        ))
    if w.temperature_c >= 30:
        alerts.append(PastureAlert(
            "local_drink",
            "Chaleur élevée : doubler les points d'eau du troupeau.",
            "warn",
        ))
    if w.temperature_c <= 5 and w.wind_speed_ms >= 4:
        alerts.append(PastureAlert(
            "ac_unit",
            "Froid + vent : risque hypothermie pour les jeunes.",
            "cold",
        ))
    return alerts


# ---------- créneaux pulvérisation ----------

@dataclass(frozen=True)
class TreatmentSlot:
    """Créneau horaire évalué pour une opération de pulvérisation."""

    label: str
    wind: float
    rain: float
    temp: float
    status: SlotStatus


def _slot_status(wind: float, rain: float, temp: float) -> SlotStatus:
    """Classe un créneau (ok/warn/no) selon vent, pluie et température.

    Seuils retenus : ``vent ≥ 7 m/s``, ``pluie ≥ 1 mm`` ou ``T ≥ 32°C``
    interdisent l'opération ; au-dessus de seuils intermédiaires, le
    créneau est considéré risqué.
    """
    if wind >= 7 or rain >= 1 or temp >= 32:
        return "no"
    if wind >= 4 or rain >= 0.2 or temp >= 28:
        return "warn"
    return "ok"


def treatment_slots(w: Weather, now: Optional[datetime] = None) -> list[TreatmentSlot]:
    """Génère 3 créneaux (–2 h / maintenant / +3 h) évalués avec ``w``.

    Les facteurs ``wind_factor`` simulent la variabilité du vent autour
    de l'heure courante en l'absence de données prévisionnelles. Le
    paramètre ``now`` est injectable pour faciliter les tests.
    """
    base = (now or datetime.now()).replace(minute=0, second=0, microsecond=0)
    out: list[TreatmentSlot] = []
    for offset_h, wind_factor, extra_rain in [(-2, 0.5, 0.0), (0, 1.0, 0.0), (3, 0.7, w.rain_1h_mm or 0.0)]:
        start = base + timedelta(hours=offset_h)
        wind = w.wind_speed_ms * wind_factor
        rain = extra_rain
        temp = w.temperature_c
        out.append(TreatmentSlot(
            label=f"{start.strftime('%H:%M')}–{(start + timedelta(hours=2)).strftime('%H:%M')}",
            wind=wind, rain=rain, temp=temp,
            status=_slot_status(wind, rain, temp),
        ))
    return out


# ---------- notifications de changement ----------

def change_notifications(prev: Optional[Weather], curr: Weather) -> list[str]:
    """Compare deux mesures successives et liste les changements notables.

    Émet une notification quand le THI franchit le seuil danger,
    quand la pluie démarre ou quand la condition (``Clear``, ``Rain``…)
    change. Renvoie une liste vide pour la toute première mesure.
    """
    if prev is None:
        return []
    msgs: list[str] = []
    thi_prev = compute_thi(prev.temperature_c, prev.humidity_pct)
    thi_now = compute_thi(curr.temperature_c, curr.humidity_pct)
    if thi_now >= 79 > thi_prev:
        msgs.append("Stress thermique : zone danger atteinte (THI)")
    rain_prev = prev.rain_1h_mm or 0
    rain_now = curr.rain_1h_mm or 0
    if rain_now > 0 and rain_prev == 0:
        msgs.append("Pluie en cours — pulvérisation à reporter")
    if curr.condition != prev.condition:
        msgs.append(f"Changement de temps : {prev.condition} → {curr.condition}")
    return msgs


# ---------- divers ----------

WEATHER_ICONS = {
    "rain": ("water_drop", "rain"),
    "drizzle": ("water_drop", "rain"),
    "snow": ("ac_unit", "snow"),
    "cloud": ("cloud", "cloud"),
    "storm": ("flash_on", "storm"),
    "thunder": ("flash_on", "storm"),
}


def icon_for_condition(condition: str) -> tuple[str, str]:
    """Associe une condition OpenWeather à un couple (icône, token couleur).

    La recherche se fait par sous-chaîne pour absorber les variantes
    (``light rain``, ``thunderstorm``, etc.). Renvoie un soleil par
    défaut si aucune correspondance n'est trouvée.
    """
    c = (condition or "").lower()
    for key, value in WEATHER_ICONS.items():
        if key in c:
            return value
    return ("wb_sunny", "sun")
