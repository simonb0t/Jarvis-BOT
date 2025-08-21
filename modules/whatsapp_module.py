from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from modules.memory_module import guardar_idea

app = Flask(__name__)

def procesar_mensaje(mensaje: str) -> str:
    """
    Lógica de Jarvis para WhatsApp:
    - Reconoce saludo
    - Guarda ideas
    - Responde por defecto
    """
    text = mensaje.strip().lower()

    if "hola" in text or "buenas" in text:
        return "¡Hola! Soy Jarvis, listo para ayudarte por WhatsApp."

    elif text.startswith("idea "):
        contenido = mensaje[5:].strip()
        guardar_idea(contenido)  # Guardamos en la base de datos
        return f"Anoté tu idea: “{contenido}” ✅"

    else:
        return f"Recibido: {mensaje}"

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    msg = request.form.get("Body", "")
    respuesta = procesar_mensaje(msg)

    twilio_resp = MessagingResponse()
    twilio_resp.message(respuesta)
    return str(twilio_resp)

if __name__ == "__main__":
    app.run(port=5000)
