# index.py
import os
from modules.whatsapp_module import app
from modules.automation_module import iniciar_automatizacion if False else None  # si aún no usas automation, ignóralo
import threading

@app.get("/")
def home():
    return "Jarvis WhatsApp OK"

if __name__ == "__main__":
    # (Si luego quieres el resumen diario, descomenta estas dos líneas)
    # t = threading.Thread(target=iniciar_automatizacion, daemon=True)
    # t.start()

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
