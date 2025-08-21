import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from whatsapp_module import send_whatsapp_reply
from agents.router import handle_text_command, handle_agent_task
from services.audio import transcribe_twilio_media

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change_me")

@app.get("/")
def health():
    return jsonify({"status": "ok", "app": "Jarvis-BOT"})

@app.post("/whatsapp")
def whatsapp_webhook():
    """
    Twilio enviará:
    - Body: texto del usuario
    - NumMedia: cantidad de adjuntos
    - MediaUrl0 / MediaContentType0: voz, imagen, etc.
    """
    from_number = request.form.get("From", "")
    body = (request.form.get("Body", "") or "").strip()
    num_media = int(request.form.get("NumMedia", 0) or 0)

    # 1) Si vienen audios, transcribimos y lo tratamos como texto
    if num_media > 0:
        media_url = request.form.get("MediaUrl0")
        media_type = request.form.get("MediaContentType0", "")
        if "audio" in media_type or media_type.endswith((".ogg", ".oga", ".mp3", ".wav")):
            text = transcribe_twilio_media(media_url)
            if not text:
                send_whatsapp_reply("No pude transcribir el audio. ¿Puedes intentar de nuevo?", from_number)
                return ("", 200)
            body = f"[voz→texto]\n{text}"

    # 2) Comandos de alto nivel para gestionar agentes
    # Formatos soportados (simples y prácticos por WhatsApp):
    # - crear agente: <nombre> | <descripción>
    # - listar agentes
    # - usar agente: <id> | <tarea>
    # - buscar: <query>   (usa tu web_search_module)
    # - recordar: <texto> (guarda en memoria)
    # - buscar en memoria: <keyword>
    try:
        reply = handle_text_command(body)
        if reply is None:
            # Si no era comando, lo interpretamos como "tarea para el agente por defecto"
            reply = handle_agent_task(body)
    except Exception as e:
        reply = f"Ocurrió un error: {e}"

    send_whatsapp_reply(reply, from_number)
    return ("", 200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

