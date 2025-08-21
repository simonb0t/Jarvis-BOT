# modules/whatsapp_module.py
from __future__ import annotations
import re
from typing import Optional, Dict

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from modules.memory_module import guardar_idea, consultar_ideas
from modules.transcribe_module import descargar_media_twilio, transcribir_audio_bytes
from modules.web_search_module import web_answer, web_images_answer
from modules.time_weather_module import (
    extract_place_from_text, geocode_city, get_time, get_weather, answer_date_question
)

# Import opcional (si no lo tienes, no rompe)
try:
    from modules.knowledge_module import responder_conocimiento  # type: ignore
except Exception:
    responder_conocimiento = None  # noqa

app = Flask(__name__)

# ===== Contexto por usuario =====
ULTIMO_TEXTO: Dict[str, str] = {}

# ===== Utilidades =====
MAX_PREVIEW_LEN = 180

def _clean(s: Optional[str]) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()

def _preview(t: str, n: int = MAX_PREVIEW_LEN) -> str:
    t = _clean(t)
    return (t[:n] + "…") if len(t) > n else t

def _as_int(v: Optional[str], default: int = 0) -> int:
    try:
        return int(v or default)
    except Exception:
        return default

def _looks_like_question(t: str) -> bool:
    low = t.lower()
    return ("?" in t or
            low.startswith(("qué", "que", "cómo", "como", "cuánto", "cuanta", "cuando", "dónde", "donde", "por qué", "porque")))

def _is_time_intent(low: str) -> bool:
    return any(k in low for k in ("hora", "qué hora", "que hora", "time"))

def _is_weather_intent(low: str) -> bool:
    return any(k in low for k in ("clima", "tiempo", "temperatura", "pronóstico", "pronostico", "weather"))

def _is_image_intent(low: str) -> bool:
    return any(k in low for k in ("imagen", "imágenes", "imagenes", "foto", "fotos", "picture", "image"))

# ===== Rutas =====
@app.get("/whatsapp")
def whatsapp_get() -> str:
    return "Endpoint WhatsApp OK (usa POST desde Twilio)"

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply() -> str:
    tw = MessagingResponse()
    try:
        phone = request.form.get("From", "desconocido")
        snapshot = {
            "From": phone,
            "Body": request.form.get("Body", ""),
            "NumMedia": request.form.get("NumMedia", "0"),
            "MediaContentType0": request.form.get("MediaContentType0", ""),
            "MediaUrl0": request.form.get("MediaUrl0", "")
        }
        print(snapshot)

        # 1) Audio: transcribe y responde con lógica
        num_media = _as_int(request.form.get("NumMedia", "0"), 0)
        if num_media > 0:
            for i in range(num_media):
                ct = request.form.get(f"MediaContentType{i}", "") or ""
                url = request.form.get(f"MediaUrl{i}", "") or ""
                if url and _es_audio(ct, url):
                    try:
                        audio_bytes = descargar_media_twilio(url)
                        ext = _ext_por_content_type(ct, url)
                        texto = _clean(transcribir_audio_bytes(audio_bytes, filename=f"audio.{ext}"))
                        if texto:
                            ULTIMO_TEXTO[phone] = texto
                        resp_texto = responder(texto, phone)
                        tw.message(f"📝 Transcripción: {texto}\n\n{resp_texto}")
                        return str(tw)
                    except Exception as e:
                        print(f"[transcripcion] fallo: {e}")
                        tw.message("No pude transcribir el audio ahora.")
                        return str(tw)

        # 2) Texto normal
        body = _clean(request.form.get("Body", ""))
        if body:
            ULTIMO_TEXTO[phone] = body
        tw.message(responder(body, phone))
        return str(tw)

    except Exception as e:
        print(f"[whatsapp] error: {e}")
        tw = MessagingResponse()
        tw.message("Hubo un error procesando tu mensaje. Intenta de nuevo.")
        return str(tw)

# ===== Conversación (modo discreto) =====
CAPACIDADES = (
    "Registro y perfeccionamiento de ideas, transcripción de audios, hora y clima de tu zona o de cualquier ciudad, "
    "búsqueda en la web (resumen + fuentes) y listados de tus ideas."
)
LIMITES = (
    "Sin voz de salida ni acceso a archivos/servicios privados. Memoria básica (último mensaje e ideas)."
)

def mejorar_texto_rapido(texto: str) -> str:
    base = _clean(texto)
    if len(base) < 10:
        return "Idea muy breve. Siguiente paso: define objetivo y una acción concreta para hoy."
    return f"{base}\n\nSiguiente paso: define un resultado medible y agenda un bloque de 25 minutos."

