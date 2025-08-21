# modules/whatsapp_module.py
import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from modules.memory_module import guardar_idea
from modules.voice_module import hablar_epico

app = Flask(__name__, static_url_path="/static", static_folder="static")

def mejorar_texto_rapido(texto: str) -> str:
    """
    Mini-‘actitud’ de Jarvis: pulir y sugerir siguiente paso de forma breve.
    (Aquí luego puedes enchufar un LLM si quieres más potencia.)
    """
    base = texto.strip()
    if len(base) < 10:
        return f"Idea registrada. Siguiente paso: define el objetivo y una acción concreta para hoy."
    return f"{base}\n\nSiguiente paso: prioriza, define un resultado medible y un primer bloque de 25 minutos."

def procesar_mensaje_usuario(mensaje: str) -> (str, str | None):
    """
    Devuelve (texto_respuesta, url_audio_opcional)
    """
    text = mensaje.strip()

    # Saluditos
    if text.lower() in ("hola", "buenas", "hey", "ola"):
        respuesta = "¡Hola! Soy Jarvis. Pásame ideas con el prefijo 'idea ' o pídeme opinión con 'opina:'."
        url_audio = hablar_epico("Hola. Soy Jarvis. ¿En qué te ayudo hoy?")
        return respuesta, url_audio

    # Registrar idea
    if text.lower().startswith("idea "):
        contenido = text[5:].strip()
        guardar_idea(contenido, categoria="ideas", prioridad=2)
        respuesta = f"Anoté tu idea: “{contenido}”. ¿La refino? Escribe: opina: {contenido}"
        url_audio = hablar_epico(f"Anoté tu idea. {contenido}. ¿Quieres que la refine ahora?")
        return respuesta, url_audio

    # Opinar/Perfeccionar
    if text.lower().startswith("opina:"):
        contenido = text.split(":", 1)[1].strip()
        mejora = mejorar_texto_rapido(contenido)
        url_audio = hablar_epico(f"Mi sugerencia: {mejora}")
        return mejora, url_audio

    # Default: eco + invitación a formato
    respuesta = "Recibido. Si es una idea, usa: 'idea Tu idea aquí'. Para que opine: 'opina: Tu texto'."
    url_audio = hablar_epico("Mensaje recibido. Si es una idea, comienza con 'idea'.")
    return respuesta, url_audio

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    msg = request.form.get("Body", "")
    texto, url_audio = procesar_mensaje_usuario(msg)

    tw_resp = MessagingResponse()

    # 1) Mensaje de texto
    tw_resp.message(texto)

    # 2) Mensaje con audio (si se generó)
    if url_audio:
        msg_audio = tw_resp.message("🎧 Audio:")
        msg_audio.media(url_audio)

    return str(tw_resp)
    # al inicio ya tienes app = Flask(__name__, ...)

@app.get("/whatsapp")
def whatsapp_get():
    return "Endpoint WhatsApp OK (use POST desde Twilio)"

