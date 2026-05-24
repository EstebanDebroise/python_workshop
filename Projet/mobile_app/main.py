"""Tableau de bord météo agriculteur (Flet).

Consomme le topic Kafka `weather_data`, affiche les indicateurs sous
forme de cartes et déclenche une notification (bannière) en cas de
changement météo (apparition de pluie/neige, basculement de condition,
chute de température, rafales).
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import flet as ft
from kafka import KafkaConsumer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "weather_data")

RAIN_CONDITIONS = {"Rain", "Drizzle", "Thunderstorm"}
SNOW_CONDITIONS = {"Snow"}


@dataclass
class WeatherSnapshot:
    location: str
    country: str
    condition: str
    description: str
    temperature_c: float
    feels_like_c: float
    humidity_pct: int
    pressure_hpa: int
    wind_speed_ms: float
    wind_gust_ms: Optional[float]
    rain_1h_mm: Optional[float]
    snow_1h_mm: Optional[float]
    clouds_pct: int
    visibility_m: int
    timestamp: str

    @classmethod
    def from_message(cls, msg: dict) -> "WeatherSnapshot":
        w = msg.get("weather", {})
        return cls(
            location=msg.get("location", "—"),
            country=msg.get("country", ""),
            condition=w.get("condition", "—"),
            description=w.get("description", ""),
            temperature_c=w.get("temperature_c", 0.0),
            feels_like_c=w.get("feels_like_c", 0.0),
            humidity_pct=w.get("humidity_pct", 0),
            pressure_hpa=w.get("pressure_hpa", 0),
            wind_speed_ms=w.get("wind_speed_ms", 0.0),
            wind_gust_ms=w.get("wind_gust_ms"),
            rain_1h_mm=w.get("rain_1h_mm"),
            snow_1h_mm=w.get("snow_1h_mm"),
            clouds_pct=w.get("clouds_pct", 0),
            visibility_m=w.get("visibility_m", 0),
            timestamp=msg.get("timestamp", ""),
        )


def detect_alerts(prev: Optional[WeatherSnapshot], curr: WeatherSnapshot) -> list[str]:
    """Compare deux mesures successives et renvoie la liste d'alertes."""
    alerts: list[str] = []

    if curr.condition in RAIN_CONDITIONS and (prev is None or prev.condition not in RAIN_CONDITIONS):
        alerts.append(f"Pluie prévue : {curr.description}")
    if curr.condition in SNOW_CONDITIONS and (prev is None or prev.condition not in SNOW_CONDITIONS):
        alerts.append(f"Neige prévue : {curr.description}")
    if curr.rain_1h_mm and (not prev or not prev.rain_1h_mm):
        alerts.append(f"Précipitations en cours : {curr.rain_1h_mm} mm/h")

    if prev is not None:
        if prev.condition != curr.condition and curr.condition not in RAIN_CONDITIONS | SNOW_CONDITIONS:
            alerts.append(f"Changement de temps : {prev.condition} → {curr.condition}")
        if curr.temperature_c - prev.temperature_c <= -3:
            alerts.append(f"Chute de température : {prev.temperature_c}°C → {curr.temperature_c}°C")
        if curr.wind_gust_ms and curr.wind_gust_ms >= 15 and (not prev.wind_gust_ms or curr.wind_gust_ms - prev.wind_gust_ms >= 5):
            alerts.append(f"Rafales fortes : {curr.wind_gust_ms} m/s")

    return alerts


def metric_card(icon: str, label: str, value: str, color: str) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(icon, color=color, size=22), ft.Text(label, size=13, color=ft.Colors.GREY_700)]),
                ft.Text(value, size=22, weight=ft.FontWeight.BOLD),
            ],
            spacing=4,
        ),
        bgcolor=ft.Colors.WHITE,
        padding=14,
        border_radius=12,
        expand=True,
        shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
    )


