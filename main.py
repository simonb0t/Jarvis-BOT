from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI

import os

app = Flask(__name__)

# Inicializar cliente de OpenAI con tu API KEY
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get('Body', '').strip()
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg:
        try:
            # Llamada al modelo de Chat de OpenAI
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres Jarvis, un asistente útil en WhatsApp."},
                    {"role": "user", "content": incoming_msg}
                ]
            )
            respuesta = completion.choices[0].message.content.strip()
            msg.body(respuesta)

        except Exception as e:
            msg.body(f"Ocurrió un error: {e}")
    else:
        msg.body("No entendí tu mensaje 🤔")

    return str(resp)


if _name_ == "_main_":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
