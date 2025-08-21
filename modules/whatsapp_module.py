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
    return "Endpoint WhatsApp OK (POST desde Twilio)"

def mejorar_texto_rapido(texto: str) -> str:
    base = texto.strip()
    if len(base) < 10:
        return "Idea registrada. Siguiente paso: define objetivo y una acción concreta para hoy."
    return f"{base}\n\nSiguiente paso: prioriza, define un resultado medible y un primer bloque de 25 minutos."

def procesar_mensaje_texto(mensaje: str) -> str:
    text = mensaje.strip()

    # Saluditos
    if text.lower() in ("hola", "buenas", "hey", "ola", "hola jarvis"):
        return "¡Hola! Soy Jarvis. Usa 'idea ...' para registrar o 'opina: ...' para que la perfeccione."

    # Registrar idea
    if text.lower().startswith("idea "):
        contenido = text[5:].strip()
        guardar_idea(contenido, categoria="ideas", prioridad=2)
        return f"Anoté tu idea: “{contenido}”. Si quieres que la refine, escribe: opina: {contenido}"

    # Opinar/Perfeccionar
    if text.lower().startswith("opina:"):
        contenido = text.split(":", 1)[1].strip()
        mejora = mejorar_texto_rapido(contenido)
        return mejora

    # Default
    return "Recibido. Si es una idea, usa: 'idea Tu idea aquí'. Para que opine: 'opina: Tu texto'."

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    tw_resp = MessagingResponse()
    try:
        # 1) ¿Viene audio?
        num_media = int(request.form.get("NumMedia", "0"))
        if num_media > 0:
            content_type = request.form.get("MediaContentType0", "")
            media_url = request.form.get("MediaUrl0", "")
            if content_type.startswith("audio") and media_url:
                # Descargar + transcribir
                audio_bytes = descargar_media_twilio(media_url)
                # Intenta inferir extensión por Content-Type
                ext = "ogg" if "ogg" in content_type or "opus" in content_type else "mp3"
                texto = transcribir_audio_bytes(audio_bytes, filename=f"audio.{ext}")
                # Procesarlo como texto
                respuesta = procesar_mensaje_texto(texto)
                tw_resp.message(f"🎙️ Transcripción: {texto}\n\n{respuesta}")
                return str(tw_resp)

        # 2) Si no hay audio, tratamos como texto normal
        body = request.form.get("Body", "")
        respuesta = procesar_mensaje_texto(body)
        tw_resp.message(respuesta)
        return str(tw_resp)

    except Exception as e:
        # Nunca rompas el webhook: responde algo útil y loguea
        print(f"[whatsapp] error: {e}")
        tw_resp.message("Hubo un error procesando tu mensaje. Intenta de nuevo.")
        return str(tw_resp)
