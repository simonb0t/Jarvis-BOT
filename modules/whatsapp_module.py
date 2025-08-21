# modules/whatsapp_module.py
from __future__ import annotations
import re
from typing import Optional, Dict

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from modules.memory_module import guardar_idea, consultar_ideas
from modules.transcribe_module import descargar_media_twilio, transcribir_audio_bytes

app = Flask(__name__)

# =========================
# Contexto por usuario
# =========================
# Clave: número (From), Valor: último texto comprendido (audio o texto)
ULTIMO_TEXTO: Dict[str, str] = {}

# =========================
# Utilidades
# =========================
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

# =========================
# Rutas (solo /whatsapp aquí)
# =========================
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

        # 1) Si llega audio, transcribe y RESPONDE con lógica
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
                        # Lógica de respuesta sobre lo transcrito
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

# =========================
# Lógica de conversación (modo discreto: sin sugerencias automáticas)
# =========================
CAPACIDADES = (
    "Puedo registrar ideas, perfeccionarlas cuando me lo pidas, transcribir audios, "
    "listar tus ideas y, si lo activamos, enviarte recordatorios."
)
LIMITES = (
    "No tengo voz de salida, no navego la web ni accedo a tus archivos locales. "
    "Guardo memoria básica (último mensaje e ideas)."
)

def mejorar_texto_rapido(texto: str) -> str:
    base = _clean(texto)
    if len(base) < 10:
        return "Idea muy breve. Siguiente paso: define objetivo y una acción concreta para hoy."
    return (
        f"{base}\n\n"
        "Siguiente paso: define un resultado medible y agenda un bloque de 25 minutos."
    )

def listar_ultimas_ideas(n: int = 5) -> str:
    filas = consultar_ideas(limit=n)
    if not filas:
        return "No hay ideas registradas."
    out = ["🗂️ Últimas ideas:"]
    for _id, txt, fecha in filas:
        out.append(f"• {txt}  ({fecha})")
    return "\n".join(out)

def responder(texto: str, phone: str) -> str:
    """
    Reglas:
      - SOLO actúo cuando me lo pides explícitamente (modo discreto).
      - Contesto preguntas directas (alcance, limitaciones, qué puedo hacer).
      - 'perfecciona/guárdala' actúan sobre el último texto de ese usuario.
    Comandos:
      • idea <texto>
      • opina: <texto>  | perfecciona / mejórala
      • guárdala / guardar
      • listar ideas  | resumen
      • ayuda
    """
    t = _clean(texto)
    low = t.lower()

    # Preguntas directas
    if any(k in low for k in ("limitaciones", "alcance")):
        return f"📌 Alcance: {CAPACIDADES}\n⚠️ {LIMITES}"
    if any(k in low for k in ("qué puedes hacer", "que puedes hacer", "como me ayudas", "que haces")):
        return f"🛠️ {CAPACIDADES}"

    # Ayuda
    if low in ("ayuda", "help", "menu"):
        return (
            "Comandos:\n"
            "• idea <texto>\n"
            "• opina: <texto>  | perfecciona\n"
            "• guárdala  | guardar\n"
            "• listar ideas  | resumen"
        )

    # Listar
    if low in ("listar ideas", "resumen"):
        return listar_ultimas_ideas()

    # Guardar explícito (usa último contexto)
    if low in ("guárdala", "guardala", "guardar", "registrar", "regístrala", "registrala"):
        ultimo = ULTIMO_TEXTO.get(phone, "")
        if not ultimo:
            return "No tengo nada para guardar. Envíame la idea o un audio primero."
        guardar_idea(ultimo, categoria="ideas", prioridad=2)
        return f"✅ Guardada: “{_preview(ultimo)}”."

    # Perfeccionar explícito (usa 'opina:' o el último contexto)
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

    # Idea explícita
    if low.startswith("idea "):
        contenido = _clean(t[5:])
        if not contenido:
            return "Escribe la idea después de 'idea '."
        guardar_idea(contenido, categoria="ideas", prioridad=2)
        return f"✅ Guardé tu idea: “{contenido}”."

    # Texto libre: solo reconocer (sin sugerencias)
    if not t:
        return "No recibí texto."
    return f"Entendido: “{_preview(t)}”."

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
