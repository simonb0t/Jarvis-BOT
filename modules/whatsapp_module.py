# modules/whatsapp_module.py
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from modules.memory_module import guardar_idea
# Si ya añadiste transcripción con OpenAI:
# from modules.transcribe_module import descargar_media_twilio, transcribir_audio_bytes

app = Flask(__name__)

@app.get("/whatsapp")
def whatsapp_get():
    return "Endpoint WhatsApp OK (usa POST desde Twilio)"

def mejorar_texto_rapido(texto: str) -> str:
    base = texto.strip()
    if len(base) < 10:
        return "Idea registrada. Siguiente paso: define objetivo y una acción concreta para hoy."
    return f"{base}\n\nSiguiente paso: prioriza, define un resultado medible y un primer bloque de 25 minutos."

def procesar_mensaje_texto(mensaje: str) -> str:
    text = mensaje.strip()

    if text.lower() in ("hola", "buenas", "hey", "ola", "hola jarvis"):
        return "¡Hola! Soy Jarvis. Usa 'idea ...' para registrar o 'opina: ...' para que la perfeccione."

    if text.lower().startswith("idea "):
        contenido = text[5:].strip()
        guardar_idea(contenido, categoria="ideas", prioridad=2)
        return f"Anoté tu idea: “{contenido}”. Si quieres que la refine, escribe: opina: {contenido}"

    if text.lower().startswith("opina:"):
        contenido = text.split(":", 1)[1].strip()
        return mejorar_texto_rapido(contenido)

    return "Recibido. Si es una idea, usa: 'idea Tu idea aquí'. Para que opine: 'opina: Tu texto'."

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    tw_resp = MessagingResponse()
    try:
        # Log para ver lo que llega en Heroku logs
        print({
            "Body": request.form.get("Body", ""),
            "NumMedia": request.form.get("NumMedia", "0"),
            "MediaContentType0": request.form.get("MediaContentType0", ""),
            "MediaUrl0": request.form.get("MediaUrl0", "")
        })

        # (Si ya activaste transcripción, aquí iría el manejo de audio)
        # num_media = int(request.form.get("NumMedia", "0"))
        # if num_media > 0 and request.form.get("MediaContentType0", "").startswith("audio"):
        #     audio_bytes = descargar_media_twilio(request.form.get("MediaUrl0"))
        #     texto = transcribir_audio_bytes(audio_bytes, filename="audio.ogg")
        #     resp_text = procesar_mensaje_texto(texto)
        #     tw_resp.message(f"🎙️ Transcripción: {texto}\n\n{resp_text}")
        #     return str(tw_resp)

        # Texto normal
        body = request.form.get("Body", "")
        respuesta = procesar_mensaje_texto(body)
        tw_resp.message(respuesta)
        return str(tw_resp)

    except Exception as e:
        print(f"[whatsapp] error: {e}")
        tw_resp.message("Hubo un error procesando tu mensaje. Intenta de nuevo.")
        return str(tw_resp)
