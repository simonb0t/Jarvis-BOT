# modules/whatsapp_module.py
from __future__ import annotations

import re
from typing import Optional

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from modules.memory_module import guardar_idea, consultar_ideas
from modules.transcribe_module import descargar_media_twilio, transcribir_audio_bytes

app = Flask(__name__)

# =========================
# Constantes / utilidades
# =========================
MAX_PREVIEW_LEN = 180

def _clean(texto: Optional[str]) -> str:
    """Normaliza texto de entrada."""
    if not texto:
        return ""
    return re.sub(r"\s+", " ", texto).strip()

def _preview(t: str, n: int = MAX_PREVIEW_LEN) -> str:
    """Corta texto para mostrarlo en respuestas."""
    t = _clean(t)
    return (t[:n] + "…") if len(t) > n else t

def _as_int(value: Optional[str], default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        return default

# =========================
# Rutas (solo /whatsapp aquí)
# =========================
@app.get("/whatsapp")
def whatsapp_get() -> str:
    return "Endpoint WhatsApp OK (usa POST desde Twilio)"

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply() -> str:
    tw_resp = MessagingResponse()
    try:
        # Snapshot mínimo para depurar
        snapshot = {
            "Body": request.form.get("Body", ""),
            "NumMedia": request.form.get("NumMedia", "0"),
            "MediaContentType0": request.form.get("MediaContentType0", ""),
            "MediaUrl0": request.form.get("MediaUrl0", "")
        }
        print(snapshot)

        # 1) ¿Hay media adjunta? -> intentar transcribir audio(s)
        num_media = _as_int(request.form.get("NumMedia", "0"), 0)
        if num_media > 0:
            for i in range(num_media):
                ct = request.form.get(f"MediaContentType{i}", "") or ""
                url = request.form.get(f"MediaUrl{i}", "") or ""
                if url and _es_audio(ct, url):
                    try:
                        audio_bytes = descargar_media_twilio(url)
                        ext = _ext_por_content_type(ct, url)
                        texto = transcribir_audio_bytes(audio_bytes, filename=f"audio.{ext}")
                        texto = _clean(texto)
                        resp_text = respuesta_inteligente(texto)
                        tw_resp.message(f"📝 Transcripción: {texto}\n\n{resp_text}")
                        return str(tw_resp)
                    except Exception as e:
                        print(f"[transcripcion] fallo: {e}")
                        # Si falla la transcripción, continúa con el cuerpo de texto

        # 2) Sin audio: procesar texto
        body = _clean(request.form.get("Body", ""))
        tw_resp.message(respuesta_inteligente(body))
        return str(tw_resp)

    except Exception as e:
        print(f"[whatsapp] error: {e}")
        tw_resp.message("Hubo un error procesando tu mensaje. Intenta de nuevo.")
        return str(tw_resp)

# =========================
# Lógica de conversación
# =========================
def mejorar_texto_rapido(texto: str) -> str:
    base = _clean(texto)
    if len(base) < 10:
        return "Idea registrada. Siguiente paso: define objetivo y una acción concreta para hoy."
    return (
        f"{base}\n\n"
        "Siguiente paso: prioriza, define un resultado medible y agenda un bloque de 25 minutos."
    )

def listar_ultimas_ideas(n: int = 5) -> str:
    filas = consultar_ideas(limit=n)
    if not filas:
        return "Aún no tienes ideas registradas."
    out = ["🗂️ Últimas ideas:"]
    for _id, txt, fecha in filas:
        out.append(f"• {txt}  ({fecha})")
    return "\n".join(out)

def respuesta_inteligente(texto: str) -> str:
    """
    Responde reconociendo lo recibido y sugiere siguiente acción.
    Comandos:
      - 'idea ...'
      - 'opina: ...'
      - 'listar ideas' / 'resumen'
      - 'ayuda'
    """
    t = _clean(texto)
    low = t.lower()

    # --- comandos ---
    if low in ("ayuda", "help", "menu"):
        return (
            "📖 Comandos:\n"
            "• idea <texto> → guardo tu idea\n"
            "• opina: <texto> → la perfecciono y doy siguiente paso\n"
            "• listar ideas / resumen → ver últimas ideas\n"
            "También puedes mandarme un audio: lo transcribo y actúo."
        )

    if low in ("listar ideas", "resumen"):
        return listar_ultimas_ideas()

    if low.startswith("idea "):
        contenido = _clean(t[5:])
        if not contenido:
            return "Escribe la idea después de 'idea '. Ej: idea crear app de hábitos."
        guardar_idea(contenido, categoria="ideas", prioridad=2)
        return (
            f"✅ Guardé tu idea: “{contenido}”.\n"
            f"➡️ ¿La refino ahora? Escribe: opina: {contenido}"
        )

    if low.startswith("opina:"):
        contenido = _clean(t.split(":", 1)[1] if ":" in t else "")
        if not contenido:
            return "Escribe el contenido después de 'opina:'."
        return "🧠 " + mejorar_texto_rapido(contenido)

    if low in ("hola", "hola jarvis", "buenas", "hey", "ola"):
        return (
            "👋 ¡Hola! Dime tu idea con: `idea ...` o pídeme mejora con: `opina: ...`.\n"
            "También puedes mandarme un audio y lo transcribo."
        )

    # --- texto libre ---
    prev = _preview(t)
    if not prev:
        return "No recibí texto. Prueba 'ayuda' o envíame un audio."
    return (
        f"🎧 Entendí esto: “{prev}”.\n"
        f"• Guardarla como idea: `idea {t}`\n"
        f"• Perfeccionarla: `opina: {t}`\n"
        f"• Ver tus ideas: `listar ideas`"
    )

# =========================
# Detección de audio
# =========================
def _es_audio(content_type: str, url: str) -> bool:
    """
    Consideramos audio si:
      - content_type empieza por 'audio'
      - o es 'application/ogg'
      - o la URL termina en .ogg / .m4a / .aac / .mp3
    """
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
    return "ogg"  # default razonable para WhatsApp (opus/ogg)
