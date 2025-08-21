from flask import Flask
from modules.whatsapp_module import whatsapp_bp

app = Flask(__name__)
app.register_blueprint(whatsapp_bp)

@app.route("/")
def home():
    return "🤖 Jarvis WhatsApp activo."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
