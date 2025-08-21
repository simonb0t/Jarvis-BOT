# main.py
import os
from modules.whatsapp_module import app
from modules.automation_module import iniciar_automatizacion
import threading

@app.get("/")   # healthcheck
def home():
    return "Jarvis WhatsApp OK"

if __name__ == "__main__":
    print("🚀 Jarvis WhatsApp server en /whatsapp")

    # Hilo para automatizaciones
    t = threading.Thread(target=iniciar_automatizacion, daemon=True)
    t.start()

    port = int(os.getenv("PORT", 5000))  # 👈 clave en Heroku
    app.run(host="0.0.0.0", port=port)   # 👈 clave en Heroku
