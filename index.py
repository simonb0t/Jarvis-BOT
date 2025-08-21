# index.py
import os
import threading
from modules.whatsapp_module import app
from modules.automation_module import iniciar_automatizacion

# Ruta de salud (solo UNA en todo el proyecto; si ya la tienes en whatsapp_module, bórrala allí)
@app.get("/")
def health():
    return "Jarvis WhatsApp OK"

def _launch_automation():
    """Arranca las automatizaciones en un hilo y nunca tumba el server si fallan."""
    try:
        print("⏰ Iniciando automatizaciones…")
        iniciar_automatizacion()
    except Exception as e:
        print(f"[automation] error: {e}")

if __name__ == "__main__":
    # Hilo para el scheduler (resumen diario, etc.)
    t = threading.Thread(target=_launch_automation, daemon=True)
    t.start()

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
