from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os

# Inicializa Flask
app = Flask(__name__)

# Inicializa OpenAI con tu API key desde variables de entorno
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Recibir mensaje de WhatsApp desde Twilio
        incoming_msg = request.values.get('Body', '').strip()
        print(f"Mensaje recibido: {incoming_msg}")

        # Preparar respuesta de Twilio
        resp = MessagingResponse()
        msg = resp.message()

        if incoming_msg:
            # Llamar al modelo de OpenAI
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres Jarvis, un asistente personal que responde en español."},
                    {"role": "user", "content": incoming_msg}
                ]
            )

            reply_text = completion.choices[0].message.content.strip()
            msg.body(reply_text)
        else:
            msg.body("No entendí tu mensaje 😅")

        return str(resp)

    except Exception as e:
        print(f"Error en webhook: {e}")
        resp = MessagingResponse()
        resp.message("Ocurrió un error en Jarvis 🚨")
        return str(resp)


# Flask necesita esto para correr en Render
if _name_ == "_main_":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
