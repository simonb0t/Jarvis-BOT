# main.py
import os
from modules.whatsapp_module import app
from modules.automation_module import iniciar_automatizacion
import threading

# Healthcheck raíz (para probar en el browser)
@app.get("/")
def home():
    return "Jarvis WhatsApp OK"

if __name__ == "__main__":
    print("🚀 Jarvis WhatsApp server en /whatsapp")

    # Lanzar automatizaciones (resumen diario) en un hilo aparte
    t = threading.Thread(target=iniciar_automatizacion, daemon=True)
    t.start()

    # Heroku asigna el puerto en la variable de entorno PORT
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
