from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import speech_recognition as sr
import os

app = Flask(__name__)

# Ruta base solo para comprobar que el server está vivo
@app.route("/")
def home():
    return "Jarvis online 🚀"

# Endpoint de WhatsApp
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").lower()
    resp = MessagingResponse()
    msg = resp.message()

    if "hola" in incoming_msg:
        msg.body("Hola, soy Jarvis. ¿En qué te ayudo?")
    elif "idea" in incoming_msg:
        msg.body("Perfecto, anoto tu idea 💡")
    else:
        msg.body("No entendí bien, ¿puedes repetir?")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
