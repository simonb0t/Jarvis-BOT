from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI

# Inicializamos Flask y OpenAI
app = Flask(_name_)
client = OpenAI()

# Ruta webhook de Twilio
@app.route("/webhook", methods=["POST"])
def webhook():
    # Capturar el mensaje que manda el usuario
    incoming_msg = request.values.get("Body", "").strip()

    # Crear la respuesta de Twilio
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg:
        try:
            # Generar respuesta con OpenAI
            respuesta = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Puedes usar gpt-4o-mini si quieres
                messages=[
                    {"role": "system", "content": "Eres Jarvis, un asistente útil y amigable."},
                    {"role": "user", "content": incoming_msg}
                ]
            )

            reply_text = respuesta.choices[0].message.content.strip()
            msg.body(reply_text)

        except Exception as e:
            msg.body(f"Ocurrió un error: {str(e)}")
    else:
        msg.body("No entendí tu mensaje, ¿puedes repetirlo?")

    return str(resp)

# Ruta raíz de prueba
@app.route("/", methods=["GET"])
def home():
    return "✅ Jarvis está corriendo en Render con Twilio WhatsApp."

# Iniciar servidor
if _name_ == "_main_":
    app.run(host="0.0.0.0", port=5000)