def main(page: ft.Page):
    page.title = "Météo Agri"
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.padding = 16
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    header_location = ft.Text("En attente de données…", size=22, weight=ft.FontWeight.BOLD)
    header_condition = ft.Text("—", size=15, color=ft.Colors.GREY_700)
    header_temp = ft.Text("--°C", size=44, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
    header_time = ft.Text("", size=11, color=ft.Colors.GREY_600)

    alert_banner = ft.Container(visible=False)

    c_feels = metric_card(ft.Icons.THERMOSTAT, "Ressenti", "--", ft.Colors.ORANGE)
    c_hum = metric_card(ft.Icons.WATER_DROP, "Humidité", "--", ft.Colors.BLUE)
    c_wind = metric_card(ft.Icons.AIR, "Vent", "--", ft.Colors.TEAL)
    c_rain = metric_card(ft.Icons.UMBRELLA, "Pluie 1h", "--", ft.Colors.INDIGO)
    c_press = metric_card(ft.Icons.SPEED, "Pression", "--", ft.Colors.PURPLE)
    c_clouds = metric_card(ft.Icons.CLOUD, "Nuages", "--", ft.Colors.BLUE_GREY)

    grid = ft.Column(
        [
            ft.Row([c_feels, c_hum], spacing=12),
            ft.Row([c_wind, c_rain], spacing=12),
            ft.Row([c_press, c_clouds], spacing=12),
        ],
        spacing=12,
    )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Row([ft.Icon(ft.Icons.AGRICULTURE, color=ft.Colors.GREEN_700), ft.Text("Tableau de bord agriculteur", size=14, color=ft.Colors.GREEN_900)]),
                    header_location,
                    header_condition,
                    header_temp,
                    header_time,
                ],
                spacing=4,
            ),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
        ),
        alert_banner,
        ft.Container(height=4),
        ft.Text("Indicateurs", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
        grid,
    )

    def update_card(card: ft.Container, value: str) -> None:
        card.content.controls[1].value = value

    def update_ui(snap: WeatherSnapshot, alerts: list[str]) -> None:
        header_location.value = f"{snap.location}, {snap.country}"
        header_condition.value = snap.description.capitalize()
        header_temp.value = f"{snap.temperature_c:.1f}°C"
        try:
            ts = datetime.fromisoformat(snap.timestamp.replace("Z", "+00:00"))
            header_time.value = f"Mis à jour : {ts.strftime('%d/%m %H:%M')}"
        except Exception:
            header_time.value = snap.timestamp

        update_card(c_feels, f"{snap.feels_like_c:.1f}°C")
        update_card(c_hum, f"{snap.humidity_pct}%")
        gust = f" (raf. {snap.wind_gust_ms:.0f})" if snap.wind_gust_ms else ""
        update_card(c_wind, f"{snap.wind_speed_ms:.1f} m/s{gust}")
        update_card(c_rain, f"{snap.rain_1h_mm or 0} mm")
        update_card(c_press, f"{snap.pressure_hpa} hPa")
        update_card(c_clouds, f"{snap.clouds_pct}%")

        if alerts:
            alert_banner.content = ft.Column(
                [
                    ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.WHITE), ft.Text("Alerte météo", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)]),
                    *[ft.Text(f"• {a}", color=ft.Colors.WHITE) for a in alerts],
                ],
                spacing=2,
            )
            alert_banner.bgcolor = ft.Colors.RED_600
            alert_banner.padding = 14
            alert_banner.border_radius = 12
            alert_banner.visible = True
            try:
                page.open(ft.SnackBar(ft.Text(alerts[0]), bgcolor=ft.Colors.RED_700))
            except Exception:
                pass

        page.update()

    def consume() -> None:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=True,
                group_id="flet-dashboard",
            )
        except Exception as e:
            header_location.value = f"Erreur Kafka : {e}"
            page.update()
            return

        prev: Optional[WeatherSnapshot] = None
        for message in consumer:
            try:
                snap = WeatherSnapshot.from_message(message.value)
            except Exception:
                continue
            alerts = detect_alerts(prev, snap)
            prev = snap
            update_ui(snap, alerts)

    threading.Thread(target=consume, daemon=True).start()


if __name__ == "__main__":
    ft.app(target=main)
