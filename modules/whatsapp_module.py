# modules/whatsapp_module.py
from __future__ import annotations
import os, re
from typing import Optional, Dict, Tuple

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from modules.memory_module import guardar_idea, consultar_ideas
from modules.transcribe_module import descargar_media_twilio, transcribir_audio_bytes

# ========= App =========
app = Flask(__name__)

# ========= Memoria ligera por usuario =========
# Clave: número WhatsApp ("From")
CTX: Dict[str, Dict[str, str]] = {}  # {"last_text": "...", "last_intent": "..."}

# ========= Config LLM opcional =========
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
USE_LLM = bool(OPENAI_API_KEY)

def llm_respond(system: str, user: str, model: str = "gpt-4o-mini") -> str:
    """Pequeño helper para llamar al LLM si hay API; si no, levanta excepción."""
    if not USE_LLM:
        raise RuntimeError("LLM_OFF")
    from openai import OpenAI
    cli = OpenAI(api_key=OPENAI_API_KEY)
    resp = cli.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
    )
    return resp.choices[0].message.content.strip()

# ========= Utilidades =========
MAX_PREVIEW_LEN = 180

def _clean(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def _preview(t: str, n: int = MAX_PREVIEW_LEN) -> str:
    t = _clean(t)
    return (t[:n] + "…") if len(t) > n else t

def _as_int(v: Optional[str], default: int = 0) -> int:
    try: return int(v or default)
    except: return default

def _get_ctx(phone: str) -> Dict[str, str]:
    if phone not in CTX: CTX[phone] = {"last_text":"", "last_intent":""}
    return CTX[phone]

# ========= Rutas =========
@app.get("/whatsapp")
def whatsapp_get() -> str:
    return "Endpoint WhatsApp OK (usa POST desde Twilio)"

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply() -> str:
    tw = MessagingResponse()
    try:
        phone = request.form.get("From", "desconocido")
        snap = {
            "From": phone,
            "Body": request.form.get("Body",""),
            "NumMedia": request.form.get("NumMedia","0"),
            "MediaContentType0": request.form.get("MediaContentType0",""),
            "MediaUrl0": request.form.get("MediaUrl0",""),
        }
        print(snap)
        ctx = _get_ctx(phone)

        # 1) Audios → transcribir y SOLO confirmar transcripción
        num_media = _as_int(request.form.get("NumMedia","0"), 0)
        if num_media > 0:
            for i in range(num_media):
                ct = request.form.get(f"MediaContentType{i}", "") or ""
                url = request.form.get(f"MediaUrl{i}", "") or ""
                if url and _es_audio(ct, url):
                    try:
                        audio = descargar_media_twilio(url)
                        ext = _ext_por_content_type(ct, url)
                        texto = _clean(transcribir_audio_bytes(audio, filename=f"audio.{ext}"))
                        if texto:
                            ctx["last_text"] = texto
                            ctx["last_intent"] = "audio"
                        tw.message(f"📝 Transcripción: {texto}")
                        return str(tw)
                    except Exception as e:
                        print(f"[transcripcion] fallo: {e}")
                        tw.message("No pude transcribir el audio ahora.")
                        return str(tw)

        # 2) Texto → procesa comandos/intenciones
        body = _clean(request.form.get("Body",""))
        if body:
            ctx["last_text"] = body
            ctx["last_intent"] = "texto"
        tw.message(responder(body, ctx))
        return str(tw)

    except Exception as e:
        print(f"[whatsapp] error: {e}")
        tw.message("Hubo un error procesando tu mensaje.")
        return str(tw)

# ========= Lógica (modo discreto, solo actúa si se lo pides) =========

CAPACIDADES = (
    "Puedo registrar ideas, perfeccionarlas cuando me lo pidas, transcribir audios, "
    "resumir, reformular, traducir, extraer tareas y planificar pasos. "
    "También puedo listar tus ideas y (si activas) enviarte recordatorios."
)
LIMITES = (
    "No tengo voz de salida; no navego la web ni accedo a tus archivos locales; "
    "memoria persistente limitada (ideas + último texto)."
)

def mejorar_basico(texto: str) -> str:
    base = _clean(texto)
    if len(base) < 10:
        return "Idea breve. Paso 1: define objetivo y una acción concreta hoy."
    return f"{base}\n\nSiguiente paso: define un resultado medible y agenda un bloque de 25 minutos."

def mejorar_llm(texto: str) -> str:
    sys = ("Eres un asistente que mejora brevemente una idea en español, "
           "concreta y con 2-4 pasos accionables. No agregues relleno.")
    usr = f"Mejora y concreta esta idea en español:\n\n{texto}"
    try:
        return llm_respond(sys, usr)
    except:
        return "🧠 " + mejorar_basico(texto)

def resumir_llm(texto: str) -> str:
    sys = "Eres conciso. Resume en 3-5 viñetas en español."
    usr = f"Resume esto:\n\n{texto}"
    try: return llm_respond(sys, usr)
    except: return _preview(texto, 200)

def reformular_llm(texto: str, tono: str = "claro y directo") -> str:
    sys = f"Eres editor. Reescribe en español, tono {tono}, sin perder información."
    usr = f"Reformula este texto:\n\n{texto}"
    try: return llm_respond(sys, usr)
    except: return mejorar_basico(texto)

def traducir_llm(texto: str, idioma: str) -> str:
    sys = "Traduce fielmente el texto al idioma indicado."
    usr = f"Idioma destino: {idioma}\n\nTexto:\n{texto}"
    try: return llm_respond(sys, usr)
    except: return f"(Sin LLM) Traducción no disponible."

def tareas_llm(texto: str) -> str:
    sys = ("Extrae una lista de tareas concretas y breves (máx 7), "
           "cada una iniciando con verbo en infinitivo. Español.")
    usr = f"Extrae tareas accionables de:\n\n{texto}"
    try: return llm_respond(sys, usr)
    except: return "• Definir objetivo\n• Crear primer borrador\n• Programar bloque de 25 min"

def plan_llm(texto: str) -> str:
    sys = ("Devuelve un plan en 3–7 pasos priorizados. Cada paso con resultado esperado. Español.")
    usr = f"Crea un plan para:\n\n{texto}"
    try: return llm_respond(sys, usr)
    except: return "1) Aclarar objetivo\n2) Dividir en subtareas\n3) Ejecutar primer bloque (25 min)"

def listar_ideas(n: int = 5) -> str:
    filas = consultar_ideas(limit=n)
    if not filas: return "No hay ideas registradas."
    out = ["🗂️ Últimas ideas:"]
    for _id, txt, fecha in filas:
        out.append(f"• {txt}  ({fecha})")
    return "\n".join(out)

def _match(cmd: str, *options: str) -> bool:
    cmd = cmd.lower()
    return any(cmd == o or cmd.startswith(o + " ") for o in options)

def _extract_after(cmd: str, prefix: str) -> str:
    return _clean(cmd[len(prefix):]) if cmd.lower().startswith(prefix + " ") else ""

def responder(texto: str, ctx: Dict[str, str]) -> str:
    t = _clean(texto)
    last = ctx.get("last_text","")

    # Preguntas de alcance/limitaciones/capacidades
    if any(k in t.lower() for k in ("limitaciones","alcance")):
        return f"📌 Alcance: {CAPACIDADES}\n⚠️ {LIMITES}"
    if any(k in t.lower() for k in ("qué puedes hacer","que puedes hacer","como me ayudas","que haces")):
        return f"🛠️ {CAPACIDADES}"

    # Ayuda / menú
    if _match(t, "ayuda","help","menu"):
        return ("Comandos:\n"
                "• idea <texto>\n"
                "• opina: <texto>  | perfecciona\n"
                "• resume  | resume: <texto>\n"
                "• reformula: <texto>\n"
                "• traduce a <idioma>: <texto (opcional)>\n"
                "• tareas  | extrae tareas\n"
                "• plan  | planifica\n"
                "• guárdala  | guardar\n"
                "• listar ideas  | resumen")

    # Listar ideas
    if _match(t, "listar ideas","resumen"):
        return listar_ideas()

    # Guardar (usa último texto)
    if _match(t, "guárdala","guardala","guardar","registrar","regístrala","registrala"):
        if not last: return "No tengo nada para guardar. Envíame la idea o un audio primero."
        guardar_idea(last, categoria="ideas", prioridad=2)
        return f"✅ Guardada: “{_preview(last)}”."

    # Idea explícita
    if t.lower().startswith("idea "):
        contenido = _extract_after(t, "idea")
        if not contenido: return "Escribe la idea después de 'idea '."
        guardar_idea(contenido, categoria="ideas", prioridad=2)
        ctx["last_text"] = contenido
        return f"✅ Guardé tu idea: “{contenido}”."

    # Perfeccionar explícito / opina:
    if t.lower().startswith("opina:"):
        contenido = _clean(t.split(":",1)[1] if ":" in t else "")
        if not contenido: return "Escribe el contenido después de 'opina:'."
        return mejorar_llm(contenido)
    if _match(t, "perfecciona","perfecciónala","perfeccionala","mejora","mejórala","mejorala"):
        if not last: return "No tengo contexto para perfeccionar. Envíame la idea o un audio primero."
        return mejorar_llm(last)

    # Resumen
    if _match(t, "resume"):
        if last and t.lower() == "resume":
            return resumir_llm(last)
        contenido = _extract_after(t, "resume")
        return resumir_llm(contenido or last or "Nada para resumir.")

    if t.lower().startswith("resume:"):
        contenido = _clean(t.split(":",1)[1] if ":" in t else "")
        return resumir_llm(contenido or last or "Nada para resumir.")

    # Reformular
    if t.lower().startswith("reformula:"):
        contenido = _clean(t.split(":",1)[1] if ":" in t else "")
        return reformular_llm(contenido or last or "Nada para reformular.")

    # Traducir
    m = re.match(r"^traduce a ([a-zA-ZñÑáéíóúü\s]+):?(.*)$", t, flags=re.I)
    if m:
        idioma = _clean(m.group(1))
        contenido = _clean(m.group(2)) or last
        if not contenido: return "No tengo texto para traducir."
        return traducir_llm(contenido, idioma)

    # Tareas
    if _match(t, "tareas") or _match(t, "extrae tareas"):
        if not last: return "No tengo texto del que extraer tareas."
        return tareas_llm(last)

    # Plan
    if _match(t, "plan") or _match(t, "planifica") or t.lower().startswith("plan:"):
        contenido = _extract_after(t, "plan") if _match(t, "plan") else _clean(t.split(":",1)[1] if ":" in t else "")
        objetivo = contenido or last
        if not objetivo: return "¿Para qué tema creo el plan?"
        return plan_llm(objetivo)

    # Saludo
    if t.lower() in ("hola","hola jarvis","buenas","hey","ola"):
        return "¿Qué hacemos? Puedes decir: idea <texto>, perfecciona, resume, tareas, plan, traducir…"

    # Texto libre: confirmar recepción (sin sugerencias)
    if not t: return "No recibí texto."
    return f"Entendido: “{_preview(t)}”."

# ========= Detección de audio =========
def _es_audio(content_type: str, url: str) -> bool:
    ct = (content_type or "").lower()
    u = (url or "").lower()
    if ct.startswith("audio"): return True
    if ct == "application/ogg": return True
    return u.endswith(".ogg") or u.endswith(".m4a") or u.endswith(".aac") or u.endswith(".mp3")

def _ext_por_content_type(content_type: str, url: str) -> str:
    ct = (content_type or "").lower()
    u = (url or "").lower()
    if "ogg" in ct or "opus" in ct or u.endswith(".ogg"): return "ogg"
    if "aac" in ct or u.endswith(".aac"): return "aac"
    if "m4a" in ct or "mp4" in ct or u.endswith(".m4a") or u.endswith(".mp4"): return "m4a"
    if "mp3" in ct or u.endswith(".mp3"): return "mp3"
    return "ogg"  # default razonable para WhatsApp

