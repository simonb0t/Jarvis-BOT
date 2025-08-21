# modules/time_weather_module.py
from __future__ import annotations
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import requests
from zoneinfo import ZoneInfo

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Config desde Heroku (opcional)
HOME_CITY = os.getenv("HOME_CITY", "").strip()
HOME_LAT = os.getenv("HOME_LAT", "").strip()
HOME_LON = os.getenv("HOME_LON", "").strip()
HOME_TZ  = os.getenv("HOME_TZ", "").strip()

@dataclass
class Place:
    name: str
    country: str
    lat: float
    lon: float
    tz: str

def _clean(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def _from_env_home() -> Optional[Place]:
    try:
        if HOME_LAT and HOME_LON and HOME_TZ:
            return Place(
                name=HOME_CITY or "tu zona", country="",
                lat=float(HOME_LAT), lon=float(HOME_LON), tz=HOME_TZ
            )
        if HOME_CITY:
            return geocode_city(HOME_CITY)
    except Exception:
        pass
    return None

def geocode_city(query: str) -> Optional[Place]:
    q = _clean(query)
    try:
        r = requests.get(GEOCODE_URL, params={"name": q, "count": 1, "language": "es", "format": "json"}, timeout=10)
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

# -------- Hora --------
def get_time(place: Optional[Place]) -> str:
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
        now = datetime.utcnow()
        label = f"{place.name}, {place.country}".strip().strip(",")
        return f"⏰ Hora (UTC) en {label}: {now.strftime('%Y-%m-%d %H:%M')}"

# -------- Clima actual --------
def get_weather(place: Optional[Place]) -> str:
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
        j = resp.json().get("current", {})
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

# -------- Fechas (“domingo de esta semana”, etc.) --------
WEEKDAYS = {
    "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2, "jueves": 3,
    "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6
}

def _now_tz() -> datetime:
    tz = ZoneInfo(HOME_TZ) if HOME_TZ else ZoneInfo("UTC")
    return datetime.now(tz)

def next_weekday_date(weekday_name: str, same_week: bool = True) -> Optional[str]:
    wd = WEEKDAYS.get(weekday_name.lower())
    if wd is None:
        return None
    today = _now_tz().date()
    today_w = today.weekday()  # 0=lunes
    if same_week:
        # domingo de ESTA semana: mover dentro de la semana actual (lunes-domingo)
        # calcular lunes de esta semana:
        monday = today - timedelta(days=today_w)
        target = monday + timedelta(days=wd)
        # si el target ya pasó, igual devolvemos el de esta semana (pasado). Si prefieres próximo, cambia lógica.
    else:
        # próximo <día>
        delta = (wd - today_w) % 7
        delta = 7 if delta == 0 else delta
        target = today + timedelta(days=delta)
    return target.isoformat()

def answer_date_question(texto: str) -> Optional[str]:
    t = _clean(texto).lower()
    # “fecha de mañana”, “fecha de hoy”
    if "fecha de hoy" in t or (("hoy" in t) and "fecha" in t):
        return f"📅 Hoy es {_now_tz().date().isoformat()} ({HOME_TZ or 'UTC'})."
    if "fecha de mañana" in t or (("mañana" in t) and "fecha" in t):
        return f"📅 Mañana es {(_now_tz().date()+timedelta(days=1)).isoformat()} ({HOME_TZ or 'UTC'})."

    # “fecha del domingo de esta semana”
    m = re.search(r"fecha del?\s+([a-záéíóúüñ]+)\s+de\s+esta\s+semana", t)
    if m:
        day = m.group(1)
        d = next_weekday_date(day, same_week=True)
        if d:
            return f"📅 {day.title()} de esta semana es {d} ({HOME_TZ or 'UTC'})."

    # “próximo domingo”, “el próximo jueves”
    m2 = re.search(r"(?:proximo|próximo)\s+([a-záéíóúüñ]+)", t)
    if m2:
        day = m2.group(1)
        d = next_weekday_date(day, same_week=False)
        if d:
            return f"📅 Próximo {day.title()} es {d} ({HOME_TZ or 'UTC'})."

    return None

# ---- Parseo básico de ubicación en texto ----
def extract_place_from_text(texto: str) -> Optional[str]:
    t = _clean(texto).lower()
    m = re.search(r"(?:en|de|para|por|sobre)\s+([a-záéíóúüñ .,'-]{2,})$", t)
    if m:
        return m.group(1).strip(" .,'-")
    return None
