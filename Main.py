from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os

# Inicializa Flask
app = Flask(__name__)

# Configura tu clave de OpenAI (puedes usar variables de entorno en Render)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/webhook", methods=["POST"])
def webhook():
    # Recibe el mensaje entrante de WhatsApp
    incoming_msg = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")

    # Prepara la respuesta Twilio
    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg:
        try:
            # Llama a OpenAI para generar la respuesta
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres Jarvis, el asistente personal del usuario. Responde de forma clara y útil."},
                    {"role": "user", "content": incoming_msg}
                ]
            )

            reply_text = completion.choices[0].message["content"].strip()
        except Exception as e:
            reply_text = f"⚠️ Error procesando tu mensaje: {str(e)}"
    else:
        reply_text = "Hola, soy Jarvis. ¿En qué puedo ayudarte?"

    # Responde al usuario en WhatsApp
    msg.body(reply_text)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
