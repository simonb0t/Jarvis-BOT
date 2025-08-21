from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

def procesar_mensaje(mensaje: str) -> str:
    """
    Lógica central de Jarvis para WhatsApp.
    Aquí luego integraremos memoria y voz.
    """
    text = mensaje.strip().lower()

    if "hola" in text or "buenas" in text:
        return "¡Hola! Soy Jarvis, listo para ayudarte por WhatsApp."
    elif text.startswith("idea "):
        # Ejemplo: "idea crear app de hábitos"
        contenido = mensaje[5:].strip()
        # Aquí luego llamaremos a guardar_idea(contenido)
        return f"Anoté tu idea: “{contenido}”. ¿La guardo en memoria?"
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
