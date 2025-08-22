import os
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.get("/")
def health():
    return jsonify({"status": "ok", "app": "Jarvis-BOT"})

@app.post("/whatsapp")
def whatsapp_webhook():
    # respuesta mínima para que Twilio reciba algo válido
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

