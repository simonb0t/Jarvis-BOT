# modules/whatsapp_module.py
import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from modules.memory_module import guardar_idea, consultar_ideas
from modules.transcribe_module import descargar_media_twilio, transcribir_audio_bytes

app = Flask(__name__)

@app.get("/")
def home():
    return "Jarvis WhatsApp OK"

@app.get("/whatsapp")
def whatsapp_get():
    return "Endpoint WhatsApp OK (usa POST desde Twilio)"

# ---------- Utilidades de respuesta ----------

def mejorar_texto_rapido(texto: str) -> str:
    base = texto.strip()
    if len(base) < 10:
        return "Idea registrada. Siguiente paso: define objetivo y una acción concreta para hoy."
    return f"{base}\n\nSiguiente paso: prioriza, define un resultado medible y un primer bloque de 25 minutos."

def listar_ultimas_ideas(n=5) -> str:
    filas = consultar_ideas(limit=n)
    if not filas:
        return "Aún no tienes ideas registradas."
    out = ["🗂️ Últimas ideas:"]
    for _id, txt, fecha in filas:
        out.append(f"• {txt}  ({fecha})")
    return "\n".join(out)

def respuesta_inteligente(texto: str) -> str:
    """
    Responde menos hermético: reconoce, refleja y propone acción concreta.
    Comandos:
      - 'idea ...'
      - 'opina: ...'
      - 'listar ideas' / 'resumen'
      - 'ayuda'
    """
    t = (texto or "").strip()
    low = t.lower()

    # ---- comandos ----
    if low in ("ayuda", "help", "menu"):
        return ("📖 Comandos:\n"
                "• idea <texto> → guardo tu idea\n"
                "• opina: <texto> → la perfecciono y te doy siguiente paso\n"
                "• listar ideas / resumen → te muestro las últimas\n"
                "También puedes mandarme un audio: lo transcribo y actúo.")

    if low in ("listar ideas", "resumen"):
        return listar_ultimas_ideas()

    if low.startswith("idea "):
        contenido = t[5:].strip()
        if not contenido:
            return "Escribe la idea después de 'idea '. Ej: idea crear app de hábitos."
        guardar_idea(contenido, categoria="ideas", prioridad=2)
        return (f"✅ Guardé tu idea: “{contenido}”.\n"
                f"➡️ ¿La refino ahora? Escribe: opina: {contenido}")

    if low.startswith("opina:"):
        contenido = t.split(":", 1)[1].strip()
        if not contenido:
            return "Escribe el contenido después de 'opina:'."
        return "🧠 " + mejorar_texto_rapido(contenido)

    if low in ("hola", "hola jarvis", "buenas", "hey", "ola"):
        return ("👋 ¡Hola! Dime tu idea con: `idea ...` o pídeme mejora con: `opina: ...`.\n"
                "También puedes mandarme un audio y lo transcribo.")

    # ---- no-comando: reconoce + opciones ----
    preview = (t[:180] + "…") if len(t) > 180 else t
    if not preview:
        return "No recibí texto. Prueba 'ayuda' o envíame un audio."
    return (f"🎧 Entendí esto: “{preview}”.\n"
            f"• Guardarla como idea: `idea {t}`\n"
            f"• Perfeccionarla: `opina: {t}`\n"
            f"• Ver tus ideas: `listar ideas`")

# ---------- Detección de audio ----------

def _es_audio(content_type: str, url: str) -> bool:
    """
    WhatsApp/Twilio puede mandar:
      - audio/ogg ; audio/ogg; codecs=opus ; application/ogg
      - audio/aac ; audio/m4a ; audio/mp4
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
    return "ogg"  # por defecto suele ser voz de WhatsApp (opus/ogg)

# ---------- Webhook principal ----------

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    tw_resp = MessagingResponse()
    try:
        # Debug útil en Heroku Logs
        snapshot = {
            "Body": request.form.get("Body", ""),
            "NumMedia": request.form.get("NumMedia", "0"),
            "MediaContentType0": request.form.get("MediaContentType0", ""),
            "MediaUrl0": request.form.get("MediaUrl0", "")
        }
        print(snapshot)

        # ¿Hay media?
        num_media = int(request.form.get("NumMedia", "0") or 0)
        if num_media > 0:
            # revisamos cada media por si envías varias
            for i in range(num_media):
                ct = request.form.get(f"MediaContentType{i}", "")
                url = request.form.get(f"MediaUrl{i}", "")
                if url and _es_audio(ct, url):
                    try:
                        audio_bytes = descargar_media_twilio(url)
                        ext = _ext_por_content_type(ct, url)
                        texto = transcribir_audio_bytes(audio_bytes, filename=f"audio.{ext}")
                        resp = respuesta_inteligente(texto)
                        tw_resp.message(f"📝 Transcripción: {texto}\n\n{resp}")
                        return str(tw_resp)
                    except Exception as e:
                        print(f"[transcripcion] fallo: {e}")
                        # si una media falla, seguimos mirando otras;
                        # si ninguna sirve, caemos a texto más abajo

        # Si no hubo audio útil, tratamos como texto
        body = request.form.get("Body", "")
        tw_resp.message(respuesta_inteligente(body))
        return str(tw_resp)

    except Exception as e:
        print(f"[whatsapp] error: {e}")
        tw_resp.message("Hubo un error procesando tu mensaje. Intenta de nuevo.")
        return str(tw_resp)
