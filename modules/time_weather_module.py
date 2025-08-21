# modules/time_weather_module.py
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests
from zoneinfo import ZoneInfo

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Config opcional desde Config Vars (Heroku)
HOME_CITY = os.getenv("HOME_CITY", "").strip()          # p.ej. "Santo Domingo, DO"
HOME_LAT = os.getenv("HOME_LAT", "").strip()            # p.ej. "18.4861"
HOME_LON = os.getenv("HOME_LON", "").strip()            # p.ej. "-69.9312"
HOME_TZ  = os.getenv("HOME_TZ", "").strip()             # p.ej. "America/Santo_Domingo"

@dataclass
class Place:
    name: str
    country: str
    lat: float
    lon: float
    tz: str

# ---- utilidades internas ----

def _clean(s: Optional[str]) -> str:
    import re as _re
    return _re.sub(r"\s+", " ", (s or "")).strip()

def _from_env_home() -> Optional[Place]:
    try:
        if HOME_LAT and HOME_LON and HOME_TZ:
            return Place(
                name=HOME_CITY or "tu zona",
                country="",
                lat=float(HOME_LAT),
                lon=float(HOME_LON),
                tz=HOME_TZ,
            )
    except Exception:
        pass
    return None

def geocode_city(query: str) -> Optional[Place]:
    """Devuelve Place usando Open-Meteo Geocoding (sin API key)."""
    q = _clean(query)
    try:
        r = requests.get(GEOCODE_URL, params={
            "name": q, "count": 1, "language": "es", "format": "json"
        }, timeout=10)
        r.raise_for_status()
        j = r.json()
        results = j.get("results") or []
        if not results: 
            return None
        x = results[0]
        return Place(
            name=x.get("name", q),
            country=x.get("country_code", "") or x.get("country", ""),
            lat=float(x["latitude"]),
            lon=float(x["longitude"]),
            tz=x.get("timezone") or "UTC",
        )
    except Exception:
        return None

def _weather_desc_from_wmo(code: int) -> str:
    # Descripciones breves (tabla WMO resumida)
    table = {
        0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado", 3: "Nublado",
        45: "Niebla", 48: "Niebla con escarcha",
        51: "Llovizna ligera", 53: "Llovizna", 55: "Llovizna intensa",
        61: "Lluvia ligera", 63: "Lluvia", 65: "Lluvia fuerte",
        66: "Lluvia helada ligera", 67: "Lluvia helada fuerte",
        71: "Nieve ligera", 73: "Nieve", 75: "Nieve fuerte",
        77: "Granos de nieve", 80: "Chubascos ligeros", 81: "Chubascos", 82: "Chubascos fuertes",
        85: "Chubascos de nieve ligeros", 86: "Chubascos de nieve fuertes",
        95: "Tormenta", 96: "Tormenta con granizo", 99: "Tormenta fuerte con granizo",
    }
    return table.get(int(code), f"Código meteo {code}")

# ---- API públicas ----

def get_time(place: Optional[Place]) -> str:
    """Devuelve hora local del lugar (o de HOME_* si place=None y está configurado)."""
    if not place:
        place = _from_env_home()
        if not place:
            return ("⏰ Para 'mi zona' configura HOME_CITY o HOME_LAT/HOME_LON/HOME_TZ en Heroku.\n"
                    "Ej: HOME_CITY=Santo Domingo, DO  o  HOME_LAT=18.4861 HOME_LON=-69.9312 HOME_TZ=America/Santo_Domingo")
    try:
        now = datetime.now(ZoneInfo(place.tz))
        label = f"{place.name}, {place.country}".strip().strip(",")
        return f"⏰ Hora local en {label}: {now.strftime('%Y-%m-%d %H:%M')}"
    except Exception:
        # Fallback sin tz: hora UTC
        now = datetime.utcnow()
        label = f"{place.name}, {place.country}".strip().strip(",")
        return f"⏰ Hora (UTC) en {label}: {now.strftime('%Y-%m-%d %H:%M')}"

def get_weather(place: Optional[Place]) -> str:
    """Clima actual en el lugar dado (o 'mi zona' vía env vars)."""
    if not place:
        place = _from_env_home()
        if not place:
            return ("🌦️ Para 'mi zona' configura HOME_CITY o HOME_LAT/HOME_LON/HOME_TZ en Heroku.\n"
                    "Ej: HOME_CITY=Santo Domingo, DO  o  HOME_LAT=18.4861 HOME_LON=-69.9312 HOME_TZ=America/Santo_Domingo")
    try:
        resp = requests.get(FORECAST_URL, params={
            "latitude": place.lat,
            "longitude": place.lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
            "forecast_days": 1,
            "timezone": place.tz or "auto",
        }, timeout=10)
        resp.raise_for_status()
        j = resp.json().get("current", {})  # API v2.0 de Open-Meteo
        t = j.get("temperature_2m")
        st = j.get("apparent_temperature")
        rh = j.get("relative_humidity_2m")
        wcode = j.get("weather_code")
        wind = j.get("wind_speed_10m")
        desc = _weather_desc_from_wmo(wcode) if wcode is not None else "—"
        label = f"{place.name}, {place.country}".strip().strip(",")
        return (f"🌦️ Clima en {label}: {desc}. Temp {t}°C (sensación {st}°C), "
                f"humedad {rh}%, viento {wind} km/h.")
    except Exception:
        return "No pude obtener el clima ahora mismo."

# ---- Parseo básico de ubicación en texto ----

def extract_place_from_text(texto: str) -> Optional[str]:
    """
    Extrae algo como 'en Madrid', 'de Buenos Aires', 'para Bogotá'.
    Devuelve la cadena de ciudad si parece presente; si no, None.
    """
    t = _clean(texto).lower()
    m = re.search(r"(?:en|de|para|por|sobre)\s+([a-záéíóúüñ .,'-]{2,})$", t)
    if m:
        return m.group(1).strip(" .,'-")
    return None
