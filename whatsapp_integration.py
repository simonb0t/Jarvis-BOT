from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    msg = request.form.get('Body')  # mensaje recibido
    response = MessagingResponse()
    
    # Aquí va tu lógica de Jarvis
    if "hola" in msg.lower():
        respuesta = "¡Hola! Soy Jarvis, tu asistente."
    else:
        respuesta = "Recibido: " + msg
    
    response.message(respuesta)
    return str(response)

if __name__ == "__main__":
    app.run(port=5000)
