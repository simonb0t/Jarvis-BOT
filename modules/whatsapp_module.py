# modules/whatsapp_module.py
import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from modules.memory_module import guardar_idea
from modules.transcribe_module import descargar_media_twilio, transcribir_audio_bytes

app = Flask(__name__)

@app.get("/")
def home():
    return "Jarvis WhatsApp OK"

@app.get("/whatsapp")
def whatsapp_get():
    return "Endpoint WhatsApp OK (usa POST desde Twilio)"

# --- Utilidades de respuesta ---

def mejorar_texto_rapido(texto: str) -> str:
    base = texto.strip()
    if len(base) < 10:
        return "Idea registrada. Siguiente paso: define objetivo y una acción concreta para hoy."
    return f"{base}\n\nSiguiente paso: prioriza, define un resultado medible y un primer bloque de 25 minutos."

def respuesta_inteligente(texto: str) -> str:
    """Responde menos hermético: reconoce, refleja y propone acción concreta."""
    t = texto.strip()

    # Comandos
    low = t.lower()
    if low.startswith("idea "):
        contenido = t[5:].strip()
        guardar_idea(contenido, categoria="ideas", prioridad=2)
        return (
            f"✅ Entendí tu idea y la guardé: “{contenido}”.\n"
            f"➡️ ¿La refino ahora? Escribe: opina: {contenido}"
        )
    if low.startswith("opina:"):
        contenido = t.split(":", 1)[1].strip()
        return "🧠 " + mejorar_texto_rapido(contenido)
    if low in ("hola", "hola jarvis", "buenas", "hey", "ola"):
        return ("👋 ¡Hola! Dime tu idea con: `idea ...` o pídeme mejora con: `opina: ...`.\n"
                "También puedes mandarme un audio y lo transcribo.")

    # No-comando: reconoce + sugiere guardar como idea
    preview = (t[:180] + "…") if len(t) > 180 else t
    return (
        f"🎧 Entendí esto: “{preview}”.\n"
        f"Si quieres, la guardo como idea. Envía: `idea {t}`\n"
        f"Para pulirla: `opina: {t}`"
    )

# --- Webhook principal ---

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    tw_resp = MessagingResponse()
    try:
        # Debug en logs (Heroku → More → View logs)
        print({
            "Body": request.form.get("Body", ""),
            "NumMedia": request.form.get("NumMedia", "0"),
            "MediaContentType0": request.form.get("MediaContentType0", ""),
            "MediaUrl0": request.form.get("MediaUrl0", "")
        })

        num_media = int(request.form.get("NumMedia", "0") or 0)

        # 1) Si viene audio, lo transcribimos y respondemos sobre esa transcripción
        if num_media > 0:
            content_type = request.form.get("MediaContentType0", "")
            media_url = request.form.get("MediaUrl0", "")
            if media_url and content_type.startswith("audio"):
                try:
                    audio_bytes = descargar_media_twilio(media_url)
                    ext = "ogg" if ("ogg" in content_type or "opus" in content_type) else "mp3"
                    texto = transcribir_audio_bytes(audio_bytes, filename=f"audio.{ext}")
                    respuesta = respuesta_inteligente(texto)
                    tw_resp.message(f"📝 Transcripción: {texto}\n\n{respuesta}")
                    return str(tw_resp)
                except Exception as e:
                    print(f"[transcripcion] fallo: {e}")
                    tw_resp.message("No pude transcribir el audio ahora. ¿Puedes mandarlo en texto o intentarlo de nuevo?")
                    return str(tw_resp)

        # 2) Si no hay audio, tratamos como texto normal
        body = request.form.get("Body", "")
        respuesta = respuesta_inteligente(body)
        tw_resp.message(respuesta)
        return str(tw_resp)

    except Exception as e:
        print(f"[whatsapp] error: {e}")
        tw_resp.message("Hubo un error procesando tu mensaje. Intenta de nuevo.")
        return str(tw_resp)