def listar_ultimas_ideas(n: int = 5) -> str:
    filas = consultar_ideas(limit=n)
    if not filas:
        return "No hay ideas registradas."
    out = ["🗂️ Últimas ideas:"]
    for _id, txt, fecha in filas:
        out.append(f"• {txt}  ({fecha})")
    return "\n".join(out)

def responder(texto: str, phone: str) -> str:
    t = _clean(texto)
    low = t.lower()

    # 0) Conocimiento local opcional
    if responder_conocimiento:
        try:
            resp_local = responder_conocimiento(t)
            if resp_local:
                return resp_local
        except Exception as e:
            print(f"[knowledge] fallo: {e}")

    # A) Fechas concretas
    resp_fecha = answer_date_question(t)
    if resp_fecha:
        return resp_fecha

    # B) Hora / Clima / Imágenes
    if _is_time_intent(low):
        is_my_zone = any(k in low for k in ("mi zona", "aquí", "aqui"))
        place = None if is_my_zone else (geocode_city(extract_place_from_text(t) or t) if extract_place_from_text(t) or len(t.split())<=5 else None)
        return get_time(place)

    if _is_weather_intent(low):
        is_my_zone = any(k in low for k in ("mi zona", "aquí", "aqui"))
        place = None if is_my_zone else (geocode_city(extract_place_from_text(t) or t) if extract_place_from_text(t) or len(t.split())<=5 else None)
        return get_weather(place)

    if _is_image_intent(low):
        # elimina la palabra 'imagen/foto de' para mejorar consulta
        q = re.sub(r"\b(imagen(es)?|foto(s)?|de|del|la|el)\b", " ", low)
        q = _clean(q)
        return web_images_answer(q or t)

    # C) Pregunta general → web
    if t and _looks_like_question(t):
        try:
            return web_answer(t)
        except Exception as e:
            print(f"[web] fallo: {e}")

    # D) Ayuda
    if low in ("ayuda", "help", "menu"):
        return (
            "Comandos:\n"
            "• hora [en <ciudad>]  | hora de mi zona\n"
            "• clima/temperatura/pronóstico [en <ciudad>] | clima de mi zona\n"
            "• imagen de <tema/persona>\n"
            "• idea <texto>  | opina: <texto>  | perfecciona  | guárdala\n"
            "• listar ideas  | resumen"
        )

    # E) Listar
    if low in ("listar ideas", "resumen"):
        return listar_ultimas_ideas()

    # F) Guardar/Perfeccionar
    if low in ("guárdala", "guardala", "guardar", "registrar", "regístrala", "registrala"):
        ultimo = ULTIMO_TEXTO.get(phone, "")
        if not ultimo:
            return "No tengo nada para guardar. Envíame la idea o un audio primero."
        guardar_idea(ultimo, categoria="ideas", prioridad=2)
        return f"✅ Guardada: “{_preview(ultimo)}”."

    if low.startswith("opina:"):
        contenido = _clean(t.split(":", 1)[1] if ":" in t else "")
        if not contenido:
            return "Escribe el contenido después de 'opina:'."
        return "🧠 " + mejorar_texto_rapido(contenido)

    if low in ("perfecciona", "perfecciónala", "perfeccionala", "mejora", "mejórala", "mejorala"):
        ultimo = ULTIMO_TEXTO.get(phone, "")
        if not ultimo:
            return "No tengo contexto para perfeccionar. Envíame la idea o un audio primero."
        return "🧠 " + mejorar_texto_rapido(ultimo)

    # G) Idea explícita
    if low.startswith("idea "):
        contenido = _clean(t[5:])
        if not contenido:
            return "Escribe la idea después de 'idea '."
        guardar_idea(contenido, categoria="ideas", prioridad=2)
        return f"✅ Guardé tu idea: “{contenido}”."

    # H) Texto libre
    if not t:
        return "No recibí texto."
    return f"Entendido: “{_preview(t)}”."

# ===== Detección de audio =====
def _es_audio(content_type: str, url: str) -> bool:
    ct = (content_type or "").lower()
    u = (url or "").lower()
    if ct.startswith("audio"):
        return True
    if ct == "application/ogg":
        return True
    return u.endswith(".ogg") or u.endswith(".m4a") or u.endswith(".aac") or u.endswith(".mp3")

def _ext_por_content_type(content_type: str, url: str) -> str:
    ct = (content_type or "").lower()
    u = (url or "").lower()
    if "ogg" in ct or "opus" in ct or u.endswith(".ogg"):
        return "ogg"
    if "aac" in ct or u.endswith(".aac"):
        return "aac"
    if "m4a" in ct or "mp4" in ct or u.endswith(".m4a") or u.endswith(".mp4"):
        return "m4a"
    if "mp3" in ct or u.endswith(".mp3"):
        return "mp3"
    return "ogg"
